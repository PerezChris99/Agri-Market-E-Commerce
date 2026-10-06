from django.urls import path
from . import health
from . import views
from . import national_api

urlpatterns = [
    path('health/live/', health.live, name='health_live'),
    path('health/ready/', health.ready, name='health_ready'),
    # Main pages
    path('', views.homepage, name="homepage"),  # Beautiful homepage
    path('shop/', views.store, name="store"),   # Product listing
    path('product/<slug:slug>/', views.product_detail, name="product_detail"),
    
    # Cart & Checkout
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),
    path('update_item/', views.updateItem, name="update_item"),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name="add_to_cart"),
    path('process_order/', views.processOrder, name="process_order"),
    
    # Authentication
    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logout_user, name="logout"),
    
    # User Account
    path('profile/', views.profile, name="profile"),
    path('order/<str:order_id>/', views.order_detail, name="order_detail"),
    
    # Wishlist
    path('wishlist/', views.wishlist, name="wishlist"),
    path('toggle-wishlist/', views.toggle_wishlist, name="toggle_wishlist"),
    
    # Reviews
    path('add-review/<int:product_id>/', views.add_review, name="add_review"),
    
    # Admin Dashboard
    path('dashboard/', views.admin_dashboard, name="admin_dashboard"),
    
    # Delivery Tracking API
    path('api/delivery/<str:order_id>/', views.delivery_tracking, name='delivery_tracking'),
    path('api/delivery/<str:order_id>/location/', views.update_delivery_location, name='delivery_location'),
    path('api/delivery/<str:order_id>/status/', views.update_delivery_status, name='delivery_status'),
    
    # Mobile Money Payment API
    path('api/momo/initiate/', views.initiate_momo_payment, name="momo_initiate"),
    path('api/momo/status/', views.check_momo_status, name="momo_status"),
    path('api/momo/callback/', views.momo_callback, name="momo_callback"),
    
    # Newsletter API
    path('api/newsletter/subscribe/', views.newsletter_subscribe, name="newsletter_subscribe"),
    path('api/v1/products/', national_api.products, name='api_v1_products'),
    path('api/v1/areas/', national_api.areas, name='api_v1_areas'),
    path('api/v1/hubs/', national_api.hubs, name='api_v1_hubs'),
    path('api/v1/readiness/', national_api.readiness, name='api_v1_readiness'),
    path('api/v1/sync/', national_api.sync, name='api_v1_sync'),
]