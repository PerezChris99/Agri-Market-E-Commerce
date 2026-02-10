from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
import uuid


class Category(models.Model):
    """Product categories for organizing agricultural products"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Customer(models.Model):
    """Extended user profile for customers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    phone = models.CharField(max_length=20, null=True, blank=True, help_text="Format: 0700000000")
    alternate_phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Farmer/Seller status
    is_farmer = models.BooleanField(default=False)
    
    # Mobile Money preferences
    preferred_payment_method = models.CharField(
        max_length=20, 
        choices=[('mtn', 'MTN Mobile Money'), ('airtel', 'Airtel Money'), ('paypal', 'PayPal')],
        default='mtn'
    )
    momo_phone = models.CharField(max_length=15, null=True, blank=True, help_text="MTN/Airtel number for payments")
    
    # Preferences
    receive_sms = models.BooleanField(default=True, help_text="Receive SMS notifications")
    receive_whatsapp = models.BooleanField(default=True, help_text="Receive WhatsApp updates")
    language_preference = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('lg', 'Luganda'), ('sw', 'Kiswahili')],
        default='en'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username if self.user else 'Anonymous'

    @property
    def name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username

    @property
    def email(self):
        return self.user.email


# Signal to automatically create Customer when User is created
@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_customer_profile(sender, instance, **kwargs):
    if hasattr(instance, 'customer'):
        instance.customer.save()


class Product(models.Model):
    """Agricultural product model with enhanced features"""
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('piece', 'Piece'),
        ('bunch', 'Bunch'),
        ('bag', 'Bag (50kg)'),
        ('crate', 'Crate'),
        ('litre', 'Litre'),
        ('dozen', 'Dozen'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    stock = models.PositiveIntegerField(default=0)
    digital = models.BooleanField(default=False, help_text='Is this a digital product (no shipping needed)?')
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    seller = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = '/static/images/placeholder.png'
        return url

    @property
    def in_stock(self):
        return self.stock > 0

    def reduce_stock(self, quantity):
        """Reduce stock after purchase"""
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False


class Order(models.Model):
    """Order model with improved status tracking"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Payment Pending'),
        ('completed', 'Payment Completed'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order_id = models.CharField(max_length=100, unique=True, editable=False, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True, related_name='orders')
    # Guest checkout fields
    guest_name = models.CharField(max_length=200, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    
    date_ordered = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.CharField(max_length=200, null=True, blank=True)
    
    complete = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_ordered']

    def __str__(self):
        return f"Order #{self.order_id or self.id}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"AGR-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def requires_shipping(self):
        """Check if order contains physical products that need shipping"""
        orderitems = self.items.all()
        for item in orderitems:
            if item.product and not item.product.digital:
                return True
        return False

    @property
    def get_cart_total(self):
        orderitems = self.items.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.items.all()
        total = sum([item.quantity for item in orderitems])
        return total

    def mark_as_paid(self, transaction_id, payment_method='paypal'):
        """Mark order as paid"""
        self.transaction_id = transaction_id
        self.payment_method = payment_method
        self.payment_status = 'completed'
        self.complete = True
        self.status = 'processing'
        self.save()
        
        # Reduce stock for all items
        for item in self.items.all():
            if item.product:
                item.product.reduce_stock(item.quantity)


class OrderItem(models.Model):
    """Individual items within an order"""
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.product.name if self.product else 'Unknown'}"

    def save(self, *args, **kwargs):
        # Save the price at time of purchase
        if not self.price_at_purchase and self.product:
            self.price_at_purchase = self.product.price
        super().save(*args, **kwargs)

    @property
    def get_total(self):
        price = self.price_at_purchase or (self.product.price if self.product else Decimal('0'))
        return price * self.quantity


class ShippingAddress(models.Model):
    """Shipping address for orders - Uganda optimized"""
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipping_address')
    
    # Contact
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True, default='')
    
    # Address
    address = models.CharField(max_length=300, help_text="Street/Road, Building, etc.")
    landmark = models.CharField(max_length=200, blank=True, default='', help_text="Nearby landmark for easy location")
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, default='Kampala')
    region = models.CharField(max_length=100, default='Central Region')
    country = models.CharField(max_length=100, default='Uganda')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    
    # Delivery
    delivery_zone = models.ForeignKey('DeliveryZone', on_delete=models.SET_NULL, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    delivery_notes = models.TextField(blank=True, help_text="Special delivery instructions")
    preferred_delivery_time = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning (8AM-12PM)'),
            ('afternoon', 'Afternoon (12PM-5PM)'),
            ('evening', 'Evening (5PM-8PM)'),
            ('anytime', 'Anytime'),
        ],
        default='anytime'
    )
    
    # GPS for boda/delivery
    gps_coordinates = models.CharField(max_length=50, blank=True, default='', help_text="lat,lng for delivery")
    
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Shipping Addresses'

    def __str__(self):
        return f"{self.full_name}, {self.district}"
    
    def calculate_delivery_fee(self, order_total):
        """Calculate delivery fee based on zone"""
        if self.delivery_zone:
            return self.delivery_zone.get_delivery_fee(order_total)
        return Decimal('10000')  # Default fee


class Wishlist(models.Model):
    """Customer wishlist for products"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['customer', 'product']

    def __str__(self):
        return f"{self.customer.name}'s wishlist - {self.product.name}"


class Review(models.Model):
    """Product reviews and ratings with enhanced features"""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    
    # Verification
    is_verified_purchase = models.BooleanField(default=False)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Engagement
    helpful_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'customer']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} - {self.product.name} ({self.rating}/5)"


# ============================================
# UGANDA-SPECIFIC MODELS FOR LOCAL COMMERCE
# ============================================

class DeliveryZone(models.Model):
    """
    Uganda delivery zones based on districts and regions.
    Allows for different delivery fees based on location.
    """
    REGION_CHOICES = [
        ('central', 'Central Region'),
        ('eastern', 'Eastern Region'),
        ('northern', 'Northern Region'),
        ('western', 'Western Region'),
        ('kampala', 'Kampala Metropolitan'),
    ]
    
    name = models.CharField(max_length=100, help_text="District or area name")
    region = models.CharField(max_length=50, choices=REGION_CHOICES)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5000'))
    estimated_days = models.PositiveIntegerField(default=2, help_text="Estimated delivery days")
    is_active = models.BooleanField(default=True)
    free_delivery_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, 
        default=Decimal('100000'),
        help_text="Order amount for free delivery"
    )
    
    class Meta:
        ordering = ['region', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.get_region_display()})"
    
    def get_delivery_fee(self, order_total):
        """Calculate delivery fee based on order total"""
        if order_total >= self.free_delivery_threshold:
            return Decimal('0')
        return self.delivery_fee


class MobileMoneyPayment(models.Model):
    """
    Mobile Money payment records for MTN MoMo and Airtel Money.
    Tracks payment requests and their status.
    """
    PROVIDER_CHOICES = [
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('timeout', 'Timeout'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='mobile_payments')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    phone_number = models.CharField(max_length=15, help_text="Format: 256700000000")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Transaction details
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    external_reference = models.CharField(max_length=200, null=True, blank=True)
    provider_reference = models.CharField(max_length=200, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_provider_display()} - {self.phone_number} - UGX {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"MM-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
    
    def mark_successful(self, provider_reference=None):
        """Mark payment as successful"""
        self.status = 'successful'
        self.completed_at = timezone.now()
        if provider_reference:
            self.provider_reference = provider_reference
        self.save()
        
        # Update the order
        self.order.mark_as_paid(
            transaction_id=self.transaction_id,
            payment_method=f"mobile_money_{self.provider}"
        )
    
    def mark_failed(self, message="Payment failed"):
        """Mark payment as failed"""
        self.status = 'failed'
        self.status_message = message
        self.save()


class SMSNotification(models.Model):
    """
    SMS notifications for order updates and marketing.
    Uses Africa's Talking or similar SMS gateway.
    """
    TYPE_CHOICES = [
        ('order_confirmation', 'Order Confirmation'),
        ('payment_received', 'Payment Received'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('promotional', 'Promotional'),
        ('otp', 'OTP Verification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    recipient = models.CharField(max_length=15, help_text="Phone number in format: 256700000000")
    message = models.TextField(max_length=480)  # 3 SMS max
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related objects
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_notifications')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Gateway response
    gateway_message_id = models.CharField(max_length=200, null=True, blank=True)
    gateway_response = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"SMS to {self.recipient} - {self.get_notification_type_display()}"


class SellerProfile(models.Model):
    """
    Extended profile for farmers/sellers who want to list products.
    Includes verification and payout information.
    """
    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=200)
    business_description = models.TextField(blank=True)
    
    # Location
    district = models.ForeignKey(DeliveryZone, on_delete=models.SET_NULL, null=True, blank=True)
    physical_address = models.TextField(blank=True)
    gps_coordinates = models.CharField(max_length=50, blank=True, help_text="lat,lng format")
    
    # Verification
    national_id = models.CharField(max_length=20, blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verification_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Payout information
    preferred_payout_method = models.CharField(max_length=20, choices=MobileMoneyPayment.PROVIDER_CHOICES, default='mtn')
    payout_phone = models.CharField(max_length=15, blank=True)
    
    # Statistics
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    total_orders = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0'))
    
    # Settings
    auto_accept_orders = models.BooleanField(default=True)
    receive_sms_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.business_name} ({self.customer.name})"
    
    @property
    def is_verified(self):
        return self.verification_status == 'verified'


class BulkOrderRequest(models.Model):
    """
    Bulk order requests for wholesalers and large buyers.
    Allows negotiation on pricing for large quantities.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('quoted', 'Quote Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    # Requester
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='bulk_requests')
    company_name = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField(blank=True)
    
    # Product details
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    preferred_unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Quote
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    quote_valid_until = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Delivery
    delivery_location = models.TextField()
    preferred_delivery_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Bulk: {self.quantity}x {self.product.name} by {self.customer.name}"
    
    @property
    def total_value(self):
        price = self.quoted_price or self.product.price
        return price * self.quantity


class PromoCode(models.Model):
    """Promotional codes for discounts"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Limits
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    times_used = models.PositiveIntegerField(default=0)
    max_uses_per_user = models.PositiveIntegerField(default=1)
    
    # Validity
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Restrictions
    applicable_categories = models.ManyToManyField(Category, blank=True)
    first_order_only = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else ' UGX'}"
    
    def is_valid(self, order_total, user=None):
        """Check if promo code is valid for use"""
        now = timezone.now()
        
        if not self.is_active:
            return False, "This promo code is not active"
        
        if now < self.valid_from or now > self.valid_until:
            return False, "This promo code has expired"
        
        if self.max_uses > 0 and self.times_used >= self.max_uses:
            return False, "This promo code has reached its usage limit"
        
        if order_total < self.min_order_amount:
            return False, f"Minimum order amount is UGX {self.min_order_amount:,.0f}"
        
        return True, "Valid"
    
    def calculate_discount(self, order_total):
        """Calculate discount amount"""
        if self.discount_type == 'percentage':
            return order_total * (self.discount_value / 100)
        return min(self.discount_value, order_total)


class USSDSession(models.Model):
    """
    USSD session tracking for feature phone users.
    Allows basic ordering via USSD codes.
    """
    SESSION_STATES = [
        ('start', 'Start'),
        ('category_select', 'Selecting Category'),
        ('product_select', 'Selecting Product'),
        ('quantity_input', 'Entering Quantity'),
        ('confirm', 'Confirming Order'),
        ('payment', 'Payment'),
        ('complete', 'Complete'),
    ]
    
    session_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15)
    state = models.CharField(max_length=30, choices=SESSION_STATES, default='start')
    
    # Session data
    selected_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    selected_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    
    # Result
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"USSD: {self.phone_number} - {self.state}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        super().save(*args, **kwargs)


# ============================================
# DELIVERY TRACKING SYSTEM
# ============================================

class DeliveryRider(models.Model):
    """Delivery riders/boda-boda drivers"""
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    vehicle_type = models.CharField(
        max_length=20,
        choices=[
            ('boda', 'Boda-Boda (Motorcycle)'),
            ('car', 'Car'),
            ('van', 'Van'),
            ('truck', 'Truck'),
            ('bicycle', 'Bicycle'),
        ],
        default='boda'
    )
    vehicle_number = models.CharField(max_length=20, blank=True)
    
    # Performance
    total_deliveries = models.PositiveIntegerField(default=0)
    successful_deliveries = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.00'))
    
    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    current_location_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    current_location_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Zones
    assigned_zones = models.ManyToManyField(DeliveryZone, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.vehicle_type})"
    
    @property
    def success_rate(self):
        if self.total_deliveries == 0:
            return 100
        return round((self.successful_deliveries / self.total_deliveries) * 100, 1)


class Delivery(models.Model):
    """Delivery tracking for orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending Assignment'),
        ('assigned', 'Rider Assigned'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('nearby', 'Nearby Destination'),
        ('delivered', 'Delivered'),
        ('failed', 'Delivery Failed'),
        ('returned', 'Returned'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    rider = models.ForeignKey(DeliveryRider, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_history = models.JSONField(default=list, blank=True)  # Track all status changes
    
    # Timing
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    
    # Location tracking
    current_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Delivery details
    delivery_notes = models.TextField(blank=True)
    signature_image = models.ImageField(upload_to='delivery_signatures/', null=True, blank=True)
    delivery_photo = models.ImageField(upload_to='delivery_photos/', null=True, blank=True)
    
    # Rating
    customer_rating = models.PositiveIntegerField(null=True, blank=True)  # 1-5
    customer_feedback = models.TextField(blank=True)
    
    # OTP verification
    delivery_otp = models.CharField(max_length=6, blank=True)
    otp_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Delivery for {self.order.order_id}"
    
    def save(self, *args, **kwargs):
        # Generate OTP if not exists
        if not self.delivery_otp:
            import random
            self.delivery_otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        super().save(*args, **kwargs)
    
    def update_status(self, new_status, notes=''):
        """Update delivery status and track in history"""
        old_status = self.status
        self.status = new_status
        
        # Add to history
        self.status_history.append({
            'from': old_status,
            'to': new_status,
            'timestamp': timezone.now().isoformat(),
            'notes': notes
        })
        
        # Update timestamps
        if new_status == 'picked_up':
            self.picked_up_at = timezone.now()
        elif new_status == 'delivered':
            self.actual_delivery = timezone.now()
            if self.rider:
                self.rider.total_deliveries += 1
                self.rider.successful_deliveries += 1
                self.rider.save()
        elif new_status == 'failed':
            if self.rider:
                self.rider.total_deliveries += 1
                self.rider.save()
        
        self.save()
    
    def get_tracking_timeline(self):
        """Get formatted timeline for frontend"""
        timeline = [
            {'status': 'pending', 'label': 'Order Confirmed', 'icon': '✓'},
            {'status': 'assigned', 'label': 'Rider Assigned', 'icon': '👤'},
            {'status': 'picked_up', 'label': 'Picked Up', 'icon': '📦'},
            {'status': 'in_transit', 'label': 'In Transit', 'icon': '🚚'},
            {'status': 'delivered', 'label': 'Delivered', 'icon': '📍'},
        ]
        
        status_order = ['pending', 'assigned', 'picked_up', 'in_transit', 'nearby', 'delivered']
        current_index = status_order.index(self.status) if self.status in status_order else 0
        
        for i, step in enumerate(timeline):
            if i < current_index:
                step['completed'] = True
                step['current'] = False
            elif i == current_index:
                step['completed'] = False
                step['current'] = True
            else:
                step['completed'] = False
                step['current'] = False
        
        return timeline


class DeliveryLocation(models.Model):
    """Track delivery rider location history"""
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='location_history')
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    accuracy = models.FloatField(null=True, blank=True)  # GPS accuracy in meters
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.delivery.order.order_id} - {self.timestamp}"


# ============================================
# ENHANCED REVIEWS WITH PHOTOS
# ============================================

class ReviewImage(models.Model):
    """Images attached to product reviews"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for review of {self.review.product.name}"


class ReviewHelpful(models.Model):
    """Track helpful votes on reviews"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    is_helpful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'customer']


# ============================================
# TESTIMONIALS
# ============================================

class Testimonial(models.Model):
    """Customer testimonials for homepage"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100, blank=True, help_text="e.g., Farmer, Restaurant Owner")
    location = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to='testimonials/', null=True, blank=True)
    content = models.TextField()
    rating = models.PositiveIntegerField(default=5, choices=[(i, str(i)) for i in range(1, 6)])
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.rating}★"


# ============================================
# NEWSLETTER
# ============================================

class NewsletterSubscriber(models.Model):
    """Newsletter email subscribers"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.email


# ============================================
# CONTACT MESSAGES
# ============================================

class ContactMessage(models.Model):
    """Contact form submissions"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.name}"


# ============================================
# SITE SETTINGS
# ============================================

class SiteSetting(models.Model):
    """Dynamic site settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key
    
    @classmethod
    def get(cls, key, default=''):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

