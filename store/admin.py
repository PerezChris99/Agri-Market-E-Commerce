from django.contrib import admin
from .models import Customer, Product, Order, OrderItem, ShippingAddress, Category, Wishlist, Review


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
