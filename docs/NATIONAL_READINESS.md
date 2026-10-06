# National Readiness

This document defines the application-layer boundary for deploying Agri-Market as national agricultural commerce infrastructure.

## Implemented application capabilities

- Transactional catalog, cart, checkout and order lifecycle
- Concurrency-safe inventory commitment
- Payment verification and idempotency
- Seller settlement ledger
- Promotion redemption ledger
- Delivery state and GPS authorization
- Audit logging and request correlation
- Redis-backed caching and Celery task infrastructure
- PostgreSQL-oriented search and indexing
- Administrative-area hierarchy
- Logistics hubs and collection/distribution structures
- Farmer verification workflow state
- Support tickets and operational incidents
- Versioned /api/v1/ catalog, geography, logistics and readiness endpoints
- Institutional API-key authentication with hashed secrets
- Idempotent offline synchronization envelope
- Machine-readable readiness reporting

## National-scale architecture boundary

The application is designed to remain stateless at the web tier. PostgreSQL is the system of record, Redis provides cache/broker infrastructure, object storage holds untrusted media, and workers execute asynchronous workloads.

Horizontal application and worker scaling should be performed only after load testing against the target infrastructure.

## Offline synchronization contract

Clients send device_id, idempotency_key, event_type and payload. The server stores the event once and returns the existing event for repeated idempotency keys. Domain-specific conflict resolution should be implemented per event type rather than blindly applying client state.

## Institutional API

API clients are represented by a database record containing only a SHA-256 hash of the issued secret. The raw key is printed once by the management command and must be stored in an external secret manager.

Current v1 endpoints: /api/v1/products/, /api/v1/areas/, /api/v1/hubs/, /api/v1/sync/, /api/v1/readiness/. The readiness endpoint is staff-protected.

## Operational readiness

The codebase cannot manufacture external availability. Before national production, operators must provision highly available PostgreSQL and tested backups, highly available Redis, durable object storage, CDN and edge protection, production email/SMS/WhatsApp providers, certified mobile-money and banking integrations, monitoring and alerting, disaster-recovery infrastructure and restoration drills, production-like load/soak/chaos tests, security assessment, and required legal/privacy/sector approvals.

The repository deliberately treats these as deployment gates rather than fake local implementations.

## Readiness command

Run: python manage.py national_readiness

The command emits JSON and exits non-zero when required application configuration is absent.
