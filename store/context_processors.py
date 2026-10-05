from .utils import cartData
from .models import Category
from django.core.cache import cache


def cart_data(request):
    """Context processor to make cart data available in all templates"""
    data = cartData(request)
    return {
        'cartItems': data['cartItems'],
    }


def categories(request):
    """Context processor to make categories available in all templates"""
    categories = cache.get('navigation:categories')
    if categories is None:
        categories = list(Category.objects.filter(is_active=True).order_by('name'))
        cache.set('navigation:categories', categories, 300)
    return {'all_categories': categories}