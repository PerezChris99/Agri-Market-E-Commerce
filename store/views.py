from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from ratelimit.decorators import ratelimit
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Sum, Count, F
from django.db.models.functions import TruncDate, Coalesce
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

import json
import datetime
import hashlib
import hmac
import uuid
from decimal import Decimal

from .models import (
    Customer, Product, Order, OrderItem, ShippingAddress, Category, Review, Wishlist,
    DeliveryZone, SellerProfile, PromoCode
)
from .utils import cookieCart, cartData, guestOrder, merge_cart_on_login
from .forms import CreateUserForm, CustomerProfileForm, ReviewForm, CheckoutForm

# Try to import new models (may not exist yet if migrations not run)
try:
    from .models import Testimonial, DeliveryRider, Delivery
    HOMEPAGE_MODELS_AVAILABLE = True
except ImportError:
    HOMEPAGE_MODELS_AVAILABLE = False


def homepage(request):
    """Render the storefront using annotated querysets instead of per-product review queries."""
    data = cartData(request)
    featured_products = list(
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related('category')
        .annotate(
            avg_rating=Coalesce(Avg('reviews__rating', filter=Q(reviews__is_approved=True)), 0),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
        )[:8]
    )

    if len(featured_products) < 4:
        featured_products = list(
            Product.objects.filter(is_active=True)
            .select_related('category')
            .annotate(
                avg_rating=Coalesce(Avg('reviews__rating', filter=Q(reviews__is_approved=True)), 0),
                review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
            )
            .order_by('-avg_rating', '-created_at')[:8]
        )

    latest_products = list(
        Product.objects.filter(is_active=True)
        .select_related('category')
        .annotate(
            avg_rating=Coalesce(Avg('reviews__rating', filter=Q(reviews__is_approved=True)), 0),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
        )
        .order_by('-created_at')[:4]
    )

    categories = list(
        Category.objects.filter(is_active=True)
        .annotate(product_count=Count('products', filter=Q(products__is_active=True)))
        .order_by('name')[:6]
    )

    stats = cache.get('homepage:stats')
    if stats is None:
        stats = {
            'products': Product.objects.filter(is_active=True).count(),
            'farmers': SellerProfile.objects.count(),
            'orders': Order.objects.filter(complete=True).count(),
            'districts': DeliveryZone.objects.filter(is_active=True).values('name').distinct().count(),
        }
        cache.set('homepage:stats', stats, 60)

    testimonials = []
    if HOMEPAGE_MODELS_AVAILABLE:
        testimonials = list(
            Testimonial.objects.filter(is_active=True).order_by('-created_at')[:6]
        )

    return render(request, 'store/homepage.html', {
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'testimonials': testimonials,
        'flash_deals': [],
        'stats': stats,
        'cartItems': data['cartItems'],
    })


def store(request):
    """Main store view with products listing, filtering, and search"""
    data = cartData(request)
    cartItems = data['cartItems']
    
    # Get filter parameters
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', 'newest')
    
    # Base queryset - only active products
    products = Product.objects.filter(is_active=True)
    
    # Filter by category
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    # Search functionality
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query[:100]) |
            Q(description__icontains=search_query[:100]) |
            Q(category__name__icontains=search_query[:100])
        )
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:  # newest
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    # Get categories for filter sidebar
    categories = Category.objects.filter(is_active=True).only('name', 'slug')
    
    # Get featured products
    featured_products = Product.objects.filter(is_active=True, is_featured=True).select_related('category')[:4]
    
    context = {
        "products": products,
        "categories": categories,
        "featured_products": featured_products,
        "cartItems": cartItems,
        "current_category": category_slug,
        "search_query": search_query,
        "sort_by": sort_by,
    }
    return render(request, "store/store.html", context)


def product_detail(request, slug):
    """Single product detail view"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    data = cartData(request)
    cartItems = data['cartItems']
    
    # Get related products from same category
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).select_related('category')[:4]
    
    # Get reviews
    reviews = product.reviews.filter(is_approved=True).select_related('customer__user').order_by('-created_at')
    review_page = Paginator(reviews, 10).get_page(request.GET.get('review_page'))
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Check if user can review (must have purchased and not already reviewed)
    can_review = False
    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__customer=request.user.customer,
            order__complete=True,
            product=product
        ).exists()
        has_reviewed = Review.objects.filter(
            customer=request.user.customer,
            product=product
        ).exists()
        can_review = has_purchased and not has_reviewed
    
    # Check if product is in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            customer=request.user.customer,
            product=product
        ).exists()
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': review_page,
        'review_page': review_page,
        'avg_rating': round(avg_rating, 1),
        'review_count': reviews.count(),
        'can_review': can_review,
        'in_wishlist': in_wishlist,
        'cartItems': cartItems,
    }
    return render(request, 'store/product_detail.html', context)


@login_required(login_url="/login/")
def cart(request):
    """Shopping cart view"""
    data = cartData(request, create=True)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    context = {
        'items': items, 
        'order': order, 
        'cartItems': cartItems
    }
    return render(request, 'store/cart.html', context)


@require_POST
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def updateItem(request):
    """Update an authenticated database cart safely under concurrency."""
    try:
        data = json.loads(request.body or '{}')
        product_id = int(data.get('productId'))
        action = str(data.get('action', '')).lower()
        if action not in {'add', 'remove'}:
            return JsonResponse({'success': False, 'message': 'Invalid cart action.'}, status=400)

        if not request.user.is_authenticated:
            return JsonResponse({'success': True, 'message': 'Cookie cart updated', 'useCookies': True})

        with transaction.atomic():
            customer = request.user.customer
            order, _ = Order.objects.get_or_create(customer=customer, complete=False)
            product = get_object_or_404(
                Product.objects.select_for_update(),
                id=product_id,
                is_active=True,
            )
            item = OrderItem.objects.filter(order=order, product=product).first()

            if action == 'add':
                current = item.quantity if item else 0
                if not product.digital and current >= product.stock:
                    return JsonResponse({'success': False, 'message': 'No more stock is available.'}, status=409)
                if item:
                    item.quantity = current + 1
                    item.save(update_fields=['quantity'])
                else:
                    item = OrderItem.objects.create(
                        order=order, product=product, quantity=1, price_at_purchase=product.price
                    )
            elif item:
                item.quantity -= 1
                if item.quantity <= 0:
                    item.delete()
                else:
                    item.save(update_fields=['quantity'])

        return JsonResponse({
            'success': True,
            'message': 'Cart updated',
            'cartItems': order.get_cart_items,
            'cartTotal': float(order.get_cart_total),
        })
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid cart request.'}, status=400)
    except Exception:
        __import__('logging').getLogger(__name__).exception('Unexpected cart update error')
        return JsonResponse({'success': False, 'message': 'Unable to update cart.'}, status=500)


@require_POST
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def add_to_cart(request, item_id):
    """Add a product to the authenticated cart or let anonymous JS manage its cookie cart."""
    try:
        if not request.user.is_authenticated:
            get_object_or_404(Product, id=item_id, is_active=True)
            return JsonResponse({'success': True, 'message': 'Product added to cart', 'useCookies': True})

        with transaction.atomic():
            customer = request.user.customer
            order, _ = Order.objects.get_or_create(customer=customer, complete=False)
            product = get_object_or_404(
                Product.objects.select_for_update(),
                id=item_id,
                is_active=True,
            )
            item = OrderItem.objects.filter(order=order, product=product).first()
            current = item.quantity if item else 0
            if not product.digital and current >= product.stock:
                return JsonResponse({'success': False, 'message': 'No more stock is available.'}, status=409)
            if item:
                item.quantity = current + 1
                item.save(update_fields=['quantity'])
            else:
                OrderItem.objects.create(
                    order=order, product=product, quantity=1, price_at_purchase=product.price
                )

        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cartItems': order.get_cart_items,
        })
    except Exception:
        __import__('logging').getLogger(__name__).exception('Unexpected add-to-cart error')
        return JsonResponse({'success': False, 'message': 'Unable to add product to cart.'}, status=500)


def checkout(request):
    """Checkout page view"""
    data = cartData(request, create=True)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    if cartItems == 0:
        messages.warning(request, 'Your cart is empty')
        return redirect('store')
    
    context = {
        'items': items, 
        'order': order, 
        'cartItems': cartItems,
        'paypal_client_id': getattr(settings, 'PAYPAL_CLIENT_ID', ''),
    }
    return render(request, 'store/checkout.html', context)


@require_POST
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def processOrder(request):
    """Complete checkout only after server-side validation and one atomic commit."""
    try:
        from .services.payments import get_verified_mobile_payment, verify_paypal

        data = json.loads(request.body or '{}')
        form_data = data.get('form') if isinstance(data.get('form'), dict) else {}
        shipping_data = data.get('shipping') if isinstance(data.get('shipping'), dict) else {}
        payment_method = str(data.get('payment_method', '')).lower()
        transaction_id = str(data.get('transaction_id', '')).strip()

        if payment_method not in {'mtn', 'airtel', 'paypal', 'cod'}:
            return JsonResponse({'success': False, 'message': 'Unsupported payment method.'}, status=400)

        if request.user.is_authenticated:
            customer = request.user.customer
            order, _ = Order.objects.get_or_create(customer=customer, complete=False)
            default_name = customer.name
            default_email = customer.email
        else:
            if payment_method != 'cod':
                return JsonResponse({'success': False, 'message': 'Authenticated checkout is required for electronic payments.'}, status=401)
            customer, order = guestOrder(request, data)
            default_name = order.guest_name
            default_email = order.guest_email

        server_total = order.get_cart_total
        client_total = Decimal(str(form_data.get('total', '0')))
        if not client_total.is_finite() or client_total != server_total:
            return JsonResponse({'success': False, 'message': 'Order total mismatch. Please refresh and try again.'}, status=400)

        requires_shipping = order.requires_shipping
        cleaned_shipping = {}
        if requires_shipping:
            shipping_form = CheckoutForm(data={
                'name': form_data.get('name') or default_name,
                'email': form_data.get('email') or default_email,
                'phone': shipping_data.get('phone', ''),
                'address': shipping_data.get('address', ''),
                'city': shipping_data.get('city', ''),
                'region': shipping_data.get('region', ''),
                'country': shipping_data.get('country', 'Uganda'),
                'postal_code': shipping_data.get('zipcode', ''),
                'delivery_notes': shipping_data.get('landmark', ''),
            })
            if not shipping_form.is_valid():
                return JsonResponse({'success': False, 'message': 'Please provide valid shipping information.'}, status=400)
            cleaned_shipping = shipping_form.cleaned_data

        if payment_method in {'mtn', 'airtel'}:
            payment = get_verified_mobile_payment(
                order=order,
                transaction_id=transaction_id,
                provider=payment_method,
                amount=server_total,
            )
            if not payment:
                return JsonResponse({'success': False, 'message': 'Verified mobile-money payment not found.'}, status=400)
        elif payment_method == 'paypal':
            if not verify_paypal(transaction_id=transaction_id, amount=server_total):
                return JsonResponse({'success': False, 'message': 'PayPal payment could not be verified.'}, status=400)
            payment = None
        else:
            payment = None

        with transaction.atomic():
            locked_order = Order.objects.select_for_update().get(pk=order.pk)
            if locked_order.complete:
                return JsonResponse({'success': False, 'message': 'This order has already been completed.'}, status=409)

            if payment_method == 'cod':
                locked_order.place_cash_on_delivery()
            elif payment_method in {'mtn', 'airtel'}:
                locked_order.mark_as_paid(payment.transaction_id, payment_method=f'mobile_money_{payment.provider}')
            else:
                locked_order.mark_as_paid(transaction_id, payment_method='paypal')

            if requires_shipping:
                ShippingAddress.objects.update_or_create(
                    order=locked_order,
                    defaults={
                        'customer': customer,
                        'full_name': cleaned_shipping['name'],
                        'phone': cleaned_shipping['phone'],
                        'address': cleaned_shipping['address'],
                        'city': cleaned_shipping['city'],
                        'district': cleaned_shipping['region'],
                        'region': cleaned_shipping['region'],
                        'country': cleaned_shipping['country'],
                        'postal_code': cleaned_shipping['postal_code'],
                        'landmark': shipping_data.get('landmark', '')[:200],
                        'delivery_notes': cleaned_shipping.get('delivery_notes', ''),
                    },
                )

        return JsonResponse({
            'success': True,
            'message': 'Order placed successfully',
            'order_id': locked_order.order_id,
        })
    except (ValueError, TypeError, json.JSONDecodeError, ArithmeticError):
        return JsonResponse({'success': False, 'message': 'Invalid order request.'}, status=400)
    except Exception:
        __import__('logging').getLogger(__name__).exception('Unexpected order processing error')
        return JsonResponse({'success': False, 'message': 'Unable to process order.'}, status=500)


@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def registerPage(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('store')
    
    form = CreateUserForm()
    
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! Please login.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    
    context = {'form': form}
    return render(request, 'store/register.html', context)


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def loginPage(request):
    """User login view"""
    if request.user.is_authenticated:
        # Redirect admin/staff to dashboard, regular users to store
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('store')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect admin/staff users to dashboard
            if user.is_staff:
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('admin_dashboard')
            
            # Merge cookie cart into database cart (for regular users)
            merge_cart_on_login(request, user)
            
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to 'next' parameter if exists
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('store')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'store/login.html')


@require_POST
def logout_user(request):
    """Logout user"""
    logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('store')


@login_required(login_url="/login/")
def profile(request):
    """User profile/dashboard view"""
    customer = request.user.customer
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            # Update User model fields
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        form = CustomerProfileForm(instance=customer)
    
    # Get order history
    orders = Paginator(
        Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered').prefetch_related('items__product').only('id', 'order_id', 'date_ordered', 'status', 'payment_status'),
        10,
    ).get_page(request.GET.get('page'))
    
    context = {
        'form': form,
        'orders': orders,
        'customer': customer,
    }
    return render(request, 'store/profile.html', context)


@login_required(login_url="/login/")
def order_detail(request, order_id):
    """View single order details"""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        order_id=order_id,
        customer=request.user.customer,
    )
    
    context = {
        'order': order,
        'items': order.items.all(),
    }
    return render(request, 'store/order_detail.html', context)


@login_required(login_url="/login/")
@require_POST
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def add_review(request, product_id):
    """Add a product review"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user already reviewed
    existing_review = Review.objects.filter(customer=request.user.customer, product=product).first()
    if existing_review:
        messages.error(request, 'You have already reviewed this product')
        return redirect('product_detail', slug=product.slug)
    
    try:
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment', '')
        
        if 1 <= rating <= 5:
            Review.objects.create(
                product=product,
                customer=request.user.customer,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Review added successfully')
        else:
            messages.error(request, 'Invalid rating')
    except (ValueError, TypeError):
        messages.error(request, 'Invalid rating value')
    
    return redirect('product_detail', slug=product.slug)


@login_required(login_url="/login/")
@require_POST
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def toggle_wishlist(request):
    """Add/remove product from wishlist"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        customer = request.user.customer
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            customer=customer,
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': f'{product.name} removed from wishlist'
            })
        
        return JsonResponse({
            'success': True,
            'action': 'added',
            'message': f'{product.name} added to wishlist'
        })
    
    except Exception:
        __import__('logging').getLogger(__name__).exception('Unexpected wishlist toggle error')
        return JsonResponse({'success': False, 'message': 'Unable to update wishlist.'}, status=500)


@login_required(login_url="/login/")
def wishlist(request):
    """View user's wishlist"""
    data = cartData(request)
    wishlist_items = Paginator(
        Wishlist.objects.filter(customer=request.user.customer).select_related('product').order_by('-date_added'),
        24,
    ).get_page(request.GET.get('page'))
    
    context = {
        'wishlist_items': wishlist_items,
        'cartItems': data['cartItems'],
    }
    return render(request, 'store/wishlist.html', context)


# ============================================
# Delivery Tracking API
# ============================================

@login_required
def delivery_tracking(request, order_id):
    """Return delivery status/location only to the customer, assigned rider, or staff."""
    if not HOMEPAGE_MODELS_AVAILABLE:
        return JsonResponse({'success': False, 'message': 'Delivery tracking unavailable.'}, status=503)
    delivery = get_object_or_404(
        Delivery.objects.select_related('order__customer', 'rider'),
        order__order_id=order_id,
    )
    is_customer = delivery.order.customer_id == getattr(request.user.customer, 'id', None)
    is_rider = delivery.rider_id and delivery.rider.user_id == request.user.id
    if not (request.user.is_staff or is_customer or is_rider):
        return JsonResponse({'success': False, 'message': 'Not authorized.'}, status=403)
    return JsonResponse({
        'success': True,
        'order_id': order_id,
        'status': delivery.status,
        'current_location': {
            'lat': str(delivery.current_lat) if delivery.current_lat is not None else None,
            'lng': str(delivery.current_lng) if delivery.current_lng is not None else None,
        },
        'timeline': delivery.get_tracking_timeline(),
        'status_history': delivery.status_history[-20:],
    })


@login_required
@require_POST
@ratelimit(key='ip', rate='60/m', method='POST', block=True)
def update_delivery_location(request, order_id):
    """Accept GPS updates from the assigned rider or staff only."""
    try:
        data = json.loads(request.body or '{}')
        delivery = get_object_or_404(Delivery.objects.select_related('rider', 'order'), order__order_id=order_id)
        from .services.delivery import update_location
        update_location(
            delivery=delivery,
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            accuracy=data.get('accuracy'),
            actor=request.user,
        )
        from .services.audit import record_event
        record_event(
            action='delivery.location_updated',
            object_type='Delivery',
            object_id=delivery.id,
            actor=request.user,
            metadata={'order_id': order_id},
        )
        return JsonResponse({'success': True})
    except PermissionError:
        return JsonResponse({'success': False, 'message': 'Not authorized.'}, status=403)
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid location payload.'}, status=400)
    except Exception:
        __import__('logging').getLogger(__name__).exception('Delivery location update failed')
        return JsonResponse({'success': False, 'message': 'Unable to update delivery location.'}, status=400)


@login_required
@require_POST
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def update_delivery_status(request, order_id):
    """Accept delivery status transitions from the assigned rider or staff only."""
    try:
        data = json.loads(request.body or '{}')
        delivery = get_object_or_404(Delivery.objects.select_related('rider', 'order'), order__order_id=order_id)
        from .services.delivery import update_status
        update_status(
            delivery=delivery,
            new_status=data.get('status', ''),
            notes=data.get('notes', ''),
            actor=request.user,
        )
        from .services.audit import record_event
        record_event(
            action='delivery.status_updated',
            object_type='Delivery',
            object_id=delivery.id,
            actor=request.user,
            metadata={'order_id': order_id, 'status': delivery.status},
        )
        return JsonResponse({'success': True, 'status': delivery.status})
    except PermissionError:
        return JsonResponse({'success': False, 'message': 'Not authorized.'}, status=403)
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid status payload.'}, status=400)
    except Exception:
        __import__('logging').getLogger(__name__).exception('Delivery status update failed')
        return JsonResponse({'success': False, 'message': 'Unable to update delivery status.'}, status=400)


# ============================================
# Mobile Money Payment API Views
# ============================================

@require_POST
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def initiate_momo_payment(request):
    """Create and initiate a server-owned mobile-money payment."""
    try:
        from .payments import PaymentGateway
        from .models import MobileMoneyPayment

        data = json.loads(request.body or '{}')
        phone = str(data.get('phone', '')).strip()
        amount = Decimal(str(data.get('amount', '0')))
        requested_provider = str(data.get('provider', '')).lower()

        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Login is required before starting a mobile-money payment.'}, status=401)
        if amount <= 0:
            return JsonResponse({'success': False, 'message': 'Invalid payment amount.'}, status=400)

        customer = request.user.customer
        order = Order.objects.filter(customer=customer, complete=False).first()
        if not order:
            return JsonResponse({'success': False, 'message': 'No pending order found.'}, status=400)

        server_total = order.get_cart_total
        if amount != server_total:
            return JsonResponse({'success': False, 'message': 'Payment amount does not match the current order total.'}, status=400)

        gateway = PaymentGateway()
        provider = None if requested_provider in {'', 'auto'} else requested_provider
        if provider not in {'mtn', 'airtel'}:
            provider = gateway.detect_provider(phone)
        if provider not in {'mtn', 'airtel'}:
            return JsonResponse({'success': False, 'message': 'Could not determine a supported mobile-money provider.'}, status=400)

        valid, normalized_phone = gateway.get_provider(provider).validate_phone(phone, provider)
        if not valid:
            return JsonResponse({'success': False, 'message': normalized_phone}, status=400)

        with transaction.atomic():
            locked_order = Order.objects.select_for_update().get(pk=order.pk)
            existing = MobileMoneyPayment.objects.filter(
                order=locked_order,
                provider=provider,
                amount=amount,
                status__in=['processing', 'pending'],
                created_at__gte=timezone.now() - datetime.timedelta(minutes=2),
            ).order_by('-created_at').first()
            if existing:
                return JsonResponse({
                    'success': True,
                    'message': 'A payment request is already in progress.',
                    'payment_id': existing.id,
                    'reference': existing.external_reference,
                })

            reference = f"AGRI-{uuid.uuid4().hex[:16].upper()}"
            payment = MobileMoneyPayment.objects.create(
                order=locked_order,
                phone_number=normalized_phone,
                amount=amount,
                provider=provider,
                external_reference=reference,
                status='processing',
            )

        success, provider_reference, message = gateway.initiate_payment(
            provider=provider,
            phone=normalized_phone,
            amount=amount,
            reference=reference,
            email=customer.email,
            description=f"Agri-Market order {order.order_id}",
        )

        if success:
            payment.provider_reference = str(provider_reference or '')
            payment.status = 'pending'
            payment.save(update_fields=['provider_reference', 'status', 'updated_at'])
            return JsonResponse({
                'success': True,
                'message': 'Payment initiated. Please approve the request on your phone.',
                'payment_id': payment.id,
                'reference': reference,
            })

        payment.status = 'failed'
        payment.status_message = message or 'Payment initiation failed'
        payment.save(update_fields=['status', 'status_message', 'updated_at'])
        return JsonResponse({'success': False, 'message': payment.status_message}, status=400)

    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({'success': False, 'message': 'Invalid payment request.'}, status=400)
    except Exception:
        logger = __import__('logging').getLogger(__name__)
        logger.exception('Unexpected mobile-money initiation error')
        return JsonResponse({'success': False, 'message': 'Payment service temporarily unavailable.'}, status=500)


@require_GET
@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def check_momo_status(request):
    """Poll a payment while preserving order ownership and provider verification."""
    try:
        from .payments import PaymentGateway
        from .models import MobileMoneyPayment

        payment_id = request.GET.get('payment_id')
        if not payment_id:
            return JsonResponse({'success': False, 'message': 'Payment ID required.'}, status=400)

        payment = get_object_or_404(
            MobileMoneyPayment.objects.select_related('order__customer'),
            id=payment_id,
        )

        if not request.user.is_authenticated or payment.order.customer_id != request.user.customer.id:
            return JsonResponse({'success': False, 'message': 'Not authorized to view this payment.'}, status=403)

        if payment.status == 'successful':
            return JsonResponse({'success': True, 'status': 'successful', 'message': 'Payment completed.'})
        if payment.status in {'failed', 'cancelled', 'timeout'}:
            return JsonResponse({'success': True, 'status': 'failed', 'message': payment.status_message or 'Payment failed.'})

        gateway = PaymentGateway()
        reference = payment.provider_reference or payment.external_reference
        status, details = gateway.check_status(payment.provider, reference)

        if status == 'successful':
            provider_amount = details.get('amount')
            if provider_amount is not None and Decimal(str(provider_amount)) != payment.amount:
                payment.mark_failed('Provider amount does not match the order amount.')
                return JsonResponse({'success': False, 'status': 'failed', 'message': 'Payment amount verification failed.'}, status=400)
            payment.mark_successful(provider_reference=details.get('transaction_id') or payment.provider_reference)
            _enqueue_payment_sms(payment.order_id)
            return JsonResponse({'success': True, 'status': 'successful', 'message': 'Payment completed.'})

        if status == 'failed':
            payment.mark_failed(details.get('message', 'Transaction declined.'))
            return JsonResponse({'success': True, 'status': 'failed', 'message': payment.status_message})

        return JsonResponse({'success': True, 'status': 'pending', 'message': 'Waiting for payment confirmation.'})

    except Exception:
        logger = __import__('logging').getLogger(__name__)
        logger.exception('Unexpected mobile-money status error')
        return JsonResponse({'success': False, 'message': 'Could not check payment status.'}, status=500)


def ratelimit_error(request, exception):
    response = JsonResponse(
        {'success': False, 'message': 'Too many requests. Please try again shortly.'},
        status=429,
    ) if request.path.startswith('/api/') or request.headers.get('Accept', '').find('application/json') >= 0 else HttpResponse(
        'Too many requests. Please try again shortly.', status=429, content_type='text/plain'
    )
    response['Retry-After'] = '60'
    return response


def _enqueue_payment_sms(order_id):
    """Queue payment SMS after the database transaction commits."""
    try:
        from .tasks import send_order_sms_task
        transaction.on_commit(lambda: send_order_sms_task.delay(order_id, 'payment_received'))
    except Exception:
        __import__('logging').getLogger(__name__).exception('Unable to queue payment SMS for order=%s', order_id)


def _verify_payment_webhook(request):
    """Verify Flutterwave or configured mobile-money webhook authenticity."""
    body = request.body
    flutterwave_hash = request.headers.get('verif-hash', '')
    configured_flutterwave = getattr(settings, 'FLUTTERWAVE_WEBHOOK_SECRET_HASH', '')
    if configured_flutterwave:
        return bool(flutterwave_hash) and hmac.compare_digest(flutterwave_hash, configured_flutterwave)

    secret = getattr(settings, 'MOMO_WEBHOOK_SECRET', '')
    signature = (
        request.headers.get('X-Webhook-Signature')
        or request.headers.get('X-Callback-Signature')
        or request.headers.get('X-Signature')
        or ''
    )
    if secret:
        expected = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
        return bool(signature) and hmac.compare_digest(signature, expected)

    return False


@csrf_exempt
@require_POST
@ratelimit(key='ip', rate='120/m', method='POST', block=True)
def momo_callback(request):
    """Process an authenticated, idempotent payment provider callback."""
    if not _verify_payment_webhook(request):
        return JsonResponse({'status': 'error', 'message': 'Webhook verification failed.'}, status=401)

    try:
        from .models import MobileMoneyPayment
        data = json.loads(request.body or '{}')
        nested = data.get('data') if isinstance(data.get('data'), dict) else {}

        reference = (
            data.get('reference')
            or data.get('transactionId')
            or data.get('tx_ref')
            or data.get('external_reference')
            or nested.get('tx_ref')
            or nested.get('id')
        )
        provider_reference = (
            data.get('provider_reference')
            or data.get('transactionId')
            or data.get('id')
            or nested.get('id')
        )

        if not reference and provider_reference:
            payment = MobileMoneyPayment.objects.filter(
                Q(provider_reference=str(provider_reference))
                | Q(external_reference=str(provider_reference))
                | Q(transaction_id=str(provider_reference))
            ).first()
        else:
            payment = MobileMoneyPayment.objects.filter(
                Q(external_reference=str(reference))
                | Q(provider_reference=str(reference))
                | Q(transaction_id=str(reference))
            ).first()

        if not payment:
            return JsonResponse({'status': 'error', 'message': 'Payment not found.'}, status=404)

        callback_amount = data.get('amount') or nested.get('amount')
        if callback_amount is not None and Decimal(str(callback_amount)) != payment.amount:
            payment.mark_failed('Provider callback amount does not match the order amount.')
            return JsonResponse({'status': 'error', 'message': 'Amount mismatch.'}, status=400)

        callback_currency = str(data.get('currency') or nested.get('currency') or 'UGX').upper()
        if callback_currency != 'UGX':
            payment.mark_failed('Provider callback currency is not UGX.')
            return JsonResponse({'status': 'error', 'message': 'Currency mismatch.'}, status=400)

        status = str(data.get('status') or nested.get('status') or '').lower()
        if status in {'successful', 'success', 'completed'}:
            payment.mark_successful(provider_reference=str(provider_reference or reference or payment.provider_reference))
            _enqueue_payment_sms(payment.order_id)
        elif status in {'failed', 'cancelled', 'declined', 'error'}:
            payment.mark_failed(data.get('message') or nested.get('message') or 'Transaction failed.')
        else:
            return JsonResponse({'status': 'ok', 'message': 'Payment remains pending.'})

        return JsonResponse({'status': 'ok'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception:
        logger = __import__('logging').getLogger(__name__)
        logger.exception('Unexpected mobile-money callback error')
        return JsonResponse({'status': 'error', 'message': 'Callback processing failed.'}, status=500)


@require_POST
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def newsletter_subscribe(request):
    """Validate and store newsletter subscriptions without leaking backend errors."""
    try:
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        data = json.loads(request.body or '{}')
        email = str(data.get('email', '')).strip().lower()
        try:
            validate_email(email)
        except DjangoValidationError:
            return JsonResponse({'success': False, 'message': 'Enter a valid email address.'}, status=400)

        from .models import NewsletterSubscriber
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={'is_active': True},
        )
        if not created and subscriber.is_active:
            return JsonResponse({'success': False, 'message': 'You are already subscribed.'}, status=409)
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=['is_active'])
        return JsonResponse({'success': True, 'message': 'Successfully subscribed.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)
    except Exception:
        __import__('logging').getLogger(__name__).exception('Newsletter subscription failed')
        return JsonResponse({'success': False, 'message': 'Unable to process subscription.'}, status=500)


@login_required
def admin_dashboard(request):
    """Custom admin dashboard with analytics and charts"""
    from django.db.models import F, Sum, Count
    from django.db.models.functions import TruncDate
    from collections import defaultdict
    
    # Only allow staff/superusers
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('homepage')
    
    # Get date range (default last 30 days)
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)
    
    # Sales data for chart - aggregate from OrderItems (quantity * price)
    orders = Order.objects.filter(
        complete=True,
        date_ordered__date__gte=start_date,
        date_ordered__date__lte=end_date
    )
    
    # Daily sales aggregation using OrderItems with F expressions
    daily_order_items = OrderItem.objects.filter(
        order__complete=True,
        order__date_ordered__date__gte=start_date,
        order__date_ordered__date__lte=end_date
    ).annotate(
        day=TruncDate('order__date_ordered'),
        item_total=F('quantity') * Coalesce(F('price_at_purchase'), F('product__price'), Decimal('0'))
    ).values('day').annotate(
        total=Sum('item_total'),
        count=Count('order', distinct=True)
    ).order_by('day')
    
    # Prepare chart data
    sales_labels = []
    sales_data = []
    orders_data = []
    
    for sale in daily_order_items:
        if sale['day']:
            sales_labels.append(sale['day'].strftime('%b %d'))
            sales_data.append(float(sale['total'] or 0))
            orders_data.append(sale['count'])
    
    # Fill missing days with 0
    if not sales_labels:
        for i in range(30):
            day = start_date + datetime.timedelta(days=i)
            sales_labels.append(day.strftime('%b %d'))
            sales_data.append(0)
            orders_data.append(0)
    
    # Category sales using F expressions
    category_sales = OrderItem.objects.filter(
        order__complete=True,
        order__date_ordered__date__gte=start_date
    ).annotate(
        item_total=F('quantity') * Coalesce(F('price_at_purchase'), F('product__price'), Decimal('0'))
    ).values('product__category__name').annotate(
        total=Sum('item_total')
    ).order_by('-total')[:6]
    
    category_labels = [c['product__category__name'] or 'Uncategorized' for c in category_sales]
    category_data = [float(c['total'] or 0) for c in category_sales]
    
    # Stats - calculate total revenue from OrderItems
    total_revenue = OrderItem.objects.filter(
        order__complete=True,
        order__date_ordered__date__gte=start_date,
        order__date_ordered__date__lte=end_date
    ).annotate(
        item_total=F('quantity') * Coalesce(F('price_at_purchase'), F('product__price'), Decimal('0'))
    ).aggregate(total=Sum('item_total'))['total'] or 0
    
    total_orders = orders.count()
    total_customers = Customer.objects.count()
    total_products = Product.objects.filter(is_active=True).count()
    
    # Recent orders
    recent_orders = Order.objects.filter(complete=True).order_by('-date_ordered')[:10]
    
    # Top products using F expressions
    top_products = OrderItem.objects.filter(
        order__complete=True
    ).annotate(
        item_total=F('quantity') * Coalesce(F('price_at_purchase'), F('product__price'), Decimal('0'))
    ).values('product__name', 'product__id').annotate(
        sold=Sum('quantity'),
        revenue=Sum('item_total')
    ).order_by('-sold')[:5]
    
    # Low stock alert
    low_stock_products = Product.objects.filter(
        is_active=True,
        stock__lt=10
    ).order_by('stock')[:5]
    
    # Customer locations for map (placeholder coordinates)
    customer_locations = []
    
    context = {
        'sales_labels': json.dumps(sales_labels),
        'sales_data': json.dumps(sales_data),
        'orders_data': json.dumps(orders_data),
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
        'customer_locations': json.dumps(customer_locations),
        'pending_orders': Order.objects.filter(complete=True, status='pending').count() if hasattr(Order, 'status') else 0,
        'processing_orders': Order.objects.filter(complete=True, status='processing').count() if hasattr(Order, 'status') else 0,
        'delivered_orders': Order.objects.filter(complete=True, status='delivered').count() if hasattr(Order, 'status') else total_orders,
    }
    
    return render(request, 'admin/dashboard.html', context)