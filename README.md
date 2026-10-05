# Agri-Market

> Production-oriented agricultural commerce platform built for Uganda.

[![CI](https://github.com/PerezChris99/Agri-Market-E-Commerce/actions/workflows/ci.yml/badge.svg)](https://github.com/PerezChris99/Agri-Market-E-Commerce/actions/workflows/ci.yml)
[![Django](https://img.shields.io/badge/Django-5.2_LTS-0C4B33?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

Agri-Market is a Django marketplace for fresh agricultural products, connecting Ugandan farmers and sellers with consumers and larger buyers. The platform is designed around local commerce requirements including UGX pricing, MTN Mobile Money, Airtel Money, Uganda-wide delivery zones, SMS notifications, seller verification, delivery tracking, and marketplace settlement.

The engineering target is straightforward: **secure transactions, predictable data integrity, efficient queries, observable services, and a deployment process that fails before bad code reaches production.**

---

## What the platform does

### Commerce
- Agricultural product catalog and category browsing
- Product search, filtering, sorting, and pagination
- Persistent authenticated carts
- Cookie-based anonymous carts
- Guest cash-on-delivery checkout
- Authenticated electronic-payment checkout
- Order history and order detail views
- Wishlist management
- Verified product reviews
- Promotional codes and redemption ledger

### Payments
- MTN Mobile Money
- Airtel Money
- PayPal
- Flutterwave integration architecture
- Cash on Delivery
- Server-side amount/reference verification
- Authenticated webhook verification
- Idempotent payment finalization
- Atomic inventory commitment
- Payment endpoint rate limiting

### Marketplace
- Farmer/seller profiles
- Seller verification state
- Seller-specific order records
- Commission calculation
- Seller settlement ledger
- Seller payout ledger
- Bulk-order foundation

### Delivery
- Uganda delivery zones
- Rider accounts
- Delivery status history
- GPS location history
- Customer/rider/staff authorization boundaries
- Delivery tracking endpoints
- Delivery OTP foundation

### Operations
- Django admin
- Sales analytics
- Redis caching
- Celery background-task infrastructure
- S3-compatible media storage
- Sentry integration hooks
- Liveness/readiness health endpoints
- Operational audit logging
- CI migration drift detection
- Dependency vulnerability auditing

---

## Architecture

~~~text
Browser
  │
  ├── Django templates
  ├── Bootstrap
  └── Static JavaScript
          │
          ▼
     Django / WSGI
          │
          ├── Views / API endpoints
          ├── Service layer
          │     ├── payments
          │     ├── delivery
          │     ├── promotions
          │     └── audit
          │
          ├── PostgreSQL
          │     ├── indexed commerce data
          │     ├── transactional order state
          │     └── seller settlement ledgers
          │
          ├── Redis
          │     ├── cache
          │     └── Celery broker/result backend
          │
          ├── Object storage
          │     └── user/product/delivery media
          │
          └── External providers
                ├── MTN / Airtel
                ├── Flutterwave / PayPal
                ├── SMS
                └── WhatsApp
~~~

The application intentionally remains a Django monolith at this stage. The domain is large enough to require clear service boundaries, but not large enough to justify the operational cost of prematurely splitting the system into microservices.

---

## Production engineering standards

### Security

The application uses Django's security middleware and production deployment controls including:

- HTTPS enforcement in production
- Secure, HttpOnly session cookies
- SameSite cookies
- CSRF protection
- Host validation
- HSTS
- clickjacking protection
- content-type sniffing protection
- referrer policy
- cross-origin opener/resource policies
- Content Security Policy
- Argon2 password hashing for new/rehardened passwords
- request body and upload-size limits
- login and mutation endpoint rate limiting
- server-side payment verification
- signed webhook verification
- open-redirect protection
- authorization checks on customer/rider delivery data
- sensitive seller KYC/payout fields restricted in admin
- dependency vulnerability scanning in CI

### Database

Production uses PostgreSQL.

Database access follows these principles:

- foreign keys for relational integrity
- unique constraints for business invariants
- conditional uniqueness for one open customer cart/order
- transactional checkout
- row locking for order finalization
- atomic stock updates
- immutable purchase-time pricing
- indexes for common filters, joins, sorting, and operational queries
- \`select_related()\` / \`prefetch_related()\` for known relationships
- no intentional N+1 query loops in core storefront flows
- migration drift checked in CI
- no SQLite production database committed to the repository

### API

Internal JSON endpoints use:

- explicit HTTP methods
- CSRF protection for browser-originated mutations
- signed provider webhooks where applicable
- ownership/authorization checks
- bounded request payloads
- rate limiting
- server-side validation
- consistent JSON error responses
- safe error messages that do not expose internal exceptions
- transactional state changes for critical operations

The \`/api/\` surface is currently an internal application API. A public versioned REST API remains a separate product milestone.

### Frontend

The frontend is server-rendered Django HTML with static JavaScript.

Production practices include:

- deferred JavaScript loading
- no unnecessary inline application JavaScript in the shared shell
- CSP allowlisting for required third-party providers
- safe DOM text rendering instead of interpolating untrusted values into HTML
- CSRF-aware AJAX requests
- bounded client-side cart state
- responsive layouts
- accessible form labels and ARIA attributes where appropriate
- paginated product, review, wishlist, and order-history views
- CDN-hosted framework assets with explicit origin allowlisting

---

## Performance

Core performance work includes:

- PostgreSQL indexes on high-frequency access paths
- composite indexes matching real filters/orderings
- cached navigation categories
- cached homepage aggregate statistics
- annotated product ratings instead of per-product review queries
- batched anonymous-cart product lookup
- batched cart merging
- \`select_related()\` and \`prefetch_related()\` on account/order views
- persistent database connections in production
- Redis-backed caching and sessions when configured
- asynchronous SMS task infrastructure through Celery
- production static-file handling through WhiteNoise
- optional S3-compatible media storage

Pagination is deliberately applied to user-visible collections rather than returning unbounded database result sets.

---

## Reliability and availability

The order lifecycle is designed around a transactional boundary:

~~~text
Client request
     │
     ▼
Validate request
     │
     ▼
Verify external payment
     │
     ▼
Acquire order lock
     │
     ├── verify order is still open
     ├── atomically reserve/decrement stock
     ├── finalize payment
     ├── create seller settlements
     └── persist shipping information
     │
     ▼
Commit transaction
     │
     ▼
Queue notifications
~~~

Duplicate payment callbacks cannot repeatedly consume inventory.

Health probes:

~~~text
GET /health/live/
GET /health/ready/
~~~

\`live\` confirms the application process is responding.

\`ready\` verifies critical runtime dependencies including the database and cache.

---

## API surface

### Commerce

~~~text
POST /update_item/
POST /add-to-cart/<product_id>/
POST /process_order/
POST /toggle-wishlist/
~~~

### Payments

~~~text
POST /api/momo/initiate/
GET  /api/momo/status/
POST /api/momo/callback/
~~~

### Delivery

~~~text
GET  /api/delivery/<order_id>/
POST /api/delivery/<order_id>/location/
POST /api/delivery/<order_id>/status/
~~~

### Operations

~~~text
GET /health/live/
GET /health/ready/
~~~

---

## Local development

### Requirements

- Python 3.12+
- PostgreSQL for production-like development
- Redis when testing cache/Celery behavior
- Git

### Setup

~~~bash
git clone https://github.com/PerezChris99/Agri-Market-E-Commerce.git
cd Agri-Market-E-Commerce

python -m venv .venv

# Windows
.venv\\Scripts\\activate

# Linux/macOS
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

copy .env.example .env
# Edit .env for your environment

python manage.py migrate
python manage.py populate_uganda_data
python manage.py createsuperuser
python manage.py runserver
~~~

For local development, SQLite may be used when \`DATABASE_URL\` is omitted. **Production must use PostgreSQL.**

---

## Production configuration

At minimum, production should provide:

~~~env
DJANGO_SECRET_KEY=<long-random-secret>
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-domain.example
CSRF_TRUSTED_ORIGINS=https://your-domain.example
SECURE_SSL_REDIRECT=True

DATABASE_URL=postgresql://...

REDIS_URL=redis://...

AWS_STORAGE_BUCKET_NAME=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_REGION_NAME=...
AWS_S3_ENDPOINT_URL=...

SENTRY_DSN=...
APP_VERSION=...
~~~

Payment and messaging credentials should be provided only for the providers actually enabled.

Never commit \`.env\`, database credentials, provider secrets, API keys, private keys, uploaded media, SQLite databases, or runtime logs.

---

## Background workers

Run the Django application with a production WSGI server such as Gunicorn.

Celery workers are used for work that should not block the HTTP request lifecycle, such as notification delivery.

Example:

~~~bash
gunicorn ecommerce.wsgi:application
celery -A ecommerce worker --loglevel=INFO
~~~

Redis must be network-restricted and authenticated in production.

---

## Testing

Run the full application test suite:

~~~bash
python manage.py test store --verbosity 2
~~~

Run Django's production checks:

~~~bash
python manage.py check --deploy
~~~

Verify migrations:

~~~bash
python manage.py makemigrations --check --dry-run
~~~

Collect production static assets:

~~~bash
python manage.py collectstatic --noinput
~~~

Audit Python dependencies:

~~~bash
pip-audit -r requirements.txt
~~~

The GitHub Actions pipeline runs these checks automatically for \`perez\`, \`main\`, and pull requests targeting \`main\`.

---

## CI/CD policy

There are two active branches:

~~~text
perez  → development / integration
main   → production
~~~

The required workflow is:

~~~text
change
  ↓
perez
  ↓
CI
  ↓
Pull Request
  ↓
CI
  ↓
merge
  ↓
main
~~~

Each production phase should be independently committed, tested, reviewed, and merged.

The CI pipeline verifies:

- dependency installation
- dependency consistency
- Python compilation
- Django system checks
- Django deployment checks
- migration drift
- database migrations
- static asset collection
- application tests
- Python dependency vulnerabilities

---

## Repository structure

~~~text
Agri-Market-E-Commerce/
├── ecommerce/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
│
├── store/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── payments.py
│   ├── sms.py
│   ├── health.py
│   ├── utils.py
│   ├── tasks.py
│   ├── services/
│   │   ├── audit.py
│   │   ├── delivery.py
│   │   ├── payments.py
│   │   └── promotions.py
│   ├── migrations/
│   ├── management/
│   ├── templates/
│   └── test_integrity.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
~~~

---

## Current production boundary

### Implemented

- Core agricultural marketplace
- Catalog/search/filtering
- Pagination
- Persistent and anonymous carts
- Transactional checkout
- Inventory concurrency protection
- Server-side payment verification
- Payment webhook verification
- Payment idempotency
- COD lifecycle
- Seller settlement ledger
- Promotion redemption ledger
- Delivery tracking authorization
- GPS/status update controls
- Redis caching
- Celery task infrastructure
- Object-storage integration
- Sentry integration
- Audit logging
- Health probes
- Security headers and CSP
- Rate limiting
- Database indexing and integrity constraints
- Automated CI checks

### Intentionally not represented as complete

These require further provider/product work before they should be considered production-complete:

- automated seller payout execution and reconciliation
- refunds and chargebacks
- real-time WebSocket/SSE rider tracking
- dedicated rider mobile application
- full B2B credit/terms workflow
- cross-border settlement
- advanced demand forecasting
- public versioned REST/mobile API

---

## Deployment principles

Production infrastructure should provide:

1. Managed PostgreSQL with automated backups and tested restoration.
2. Redis with authentication/network isolation.
3. Object storage for media.
4. HTTPS termination at the trusted edge.
5. Gunicorn or another production WSGI/ASGI server.
6. Celery workers where asynchronous work is enabled.
7. Error monitoring.
8. Centralized logs.
9. Health-based deployment checks.
10. CI-gated migrations and application tests.
11. Database and media backup/retention policies.
12. Secret management outside Git.

The application repository cannot prove that external infrastructure is correctly backed up or configured; those controls belong in the deployment environment and must be verified there.

---

## License

MIT. See [LICENSE](LICENSE).

---

## Project

**Agri-Market**  
Uganda-focused agricultural commerce infrastructure.

Built with Django, PostgreSQL, Redis, Celery, and a production-first engineering approach.
