# Google Business Profile APIs

## Status & Versions

The Google Business Profile (GBP) API suite was restructured in late 2021/early 2022 from a monolithic
"Google My Business API v4.9" into multiple purpose-specific APIs, each with its own hostname and versioning.

| API | Current Version | Status | Notes |
|---|---|---|---|
| My Business Account Management API | v1 | Active | Replaced v4 account management |
| My Business Business Information API | v1 | Active | Replaced v4 location data |
| Business Profile Performance API | v1 | Active | Replaced deprecated v4 Insights endpoints |
| Google My Business API (legacy) | v4 | Partially active | Reviews + Posts still here; most other resources sunset |
| My Business Business Calls API | — | **Sunset** | Discontinued May 30, 2023 |

**Legacy v4 sunset history** (source: https://developers.google.com/my-business/content/sunset-dates):
- `accounts.locations.reportInsights` — discontinued March 30, 2023
- `accounts.locations.localPosts.reportInsights` — discontinued February 20, 2023
- `accounts.locations.getHealthProviderAttributes` / `updateHealthProviderAttributes` / `insuranceNetworks` — discontinued July 1, 2024
- **Reviews endpoints** (`list`, `get`, `updateReply`, `deleteReply`) — **NOT sunset, still active as of June 2026**

The reviews and local posts endpoints remain on `mybusiness.googleapis.com/v4` with no announced sunset date
as of June 2026. Google has indicated these will migrate to v1 "eventually" but has not committed to a timeline.

---

## Base URLs

| API | Base URL |
|---|---|
| Account Management | `https://mybusinessaccountmanagement.googleapis.com` |
| Business Information | `https://mybusinessbusinessinformation.googleapis.com` |
| Business Profile Performance | `https://businessprofileperformance.googleapis.com` |
| Legacy (Reviews, Posts) | `https://mybusiness.googleapis.com` |

---

## Auth / OAuth Scopes

All GBP APIs use OAuth 2.0. The primary scope covers all APIs:

| Scope | Coverage |
|---|---|
| `https://www.googleapis.com/auth/business.manage` | All current GBP APIs (Account Mgmt, Business Info, Performance) |
| `https://www.googleapis.com/auth/plus.business.manage` | Legacy v4 only (reviews endpoints also accept this scope) |

**Recommendation:** Use `business.manage` — it is accepted by all endpoints including v4 reviews.
The `plus.business.manage` scope is legacy and maps to v4 only.

Sources:
- https://developers.google.com/my-business/reference/performance/rest/v1/locations/fetchMultiDailyMetricsTimeSeries
- https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/list
- https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/updateReply

---

## APIs Overview

| API | Host | Version | Status | Purpose |
|---|---|---|---|---|
| My Business Account Management API | `mybusinessaccountmanagement.googleapis.com` | v1 | Active | Manage accounts, admins, invitations |
| My Business Business Information API | `mybusinessbusinessinformation.googleapis.com` | v1 | Active | CRUD on locations, attributes, categories |
| Business Profile Performance API | `businessprofileperformance.googleapis.com` | v1 | Active | Daily metric time series, search keyword impressions |
| Google My Business API (legacy) | `mybusiness.googleapis.com` | v4 | Partially active | Reviews, local posts (no v1 replacements yet) |

---

## Resources & Endpoints

| API | Resource | Method | HTTP | Path | Purpose | Source URL |
|---|---|---|---|---|---|---|
| Account Mgmt | accounts | list | GET | `/v1/accounts` | List all accounts accessible to authenticated user | https://developers.google.com/my-business/reference/accountmanagement/rest/v1/accounts/list |
| Account Mgmt | accounts | get | GET | `/v1/{name=accounts/*}` | Get a single account | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Account Mgmt | accounts | create | POST | `/v1/accounts` | Create a new account | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Account Mgmt | accounts | patch | PATCH | `/v1/{account.name=accounts/*}` | Update account | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Account Mgmt | accounts.admins | list | GET | `/v1/{parent=accounts/*}/admins` | List admins for an account | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Account Mgmt | accounts.admins | create | POST | `/v1/{parent=accounts/*}/admins` | Add admin to account | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Account Mgmt | accounts.admins | delete | DELETE | `/v1/{name=accounts/*/admins/*}` | Remove admin | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Account Mgmt | accounts.invitations | list | GET | `/v1/{parent=accounts/*}/invitations` | List pending invitations | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Account Mgmt | accounts.invitations | accept | POST | `/v1/{name=accounts/*/invitations/*}:accept` | Accept invitation | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Account Mgmt | accounts.invitations | decline | POST | `/v1/{name=accounts/*/invitations/*}:decline` | Decline invitation | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Account Mgmt | locations | transfer | POST | `/v1/{name=locations/*}:transfer` | Transfer location to another account | https://developers.google.com/my-business/reference/accountmanagement/rest |
| Business Info | accounts.locations | list | GET | `/v1/{parent=accounts/*}/locations` | List locations for account (readMask required) | https://developers.google.com/my-business/reference/businessinformation/rest/v1/accounts.locations/list |
| Business Info | accounts.locations | create | POST | `/v1/{parent=accounts/*}/locations` | Create a new location | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | locations | get | GET | `/v1/{name=locations/*}` | Get single location (readMask required) | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | locations | patch | PATCH | `/v1/{location.name=locations/*}` | Update location | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | locations | delete | DELETE | `/v1/{name=locations/*}` | Delete location | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | locations | getAttributes | GET | `/v1/{name=locations/*/attributes}` | Get location attributes | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | locations | updateAttributes | PATCH | `/v1/{attributes.name=locations/*/attributes}` | Update location attributes | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | locations | getGoogleUpdated | GET | `/v1/{name=locations/*}:getGoogleUpdated` | Get Google-suggested location updates | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | attributes | list | GET | `/v1/attributes` | List all available attributes | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | categories | list | GET | `/v1/categories` | List available business categories | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | categories | batchGet | GET | `/v1/categories:batchGet` | Get multiple categories | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | chains | get | GET | `/v1/{name=chains/*}` | Get a chain | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | chains | search | GET | `/v1/chains:search` | Search for chains | https://developers.google.com/my-business/reference/businessinformation/rest |
| Business Info | googleLocations | search | POST | `/v1/googleLocations:search` | Search Google Maps for locations | https://developers.google.com/my-business/reference/businessinformation/rest |
| Performance | locations | fetchMultiDailyMetricsTimeSeries | GET | `/v1/{location=locations/*}:fetchMultiDailyMetricsTimeSeries` | Fetch multiple daily metrics in one call | https://developers.google.com/my-business/reference/performance/rest/v1/locations/fetchMultiDailyMetricsTimeSeries |
| Performance | locations | getDailyMetricsTimeSeries | GET | `/v1/{name=locations/*}:getDailyMetricsTimeSeries` | Fetch a single daily metric | https://developers.google.com/my-business/reference/performance/rest/v1/locations/getDailyMetricsTimeSeries |
| Performance | locations.searchkeywords.impressions.monthly | list | GET | `/v1/{parent=locations/*}/searchkeywords/impressions/monthly` | Monthly search keyword impressions | https://developers.google.com/my-business/reference/performance/rest |
| Legacy v4 | accounts.locations.reviews | list | GET | `/v4/{parent=accounts/*/locations/*}/reviews` | List reviews for a location | https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/list |
| Legacy v4 | accounts.locations.reviews | get | GET | `/v4/{name=accounts/*/locations/*/reviews/*}` | Get a specific review | https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews |
| Legacy v4 | accounts.locations.reviews | updateReply | PUT | `/v4/{name=accounts/*/locations/*/reviews/*}/reply` | Create or update reply to a review | https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/updateReply |
| Legacy v4 | accounts.locations.reviews | deleteReply | DELETE | `/v4/{name=accounts/*/locations/*/reviews/*}/reply` | Delete a review reply | https://developers.google.com/my-business/reference/rest |
| Legacy v4 | accounts.locations.localPosts | list | GET | `/v4/{parent=accounts/*/locations/*}/localPosts` | List local posts | https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts |
| Legacy v4 | accounts.locations.localPosts | create | POST | `/v4/{parent=accounts/*/locations/*}/localPosts` | Create a local post | https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts |
| Legacy v4 | accounts.locations.localPosts | patch | PATCH | `/v4/{localPost.name=accounts/*/locations/*/localPosts/*}` | Update a local post | https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts |
| Legacy v4 | accounts.locations.localPosts | delete | DELETE | `/v4/{name=accounts/*/locations/*/localPosts/*}` | Delete a local post | https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts |
| Legacy v4 | accounts.locations.localPosts | get | GET | `/v4/{name=accounts/*/locations/*/localPosts/*}` | Get a local post | https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts |

---

## Concrete Endpoint Reference

Each section below gives the exact HTTP call, all parameters typed and annotated required/optional,
a realistic example request, and a realistic example response. Use these to implement new CLI subcommands.

---

### GET /v1/accounts — List Accounts

**Base URL:** `https://mybusinessaccountmanagement.googleapis.com`

**Full URL:**
```
GET https://mybusinessaccountmanagement.googleapis.com/v1/accounts
```

**Query parameters:**

| Parameter | Type | Req? | Notes |
|---|---|---|---|
| `pageSize` | integer | optional | Max 20, default 20 |
| `pageToken` | string | optional | Cursor from previous response `nextPageToken` |
| `parentAccount` | string | optional | Filter to sub-accounts: `accounts/{id}` |
| `filter` | string | optional | e.g. `type=USER_GROUP` |

**Headers:**
```
Authorization: Bearer {access_token}
```
No `Content-Type` header needed (GET with no body).

**Example request:**
```
GET https://mybusinessaccountmanagement.googleapis.com/v1/accounts?pageSize=20
Authorization: Bearer ya29.a0AfH6...
```

**Example response:**
```json
{
  "accounts": [
    {
      "name": "accounts/111222333444",
      "accountName": "Talas Auto Parts",
      "type": "LOCATION_GROUP",
      "role": "OWNER",
      "verificationState": "VERIFIED",
      "vettedState": "IS_VETTED"
    },
    {
      "name": "accounts/555666777888",
      "accountName": "Mohammed Al Rashid",
      "type": "PERSONAL",
      "role": "OWNER",
      "verificationState": "VERIFICATION_REQUESTED",
      "vettedState": "NOT_VETTED"
    }
  ],
  "nextPageToken": "CAUQAA"
}
```

**Account object fields:**

| Field | Type | Notes |
|---|---|---|
| `name` | string | Resource name: `accounts/{accountId}` |
| `accountName` | string | Display name of the account |
| `type` | enum | `PERSONAL`, `LOCATION_GROUP`, `USER_GROUP`, `ORGANIZATION` |
| `role` | enum | Authenticated user's role: `OWNER`, `CO_OWNER`, `MANAGER`, `SITE_MANAGER` |
| `verificationState` | enum | `VERIFIED`, `UNVERIFIED`, `VERIFICATION_REQUESTED` |
| `vettedState` | enum | `IS_VETTED`, `NOT_VETTED`, `IS_VETTED_UNCONFIRMED` |

**Error cases:**
- `401 UNAUTHENTICATED` — token missing or expired; refresh with `./gads auth refresh`
- `403 PERMISSION_DENIED` — token lacks `business.manage` scope
- `429 RESOURCE_EXHAUSTED` — quota is 0 (allowlist not approved — see Access Requirements)

Source: https://developers.google.com/my-business/reference/accountmanagement/rest/v1/accounts/list

---

### GET /v1/{accountName}/locations — List Locations

**Base URL:** `https://mybusinessbusinessinformation.googleapis.com`

**Full URL:**
```
GET https://mybusinessbusinessinformation.googleapis.com/v1/{accountName}/locations
```

**Path variables:**

| Variable | Type | Req? | Example |
|---|---|---|---|
| `accountName` | string | required | `accounts/111222333444` |

**Query parameters:**

| Parameter | Type | Req? | Notes |
|---|---|---|---|
| `readMask` | string | **required** | Comma-separated field names; omitting causes 400 error |
| `pageSize` | integer | optional | Range 1–100, default 10 |
| `pageToken` | string | optional | Cursor from previous response |
| `filter` | string | optional | SQL-style filter e.g. `storeCode="QZ3"` |
| `orderBy` | string | optional | `title`, `title desc`, `storeCode`, `storeCode desc` |

**Headers:**
```
Authorization: Bearer {access_token}
```

**Example request (all useful fields):**
```
GET https://mybusinessbusinessinformation.googleapis.com/v1/accounts/111222333444/locations
    ?readMask=name,title,phoneNumbers,categories,storefrontAddress,websiteUri,regularHours,metadata,latlng,storeCode
    &pageSize=100
Authorization: Bearer ya29.a0AfH6...
```

**Example response:**
```json
{
  "locations": [
    {
      "name": "locations/17303088970776446827",
      "title": "Talas Auto Parts - Qatar Zone 3",
      "storeCode": "QZ3",
      "phoneNumbers": {
        "primaryPhone": "+974 4444 1234",
        "additionalPhones": ["+974 5555 9876"]
      },
      "categories": {
        "primaryCategory": {
          "name": "categories/gcid:auto_parts_store",
          "displayName": "Auto Parts Store"
        },
        "additionalCategories": [
          {
            "name": "categories/gcid:used_auto_parts_store",
            "displayName": "Used Auto Parts Store"
          }
        ]
      },
      "storefrontAddress": {
        "regionCode": "AE",
        "languageCode": "en",
        "postalCode": "00000",
        "administrativeArea": "Dubai",
        "locality": "Al Quoz",
        "addressLines": ["Zone 3, Industrial Area", "Warehouse 12, Street 8"]
      },
      "websiteUri": "https://shop.talas.ae/?branch=QZ3",
      "regularHours": {
        "periods": [
          {
            "openDay": "MONDAY",
            "openTime": { "hours": 8, "minutes": 0 },
            "closeDay": "MONDAY",
            "closeTime": { "hours": 18, "minutes": 0 }
          },
          {
            "openDay": "SATURDAY",
            "openTime": { "hours": 9, "minutes": 0 },
            "closeDay": "SATURDAY",
            "closeTime": { "hours": 14, "minutes": 0 }
          }
        ]
      },
      "latlng": {
        "latitude": 25.1234,
        "longitude": 55.5678
      },
      "metadata": {
        "mapsUri": "https://maps.google.com/?cid=17303088970776446827",
        "newReviewUri": "https://search.google.com/local/writereview?placeid=ChIJXXXXXXX",
        "placeId": "ChIJXXXXXXXXXXXXXXXXXXXX",
        "hasPendingEdits": false,
        "canDelete": false,
        "canOperateLocalPost": true,
        "canModifyServiceList": true,
        "canHaveFoodMenus": false,
        "canOperateHealthData": false,
        "canOperateLodgingData": false
      }
    }
  ],
  "totalSize": 3,
  "nextPageToken": "CAUQBA"
}
```

**Key Location object fields** (all available in `readMask`):

| Field | Type | Notes |
|---|---|---|
| `name` | string | Resource name: `locations/{locationId}` — the numeric ID is the GBP listing ID |
| `title` | string | Business name as customers see it; no taglines, codes, or URLs |
| `storeCode` | string | Owner-assigned identifier (e.g. `QZ3`, `IND4`, `SJA`) |
| `phoneNumbers` | object | `primaryPhone` (string) + `additionalPhones` (string[]) |
| `categories` | object | `primaryCategory` + `additionalCategories[]`; each has `name` and `displayName` |
| `storefrontAddress` | object | `regionCode`, `administrativeArea`, `locality`, `addressLines[]` |
| `websiteUri` | string | Business website URL |
| `regularHours` | object | `periods[]` each with `openDay`, `openTime`, `closeDay`, `closeTime` |
| `specialHours` | object | Holiday/exception hours |
| `latlng` | object | `latitude` (float), `longitude` (float) |
| `metadata` | object | Output-only: `placeId`, `mapsUri`, `newReviewUri`, `hasPendingEdits`, capability flags |
| `serviceArea` | object | For service-area businesses (no storefront) |

**Error cases:**
- `400 INVALID_ARGUMENT` — `readMask` is missing or contains an invalid field name
- `403 PERMISSION_DENIED` — account not accessible to this token
- `429 RESOURCE_EXHAUSTED` — zero quota (allowlist not approved)

Source: https://developers.google.com/my-business/reference/businessinformation/rest/v1/accounts.locations/list

---

### GET /v4/{locationName}/reviews — List Reviews

**Base URL:** `https://mybusiness.googleapis.com`

> **v4 LEGACY — still the only way to access reviews as of June 2026. No v1 replacement exists.**

**Full URL:**
```
GET https://mybusiness.googleapis.com/v4/{locationName}/reviews
```

**Path variables:**

| Variable | Type | Req? | Example |
|---|---|---|---|
| `locationName` | string | required | `accounts/111222333444/locations/17303088970776446827` |

Note: unlike Business Info API, reviews use the full `accounts/{id}/locations/{id}` path, not just `locations/{id}`.

**Query parameters:**

| Parameter | Type | Req? | Notes |
|---|---|---|---|
| `pageSize` | integer | optional | Max 50, no documented default |
| `pageToken` | string | optional | Cursor from previous response |
| `orderBy` | string | optional | `rating`, `rating desc`, `updateTime desc` |

**Headers:**
```
Authorization: Bearer {access_token}
```

**Example request:**
```
GET https://mybusiness.googleapis.com/v4/accounts/111222333444/locations/17303088970776446827/reviews
    ?pageSize=50&orderBy=updateTime+desc
Authorization: Bearer ya29.a0AfH6...
```

**Example response:**
```json
{
  "reviews": [
    {
      "name": "accounts/111222333444/locations/17303088970776446827/reviews/AbCdEfGhIjKlMnOp",
      "reviewId": "AbCdEfGhIjKlMnOp",
      "reviewer": {
        "displayName": "Ahmed Al Mansoori",
        "profilePhotoUrl": "https://lh3.googleusercontent.com/a-/XXXXXXXX",
        "isAnonymous": false
      },
      "starRating": "FIVE",
      "comment": "Excellent service! Found the Tesla Model 3 rear bumper I needed. Fast shipping.",
      "createTime": "2026-05-15T10:23:45.000Z",
      "updateTime": "2026-05-15T10:23:45.000Z",
      "reviewReply": {
        "comment": "Thank you Ahmed! We're glad we could help with your Tesla parts. Visit us again!",
        "updateTime": "2026-05-16T08:00:00.000Z",
        "reviewReplyState": "APPROVED"
      }
    },
    {
      "name": "accounts/111222333444/locations/17303088970776446827/reviews/QrStUvWxYzAbCd",
      "reviewId": "QrStUvWxYzAbCd",
      "reviewer": {
        "isAnonymous": true
      },
      "starRating": "THREE",
      "comment": "Good selection but had to wait a while.",
      "createTime": "2026-04-20T14:11:00.000Z",
      "updateTime": "2026-04-20T14:11:00.000Z"
    }
  ],
  "averageRating": 4.3,
  "totalReviewCount": 47,
  "nextPageToken": "CAUQBA"
}
```

**Review object fields:**

| Field | Type | Notes |
|---|---|---|
| `name` | string | Full resource path: `accounts/{id}/locations/{id}/reviews/{id}` |
| `reviewId` | string | Unique identifier for this review |
| `reviewer.displayName` | string | Only present when `isAnonymous=false` |
| `reviewer.profilePhotoUrl` | string | Only present when `isAnonymous=false` |
| `reviewer.isAnonymous` | boolean | Always present |
| `starRating` | enum | `ONE`, `TWO`, `THREE`, `FOUR`, `FIVE` |
| `comment` | string | Review text; may include markup |
| `createTime` | string | RFC3339 timestamp |
| `updateTime` | string | RFC3339 timestamp (changes when reviewer edits) |
| `reviewReply` | object | Present if owner has replied; absent otherwise |
| `reviewMediaItems` | array | Associated photos/videos (if any) |

**reviewReply sub-fields:**

| Field | Type | Notes |
|---|---|---|
| `comment` | string | Owner reply text, max 4,096 bytes |
| `updateTime` | string | RFC3339 timestamp (output only) |
| `reviewReplyState` | enum | `PENDING`, `REJECTED`, `APPROVED` |

**ListReviewsResponse fields:**

| Field | Notes |
|---|---|
| `reviews[]` | Array of Review objects |
| `averageRating` | Float 1.0–5.0 across all reviews for this location |
| `totalReviewCount` | Total reviews (all pages) |
| `nextPageToken` | Present if more pages; absent on last page |

**Error cases:**
- `403 PERMISSION_DENIED` — location not accessible or not verified
- `404 NOT_FOUND` — location name is wrong (check full `accounts/.../locations/...` path)
- `429 RESOURCE_EXHAUSTED` — zero quota (allowlist not approved)

Source: https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/list

---

### PUT /v4/{reviewName}/reply — Reply to Review

**Base URL:** `https://mybusiness.googleapis.com`

> **v4 LEGACY — still the only way to reply to reviews as of June 2026.**

**Full URL:**
```
PUT https://mybusiness.googleapis.com/v4/{reviewName}/reply
```

**Path variables:**

| Variable | Type | Req? | Example |
|---|---|---|---|
| `reviewName` | string | required | `accounts/111222333444/locations/17303088970776446827/reviews/AbCdEfGhIjKlMnOp` |

**Request body:**

```json
{
  "comment": "string (required, max 4096 bytes)"
}
```

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Example request:**
```
PUT https://mybusiness.googleapis.com/v4/accounts/111222333444/locations/17303088970776446827/reviews/AbCdEfGhIjKlMnOp/reply
Authorization: Bearer ya29.a0AfH6...
Content-Type: application/json

{
  "comment": "Thank you for your kind words! We're happy to help with your Tesla parts needs. Come back anytime!"
}
```

**Example response** (ReviewReply object):
```json
{
  "comment": "Thank you for your kind words! We're happy to help with your Tesla parts needs. Come back anytime!",
  "updateTime": "2026-06-23T09:15:00.000Z",
  "reviewReplyState": "PENDING"
}
```

Note: `reviewReplyState` starts as `PENDING` — Google moderates replies before showing them publicly.
Typically transitions to `APPROVED` within minutes to hours.

**Constraints:**
- Location must be verified
- If a reply already exists, this replaces it (idempotent upsert — creates if missing, updates if present)

**Error cases:**
- `400 INVALID_ARGUMENT` — `comment` field missing or over 4,096 bytes
- `403 PERMISSION_DENIED` — location not verified, or token lacks write access
- `404 NOT_FOUND` — review name path is wrong
- `429 RESOURCE_EXHAUSTED` — zero quota

Source: https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/updateReply

---

### DELETE /v4/{reviewName}/reply — Delete Review Reply

**Full URL:**
```
DELETE https://mybusiness.googleapis.com/v4/{reviewName}/reply
```

**Example request:**
```
DELETE https://mybusiness.googleapis.com/v4/accounts/111222333444/locations/17303088970776446827/reviews/AbCdEfGhIjKlMnOp/reply
Authorization: Bearer ya29.a0AfH6...
```

**Response:** Empty body, HTTP 200 on success.

**Error cases:**
- `404 NOT_FOUND` — no reply exists to delete, or review name is wrong
- `403 PERMISSION_DENIED` — location not verified or no write access

---

### GET /v1/{location}:fetchMultiDailyMetricsTimeSeries — Performance Metrics (Multi)

**Base URL:** `https://businessprofileperformance.googleapis.com`

> **IMPORTANT — CORRECT ENDPOINT NAME:**
> The documented endpoint is `fetchMultiDailyMetricsTimeSeries` (GET with repeated query params).
> The gads CLI `gbp_multi_daily_metrics()` function uses this correctly via GET.
> There is NO `fetchMultiDailyMetrics` POST endpoint. An earlier comment in the Coverage section
> flagged this as a potential bug — that was incorrect. The CLI implementation is correct.
> Source: https://developers.google.com/my-business/reference/performance/rest/v1/locations/fetchMultiDailyMetricsTimeSeries

**Full URL:**
```
GET https://businessprofileperformance.googleapis.com/v1/{location}:fetchMultiDailyMetricsTimeSeries
```

**Path variables:**

| Variable | Type | Req? | Example |
|---|---|---|---|
| `location` | string | required | `locations/17303088970776446827` (no `accounts/` prefix) |

**Query parameters:**

| Parameter | Type | Req? | Notes |
|---|---|---|---|
| `dailyMetrics` | string (repeated) | required | One param per metric; repeat the key for each metric |
| `dailyRange.startDate.year` | integer | required | e.g. `2026` |
| `dailyRange.startDate.month` | integer | required | e.g. `6` |
| `dailyRange.startDate.day` | integer | required | e.g. `1` |
| `dailyRange.endDate.year` | integer | required | e.g. `2026` |
| `dailyRange.endDate.month` | integer | required | e.g. `22` |
| `dailyRange.endDate.day` | integer | required | e.g. `22` |

**Headers:**
```
Authorization: Bearer {access_token}
```

**Example request (three metrics, 30-day window):**
```
GET https://businessprofileperformance.googleapis.com/v1/locations/17303088970776446827:fetchMultiDailyMetricsTimeSeries
    ?dailyMetrics=WEBSITE_CLICKS
    &dailyMetrics=CALL_CLICKS
    &dailyMetrics=BUSINESS_DIRECTION_REQUESTS
    &dailyRange.startDate.year=2026
    &dailyRange.startDate.month=5
    &dailyRange.startDate.day=1
    &dailyRange.endDate.year=2026
    &dailyRange.endDate.month=5
    &dailyRange.endDate.day=31
Authorization: Bearer ya29.a0AfH6...
```

**Example response:**
```json
{
  "multiDailyMetricTimeSeries": [
    {
      "dailyMetricTimeSeries": [
        {
          "dailyMetric": "WEBSITE_CLICKS",
          "timeSeries": {
            "datedValues": [
              { "date": { "year": 2026, "month": 5, "day": 1 }, "value": "14" },
              { "date": { "year": 2026, "month": 5, "day": 2 }, "value": "9" },
              { "date": { "year": 2026, "month": 5, "day": 3 }, "value": "0" }
            ]
          }
        },
        {
          "dailyMetric": "CALL_CLICKS",
          "timeSeries": {
            "datedValues": [
              { "date": { "year": 2026, "month": 5, "day": 1 }, "value": "3" },
              { "date": { "year": 2026, "month": 5, "day": 2 }, "value": "5" },
              { "date": { "year": 2026, "month": 5, "day": 3 }, "value": "0" }
            ]
          }
        },
        {
          "dailyMetric": "BUSINESS_DIRECTION_REQUESTS",
          "timeSeries": {
            "datedValues": [
              { "date": { "year": 2026, "month": 5, "day": 1 }, "value": "7" },
              { "date": { "year": 2026, "month": 5, "day": 2 }, "value": "2" },
              { "date": { "year": 2026, "month": 5, "day": 3 }, "value": "0" }
            ]
          }
        }
      ]
    }
  ]
}
```

**Response structure notes:**
- Top-level key: `multiDailyMetricTimeSeries` (array)
- Each element has a `dailyMetricTimeSeries` array (the inner grouping)
- Each series has `dailyMetric` (string) and `timeSeries.datedValues[]`
- Each dated value: `{ date: { year, month, day }, value: "N" }` — value is a **string**, not integer; parse with `int()`
- Days with no data return `value: "0"`, not `null`
- Recent days (last 2–3 days) may return `0` due to processing lag

**Error cases:**
- `400 INVALID_ARGUMENT` — invalid metric name or date range
- `403 PERMISSION_DENIED` — location not accessible or token lacks `business.manage` scope
- `429 RESOURCE_EXHAUSTED` — zero quota (allowlist not approved)

Source: https://developers.google.com/my-business/reference/performance/rest/v1/locations/fetchMultiDailyMetricsTimeSeries

---

### GET /v1/{location}:getDailyMetricsTimeSeries — Performance Metrics (Single)

**Full URL:**
```
GET https://businessprofileperformance.googleapis.com/v1/{location}:getDailyMetricsTimeSeries
```

**Query parameters:**

| Parameter | Type | Req? | Notes |
|---|---|---|---|
| `dailyMetric` | string | required | Single `DailyMetric` enum value (singular, not repeated) |
| `dailyRange.startDate.year/month/day` | integer | required | Start of date range |
| `dailyRange.endDate.year/month/day` | integer | required | End of date range |
| `dailySubEntityType` | object | optional | Sub-entity breakdown for supported metrics |

**Example response:**
```json
{
  "timeSeries": {
    "datedValues": [
      { "date": { "year": 2026, "month": 5, "day": 1 }, "value": "14" },
      { "date": { "year": 2026, "month": 5, "day": 2 }, "value": "9" }
    ]
  }
}
```

Use `fetchMultiDailyMetricsTimeSeries` instead when fetching more than one metric — it saves API calls.

Source: https://developers.google.com/my-business/reference/performance/rest/v1/locations/getDailyMetricsTimeSeries

---

## Performance Metrics — Complete DailyMetric Enum

Source: https://developers.google.com/my-business/reference/performance/rest/v1/DailyMetric

| Enum Value | Description |
|---|---|
| `DAILY_METRIC_UNKNOWN` | Default/unknown — do not request this value |
| `BUSINESS_IMPRESSIONS_DESKTOP_MAPS` | Views on Google Maps desktop; deduplicated: 1 per unique user per day |
| `BUSINESS_IMPRESSIONS_DESKTOP_SEARCH` | Views on Google Search desktop; deduplicated: 1 per unique user per day |
| `BUSINESS_IMPRESSIONS_MOBILE_MAPS` | Views on Google Maps mobile; deduplicated: 1 per unique user per day |
| `BUSINESS_IMPRESSIONS_MOBILE_SEARCH` | Views on Google Search mobile; deduplicated: 1 per unique user per day |
| `BUSINESS_CONVERSATIONS` | Message conversations received on the business profile |
| `BUSINESS_DIRECTION_REQUESTS` | Direction requests to the business location |
| `CALL_CLICKS` | Clicks on the call button on the profile |
| `WEBSITE_CLICKS` | Clicks on the website link on the profile |
| `BUSINESS_BOOKINGS` | Bookings made via Reserve with Google |
| `BUSINESS_FOOD_ORDERS` | Food orders received from the business profile |
| `BUSINESS_FOOD_MENU_CLICKS` | Menu interactions; deduplicated: 1 per unique user per day |

---

## Local Posts (Implementation-Ready Reference)

Local posts appear on the Google Business Profile in Google Search and Maps results.
All localPosts endpoints are on the legacy v4 API — `mybusiness.googleapis.com/v4`.

> **Note:** `localPosts.reportInsights` was discontinued February 20, 2023. Do not implement it.
> All other localPosts methods (create, list, get, patch, delete) remain active as of June 2026.

### POST /v4/{locationName}/localPosts — Create Post

**Full URL:**
```
POST https://mybusiness.googleapis.com/v4/{locationName}/localPosts
```

**Path variables:**

| Variable | Type | Req? | Example |
|---|---|---|---|
| `locationName` | string | required | `accounts/111222333444/locations/17303088970776446827` |

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request body — LocalPost object:**

| Field | Type | Req? | Notes |
|---|---|---|---|
| `topicType` | enum | required | `STANDARD`, `EVENT`, `OFFER`, `ALERT` |
| `summary` | string | required for STANDARD | Main post text |
| `callToAction` | object | optional | See below |
| `media` | array | optional | See below |
| `event` | object | required for EVENT/OFFER | See below |
| `languageCode` | string | optional | e.g. `en`, `ar` |
| `alertType` | enum | optional (ALERT posts) | `COVID_19` |
| `offer` | object | optional (OFFER posts) | `couponCode`, `redeemOnlineUrl`, `termsConditions` |

**callToAction object:**

| Field | Type | Notes |
|---|---|---|
| `actionType` | enum | `BOOK`, `ORDER`, `SHOP`, `LEARN_MORE`, `SIGN_UP`, `CALL` |
| `url` | string | Landing URL (omit for `CALL` type) |

**media array item:**

| Field | Type | Notes |
|---|---|---|
| `mediaFormat` | enum | `PHOTO`, `VIDEO` |
| `sourceUrl` | string | Publicly accessible URL to the media file |

**event object:**

| Field | Type | Notes |
|---|---|---|
| `title` | string | Event name |
| `schedule` | object | `{ startDate, startTime, endDate, endTime }` — uses Date and TimeOfDay objects |
| `schedule.startDate` | object | `{ year, month, day }` |
| `schedule.startTime` | object | `{ hours, minutes }` |
| `schedule.endDate` | object | `{ year, month, day }` |
| `schedule.endTime` | object | `{ hours, minutes }` |

**Example request — STANDARD post with CTA:**
```
POST https://mybusiness.googleapis.com/v4/accounts/111222333444/locations/17303088970776446827/localPosts
Authorization: Bearer ya29.a0AfH6...
Content-Type: application/json

{
  "topicType": "STANDARD",
  "summary": "Original Tesla Model 3 used body parts now available at Talas — Qatar Zone 3. Front doors, bumpers, hoods. Call or visit us.",
  "callToAction": {
    "actionType": "CALL"
  },
  "languageCode": "en"
}
```

**Example request — OFFER post:**
```
POST https://mybusiness.googleapis.com/v4/accounts/111222333444/locations/17303088970776446827/localPosts
Authorization: Bearer ya29.a0AfH6...
Content-Type: application/json

{
  "topicType": "OFFER",
  "summary": "10% off all Tesla Model 3 rear bumpers this week only.",
  "event": {
    "title": "Tesla Parts Sale",
    "schedule": {
      "startDate": { "year": 2026, "month": 6, "day": 23 },
      "startTime": { "hours": 8, "minutes": 0 },
      "endDate": { "year": 2026, "month": 6, "day": 30 },
      "endTime": { "hours": 18, "minutes": 0 }
    }
  },
  "offer": {
    "couponCode": "TESLA10",
    "redeemOnlineUrl": "https://shop.talas.ae/?branch=QZ3",
    "termsConditions": "Valid in-store and online. One use per customer."
  },
  "callToAction": {
    "actionType": "SHOP",
    "url": "https://shop.talas.ae/?branch=QZ3"
  }
}
```

**Example request — EVENT post with photo:**
```
POST https://mybusiness.googleapis.com/v4/accounts/111222333444/locations/17303088970776446827/localPosts
Authorization: Bearer ya29.a0AfH6...
Content-Type: application/json

{
  "topicType": "EVENT",
  "summary": "New Tesla Model Y parts just arrived. Limited stock.",
  "event": {
    "title": "Model Y Parts Arrival",
    "schedule": {
      "startDate": { "year": 2026, "month": 7, "day": 1 },
      "startTime": { "hours": 8, "minutes": 0 },
      "endDate": { "year": 2026, "month": 7, "day": 7 },
      "endTime": { "hours": 18, "minutes": 0 }
    }
  },
  "media": [
    {
      "mediaFormat": "PHOTO",
      "sourceUrl": "https://cdn.talas.ae/photos/model-y-parts-2026.jpg"
    }
  ],
  "callToAction": {
    "actionType": "LEARN_MORE",
    "url": "https://shop.talas.ae/tesla/model-y?branch=QZ3"
  }
}
```

**Example response:**
```json
{
  "name": "accounts/111222333444/locations/17303088970776446827/localPosts/102345678901234567",
  "languageCode": "en",
  "summary": "Original Tesla Model 3 used body parts now available at Talas — Qatar Zone 3. Front doors, bumpers, hoods. Call or visit us.",
  "topicType": "STANDARD",
  "state": "LIVE",
  "callToAction": {
    "actionType": "CALL"
  },
  "createTime": "2026-06-23T09:30:00.000Z",
  "updateTime": "2026-06-23T09:30:00.000Z",
  "searchUrl": "https://search.google.com/local/posts?q=Talas+Auto+Parts&ludocid=17303088970776446827"
}
```

**LocalPost state enum:**

| Value | Meaning |
|---|---|
| `LIVE` | Visible on Google |
| `PROCESSING` | Under review |
| `SCHEDULED` | Set to go live in the future |
| `REJECTED` | Violates policy; post not shown |
| `RECURRING` | A recurring post |

**Error cases:**
- `400 INVALID_ARGUMENT` — `topicType` missing, `event` missing for EVENT/OFFER type, or `media.sourceUrl` not publicly accessible
- `403 PERMISSION_DENIED` — location not accessible or not verified
- `404 NOT_FOUND` — location path is wrong
- `429 RESOURCE_EXHAUSTED` — zero quota

Source: https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts/create

---

### GET /v4/{locationName}/localPosts — List Posts

**Full URL:**
```
GET https://mybusiness.googleapis.com/v4/{locationName}/localPosts
```

**Query parameters:**

| Parameter | Type | Req? | Notes |
|---|---|---|---|
| `pageSize` | integer | optional | Range 1–100, default 20 |
| `pageToken` | string | optional | Cursor from previous response |

**Example request:**
```
GET https://mybusiness.googleapis.com/v4/accounts/111222333444/locations/17303088970776446827/localPosts
    ?pageSize=50
Authorization: Bearer ya29.a0AfH6...
```

**Example response:**
```json
{
  "localPosts": [
    {
      "name": "accounts/111222333444/locations/17303088970776446827/localPosts/102345678901234567",
      "summary": "Original Tesla Model 3 used body parts now available...",
      "topicType": "STANDARD",
      "state": "LIVE",
      "callToAction": { "actionType": "CALL" },
      "createTime": "2026-06-23T09:30:00.000Z",
      "updateTime": "2026-06-23T09:30:00.000Z",
      "searchUrl": "https://search.google.com/local/posts?..."
    }
  ],
  "nextPageToken": "CAUQBA"
}
```

Source: https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts/list

---

### PATCH /v4/{localPostName} — Update Post

**Full URL:**
```
PATCH https://mybusiness.googleapis.com/v4/{localPostName}
```

**Path variables:**

| Variable | Type | Req? | Example |
|---|---|---|---|
| `localPostName` | string | required | `accounts/111222333444/locations/17303088970776446827/localPosts/102345678901234567` |

**Query parameters:**

| Parameter | Type | Req? | Notes |
|---|---|---|---|
| `updateMask` | string | required | Comma-separated field paths to update; omitting updates all fields |

**Example request (update summary only):**
```
PATCH https://mybusiness.googleapis.com/v4/accounts/111222333444/locations/17303088970776446827/localPosts/102345678901234567
      ?updateMask=summary
Authorization: Bearer ya29.a0AfH6...
Content-Type: application/json

{
  "summary": "Updated: Tesla Model 3 parts — front and rear bumpers in stock now."
}
```

**Response:** Returns the updated LocalPost object.

### DELETE /v4/{localPostName} — Delete Post

**Full URL:**
```
DELETE https://mybusiness.googleapis.com/v4/{localPostName}
```

**Example request:**
```
DELETE https://mybusiness.googleapis.com/v4/accounts/111222333444/locations/17303088970776446827/localPosts/102345678901234567
Authorization: Bearer ya29.a0AfH6...
```

**Response:** Empty body, HTTP 200 on success.

---

## Key Request/Response Fields

### Accounts

Resource: `Account`

| Field | Type | Notes |
|---|---|---|
| `name` | string | Resource name: `accounts/{accountId}` |
| `accountName` | string | Display name of the account |
| `type` | enum | `PERSONAL`, `LOCATION_GROUP`, `USER_GROUP`, `ORGANIZATION` |
| `role` | enum | Authenticated user's role: `OWNER`, `CO_OWNER`, `MANAGER`, `SITE_MANAGER` |
| `verificationState` | enum | Verification status |
| `vettedState` | enum | Vetting status |

**accounts.list request parameters:**
- `pageSize` — max 20, default 20
- `pageToken` — pagination token
- `parentAccount` — filter by parent account resource name
- `filter` — supports `type=USER_GROUP`

Source: https://developers.google.com/my-business/reference/accountmanagement/rest/v1/accounts/list

### Locations

Resource: `Location` (Business Information API v1)

**accounts.locations.list request parameters:**
- `parent` (required) — `accounts/{accountId}`
- `readMask` (required) — comma-separated field list; request will fail with 400 without it
- `pageSize` — range 1–100, default 10
- `pageToken` — pagination token
- `filter` — SQL-style filter on location fields
- `orderBy` — sort by `title` or `storeCode` (append ` desc` for descending)

**Response:** `{ locations: [...], nextPageToken: "...", totalSize: N }`

**readMask field reference:**

```
name,title,storeCode,phoneNumbers,categories,storefrontAddress,websiteUri,
regularHours,specialHours,latlng,metadata,serviceArea,openInfo,labels
```

**Recommended readMask for most CLI uses:**
```
name,title,storeCode,phoneNumbers,categories,storefrontAddress,websiteUri,regularHours,latlng,metadata
```

Source: https://developers.google.com/my-business/reference/businessinformation/rest/v1/accounts.locations/list

### Reviews (v4 legacy — still active)

The reviews endpoints live at `mybusiness.googleapis.com/v4`. There is no v1 replacement as of June 2026.
See the Concrete Endpoint Reference sections above for full request/response examples.

### Performance Metrics

See the Concrete Endpoint Reference sections above for full examples.

---

## Pagination & Quotas

### Pagination

All list methods use cursor-based pagination via `pageToken`:

| API / Method | Default pageSize | Max pageSize |
|---|---|---|
| accounts.list | 20 | 20 |
| accounts.locations.list (Business Info) | 10 | 100 |
| reviews.list (v4) | — | 50 |
| localPosts.list (v4) | 20 | 100 |
| searchkeywords.impressions.monthly.list | — | unspecified |

Pattern: Include `pageToken` from the previous response's `nextPageToken` to fetch the next page.
When `nextPageToken` is absent from the response, you've reached the last page.

### Quotas & Rate Limits

- Rate limits exist but specific QPM values are not published in the reference docs
- After enabling any GBP API in Google Cloud Console, **default quota is 0** — API calls will
  return HTTP 429 (RESOURCE_EXHAUSTED) until access is approved (see Access Requirements below)
- Source: https://developers.google.com/my-business/reference/businessinformation/rest (quota note)

---

## Access Requirements

**There is a mandatory allowlist/approval gate** for the GBP APIs that is separate from simply
enabling the API in Google Cloud Console.

**Steps:**
1. Enable the desired APIs in Google Cloud Console (Account Management, Business Information, Performance, Google My Business)
2. Create OAuth 2.0 credentials
3. **Request API access** via: `https://support.google.com/business/contact/api_default`
   - Select "Application for Basic API Access"
   - Sign in as the GBP account owner (not a manager)
   - Describe your use case and specific endpoints needed
4. Wait for approval (typically 7–10 business days, but can range from 4 days to 6 weeks)

**Prerequisites before applying:**
- Business profile must be at least 60 days old
- Profile must be verified
- You must be the account owner

**What happens without approval:**
- API calls return HTTP 429 (`RESOURCE_EXHAUSTED`) — looks like a rate limit but is actually zero quota
- This is NOT a rate limit that resolves with slower requests; only approval resolves it

Sources:
- https://xovionlabs.com/blog/google-business-profile-api-hidden-gate/
- https://developers.google.com/my-business/reference/businessinformation/rest ("If you have a quota of 0 after enabling the API, please request for GBP API access")

---

## Gotchas

1. **`readMask` is required** on `accounts.locations.list` and `locations.get` in the Business
   Information API. Omitting it causes a `400 INVALID_ARGUMENT` error. Supply a comma-separated
   list of field names you need.

2. **Reviews are stuck on v4** — `mybusiness.googleapis.com/v4` for reviews is still the only way
   to list/reply to reviews. There is no v1 reviews API as of June 2026. The gads-cli correctly uses
   v4 for reviews. Do not try to migrate to v1 — no such endpoint exists yet.

3. **Local posts are also stuck on v4** — same situation as reviews. The `localPosts` resource
   lives at `mybusiness.googleapis.com/v4`.

4. **Location ID format differs between APIs:**
   - Business Information API: `locations/{locationId}` (no account prefix)
   - Performance API: `locations/{locationId}` (same, no account prefix)
   - v4 reviews: `accounts/{accountId}/locations/{locationId}/reviews/{reviewId}` (full path)
   - v4 localPosts: `accounts/{accountId}/locations/{locationId}/localPosts/{postId}` (full path)
   Mixing up these formats causes `404 NOT_FOUND`.

5. **Allowlist is mandatory** — enabling the API in Cloud Console is not enough. Zero quota = 429
   errors that look like rate limiting. See Access Requirements.

6. **`plus.business.manage` scope is legacy** — both scopes work for v4 reviews/posts, but
   `business.manage` is the current standard and works across all APIs. Prefer it.

7. **Daily metrics are deduplicated per surface per user per day** — impression metrics count
   unique users. `BUSINESS_IMPRESSIONS_DESKTOP_MAPS` and `BUSINESS_IMPRESSIONS_MOBILE_MAPS` can
   each fire for the same user (one per surface), but each surface deduplicates within itself.

8. **Performance API uses `locations/` path without account prefix** — unlike v4 which requires
   `accounts/*/locations/*`, the Performance API only needs `locations/{locationId}`.

9. **`fetchMultiDailyMetricsTimeSeries` is GET, not POST** — it uses repeated `dailyMetrics=`
   query params (one per metric), not a JSON body. The gads CLI (`gbp_multi_daily_metrics`)
   implements this correctly. There is no `fetchMultiDailyMetrics` POST endpoint.

10. **Performance data lags 2–3 days** — recent days typically return `value: "0"` even when
    there was real activity. Never alert on zeros within the last 3 days.

11. **`value` in datedValues is a string, not integer** — the API returns `"value": "42"` (quoted).
    Always parse with `int(dv.get("value", 0))`.

12. **`reviewReplyState` starts as `PENDING`** — after `PUT .../reply`, the reply is not
    immediately visible. Google moderates it; transitions to `APPROVED` or `REJECTED`.

13. **`media.sourceUrl` for local posts must be publicly accessible** — private URLs (signed S3,
    Cloudinary auth-required) fail with `400 INVALID_ARGUMENT`. Use public CDN URLs.

---

## Coverage vs Current gads CLI

The current `gads_lib/gbp.py` uses these endpoints:

| Feature | gads CLI function | Endpoint | Status |
|---|---|---|---|
| List accounts | `gbp_list_accounts` | `GET /v1/accounts` | Correct |
| List locations | `gbp_list_locations` | `GET /v1/{account}/locations` | Correct; readMask passed as param |
| Get location | `gbp_get_location` | `GET /v1/{location}` | Correct; readMask passed as param |
| List reviews | `gbp_list_reviews` | `GET /v4/{location}/reviews` | Correct; v4 is the only option |
| Reply to review | `gbp_reply_review` | `PUT /v4/{review}/reply` | Correct |
| Delete reply | `gbp_delete_reply` | `DELETE /v4/{review}/reply` | Correct |
| Single daily metric | `gbp_daily_metrics` | `GET /v1/{location}:getDailyMetricsTimeSeries` | Correct |
| Multi daily metrics | `gbp_multi_daily_metrics` | `GET /v1/{location}:fetchMultiDailyMetricsTimeSeries` | Correct — GET with repeated query params |
| Search keywords | `gbp_search_keywords_monthly` | `GET /v1/{location}/searchkeywords/impressions/monthly` | Correct; handles pagination |

**Endpoints/features NOT yet in gads CLI (implementation gaps):**

| Feature | API | HTTP | Path | Notes |
|---|---|---|---|---|
| Local posts — create | v4 | POST | `/v4/{location}/localPosts` | topicType, summary, callToAction, media, event |
| Local posts — list | v4 | GET | `/v4/{location}/localPosts` | pageSize max 100 |
| Local posts — update | v4 | PATCH | `/v4/{localPost}?updateMask=...` | updateMask required |
| Local posts — delete | v4 | DELETE | `/v4/{localPost}` | No body |
| Batch get reviews | v4 | POST | `/v4/{account}/locations:batchGetReviews` | Multi-location review fetch |
| Business attributes | Business Info v1 | GET | `/v1/{location}/attributes` | Hours, accessibility, amenities |
| Account admins | Account Mgmt v1 | GET | `/v1/{account}/admins` | Who has access to each account |
| Location categories | Business Info v1 | GET | `/v1/categories` | Enumerate valid categories |
| Google-suggested updates | Business Info v1 | GET | `/v1/{location}:getGoogleUpdated` | See what Google has auto-changed |

---

## Sources

All claims in this document are sourced from the following URLs, fetched June 2026:

- https://developers.google.com/my-business/reference/accountmanagement/rest — Account Management API reference
- https://developers.google.com/my-business/reference/accountmanagement/rest/v1/accounts/list — accounts.list details
- https://developers.google.com/my-business/reference/businessinformation/rest — Business Information API reference
- https://developers.google.com/my-business/reference/businessinformation/rest/v1/accounts.locations/list — accounts.locations.list details
- https://developers.google.com/my-business/reference/performance/rest — Performance API reference
- https://developers.google.com/my-business/reference/performance/rest/v1/locations/fetchMultiDailyMetricsTimeSeries — fetchMultiDailyMetricsTimeSeries details
- https://developers.google.com/my-business/reference/performance/rest/v1/locations/getDailyMetricsTimeSeries — getDailyMetricsTimeSeries details
- https://developers.google.com/my-business/reference/performance/rest/v1/DailyMetric — Complete DailyMetric enum values
- https://developers.google.com/my-business/reference/rest — Legacy v4 API reference (reviews, posts)
- https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/list — reviews.list details
- https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/updateReply — updateReply details
- https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts — localPosts resource overview
- https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts/create — localPosts.create details
- https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts/list — localPosts.list details
- https://developers.google.com/my-business/content/review-data — Reviews API working guide
- https://developers.google.com/my-business/content/sunset-dates — Deprecation and sunset schedule
- https://xovionlabs.com/blog/google-business-profile-api-hidden-gate/ — API access approval gate details
