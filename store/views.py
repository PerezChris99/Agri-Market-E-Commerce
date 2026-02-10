from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Sum, Count, F
from django.db.models.functions import TruncDate
from django.conf import settings

import json
import datetime
from decimal import Decimal

from .models import (
    Customer, Product, Order, OrderItem, ShippingAddress, Category, Review, Wishlist,
    DeliveryZone, SellerProfile, PromoCode
)
from .utils import cookieCart, cartData, guestOrder, merge_cart_on_login
from .forms import CreateUserForm, CustomerProfileForm, ReviewForm

# Try to import new models (may not exist yet if migrations not run)
try:
    from .models import Testimonial, DeliveryRider, Delivery
    HOMEPAGE_MODELS_AVAILABLE = True
except ImportError:
    HOMEPAGE_MODELS_AVAILABLE = False


def homepage(request):
    """Beautiful homepage with featured products, categories, and testimonials"""
    data = cartData(request)
    cartItems = data['cartItems']
    
    # Get all active categories with product count (limited to 6 for homepage)
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )[:6]
    
    # Get featured products
    featured_products = Product.objects.filter(
        is_active=True, 
        is_featured=True
    ).select_related('category')[:8]
    
    # If not enough featured, get popular ones
    if featured_products.count() < 4:
        featured_products = Product.objects.filter(
            is_active=True
        ).annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating', '-created_at')[:8]
    
    # Add ratings to products
    for product in featured_products:
        reviews = product.reviews.all()
        product.avg_rating = int(reviews.aggregate(Avg('rating'))['rating__avg'] or 0)
        product.review_count = reviews.count()
    
    # Get latest products (limited to 4 for homepage)
    latest_products = Product.objects.filter(
        is_active=True
    ).order_by('-created_at').select_related('category')[:4]
    
    for product in latest_products:
        reviews = product.reviews.all()
        product.avg_rating = int(reviews.aggregate(Avg('rating'))['rating__avg'] or 0)
        product.review_count = reviews.count()
    
    # Get testimonials if model exists
    testimonials = []
    if HOMEPAGE_MODELS_AVAILABLE:
        try:
            testimonials = Testimonial.objects.filter(is_active=True).order_by('-created_at')[:6]
        except:
            pass
    
    # Stats for hero section
    stats = {
        'products': Product.objects.filter(is_active=True).count(),
        'farmers': SellerProfile.objects.count() if SellerProfile else 0,
        'orders': Order.objects.filter(complete=True).count(),
        'districts': DeliveryZone.objects.filter(is_active=True).values('name').distinct().count() if DeliveryZone else 110,
    }
    
    # Flash deals (products with discounts) - placeholder for now
    flash_deals = []
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'testimonials': testimonials,
        'flash_deals': flash_deals,
        'stats': stats,
        'cartItems': cartItems,
    }
    return render(request, 'store/homepage.html', context)


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
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
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
    categories = Category.objects.filter(is_active=True)
    
    # Get featured products
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:4]
    
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
    ).exclude(id=product.id)[:4]
    
    # Get reviews
    reviews = product.reviews.all()
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
        'reviews': reviews,
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
    data = cartData(request)
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
def updateItem(request):
    """Update cart item quantity via AJAX"""
    try:
        data = json.loads(request.body)
        productId = data.get("productId")
        action = data.get("action")
        
        product = get_object_or_404(Product, id=productId)
        
        if request.user.is_authenticated:
            # Database cart for logged in users
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
            
            if action == "add":
                # Check stock
                if product.stock <= 0 and not product.digital:
                    return JsonResponse({
                        'success': False,
                        'message': 'Product is out of stock'
                    })
                orderItem.quantity += 1
            elif action == "remove":
                orderItem.quantity -= 1
            
            orderItem.save()
            
            if orderItem.quantity <= 0:
                orderItem.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Cart updated',
                'cartItems': order.get_cart_items,
                'cartTotal': float(order.get_cart_total)
            })
        else:
            # Cookie cart for anonymous users - handled by JavaScript
            return JsonResponse({
                'success': True,
                'message': 'Cookie cart updated',
                'useCookies': True
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@require_POST
def add_to_cart(request, item_id):
    """Add single item to cart via AJAX"""
    try:
        product = get_object_or_404(Product, id=item_id)
        
        # Check stock for physical products
        if product.stock <= 0 and not product.digital:
            return JsonResponse({
                'success': False,
                'message': 'Product is out of stock'
            })
        
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
            
            if not created:
                orderItem.quantity += 1
                orderItem.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart',
                'cartItems': order.get_cart_items
            })
        else:
            # For anonymous users, JavaScript handles cookie cart
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart',
                'useCookies': True
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


def checkout(request):
    """Checkout page view"""
    data = cartData(request)
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
def processOrder(request):
    """Process order after payment"""
    try:
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id', datetime.datetime.now().timestamp())
        
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        else:
            # Guest checkout
            customer, order = guestOrder(request, data)
        
        total = Decimal(str(data['form']['total']))
        
        # Verify the total matches
        if abs(total - order.get_cart_total) > Decimal('0.01'):
            return JsonResponse({
                'success': False,
                'message': 'Order total mismatch. Please refresh and try again.'
            }, status=400)
        
        # Mark order as paid
        order.mark_as_paid(str(transaction_id), payment_method='paypal')
        
        # Create shipping address if required
        if order.requires_shipping:
            shipping_data = data.get('shipping', {})
            ShippingAddress.objects.create(
                customer=customer if request.user.is_authenticated else None,
                order=order,
                full_name=data['form'].get('name', ''),
                phone=shipping_data.get('phone', ''),
                address=shipping_data.get('address', ''),
                city=shipping_data.get('city', ''),
                region=shipping_data.get('region', ''),
                country=shipping_data.get('country', 'Uganda'),
                postal_code=shipping_data.get('zipcode', ''),
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Order placed successfully',
            'order_id': order.order_id
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


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
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('store')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'store/login.html')


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
    orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered')[:10]
    
    context = {
        'form': form,
        'orders': orders,
        'customer': customer,
    }
    return render(request, 'store/profile.html', context)


@login_required(login_url="/login/")
def order_detail(request, order_id):
    """View single order details"""
    order = get_object_or_404(Order, order_id=order_id, customer=request.user.customer)
    
    context = {
        'order': order,
        'items': order.items.all(),
    }
    return render(request, 'store/order_detail.html', context)


@login_required(login_url="/login/")
@require_POST
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
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url="/login/")
def wishlist(request):
    """View user's wishlist"""
    data = cartData(request)
    wishlist_items = Wishlist.objects.filter(customer=request.user.customer)
    
    context = {
        'wishlist_items': wishlist_items,
        'cartItems': data['cartItems'],
    }
    return render(request, 'store/wishlist.html', context)


# ============================================
# Mobile Money Payment API Views
# ============================================

@require_POST
def initiate_momo_payment(request):
    """
    Initiate a Mobile Money payment (MTN MoMo or Airtel Money)
    
    Request body:
        phone: Phone number (256XXXXXXXXX format)
        amount: Amount in UGX
        provider: 'mtn' or 'airtel'
    """
    try:
        from .payments import PaymentGateway
        from .models import MobileMoneyPayment
        
        data = json.loads(request.body)
        phone = data.get('phone', '').replace(' ', '').replace('+', '')
        amount = Decimal(str(data.get('amount', 0)))
        provider = data.get('provider', 'auto')
        
        if not phone or amount <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Invalid phone number or amount'
            }, status=400)
        
        # Get order for this payment
        if request.user.is_authenticated:
            customer = request.user.customer
            order = Order.objects.filter(customer=customer, complete=False).first()
            if not order:
                return JsonResponse({
                    'success': False,
                    'message': 'No pending order found'
                }, status=400)
        else:
            # For guests, we need to handle differently
            order = None
        
        # Create payment gateway
        gateway = PaymentGateway()
        
        # Generate unique reference
        import uuid
        reference = f"AGRI-{uuid.uuid4().hex[:8].upper()}"
        
        # Create payment record
        payment = MobileMoneyPayment.objects.create(
            order=order,
            customer=request.user.customer if request.user.is_authenticated else None,
            phone_number=phone,
            amount=amount,
            provider=provider if provider != 'auto' else gateway.detect_provider(phone),
            reference=reference,
            status='pending'
        )
        
        # Initiate payment
        result = gateway.initiate_payment(
            phone_number=phone,
            amount=float(amount),
            reference=reference
        )
        
        if result['success']:
            payment.external_reference = result.get('external_ref')
            payment.status = 'pending'
            payment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Payment initiated. Please check your phone.',
                'payment_id': payment.id,
                'reference': reference
            })
        else:
            payment.status = 'failed'
            payment.failure_reason = result.get('message', 'Unknown error')
            payment.save()
            
            return JsonResponse({
                'success': False,
                'message': result.get('message', 'Failed to initiate payment')
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_GET
def check_momo_status(request):
    """
    Check Mobile Money payment status
    
    Query params:
        payment_id: ID of the MobileMoneyPayment record
    """
    try:
        from .payments import PaymentGateway
        from .models import MobileMoneyPayment
        
        payment_id = request.GET.get('payment_id')
        
        if not payment_id:
            return JsonResponse({
                'success': False,
                'message': 'Payment ID required'
            }, status=400)
        
        payment = MobileMoneyPayment.objects.filter(id=payment_id).first()
        
        if not payment:
            return JsonResponse({
                'success': False,
                'message': 'Payment not found'
            }, status=404)
        
        # If already completed, return status
        if payment.status == 'successful':
            return JsonResponse({
                'success': True,
                'status': 'successful',
                'message': 'Payment completed'
            })
        elif payment.status == 'failed':
            return JsonResponse({
                'success': True,
                'status': 'failed',
                'message': payment.failure_reason or 'Payment failed'
            })
        
        # Check with payment gateway
        gateway = PaymentGateway()
        result = gateway.check_status(payment.reference)
        
        if result.get('status') == 'successful':
            payment.status = 'successful'
            payment.save()
            
            # Mark order as paid if exists
            if payment.order:
                payment.order.mark_as_paid(payment.reference, payment_method=payment.provider)
            
            return JsonResponse({
                'success': True,
                'status': 'successful',
                'message': 'Payment completed'
            })
        elif result.get('status') == 'failed':
            payment.status = 'failed'
            payment.failure_reason = result.get('message', 'Transaction declined')
            payment.save()
            
            return JsonResponse({
                'success': True,
                'status': 'failed',
                'message': payment.failure_reason
            })
        else:
            return JsonResponse({
                'success': True,
                'status': 'pending',
                'message': 'Waiting for payment confirmation'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def momo_callback(request):
    """
    Mobile Money payment callback endpoint
    Called by payment provider when payment status changes
    """
    try:
        from .models import MobileMoneyPayment
        from .sms import send_order_sms
        
        data = json.loads(request.body) if request.body else {}
        
        reference = data.get('reference') or data.get('transactionId') or data.get('tx_ref')
        status = data.get('status', '').lower()
        
        if not reference:
            return JsonResponse({'status': 'error', 'message': 'No reference'}, status=400)
        
        payment = MobileMoneyPayment.objects.filter(
            Q(reference=reference) | Q(external_reference=reference)
        ).first()
        
        if not payment:
            return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
        
        # Update payment status
        if status in ['successful', 'success', 'completed']:
            payment.status = 'successful'
            payment.save()
            
            # Mark order as paid
            if payment.order:
                payment.order.mark_as_paid(reference, payment_method=payment.provider)
                
                # Send SMS confirmation
                try:
                    send_order_sms(payment.order, 'payment_received')
                except:
                    pass
        
        elif status in ['failed', 'cancelled', 'declined']:
            payment.status = 'failed'
            payment.failure_reason = data.get('message', 'Transaction failed')
            payment.save()
        
        return JsonResponse({'status': 'ok'})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_POST
def newsletter_subscribe(request):
    """Subscribe to newsletter"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required'
            })
        
        # Try to use NewsletterSubscriber model if available
        try:
            from .models import NewsletterSubscriber
            
            # Check if already subscribed
            if NewsletterSubscriber.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'You are already subscribed!'
                })
            
            # Create subscription
            NewsletterSubscriber.objects.create(email=email)
            return JsonResponse({
                'success': True,
                'message': 'Successfully subscribed! You\'ll receive our latest updates.'
            })
        except:
            # Model doesn't exist yet, just return success
            return JsonResponse({
                'success': True,
                'message': 'Thank you for subscribing!'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


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
        item_total=F('quantity') * F('product__price')
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
        item_total=F('quantity') * F('product__price')
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
        item_total=F('quantity') * F('product__price')
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
        item_total=F('quantity') * F('product__price')
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