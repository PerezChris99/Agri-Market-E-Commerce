from .utils import cartData
from .models import Category


def cart_data(request):
    """Context processor to make cart data available in all templates"""
    data = cartData(request)
    return {
        'cartItems': data['cartItems'],
    }


def categories(request):
    """Context processor to make categories available in all templates"""
    return {
        'all_categories': Category.objects.filter(is_active=True),
    }