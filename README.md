# 🌾 Agri-Market E-Commerce

**Uganda's Premier Online Marketplace for Fresh Agricultural Products**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AgriMarket is a comprehensive e-commerce platform designed specifically for the Ugandan agricultural market. It connects farmers directly with consumers, supports local mobile money payments (MTN MoMo & Airtel Money), and provides SMS notifications for order updates.

---

## ✨ Features

### 🏠 Beautiful Homepage
- **Hero Section**: Stunning hero with animated statistics counter
- **Trust Badges**: Fresh guarantee, free delivery, mobile money, 24/7 support
- **Category Grid**: Browse by category with emoji icons
- **Featured Products**: Handpicked products with ratings and quick add-to-cart
- **How It Works**: 4-step process visualization
- **Customer Testimonials**: Social proof carousel
- **Newsletter Signup**: AJAX-powered subscription form
- **Contact Section**: Full contact form and info cards
- **WhatsApp Float Button**: Quick messaging support

### 📊 Admin Dashboard
- **Real-time Stats**: Revenue, orders, customers, products at a glance
- **Sales Line Chart**: 30-day sales trend visualization
- **Orders Bar Chart**: Orders by status breakdown
- **Category Pie Chart**: Sales distribution by category
- **Payment Donut Chart**: Payment methods breakdown
- **Uganda Map**: Order density heatmap by region
- **Recent Orders Table**: Quick order management
- **Top Products**: Best-selling products list
- **Active Deliveries**: Live delivery tracking with progress timeline

### 🛒 Core E-Commerce
- **Product Catalog**: Browse 44+ agricultural products across 11 categories
- **Smart Search**: Filter by category, price, and availability
- **Shopping Cart**: Persistent cart for logged-in users, cookie-based cart for guests
- **Guest Checkout**: Purchase without creating an account
- **Order Tracking**: Real-time order status updates

### 💳 Uganda Payment Methods
- **MTN Mobile Money** - Support for 076X, 077X, 078X numbers
- **Airtel Money** - Support for 070X, 074X, 075X numbers  
- **PayPal/Cards** - International payment option
- **Cash on Delivery** - Pay when you receive your order
- **Flutterwave Integration** - Unified payment gateway

### 📱 SMS & WhatsApp Notifications
- Order confirmations in English & Luganda
- Payment receipts
- Delivery updates with rider details
- OTP verification
- Promotional messages (opt-in)

### 🚚 Delivery System
- **110 Delivery Zones** covering all Uganda districts
- **Delivery Tracking**: Real-time GPS tracking with progress timeline
- **Delivery Riders**: Rider profiles with ratings and vehicle types
- Region-based delivery fees (UGX 3,000 - 28,000)
- Estimated delivery times by region
- GPS coordinates for boda-boda riders
- Landmark-based directions
- Preferred delivery time slots
- OTP verification on delivery

### ⭐ Reviews & Ratings
- **Verified Purchase Badge**: Only buyers can review
- **Review Images**: Upload photos with reviews
- **Helpful Votes**: Vote on helpful reviews
- **Featured Reviews**: Highlight best reviews

### 👨‍🌾 Farmer Features
- Seller/Farmer profiles with verification
- Bulk order requests for wholesalers
- Product management
- Sales analytics

### 🎨 Modern UI/UX
- Beautiful agricultural green & cream theme
- Fully responsive Bootstrap 5.3 design
- Chart.js for data visualizations
- Leaflet.js for interactive maps
- Animated product cards
- Toast notifications
- Custom scrollbar styling

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Agri-Market-E-Commerce.git
cd Agri-Market-E-Commerce

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
copy .env.example .env
# Edit .env with your API keys

# Run migrations
python manage.py migrate

# Populate Uganda data (delivery zones, categories, products)
python manage.py populate_uganda_data

# Create admin user
python manage.py createsuperuser

# Start the server
python manage.py runserver
```

### Access the Application
- **Store**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/

---

## 📁 Project Structure

```
Agri-Market-E-Commerce/
├── ecommerce/              # Django project settings
│   ├── settings.py         # Configuration (payments, SMS, etc.)
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI application
├── store/                  # Main store application
│   ├── models.py           # Data models (15+ models)
│   ├── views.py            # View logic & API endpoints
│   ├── payments.py         # Mobile money integration
│   ├── sms.py              # SMS notification service
│   ├── urls.py             # Store URL routing
│   ├── forms.py            # Django forms
│   ├── utils.py            # Cart utilities
│   ├── admin.py            # Admin customization
│   ├── management/         # Custom management commands
│   │   └── commands/
│   │       └── populate_uganda_data.py
│   └── templates/store/    # HTML templates
├── static/
│   ├── css/main.css        # Custom agricultural theme
│   ├── js/cart.js          # Cart JavaScript
│   └── images/             # Static images
├── logs/                   # Application logs
├── .env.example            # Environment variables template
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True

# PayPal
PAYPAL_CLIENT_ID=your-paypal-client-id

# MTN Mobile Money
MTN_MOMO_API_USER=your-api-user
MTN_MOMO_API_KEY=your-api-key
MTN_MOMO_SUBSCRIPTION_KEY=your-subscription-key
MTN_MOMO_ENVIRONMENT=sandbox

# Airtel Money
AIRTEL_CLIENT_ID=your-client-id
AIRTEL_CLIENT_SECRET=your-client-secret
AIRTEL_ENVIRONMENT=sandbox

# Flutterwave
FLUTTERWAVE_PUBLIC_KEY=your-public-key
FLUTTERWAVE_SECRET_KEY=your-secret-key

# SMS (Africa's Talking)
AT_USERNAME=sandbox
AT_API_KEY=your-api-key
AT_SENDER_ID=AgriMarket
```

### Payment Provider Registration

| Provider | Registration URL |
|----------|-----------------|
| MTN MoMo | https://momodeveloper.mtn.com/ |
| Airtel Money | https://developers.airtel.africa/ |
| Flutterwave | https://dashboard.flutterwave.com/ |
| Africa's Talking | https://africastalking.com/ |
| PayPal | https://developer.paypal.com/ |

---

## 📊 Database Models

| Model | Description |
|-------|-------------|
| `Category` | Product categories (11 predefined) |
| `Product` | Agricultural products with pricing |
| `Customer` | Extended user profiles with MoMo preferences |
| `Order` | Customer orders with status tracking |
| `OrderItem` | Individual items in orders |
| `ShippingAddress` | Delivery addresses with GPS support |
| `DeliveryZone` | Uganda districts with delivery fees |
| `MobileMoneyPayment` | MoMo/Airtel transaction records |
| `SMSNotification` | SMS message logging |
| `SellerProfile` | Farmer verification profiles |
| `BulkOrderRequest` | Wholesale order requests |
| `PromoCode` | Discount codes |
| `Review` | Product reviews and ratings |
| `Wishlist` | Customer wishlists |
| `USSDSession` | Feature phone USSD support |

---

## 🔌 API Endpoints

### Mobile Money Payment API

```
POST /api/momo/initiate/    - Initiate mobile money payment
GET  /api/momo/status/      - Check payment status
POST /api/momo/callback/    - Payment callback (webhook)
```

### Store API

```
POST /update_item/          - Update cart item quantity
POST /add-to-cart/<id>/     - Add item to cart
POST /process_order/        - Process checkout
POST /toggle-wishlist/      - Toggle wishlist item
```

---

## 🗺️ Uganda Coverage

### Delivery Zones (110 Districts)

| Region | Districts | Delivery Fee Range | Delivery Time |
|--------|-----------|-------------------|---------------|
| Central | 21 districts | UGX 3,000 - 20,000 | 1 day |
| Eastern | 31 districts | UGX 10,000 - 20,000 | 2 days |
| Western | 29 districts | UGX 14,000 - 22,000 | 2 days |
| Northern | 30 districts | UGX 16,000 - 28,000 | 3 days |

### Product Categories

🍎 Fresh Fruits • 🥬 Vegetables • 🌾 Grains & Cereals • 🫘 Legumes & Pulses  
🥔 Roots & Tubers • 🥛 Dairy & Eggs • 🍗 Poultry & Meat • 🐟 Fish & Seafood  
☕ Coffee & Tea • 🍯 Honey & Bee Products • 🌻 Oil Seeds

---

## 🛠️ Management Commands

```bash
# Populate Uganda data (zones, categories, products)
python manage.py populate_uganda_data

# Only populate delivery zones
python manage.py populate_uganda_data --zones-only

# Only populate products
python manage.py populate_uganda_data --products-only
```

---

## 🔒 Security Features

- CSRF protection on all forms
- Secure password hashing
- Session-based authentication
- Environment variable for secrets
- SQL injection prevention (Django ORM)
- XSS protection headers

---

## 🧪 Development

### Admin Credentials (Development Only)
- **Username**: admin
- **Password**: admin123

### Running Tests
```bash
python manage.py test store
```

### Creating Migrations
```bash
python manage.py makemigrations store
python manage.py migrate
```

---

## 📦 Technologies

| Category | Technology |
|----------|------------|
| Backend | Django 4.2+, Python 3.10+ |
| Database | SQLite (dev), PostgreSQL (prod) |
| Frontend | Bootstrap 5.3, JavaScript |
| Payments | MTN MoMo, Airtel Money, PayPal, Flutterwave |
| SMS | Africa's Talking, Twilio |
| Timezone | Africa/Kampala (UTC+3) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Email**: support@agrimarket.ug
- **WhatsApp**: +256 700 000 000
- **Phone**: +256 700 000 000

---

<p align="center">
  Made with ❤️ for Ugandan Farmers 🇺🇬
</p>
