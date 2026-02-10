from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import json

from .models import Customer, Product, Order, OrderItem, ShippingAddress, Category, Wishlist, Review

# Try to import new models
try:
    from .models import (
        DeliveryZone, MobileMoneyPayment, SMSNotification, SellerProfile,
        BulkOrderRequest, PromoCode, USSDSession
    )
    UGANDA_MODELS = True
except ImportError:
    UGANDA_MODELS = False

try:
    from .models import (
        DeliveryRider, Delivery, DeliveryLocation, ReviewImage, ReviewHelpful,
        Testimonial, NewsletterSubscriber, ContactMessage, SiteSetting
    )
    EXTENDED_MODELS = True
except ImportError:
    EXTENDED_MODELS = False


class AgriMarketAdminSite(admin.AdminSite):
    """Custom Admin Site with Dashboard"""
    site_header = '🌾 Agri-Market Admin'
    site_title = 'Agri-Market Administration'
    index_title = 'Dashboard'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom admin dashboard with visualizations"""
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        seven_days_ago = today - timedelta(days=7)
        
        # Basic stats
        total_revenue = Order.objects.filter(
            complete=True, payment_status='paid'
        ).aggregate(total=Sum('orderitem__price_at_purchase'))['total'] or 0
        
        total_orders = Order.objects.filter(complete=True).count()
        pending_orders = Order.objects.filter(status='pending').count()
        total_customers = Customer.objects.count()
        total_products = Product.objects.filter(is_active=True).count()
        low_stock_count = Product.objects.filter(stock__lt=10, is_active=True).count()
        
        # Sales data for last 30 days (line chart)
        sales_by_date = Order.objects.filter(
            complete=True,
            date_ordered__date__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('date_ordered')
        ).values('date').annotate(
            total=Count('id'),
            revenue=Sum('orderitem__price_at_purchase')
        ).order_by('date')
        
        sales_labels = [item['date'].strftime('%b %d') for item in sales_by_date]
        sales_data = [float(item['revenue'] or 0) for item in sales_by_date]
        
        # Orders by status (bar chart)
        orders_by_status = list(Order.objects.values('status').annotate(count=Count('id')))
        
        # Sales by category (pie chart)
        category_sales = OrderItem.objects.filter(
            order__complete=True
        ).values('product__category__name').annotate(
            total=Sum('price_at_purchase')
        ).order_by('-total')[:8]
        
        category_labels = [item['product__category__name'] or 'Uncategorized' for item in category_sales]
        category_data = [float(item['total'] or 0) for item in category_sales]
        
        # Payment methods (donut chart)
        payment_methods = list(Order.objects.filter(
            complete=True
        ).values('payment_method').annotate(count=Count('id')))
        
        # Recent orders
        recent_orders = Order.objects.select_related('customer').order_by('-date_ordered')[:10]
        
        # Top selling products
        top_products = Product.objects.annotate(
            sold=Count('orderitem', filter=models.Q(orderitem__order__complete=True))
        ).order_by('-sold')[:10]
        
        # Order locations for map (based on shipping addresses)
        order_locations = []
        for addr in ShippingAddress.objects.filter(order__complete=True).values('region').annotate(count=Count('id'))[:20]:
            # Uganda region coordinates approximation
            region_coords = {
                'Central': [0.3476, 32.5825],
                'Eastern': [1.2921, 34.2614],
                'Northern': [2.7706, 32.2990],
                'Western': [0.6025, 30.6500],
                'Kampala': [0.3163, 32.5822],
            }
            region = addr.get('region', 'Central')
            coords = region_coords.get(region, [0.3476, 32.5825])
            order_locations.append({
                'lat': coords[0],
                'lng': coords[1],
                'region': region,
                'count': addr['count']
            })
        
        # Active deliveries (if model exists)
        active_deliveries = []
        if EXTENDED_MODELS:
            try:
                active_deliveries = Delivery.objects.exclude(
                    status='delivered'
                ).select_related('order', 'rider').order_by('-created_at')[:5]
            except:
                pass
        
        context = {
            'title': 'Dashboard',
            # Stats
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_customers': total_customers,
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            # Chart data
            'sales_labels': json.dumps(sales_labels),
            'sales_data': json.dumps(sales_data),
            'orders_by_status': json.dumps(orders_by_status),
            'category_labels': json.dumps(category_labels),
            'category_data': json.dumps(category_data),
            'payment_methods': json.dumps(payment_methods),
            'order_locations': json.dumps(order_locations),
            # Lists
            'recent_orders': recent_orders,
            'top_products': top_products,
            'active_deliveries': active_deliveries,
        }
        return render(request, 'admin/dashboard.html', context)


# Use custom admin site
# admin_site = AgriMarketAdminSite(name='agrimarket_admin')

# For now, use default admin with custom models
from django.db import models


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'region', 'is_farmer', 'created_at']
    list_filter = ['is_farmer', 'region', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'city']
    ordering = ['-created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'unit', 'is_active', 'is_featured', 'created_at']
    list_filter = ['category', 'is_active', 'is_featured', 'unit', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock', 'is_active', 'is_featured']
    ordering = ['-created_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price_at_purchase', 'get_total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer', 'guest_name', 'status', 'payment_status', 'get_cart_total', 'date_ordered']
    list_filter = ['status', 'payment_status', 'complete', 'date_ordered']
    search_fields = ['order_id', 'customer__user__username', 'guest_name', 'guest_email', 'transaction_id']
    readonly_fields = ['order_id', 'get_cart_total', 'get_cart_items', 'date_ordered']
    inlines = [OrderItemInline]
    ordering = ['-date_ordered']
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_id', 'customer', 'guest_name', 'guest_email')
        }),
        ('Status', {
            'fields': ('status', 'payment_status', 'complete')
        }),
        ('Payment', {
            'fields': ('payment_method', 'transaction_id')
        }),
        ('Details', {
            'fields': ('get_cart_total', 'get_cart_items', 'notes', 'date_ordered')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price_at_purchase', 'get_total', 'date_added']
    list_filter = ['date_added']
    search_fields = ['order__order_id', 'product__name']


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'order', 'city', 'region', 'country', 'phone', 'date_added']
    list_filter = ['city', 'region', 'country', 'date_added']
    search_fields = ['full_name', 'address', 'phone', 'order__order_id']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['customer', 'product', 'date_added']
    list_filter = ['date_added']
    search_fields = ['customer__user__username', 'product__name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'customer', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'customer__user__username', 'comment']
    ordering = ['-created_at']


# Register Uganda-specific models if available
if UGANDA_MODELS:
    @admin.register(DeliveryZone)
    class DeliveryZoneAdmin(admin.ModelAdmin):
        list_display = ['name', 'region', 'delivery_fee', 'estimated_days', 'is_active']
        list_filter = ['region', 'is_active']
        search_fields = ['name']
        list_editable = ['delivery_fee', 'is_active']

    @admin.register(MobileMoneyPayment)
    class MobileMoneyPaymentAdmin(admin.ModelAdmin):
        list_display = ['transaction_id', 'order', 'provider', 'phone_number', 'amount', 'status', 'created_at']
        list_filter = ['provider', 'status', 'created_at']
        search_fields = ['transaction_id', 'phone_number', 'order__order_id']
        readonly_fields = ['transaction_id', 'created_at']

    @admin.register(SMSNotification)
    class SMSNotificationAdmin(admin.ModelAdmin):
        list_display = ['recipient', 'notification_type', 'status', 'created_at']
        list_filter = ['notification_type', 'status', 'created_at']
        search_fields = ['recipient', 'message']

    @admin.register(SellerProfile)
    class SellerProfileAdmin(admin.ModelAdmin):
        list_display = ['business_name', 'customer', 'verification_status', 'total_sales', 'rating']
        list_filter = ['verification_status']
        search_fields = ['business_name', 'customer__user__username']
        list_editable = ['verification_status']

    @admin.register(BulkOrderRequest)
    class BulkOrderRequestAdmin(admin.ModelAdmin):
        list_display = ['product', 'quantity', 'company_name', 'status', 'created_at']
        list_filter = ['status', 'created_at']
        search_fields = ['company_name', 'product__name']

    @admin.register(PromoCode)
    class PromoCodeAdmin(admin.ModelAdmin):
        list_display = ['code', 'discount_type', 'discount_value', 'is_active', 'times_used', 'max_uses']
        list_filter = ['discount_type', 'is_active']
        search_fields = ['code']
        list_editable = ['is_active']


# Register extended models if available
if EXTENDED_MODELS:
    try:
        @admin.register(DeliveryRider)
        class DeliveryRiderAdmin(admin.ModelAdmin):
            list_display = ['name', 'phone', 'vehicle_type', 'is_active', 'is_available', 'total_deliveries', 'average_rating']
            list_filter = ['vehicle_type', 'is_active', 'is_available']
            search_fields = ['name', 'phone']
            list_editable = ['is_active', 'is_available']

        @admin.register(Delivery)
        class DeliveryAdmin(admin.ModelAdmin):
            list_display = ['order', 'rider', 'status', 'estimated_delivery', 'actual_delivery', 'customer_rating']
            list_filter = ['status', 'created_at']
            search_fields = ['order__order_id', 'rider__name']

        @admin.register(Testimonial)
        class TestimonialAdmin(admin.ModelAdmin):
            list_display = ['name', 'role', 'rating', 'is_active', 'created_at']
            list_filter = ['is_active', 'rating']
            search_fields = ['name', 'content']
            list_editable = ['is_active']

        @admin.register(NewsletterSubscriber)
        class NewsletterSubscriberAdmin(admin.ModelAdmin):
            list_display = ['email', 'is_active', 'subscribed_at']
            list_filter = ['is_active']
            search_fields = ['email']

        @admin.register(ContactMessage)
        class ContactMessageAdmin(admin.ModelAdmin):
            list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
            list_filter = ['is_read', 'subject', 'created_at']
            search_fields = ['name', 'email', 'message']

        @admin.register(SiteSetting)
        class SiteSettingAdmin(admin.ModelAdmin):
            list_display = ['key', 'value']
            search_fields = ['key']
    except:
        pass
