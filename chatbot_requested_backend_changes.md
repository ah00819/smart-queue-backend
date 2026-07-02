#  SmartIQ Chatbot Backend Change Log

> This document summarizes only the backend modifications that were explicitly requested during the chatbot integration.  
> It does **not** include n8n workflow changes, Flutter changes, or existing backend features that were reused without modification.

---

# 1. Expose Organization Name in Service API

## Objective

The chatbot needed to display the organization name associated with each service without making an additional API request.

---

## Modified Files

- `api/serializers.py`
- `api/views.py`

---

## Implementation

### Service Serializer

Added a new read-only field:

```python
organization_name = serializers.CharField(
    source="organization.name",
    read_only=True
)
```

### Service ViewSet

Optimized the queryset to eagerly load the related organization and required documents:

```python
select_related("organization")
prefetch_related("required_documents")
```

This prevents unnecessary database queries (N+1 Query Problem).

---

## Affected APIs

- `GET /api/services/`
- `GET /api/services/{id}/`

---

## Chatbot Usage

The chatbot can now retrieve the organization name directly from the Service API response without issuing another backend request.

---

## Status

✅ Implemented

---

# 2. Booking API Integration

## Objective

Replace the temporary Google Sheets booking workflow with the official Django booking system.

---

## Backend Changes

No backend modifications were required.

The existing booking implementation already provided all required functionality, including:

- Appointment creation
- Counter validation
- Slot validation
- Duplicate booking protection
- Time conflict validation

The chatbot simply consumes the existing APIs.

---

## APIs Used

- `GET /api/organizations/{id}/branches/`
- `GET /api/branches/{id}/service-counters/`
- `GET /api/branches/{id}/service-counters/{counter_id}/available_slots/`
- `POST /api/appointments/`

---

## Chatbot Usage

The chatbot now books appointments directly through the production booking APIs instead of generating local records.

---

## Status

♻️ Reused Existing Backend (No Code Changes)

---

# 3. Authentication Flow Review

## Objective

Verify how authenticated users are identified when creating appointments through the chatbot.

---

## Backend Changes

No backend modifications were required.

The backend already supports JWT authentication through Django REST Framework and automatically resolves:

```text
request.user
        ↓
request.user.client
```

Therefore, the chatbot does not need to send a `client_id`.

The only responsibility of n8n is forwarding the user's JWT as the standard `Authorization` header.

---

## Affected API

- `POST /api/appointments/`

---

## Chatbot Usage

Appointments are automatically linked to the authenticated client profile.

---

## Status

♻️ Reused Existing Backend (No Code Changes)

---

# Summary

| Requested Feature | Backend Changes | Status |
|-------------------|-----------------|--------|
| Expose organization name in Service API | `api/serializers.py`, `api/views.py` | ✅ Implemented |
| Booking API integration | No backend changes | ♻️ Reused |
| JWT authentication flow | No backend changes | ♻️ Reused |

---

# Final Notes

During the chatbot integration, only one functional backend enhancement was required:

- Exposing the organization name through the Service API.

All other chatbot capabilities—including appointment creation, slot generation, validation rules, duplicate booking protection, and JWT authentication—were already supported by the existing backend and were integrated without modifying backend business logic.