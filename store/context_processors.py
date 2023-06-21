import json

def cart_data(request):
    print(request.COOKIES)

    cart_items = request.COOKIES.get('cart')
    cart = json.loads(cart_items) if cart_items else []

    # You can perform additional logic or filtering on the cart list if needed

    return {
        'cartItems': cart,
    }