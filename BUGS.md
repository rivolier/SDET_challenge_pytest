# Bugs Report

Bugs found while testing the User Management API against
`sdet_challenge_api.yml`. Each entry references the automated test
that exposes the issue. Confirmed via a real local run against the
Docker image on 2026-08-16.

---

## Bug #1 — Email format is not validated on create

- **Endpoint**: `POST /{env}/users`
- **Test**: `tests/test_create_user.py::test_create_user_invalid_email_returns_400`
- **Severity**: High

**Expected (per spec)**: `email` has `format: email`. Malformed values
(`not-an-email`, `missing-at-sign.com`, `@no-local-part.com`, values
with embedded spaces) should be rejected with `400`.

**Observed**: The API returns `201` and creates the user as-is, with
no format validation at all. Confirmed cleanly on a fresh container
(all four malformed variants tested independently return `201`).

**Request used to reproduce**:
```
POST /dev/users
Body: {"name": "QA Test User", "email": "not-an-email", "age": 30}
```

**Response received**:
```
Status: 201
Body: {"name": "QA Test User", "email": "not-an-email", "age": 30}
```

---

## Bug #2 — Duplicate email crashes the server instead of returning 409

- **Endpoint**: `POST /{env}/users`
- **Test**: `tests/test_create_user.py::test_create_user_duplicate_email_same_environment_returns_409`
- **Severity**: High

**Expected (per spec)**: Creating a user with an email that already
exists should return `409` with an `ErrorResponse` body.

**Observed**: The server returns `500` — an unhandled exception,
likely from an uniqueness check implemented as an unguarded insert
(e.g. an unhandled `KeyError`/constraint violation instead of an
explicit existence check before insert).

**Request used to reproduce**:
```
POST /dev/users   (email already exists from a prior successful create)
Body: {"name": "QA Test User", "email": "<existing email>", "age": 30}
```

**Response received**:
```
Status: 500
```

---

## Bug #3 — DELETE does not actually enforce authentication

- **Endpoint**: `DELETE /{env}/users/{email}`
- **Test**: `tests/test_delete_user.py::test_delete_without_token_returns_401`,
  `tests/test_delete_user.py::test_delete_with_invalid_token_returns_401`
- **Severity**: Critical (security)

**Expected (per spec)**: `Authentication` header is `required`;
missing or invalid token should return `401`.

**Observed**: The delete succeeds (`204`) with no token at all, and
also with a clearly invalid token. Auth is effectively not enforced
on this endpoint, even though it's the one endpoint the spec
explicitly protects.

**Request used to reproduce**:
```
DELETE /dev/users/<existing email>
Headers: (none)
```

**Response received**:
```
Status: 204
```

---

## Bug #4 — GET on a nonexistent user crashes instead of returning 404

- **Endpoint**: `GET /{env}/users/{email}`
- **Test**: `tests/test_get_user.py::test_get_nonexistent_user_returns_404`,
  `tests/test_delete_user.py::test_deleted_user_is_not_retrievable`
- **Severity**: High

**Expected (per spec)**: `404` with an `ErrorResponse` body when the
email doesn't exist.

**Observed**: `500`. Reproduced two different ways (an email that was
never created, and an email that existed but was just deleted) —
consistent behavior both times, so this isn't a fluke.

**Request used to reproduce**:
```
GET /dev/users/never-created@example.com
```

**Response received**:
```
Status: 500
```

---

## Bug #5 — Unsupported HTTP verb returns 500 instead of 404/405

- **Endpoint**: `PATCH /{env}/users` (not defined in spec)
- **Test**: `tests/test_cross_cutting.py::test_unsupported_http_verb_on_collection`
- **Severity**: Medium

**Expected**: Framework-level routing should return `404` (route
doesn't exist for that method) or `405` (method not allowed).

**Observed**: `500`.

---

## Candidate #6 — PUT with mismatched body/path email (pending confirmation)

- **Endpoint**: `PUT /{env}/users/{email}`
- **Test**: `tests/test_update_user.py::test_update_user_email_in_body_differs_from_path`
- **Severity**: TBD (depends on actual observed behavior)

**Expected (design decision, not explicit in spec)**: the spec lists
`email` as the resource's primary key *and* a required field in the
update body, but never defines what should happen when the two
differ. Decided to treat this as `400` (validation error) -- the path
is the source of truth for which resource is being updated, and
silently renaming a primary key via `PUT`, or accepting an ambiguous
request, is riskier than rejecting it outright.

**Observed**: not yet confirmed with a real run since the assertion
was tightened from a soft check (`200/400/404/409`) to a strict
`400`. Run the suite and update this entry with the actual status
code. If it's not `400`, log the real behavior here and keep the
test failing as documentation of the gap (same pattern as the other
bugs above).

---

## Under investigation — possible state corruption after Bug #2

**Resolved — not an API bug, and not `dict(user_payload)` either.**
Initial suspicion was that Bug #2's unhandled exception left the
in-memory store in a bad state. That was ruled out: other `POST`
calls immediately surrounding the Bug #2 trigger in the same test run
succeeded normally.

The real cause was a pytest fixture-caching pitfall, and it took two
attempts to fully fix: pytest caches a function-scoped fixture's
value for the whole test, no matter how many other fixtures (directly
or indirectly) depend on it or how many times it's requested. The
failing test's setup wanted a genuinely new, independent second user,
but every approach that pulled the email from a fixture already
consumed elsewhere in the same test (`user_payload`, then even
`unique_email` on the next attempt) kept handing back the *same*
cached value already used by `created_user` -- silently turning
"create an independent second user" into a duplicate-email request,
which correctly (if you can call a 500 correct) re-triggered Bug #2.
Fixed by generating the second email inline with `uuid` instead of
via any shared fixture.

---

## Ruled out / working as expected

- Age boundary validation (`1`–`150`, integer-only) — enforced correctly.
- Cross-environment isolation (same email in `dev` and `prod`) — working.
- Double delete → second attempt correctly returns `404`.
- `PUT` to a wrong environment correctly returns `404`.
- Missing required fields on `POST`/`PUT` correctly return `400`.
