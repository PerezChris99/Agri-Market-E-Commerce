import json
from decimal import Decimal
from .models import Product, Order, OrderItem, Customer


def cookieCart(request):
    """Parse cart data from cookies for anonymous users"""
    try:
        cart = json.loads(request.COOKIES.get('cart', '{}'))
    except (json.JSONDecodeError, TypeError):
        cart = {}

    items = []
    order = {
        'get_cart_total': Decimal('0'),
        'get_cart_items': 0,
        'requires_shipping': False
    }
    cartItems = 0

    for product_id in cart:
        try:
            quantity = cart[product_id].get("quantity", 0)
            if quantity <= 0:
                continue
                
            product = Product.objects.get(id=product_id, is_active=True)
            total = product.price * quantity

            cartItems += quantity
            order['get_cart_total'] += total
            order['get_cart_items'] += quantity

            item = {
                'id': product.id,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'imageURL': product.imageURL,
                    'slug': product.slug,
                    'in_stock': product.in_stock,
                },
                'quantity': quantity,
                'get_total': total,
            }
            items.append(item)

            if not product.digital:
                order['requires_shipping'] = True
                
        except Product.DoesNotExist:
            # Product no longer exists or is inactive
            continue
        except Exception:
            continue

    return {
        'cartItems': cartItems, 
        'order': order, 
        'items': items
    }


def cartData(request):
    """Get cart data - from database for authenticated users, cookies for anonymous"""
    if request.user.is_authenticated:
        try:
            customer = request.user.customer
        except Customer.DoesNotExist:
            # Create customer profile if it doesn't exist
            customer = Customer.objects.create(user=request.user)
        
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.items.select_related('product').all()
        
        cart_items = []
        for item in items:
            if item.product and item.product.is_active:
                cart_items.append({
                    'id': item.id,
                    'product': {
                        'id': item.product.id,
                        'name': item.product.name,
                        'price': item.product.price,
                        'imageURL': item.product.imageURL,
                        'slug': item.product.slug,
                        'in_stock': item.product.in_stock,
                    },
                    'quantity': item.quantity,
                    'get_total': item.get_total,
                })
        
        return {
            'cartItems': order.get_cart_items,
            'order': order,
            'items': cart_items
        }
    else:
        return cookieCart(request)


def merge_cart_on_login(request, user):
    """Merge cookie cart into database cart when user logs in"""
    try:
        cart = json.loads(request.COOKIES.get('cart', '{}'))
    except (json.JSONDecodeError, TypeError):
        return
    
    if not cart:
        return
    
    try:
        customer = user.customer
    except Customer.DoesNotExist:
        customer = Customer.objects.create(user=user)
    
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    
    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            quantity = item_data.get('quantity', 1)
            
            if quantity > 0:
                order_item, created = OrderItem.objects.get_or_create(
                    order=order,
                    product=product
                )
                if created:
                    order_item.quantity = quantity
                else:
                    # Add to existing quantity
                    order_item.quantity += quantity
                order_item.save()
                
        except Product.DoesNotExist:
            continue
        except Exception:
            continue


def guestOrder(request, data):
    """Create order for guest checkout"""
    name = data['form'].get('name', 'Guest')
    email = data['form'].get('email', '')

    cookieData = cookieCart(request)
    items = cookieData['items']

    if not items:
        raise ValueError("Cart is empty")

    # Create or get customer based on email (for order tracking)
    customer = None
    if email:
        from django.contrib.auth.models import User
        # Check if there's a user with this email
        try:
            user = User.objects.get(email=email)
            customer = user.customer
        except (User.DoesNotExist, Customer.DoesNotExist):
            pass

    # Create order
    order = Order.objects.create(
        customer=customer,
        guest_name=name,
        guest_email=email,
        complete=False,
    )
    
    # Create order items
    for item in items:
        try:
            product = Product.objects.get(id=item['product']['id'])
            OrderItem.objects.create(
                product=product,
                order=order,
                quantity=item['quantity'],
                price_at_purchase=product.price
            )
        except Product.DoesNotExist:
            continue

    return customer, order


def format_currency(amount):
    """Format amount as Ugandan Shillings"""
    return f"UGX {amount:,.0f}"