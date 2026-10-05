from decimal import Decimal
import hashlib
import hmac
import json

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Customer, MobileMoneyPayment, Order, OrderItem, Product, PromoCode


class CommerceIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='strong-password-123')
        self.customer = self.user.customer
        self.product = Product.objects.create(
            name='Matoke',
            price=Decimal('5000.00'),
            stock=5,
            is_active=True,
        )

    def make_order(self, quantity=2):
        order = Order.objects.create(customer=self.customer)
        OrderItem.objects.create(order=order, product=self.product, quantity=quantity)
        return order

    def test_order_item_preserves_purchase_price(self):
        order = self.make_order(quantity=1)
        item = order.items.get()
        self.product.price = Decimal('9000.00')
        self.product.save(update_fields=['price'])
        item.refresh_from_db()
        self.assertEqual(item.price_at_purchase, Decimal('5000.00'))
        self.assertEqual(item.get_total, Decimal('5000.00'))

    def test_payment_completion_decrements_stock_once(self):
        order = self.make_order(quantity=2)
        self.assertTrue(order.mark_as_paid('TX-001', 'mobile_money_mtn'))
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertTrue(order.complete)
        self.assertEqual(order.payment_status, 'completed')
        self.assertFalse(order.mark_as_paid('TX-001', 'mobile_money_mtn'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_payment_completion_rejects_overselling(self):
        order = self.make_order(quantity=6)
        with self.assertRaises(Exception):
            order.mark_as_paid('TX-002', 'mobile_money_mtn')
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertFalse(order.complete)
        self.assertEqual(self.product.stock, 5)

    def test_mobile_payment_finalization_is_idempotent(self):
        order = self.make_order(quantity=1)
        payment = MobileMoneyPayment.objects.create(
            order=order,
            provider='mtn',
            phone_number='256771234567',
            amount=Decimal('5000.00'),
        )
        self.assertTrue(payment.mark_successful('PROVIDER-1'))
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'successful')
        self.assertFalse(payment.mark_successful('PROVIDER-1'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)


class PaymentEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='payer', password='strong-password-123')
        self.client = Client()
        self.client.login(username='payer', password='strong-password-123')
        product = Product.objects.create(name='Coffee', price=Decimal('10000.00'), stock=10)
        self.order = Order.objects.create(customer=self.user.customer)
        OrderItem.objects.create(order=self.order, product=product, quantity=1)

    def test_initiation_rejects_client_amount_tampering(self):
        response = self.client.post(
            reverse('momo_initiate'),
            data=json.dumps({'phone': '0771234567', 'amount': '1', 'provider': 'mtn'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('does not match', response.json()['message'])

    @override_settings(MOMO_WEBHOOK_SECRET='test-webhook-secret')
    def test_webhook_rejects_invalid_signature(self):
        response = self.client.post(
            reverse('momo_callback'),
            data=json.dumps({'reference': 'missing', 'status': 'successful'}),
            content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE='invalid',
        )
        self.assertEqual(response.status_code, 401)

    @override_settings(MOMO_WEBHOOK_SECRET='test-webhook-secret')
    def test_webhook_accepts_valid_signature_for_known_payment(self):
        payment = MobileMoneyPayment.objects.create(
            order=self.order,
            provider='mtn',
            phone_number='256771234567',
            amount=Decimal('10000.00'),
            external_reference='AGRI-TEST-1',
        )
        payload = json.dumps({
            'reference': payment.external_reference,
            'status': 'successful',
            'amount': '10000.00',
            'currency': 'UGX',
            'transactionId': 'PROVIDER-TEST-1',
        }).encode()
        signature = hmac.new(b'test-webhook-secret', payload, hashlib.sha256).hexdigest()
        response = self.client.post(
            reverse('momo_callback'),
            data=payload,
            content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'successful')


class PromotionIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='promo-user', password='strong-password-123')
        self.customer = self.user.customer
        self.product = Product.objects.create(name='Beans', price=Decimal('20000.00'), stock=10)
        self.order = Order.objects.create(customer=self.customer)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)
        from django.utils import timezone
        self.promo = PromoCode.objects.create(
            code='WELCOME10',
            discount_type='percentage',
            discount_value=Decimal('10'),
            max_uses=1,
            max_uses_per_user=1,
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_until=timezone.now() + timezone.timedelta(days=1),
        )

    def test_promo_redemption_is_ledgered_and_usage_is_counted(self):
        from .services.promotions import redeem_promo
        redemption = redeem_promo(self.promo, self.customer, self.order, Decimal('20000'))
        self.assertEqual(redemption.discount_amount, Decimal('2000'))
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.times_used, 1)
        valid, message = self.promo.is_valid(Decimal('20000'), self.customer)
        self.assertFalse(valid)
        self.assertIn('usage limit', message.lower())
