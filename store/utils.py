import json
from decimal import Decimal
from django.contrib.auth.models import User
from .models import Product, Order, OrderItem, Customer


def cookieCart(request):
    """Parse anonymous cart in one product query instead of N+1 queries."""
    try:
        raw_cart = json.loads(request.COOKIES.get('cart', '{}'))
    except (json.JSONDecodeError, TypeError):
        raw_cart = {}

    quantities = {}
    for product_id, item in raw_cart.items():
        try:
            quantity = int(item.get('quantity', 0))
            if quantity > 0:
                quantities[int(product_id)] = quantity
        except (TypeError, ValueError, AttributeError):
            continue

    if not quantities:
        return {'cartItems': 0, 'order': None, 'items': []}

    products = Product.objects.filter(
        id__in=quantities, is_active=True
    ).only(
        'id', 'name', 'price', 'image', 'slug', 'stock', 'digital'
    )
    items = []
    cart_items = 0
    total = Decimal('0')
    requires_shipping = False

    for product in products:
        quantity = quantities[product.id]
        line_total = product.price * quantity
        cart_items += quantity
        total += line_total
        requires_shipping = requires_shipping or not product.digital
        items.append({
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
            'get_total': line_total,
        })

    return {
        'cartItems': cart_items,
        'order': {
            'get_cart_total': total,
            'get_cart_items': cart_items,
            'requires_shipping': requires_shipping,
        },
        'items': items,
    }


def cartData(request, create=False):
    """Read cart state without creating database rows on ordinary page views."""
    if request.user.is_authenticated:
        try:
            customer = request.user.customer
        except Customer.DoesNotExist:
            customer = Customer.objects.create(user=request.user)

        order = Order.objects.filter(customer=customer, complete=False).first()
        if not order:
            if not create:
                return {'cartItems': 0, 'order': None, 'items': []}
            order = Order.objects.create(customer=customer, complete=False)

        items = order.items.select_related('product').all()
        cart_items = [{
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
        } for item in items if item.product and item.product.is_active]

        return {
            'cartItems': order.get_cart_items,
            'order': order,
            'items': cart_items,
        }

    return cookieCart(request)


def merge_cart_on_login(request, user):
    """Merge an anonymous cart with a user's open cart using batched product lookup."""
    try:
        raw_cart = json.loads(request.COOKIES.get('cart', '{}'))
    except (json.JSONDecodeError, TypeError):
        return

    quantities = {}
    for product_id, item_data in raw_cart.items():
        try:
            quantity = int(item_data.get('quantity', 0))
            if quantity > 0:
                quantities[int(product_id)] = quantity
        except (TypeError, ValueError, AttributeError):
            continue
    if not quantities:
        return

    customer, _ = Customer.objects.get_or_create(user=user)
    order = Order.objects.filter(customer=customer, complete=False).first()
    if not order:
        order = Order.objects.create(customer=customer, complete=False)

    products = Product.objects.filter(id__in=quantities, is_active=True)
    existing = {
        item.product_id: item
        for item in OrderItem.objects.filter(order=order, product_id__in=quantities)
    }

    for product in products:
        quantity = quantities[product.id]
        item = existing.get(product.id)
        if item:
            item.quantity += quantity
            item.save(update_fields=['quantity'])
        else:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=product.price,
            )


def guestOrder(request, data):
    """Create a guest order from the validated cookie cart with one product query."""
    name = str(data.get('form', {}).get('name', 'Guest')).strip()[:200]
    email = str(data.get('form', {}).get('email', '')).strip()

    cookie_data = cookieCart(request)
    if not cookie_data['items']:
        raise ValueError('Cart is empty')

    customer = None
    if email:
        user = User.objects.filter(email__iexact=email).select_related('customer').first()
        if user:
            customer = getattr(user, 'customer', None)

    order = Order.objects.create(
        customer=customer,
        guest_name=name,
        guest_email=email,
        complete=False,
    )

    product_ids = [item['product']['id'] for item in cookie_data['items']]
    products = {
        p.id: p for p in Product.objects.filter(id__in=product_ids, is_active=True)
    }
    OrderItem.objects.bulk_create([
        OrderItem(
            product=products[item['product']['id']],
            order=order,
            quantity=item['quantity'],
            price_at_purchase=products[item['product']['id']].price,
        )
        for item in cookie_data['items']
        if item['product']['id'] in products
    ])
    return customer, order


def format_currency(amount):
    return f'UGX {amount:,.0f}'
