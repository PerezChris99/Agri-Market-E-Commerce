import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from ecommerce.middleware import RequestIDMiddleware
from store.forms import CheckoutForm, CreateUserForm
from store.models import (
    AuditLog,
    Category,
    Customer,
    Delivery,
    DeliveryLocation,
    DeliveryRider,
    DeliveryZone,
    MobileMoneyPayment,
    Order,
    OrderItem,
    Product,
    PromoCode,
    PromoRedemption,
    SellerOrder,
    SellerProfile,
    Wishlist,
)
from store.services.delivery import update_location, update_status
from store.services.orders import finalize_order
from store.services.promos import redeem_promo


class UserFactoryMixin:
    def make_user(self, username='user', password='StrongPassword123!'):
        user = User.objects.create_user(username=username, password=password, email=f'{username}@example.com')
        return user, user.customer

    def make_product(self, *, name='Tomatoes', price='5000.00', stock=20, seller=None, digital=False):
        category = Category.objects.get_or_create(name='Vegetables', slug='vegetables')[0]
        return Product.objects.create(
            name=name,
            price=Decimal(price),
            stock=stock,
            category=category,
            seller=seller,
            digital=digital,
        )

    def make_order(self, customer, product=None, quantity=1):
        order = Order.objects.create(customer=customer)
        if product is not None:
            OrderItem.objects.create(order=order, product=product, quantity=quantity)
        return order


class FormTests(TestCase):
    def test_checkout_form_accepts_common_uganda_phone_formats(self):
        for phone in ('0700123456', '+256700123456', '0700 123 456', '+256 700-123-456'):
            form = CheckoutForm(data={
                'name': 'Customer',
                'email': 'customer@example.com',
                'phone': phone,
                'address': 'Kampala Road',
                'city': 'Kampala',
                'region': 'Central',
                'country': 'Uganda',
            })
            self.assertTrue(form.is_valid(), form.errors)

    def test_checkout_form_rejects_invalid_phone(self):
        form = CheckoutForm(data={
            'name': 'Customer',
            'email': 'customer@example.com',
            'phone': 'not-a-phone',
            'address': 'Kampala Road',
            'city': 'Kampala',
            'region': 'Central',
            'country': 'Uganda',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_registration_requires_email_and_strong_password(self):
        form = CreateUserForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'short',
            'password2': 'short',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        User.objects.create_user(username='existing', email='User@Example.com', password='StrongPassword123!')
        form = CreateUserForm(data={
            'username': 'newuser',
            'email': 'user@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class OrderReliabilityTests(UserFactoryMixin, TestCase):
    def test_paid_order_decrements_inventory_once(self):
        _, customer = self.make_user()
        product = self.make_product(stock=5)
        order = self.make_order(customer, product, 2)

        self.assertTrue(order.mark_as_paid('TX-1', 'paypal'))
        product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(product.stock, 3)
        self.assertTrue(order.complete)
        self.assertTrue(order.inventory_committed)

        self.assertFalse(order.mark_as_paid('TX-2', 'paypal'))
        product.refresh_from_db()
        self.assertEqual(product.stock, 3)

    def test_paid_order_rejects_empty_order(self):
        _, customer = self.make_user()
        order = self.make_order(customer)
        with self.assertRaises(ValidationError):
            order.mark_as_paid('TX-empty')

    def test_cod_rejects_empty_order(self):
        _, customer = self.make_user()
        order = self.make_order(customer)
        with self.assertRaises(ValidationError):
            order.place_cash_on_delivery()

    def test_cod_commits_inventory_but_leaves_payment_pending(self):
        _, customer = self.make_user()
        product = self.make_product(stock=4)
        order = self.make_order(customer, product, 2)

        self.assertTrue(order.place_cash_on_delivery())
        product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(product.stock, 2)
        self.assertEqual(order.payment_status, 'pending')
        self.assertTrue(order.complete)
        self.assertTrue(order.inventory_committed)

    def test_cancel_releases_committed_inventory_only_once(self):
        _, customer = self.make_user()
        product = self.make_product(stock=4)
        order = self.make_order(customer, product, 2)
        order.place_cash_on_delivery()

        self.assertTrue(order.cancel())
        product.refresh_from_db()
        self.assertEqual(product.stock, 4)
        self.assertFalse(order.cancel())
        product.refresh_from_db()
        self.assertEqual(product.stock, 4)

    def test_delivered_order_cannot_be_cancelled(self):
        _, customer = self.make_user()
        product = self.make_product()
        order = self.make_order(customer, product)
        order.place_cash_on_delivery()
        order.status = 'delivered'
        order.save(update_fields=['status'])

        with self.assertRaises(ValidationError):
            order.cancel()

    def test_price_is_snapshotted_on_order_item(self):
        _, customer = self.make_user()
        product = self.make_product(price='1000.00')
        order = self.make_order(customer, product)
        item = order.items.get()
        product.price = Decimal('2500.00')
        product.save(update_fields=['price'])
        item.refresh_from_db()
        self.assertEqual(item.price_at_purchase, Decimal('1000.00'))
        self.assertEqual(item.get_total, Decimal('1000.00'))

    def test_seller_settlement_is_materialized(self):
        user, customer = self.make_user()
        seller = SellerProfile.objects.create(
            customer=customer,
            business_name='Kampala Farms',
            commission_rate=Decimal('10.00'),
            verification_status='verified',
        )
        product = self.make_product(price='10000.00', seller=customer)
        order = self.make_order(customer, product, 2)
        order.mark_as_paid('TX-SELLER')

        settlement = SellerOrder.objects.get(order=order, seller=seller)
        self.assertEqual(settlement.subtotal, Decimal('20000.00'))
        self.assertEqual(settlement.commission_amount, Decimal('2000.00'))
        self.assertEqual(settlement.seller_amount, Decimal('18000.00'))
        self.assertEqual(order.items.get().seller_order_id, settlement.id)

    def test_insufficient_stock_rolls_back_entire_payment(self):
        _, customer = self.make_user()
        product = self.make_product(stock=1)
        order = self.make_order(customer, product, 2)

        with self.assertRaises(ValidationError):
            order.mark_as_paid('TX-NOSTOCK')

        product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(product.stock, 1)
        self.assertFalse(order.complete)
        self.assertEqual(order.payment_status, 'pending')

    def test_finalize_order_is_idempotent(self):
        _, customer = self.make_user()
        product = self.make_product(stock=5)
        order = self.make_order(customer, product, 1)
        first = finalize_order(order_id=order.pk, payment_method='paypal', transaction_id='PAY-1')
        second = finalize_order(order_id=order.pk, payment_method='paypal', transaction_id='PAY-2')
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        product.refresh_from_db()
        self.assertEqual(product.stock, 4)


class PaymentTests(UserFactoryMixin, TestCase):
    @override_settings(MOMO_WEBHOOK_SECRET='test-secret')
    def test_authenticated_webhook_completes_payment_and_order(self):
        _, customer = self.make_user()
        product = self.make_product(stock=5)
        order = self.make_order(customer, product, 1)
        payment = MobileMoneyPayment.objects.create(
            order=order,
            provider='mtn',
            phone_number='256700123456',
            amount=order.get_cart_total,
            external_reference='EXT-123',
        )
        payload = {
            'reference': 'EXT-123',
            'provider_reference': 'PROV-123',
            'status': 'successful',
            'amount': str(payment.amount),
            'currency': 'UGX',
        }
        body = json.dumps(payload).encode()
        signature = hmac.new(b'test-secret', body, hashlib.sha256).hexdigest()

        response = self.client.post(
            reverse('momo_callback'),
            data=body,
            content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(payment.status, 'successful')
        self.assertTrue(order.complete)

    @override_settings(MOMO_WEBHOOK_SECRET='test-secret')
    def test_webhook_rejects_invalid_signature(self):
        response = self.client.post(
            reverse('momo_callback'),
            data=json.dumps({'status': 'successful'}).encode(),
            content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE='wrong',
        )
        self.assertEqual(response.status_code, 401)

    @override_settings(MOMO_WEBHOOK_SECRET='test-secret')
    def test_webhook_rejects_amount_mismatch(self):
        _, customer = self.make_user()
        product = self.make_product(stock=5)
        order = self.make_order(customer, product, 1)
        payment = MobileMoneyPayment.objects.create(
            order=order,
            provider='mtn',
            phone_number='256700123456',
            amount=order.get_cart_total,
            external_reference='EXT-456',
        )
        payload = {
            'reference': 'EXT-456',
            'status': 'successful',
            'amount': '1',
            'currency': 'UGX',
        }
        body = json.dumps(payload).encode()
        signature = hmac.new(b'test-secret', body, hashlib.sha256).hexdigest()
        response = self.client.post(
            reverse('momo_callback'),
            data=body,
            content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 400)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')

    def test_payment_status_is_private_to_order_owner(self):
        owner, customer = self.make_user('owner')
        _, other_customer = self.make_user('other')
        product = self.make_product()
        order = self.make_order(customer, product)
        payment = MobileMoneyPayment.objects.create(
            order=order,
            provider='mtn',
            phone_number='256700123456',
            amount=order.get_cart_total,
        )
        self.client.force_login(other_customer.user)
        response = self.client.get(reverse('momo_status'), {'payment_id': payment.id})
        self.assertEqual(response.status_code, 403)


class AuthorizationTests(UserFactoryMixin, TestCase):
    def test_order_detail_is_scoped_to_authenticated_customer(self):
        _, owner = self.make_user('owner')
        _, other = self.make_user('other')
        product = self.make_product()
        order = self.make_order(owner, product)
        order.order_id = 'AGR-PRIVATE-ORDER'
        order.save(update_fields=['order_id'])

        self.client.force_login(other.user)
        response = self.client.get(reverse('order_detail', kwargs={'order_id': order.order_id}))
        self.assertEqual(response.status_code, 404)

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_dashboard_rejects_non_staff(self):
        _, customer = self.make_user()
        self.client.force_login(customer.user)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('homepage'))

    def test_dashboard_allows_staff(self):
        user = User.objects.create_user(username='staff', password='StrongPassword123!', is_staff=True)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_delivery_tracking_is_scoped(self):
        _, owner = self.make_user('owner')
        _, other = self.make_user('other')
        product = self.make_product()
        order = self.make_order(owner, product)
        delivery = Delivery.objects.create(order=order)

        self.client.force_login(other.user)
        response = self.client.get(reverse('delivery_tracking', kwargs={'order_id': order.order_id}))
        self.assertEqual(response.status_code, 403)

    def test_delivery_location_requires_assigned_rider_or_staff(self):
        _, owner = self.make_user('owner')
        _, other = self.make_user('other')
        product = self.make_product()
        order = self.make_order(owner, product)
        rider = DeliveryRider.objects.create(user=owner.user, name='Rider', phone='256700123456')
        delivery = Delivery.objects.create(order=order, rider=rider)

        self.client.force_login(other.user)
        response = self.client.post(
            reverse('delivery_location', kwargs={'order_id': order.order_id}),
            data=json.dumps({'latitude': '0.31', 'longitude': '32.58'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)


class DeliveryTests(UserFactoryMixin, TestCase):
    def setUp(self):
        self.user, self.customer = self.make_user()
        self.rider_user, _ = self.make_user('rider')
        self.rider = DeliveryRider.objects.create(user=self.rider_user, name='Rider', phone='256700000001')
        product = self.make_product()
        self.order = self.make_order(self.customer, product)
        self.delivery = Delivery.objects.create(order=self.order, rider=self.rider)

    def test_valid_location_is_recorded(self):
        update_location(
            delivery=self.delivery,
            latitude='0.3136',
            longitude='32.5811',
            accuracy=8.5,
            actor=self.rider_user,
        )
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.current_lat, Decimal('0.3136000'))
        self.assertEqual(self.delivery.current_lng, Decimal('32.5811000'))
        self.assertEqual(DeliveryLocation.objects.filter(delivery=self.delivery).count(), 1)

    def test_invalid_location_is_rejected(self):
        with self.assertRaises(ValidationError):
            update_location(
                delivery=self.delivery,
                latitude='91',
                longitude='32',
                actor=self.rider_user,
            )

    def test_unassigned_user_cannot_update_location(self):
        other, _ = self.make_user('intruder')
        with self.assertRaises(PermissionError):
            update_location(
                delivery=self.delivery,
                latitude='0',
                longitude='32',
                actor=other,
            )

    def test_rider_can_update_status(self):
        update_status(delivery=self.delivery, new_status='picked_up', actor=self.rider_user)
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, 'picked_up')
        self.assertEqual(len(self.delivery.status_history), 1)

    def test_invalid_delivery_status_is_rejected(self):
        with self.assertRaises(ValidationError):
            update_status(delivery=self.delivery, new_status='bogus', actor=self.rider_user)

    def test_delivered_delivery_cannot_move_backwards(self):
        self.delivery.status = 'delivered'
        self.delivery.save(update_fields=['status'])
        with self.assertRaises(ValidationError):
            update_status(delivery=self.delivery, new_status='in_transit', actor=self.rider_user)

    def test_delivery_tracking_timeline_marks_current_step(self):
        self.delivery.status = 'in_transit'
        self.delivery.save(update_fields=['status'])
        timeline = self.delivery.get_tracking_timeline()
        current = [step for step in timeline if step['current']]
        self.assertEqual(len(current), 1)


class PromoTests(UserFactoryMixin, TestCase):
    def make_promo(self, **kwargs):
        now = timezone.now()
        defaults = {
            'code': 'WELCOME10',
            'discount_type': 'percentage',
            'discount_value': Decimal('10'),
            'max_uses': 2,
            'max_uses_per_user': 1,
            'valid_from': now - timezone.timedelta(hours=1),
            'valid_until': now + timezone.timedelta(hours=1),
        }
        defaults.update(kwargs)
        return PromoCode.objects.create(**defaults)

    def test_atomic_redemption_creates_ledger_and_increments_usage(self):
        _, customer = self.make_user()
        product = self.make_product(price='10000')
        order = self.make_order(customer, product)
        promo = self.make_promo()

        redemption = redeem_promo(
            promo_code=promo,
            customer=customer,
            order=order,
            order_total=Decimal('10000'),
        )
        promo.refresh_from_db()
        self.assertEqual(redemption.discount_amount, Decimal('1000'))
        self.assertEqual(promo.times_used, 1)
        self.assertEqual(PromoRedemption.objects.count(), 1)

    def test_second_redemption_by_same_user_is_rejected(self):
        _, customer = self.make_user()
        product = self.make_product(price='10000')
        promo = self.make_promo()
        first = self.make_order(customer, product)
        redeem_promo(promo_code=promo, customer=customer, order=first, order_total=Decimal('10000'))
        first.place_cash_on_delivery()
        second = self.make_order(customer, product)

        with self.assertRaises(ValidationError):
            redeem_promo(promo_code=promo, customer=customer, order=second, order_total=Decimal('10000'))

    def test_promo_rejects_expired_code(self):
        _, customer = self.make_user()
        product = self.make_product()
        order = self.make_order(customer, product)
        promo = self.make_promo(valid_until=timezone.now() - timezone.timedelta(minutes=1))
        with self.assertRaises(ValidationError):
            redeem_promo(promo_code=promo, customer=customer, order=order, order_total=order.get_cart_total)

    def test_promo_rejects_wrong_order_owner(self):
        _, owner = self.make_user('owner')
        _, other = self.make_user('other')
        product = self.make_product()
        order = self.make_order(owner, product)
        promo = self.make_promo()
        with self.assertRaises(ValidationError):
            redeem_promo(promo_code=promo, customer=other, order=order, order_total=order.get_cart_total)


class MiddlewareAndHealthTests(TestCase):
    def test_request_id_is_generated_and_returned(self):
        factory = RequestFactory()
        request = factory.get('/health/live/')
        captured = {}

        def get_response(request):
            captured['request_id'] = request.request_id
            return __import__('django').http.HttpResponse('ok')

        response = RequestIDMiddleware(get_response)(request)
        self.assertTrue(captured['request_id'])
        self.assertEqual(response['X-Request-ID'], captured['request_id'])
        self.assertEqual(response['Permissions-Policy'], 'camera=(), microphone=(), geolocation=(self)')

    def test_valid_request_id_is_preserved(self):
        factory = RequestFactory()
        request = factory.get('/health/live/', HTTP_X_REQUEST_ID='client-request-123')
        response = RequestIDMiddleware(lambda request: __import__('django').http.HttpResponse('ok'))(request)
        self.assertEqual(response['X-Request-ID'], 'client-request-123')

    def test_invalid_request_id_is_replaced(self):
        factory = RequestFactory()
        request = factory.get('/health/live/', HTTP_X_REQUEST_ID='bad value with spaces')
        response = RequestIDMiddleware(lambda request: __import__('django').http.HttpResponse('ok'))(request)
        self.assertNotEqual(response['X-Request-ID'], 'bad value with spaces')
        self.assertLessEqual(len(response['X-Request-ID']), 64)

    def test_live_health_is_uncached(self):
        response = self.client.get(reverse('health_live'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])

    def test_ready_health_reports_database_and_cache(self):
        response = self.client.get(reverse('health_ready'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        self.assertEqual(response.json()['checks']['database'], 'ok')
        self.assertEqual(response.json()['checks']['cache'], 'ok')


class WishlistAndModelIntegrityTests(UserFactoryMixin, TestCase):
    def test_wishlist_is_unique_per_customer_and_product(self):
        _, customer = self.make_user()
        product = self.make_product()
        Wishlist.objects.create(customer=customer, product=product)
        with self.assertRaises(Exception):
            Wishlist.objects.create(customer=customer, product=product)

    def test_delivery_zone_free_threshold(self):
        zone = DeliveryZone.objects.create(
            name='Kampala',
            region='kampala',
            delivery_fee=Decimal('5000'),
            free_delivery_threshold=Decimal('100000'),
        )
        self.assertEqual(zone.get_delivery_fee(Decimal('50000')), Decimal('5000'))
        self.assertEqual(zone.get_delivery_fee(Decimal('100000')), Decimal('0'))

    def test_audit_event_records_actor(self):
        user, _ = self.make_user()
        event = AuditLog.objects.create(
            action='test.event',
            object_type='Order',
            object_id='123',
            actor=user,
            metadata={'safe': True},
        )
        self.assertEqual(event.actor_id, user.id)
        self.assertEqual(event.metadata, {'safe': True})

    def test_product_reduce_stock_is_atomic(self):
        _, _ = self.make_user()
        product = self.make_product(stock=3)
        self.assertTrue(product.reduce_stock(2))
        product.refresh_from_db()
        self.assertEqual(product.stock, 1)
        self.assertFalse(product.reduce_stock(2))
        product.refresh_from_db()
        self.assertEqual(product.stock, 1)


class ProductionSecurityRegressionTests(TestCase):
    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_health_endpoints_are_never_cached(self):
        for name in ('health_live', 'health_ready'):
            response = self.client.get(reverse(name))
            self.assertEqual(response['Cache-Control'], 'no-store, max-age=0')

    def test_authenticated_sensitive_pages_send_no_store(self):
        user = User.objects.create_user(username='cacheuser', password='StrongPassword123!')
        self.client.force_login(user)
        for name in ('profile', 'cart', 'wishlist'):
            response = self.client.get(reverse(name))
            self.assertIn('no-store', response.get('Cache-Control', ''))

    def test_permissions_policy_is_present_on_normal_responses(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(
            response['Permissions-Policy'],
            'camera=(), microphone=(), geolocation=(self)',
        )
