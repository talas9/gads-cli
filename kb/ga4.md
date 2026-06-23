# Google Analytics 4 APIs

## Status & Versions

### Data API
- **v1beta** — stable, production-ready; the primary version used for reporting
- **v1alpha** — experimental; adds funnel reports, audience lists, recurring audience lists, report tasks, and property quota snapshots
- No separate `v1` (fully GA) release found; `v1beta` is the current stable channel as of 2026-06-23
- Source: https://developers.google.com/analytics/devguides/reporting/data/v1/rest

### Admin API
- **v1beta** — stable; "No breaking changes are expected in this channel" — covers account/property management, key events, custom dimensions/metrics, service links
- **v1alpha** — early preview; adds audiences, BigQuery links, Search Ads 360, channel groups, event edit rules, subproperties, data redaction, etc.
- Source: https://developers.google.com/analytics/devguides/config/admin/v1

### Admin API v1alpha vs v1beta — Key Events specifically

The `properties.keyEvents` resource exists in **both** v1alpha and v1beta with identical method sets (create, delete, get, list, patch). No behavioral differences are documented between the two versions for key events.

**Recommendation for new gads CLI subcommands:** Switch key events calls to `v1beta` — it carries the "no breaking changes" stability guarantee. The current CLI uses `v1alpha`, which works but is technically on the early-preview channel.

**v1alpha sunset:** No sunset date has been announced (as of 2026-06-23). Google typically promotes features from v1alpha → v1beta when they stabilize, rather than removing v1alpha. However, relying on v1alpha for production code is discouraged for resources that are already promoted to v1beta.

Sources: https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.keyEvents, https://developers.google.com/analytics/devguides/config/admin/v1

---

## Base URLs

| API | Base URL |
|-----|----------|
| Data API (v1beta) | `https://analyticsdata.googleapis.com/v1beta` |
| Data API (v1alpha) | `https://analyticsdata.googleapis.com/v1alpha` |
| Admin API (v1beta) | `https://analyticsadmin.googleapis.com/v1beta` |
| Admin API (v1alpha) | `https://analyticsadmin.googleapis.com/v1alpha` |

Sources: https://developers.google.com/analytics/devguides/reporting/data/v1/rest, https://developers.google.com/analytics/devguides/config/admin/v1/rest

---

## Auth / OAuth Scopes

| Scope | URI | What it Covers |
|-------|-----|----------------|
| `analytics.readonly` | `https://www.googleapis.com/auth/analytics.readonly` | Read all Data API endpoints (`runReport`, `runRealtimeReport`, `getMetadata`, etc.) and read Admin API resources (key events list/get) |
| `analytics.edit` | `https://www.googleapis.com/auth/analytics.edit` | Mutate Admin API resources: create, patch, delete key events, custom dimensions, etc. |
| `analytics` | `https://www.googleapis.com/auth/analytics` | Full access (superset of `analytics.readonly`); also accepted by `runReport` and `getMetadata` |

The gads CLI project's `generate_token.py` already includes both `analytics.readonly` and `analytics.edit`. If a `403 Forbidden` appears on write calls, the token was generated before `analytics.edit` was added — regenerate it.

Sources: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport, https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents/list

---

## Resources & Endpoints

### Data API (v1beta)

| Resource | Method | HTTP | Path | Purpose | Source URL |
|----------|--------|------|------|---------|------------|
| properties | runReport | POST | `/v1beta/{property=properties/*}:runReport` | Standard customized report of GA4 event data | https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport |
| properties | runRealtimeReport | POST | `/v1beta/{property=properties/*}:runRealtimeReport` | Real-time event data (last 30 min, up to 60 min for 360) | https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runRealtimeReport |
| properties | runPivotReport | POST | `/v1beta/{property=properties/*}:runPivotReport` | Pivot-format report of GA4 event data | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties | batchRunReports | POST | `/v1beta/{property=properties/*}:batchRunReports` | Multiple standard reports in one request | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties | batchRunPivotReports | POST | `/v1beta/{property=properties/*}:batchRunPivotReports` | Multiple pivot reports in one request | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties | checkCompatibility | POST | `/v1beta/{property=properties/*}:checkCompatibility` | Check which dimensions/metrics can be added together | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties.metadata | get | GET | `/v1beta/{name=properties/*/metadata}` | Dimension/metric catalog for a property | https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/getMetadata |
| properties.audienceExports | create | POST | `/v1beta/{parent=properties/*}/audienceExports` | Create an audience export for later retrieval | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties.audienceExports | get | GET | `/v1beta/{name=properties/*/audienceExports/*}` | Get audience export metadata | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties.audienceExports | list | GET | `/v1beta/{parent=properties/*}/audienceExports` | List all audience exports for a property | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties.audienceExports | query | POST | `/v1beta/{name=properties/*/audienceExports/*}:query` | Retrieve audience export user rows | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |

### Data API (v1alpha — experimental)

| Resource | Method | HTTP | Path | Purpose | Source URL |
|----------|--------|------|------|---------|------------|
| properties | runFunnelReport | POST | `/v1alpha/{property=properties/*}:runFunnelReport` | Funnel report (alpha only) | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties | getPropertyQuotasSnapshot | GET | `/v1alpha/{name=properties/*/propertyQuotasSnapshot}` | All quota categories for a property | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties.audienceLists | create/get/list/query | POST/GET | `/v1alpha/{parent=properties/*}/audienceLists` | Audience lists (alpha predecessor to audienceExports) | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties.recurringAudienceLists | create/get/list | POST/GET | `/v1alpha/{parent=properties/*}/recurringAudienceLists` | Scheduled recurring audience list snapshots | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |
| properties.reportTasks | create/get/list/query | POST/GET | `/v1alpha/{parent=properties/*}/reportTasks` | Async large report tasks | https://developers.google.com/analytics/devguides/reporting/data/v1/rest |

### Admin API (v1alpha — key events used by current gads CLI)

| Resource | Method | HTTP | Path | Purpose | Source URL |
|----------|--------|------|------|---------|------------|
| properties.keyEvents | list | GET | `/v1alpha/{parent=properties/*}/keyEvents` | List all key events for a property (paginated) | https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents/list |
| properties.keyEvents | create | POST | `/v1alpha/{parent=properties/*}/keyEvents` | Create a new key event | https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents |
| properties.keyEvents | get | GET | `/v1alpha/{name=properties/*/keyEvents/*}` | Get a single key event | https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents |
| properties.keyEvents | patch | PATCH | `/v1alpha/{keyEvent.name=properties/*/keyEvents/*}` | Update key event fields (e.g. countingMethod) | https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents |
| properties.keyEvents | delete | DELETE | `/v1alpha/{name=properties/*/keyEvents/*}` | Delete a key event | https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents |

### Admin API (v1beta — stable alternative for key events)

The `properties.keyEvents` resource exposes the same five methods (create, delete, get, list, patch) in v1beta. No documented behavioral differences vs v1alpha for key events. New subcommands should prefer v1beta.

To switch: replace `analyticsadmin.googleapis.com/v1alpha` with `analyticsadmin.googleapis.com/v1beta` in the base URL. No other changes needed for key events.

Source: https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.keyEvents

---

## Concrete Examples — Priority Endpoints

All examples use:
- Property ID: `271773771` (from `GOOGLE_GA4_PROPERTY_ID`)
- Token: obtained via `google-auth` library — `credentials.token` after `credentials.refresh(Request())`

---

### POST /v1beta/properties/{pid}:runReport

**Full HTTP request:**

```
POST https://analyticsdata.googleapis.com/v1beta/properties/271773771:runReport
Authorization: Bearer ya29.a0ARrdaM...{token}
Content-Type: application/json

{
  "dimensions": [
    {"name": "sessionSource"},
    {"name": "sessionMedium"}
  ],
  "metrics": [
    {"name": "sessions"},
    {"name": "keyEvents"},
    {"name": "totalRevenue"}
  ],
  "dateRanges": [
    {"startDate": "7daysAgo", "endDate": "yesterday"}
  ],
  "orderBys": [
    {"metric": {"metricName": "sessions"}, "desc": true}
  ],
  "limit": 100,
  "offset": 0,
  "returnPropertyQuota": true
}
```

**All request fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `dimensions[]` | array of `{name: string}` | optional | Max ~9 dimensions per request |
| `metrics[]` | array of `{name: string}` | optional | At least one dimension or metric required |
| `dateRanges[]` | array of `{startDate, endDate}` | optional (default: none) | Accepts `"today"`, `"yesterday"`, `"NdaysAgo"`, `"YYYY-MM-DD"`. Up to 4 ranges. |
| `dimensionFilter` | `FilterExpression` | optional | SQL WHERE equivalent on dimensions |
| `metricFilter` | `FilterExpression` | optional | SQL HAVING equivalent, applied post-aggregation |
| `offset` | integer | optional | 0-indexed row offset for pagination (default: 0) |
| `limit` | integer | optional | Max rows to return (default: 10,000; max: 250,000) |
| `orderBys[]` | array | optional | Each element is `{metric: {metricName}, desc: bool}` or `{dimension: {dimensionName}, desc: bool}` |
| `metricAggregations[]` | array of enum | optional | `"TOTAL"`, `"MINIMUM"`, `"MAXIMUM"`, `"COUNT"` — appends aggregate rows |
| `keepEmptyRows` | boolean | optional | Include rows with zero metric values (default: false) |
| `returnPropertyQuota` | boolean | optional | Include quota state in response (default: false) |
| `currencyCode` | string | optional | ISO 4217; overrides property default |
| `comparisons[]` | array | optional | Side-by-side comparison columns |
| `cohortSpec` | object | optional | Cohort analysis configuration |

**Example response:**

```json
{
  "dimensionHeaders": [
    {"name": "sessionSource"},
    {"name": "sessionMedium"}
  ],
  "metricHeaders": [
    {"name": "sessions", "type": "TYPE_INTEGER"},
    {"name": "keyEvents", "type": "TYPE_INTEGER"},
    {"name": "totalRevenue", "type": "TYPE_CURRENCY"}
  ],
  "rows": [
    {
      "dimensionValues": [
        {"value": "google"},
        {"value": "cpc"}
      ],
      "metricValues": [
        {"value": "1842"},
        {"value": "37"},
        {"value": "4120.50"}
      ]
    },
    {
      "dimensionValues": [
        {"value": "google"},
        {"value": "organic"}
      ],
      "metricValues": [
        {"value": "923"},
        {"value": "11"},
        {"value": "890.00"}
      ]
    },
    {
      "dimensionValues": [
        {"value": "(direct)"},
        {"value": "(none)"}
      ],
      "metricValues": [
        {"value": "511"},
        {"value": "8"},
        {"value": "630.00"}
      ]
    }
  ],
  "rowCount": 12,
  "metadata": {
    "currencyCode": "AED",
    "timeZone": "Asia/Dubai",
    "dataLossFromOtherRow": false,
    "schemaRestrictionResponse": {
      "activeMetricRestrictions": []
    }
  },
  "propertyQuota": {
    "tokensPerDay": {"consumed": 14, "remaining": 199986},
    "tokensPerHour": {"consumed": 14, "remaining": 39986},
    "concurrentRequests": {"consumed": 0, "remaining": 10},
    "serverErrorsPerProjectPerHour": {"consumed": 0, "remaining": 10},
    "potentiallyThresholdedRequestsPerHour": {"consumed": 0, "remaining": 120}
  },
  "kind": "analyticsData#runReport"
}
```

**Key response field notes:**
- `rows[i].dimensionValues[j].value` — always a string, even for numeric dimension values
- `rows[i].metricValues[j].value` — always a string; parse to int/float as needed based on `metricHeaders[j].type`
- `rowCount` — total rows matching the query, NOT the number of rows returned (used to compute whether more pages exist: `if offset + len(rows) < rowCount: fetch next page`)
- Metric types: `TYPE_INTEGER`, `TYPE_FLOAT`, `TYPE_CURRENCY`, `TYPE_SECONDS`, `TYPE_MILLISECONDS`, `TYPE_MINUTES`, `TYPE_HOURS`, `TYPE_STANDARD`, `TYPE_CURRENCY`, `TYPE_FEET`, `TYPE_MILES`, `TYPE_METERS`, `TYPE_KILOMETERS`

**Pagination pattern:**
```python
offset = 0
limit = 10000
all_rows = []
while True:
    body["offset"] = offset
    body["limit"] = limit
    resp = requests.post(url, json=body, headers=headers).json()
    rows = resp.get("rows", [])
    all_rows.extend(rows)
    row_count = resp.get("rowCount", 0)
    offset += len(rows)
    if offset >= row_count or not rows:
        break
```

Source: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport

---

### POST /v1beta/properties/{pid}:runRealtimeReport

**Full HTTP request:**

```
POST https://analyticsdata.googleapis.com/v1beta/properties/271773771:runRealtimeReport
Authorization: Bearer ya29.a0ARrdaM...{token}
Content-Type: application/json

{
  "dimensions": [
    {"name": "city"},
    {"name": "deviceCategory"}
  ],
  "metrics": [
    {"name": "activeUsers"}
  ],
  "minuteRanges": [
    {"name": "last_30_min", "startMinutesAgo": 29, "endMinutesAgo": 0}
  ],
  "orderBys": [
    {"metric": {"metricName": "activeUsers"}, "desc": true}
  ],
  "limit": 50,
  "returnPropertyQuota": true
}
```

**All request fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `dimensions[]` | array of `{name: string}` | optional | Realtime-specific dimensions available (e.g. `"city"`, `"country"`, `"deviceCategory"`, `"platform"`, `"unifiedScreenName"`) |
| `metrics[]` | array of `{name: string}` | optional | Realtime metrics: `"activeUsers"`, `"screenPageViews"`, `"eventCount"` |
| `minuteRanges[]` | array of `{name?, startMinutesAgo, endMinutesAgo}` | optional | Default = last 30 min. Max 2 ranges. Values: 0 (now) to 29 (standard) / 59 (360). `name` is optional label for multi-range responses. |
| `dimensionFilter` | `FilterExpression` | optional | Same structure as runReport |
| `metricFilter` | `FilterExpression` | optional | Same structure as runReport |
| `limit` | integer | optional | Max rows (default 10,000; max 250,000) |
| `metricAggregations[]` | array of enum | optional | Same as runReport |
| `orderBys[]` | array | optional | Same as runReport |
| `returnPropertyQuota` | boolean | optional | Include realtime quota state |

**NOT valid in runRealtimeReport** (will cause 400 error):
- `dateRanges` — use `minuteRanges` instead
- `offset` — realtime has no pagination
- `keepEmptyRows`
- `cohortSpec`
- `comparisons`

**Example response:**

```json
{
  "dimensionHeaders": [
    {"name": "city"},
    {"name": "deviceCategory"}
  ],
  "metricHeaders": [
    {"name": "activeUsers", "type": "TYPE_INTEGER"}
  ],
  "rows": [
    {
      "dimensionValues": [{"value": "Dubai"}, {"value": "mobile"}],
      "metricValues": [{"value": "23"}]
    },
    {
      "dimensionValues": [{"value": "Abu Dhabi"}, {"value": "mobile"}],
      "metricValues": [{"value": "7"}]
    },
    {
      "dimensionValues": [{"value": "Dubai"}, {"value": "desktop"}],
      "metricValues": [{"value": "4"}]
    }
  ],
  "rowCount": 8,
  "propertyQuota": {
    "tokensPerDay": {"consumed": 3, "remaining": 199997},
    "tokensPerHour": {"consumed": 3, "remaining": 39997},
    "concurrentRequests": {"consumed": 0, "remaining": 10},
    "serverErrorsPerProjectPerHour": {"consumed": 0, "remaining": 10}
  },
  "kind": "analyticsData#runRealtimeReport"
}
```

**Realtime-specific notes:**
- `rowCount` may be less than `limit`; there is no more data to page through
- Data reflects events received within the last 30 minutes (standard) or 60 minutes (360)
- Events appear typically within seconds of firing; some latency is expected
- Realtime dimensions are a subset of standard dimensions — not all standard dimensions work in realtime

Source: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runRealtimeReport

---

### GET /v1beta/properties/{pid}/metadata

**Full HTTP request:**

```
GET https://analyticsdata.googleapis.com/v1beta/properties/271773771/metadata
Authorization: Bearer ya29.a0ARrdaM...{token}
```

No request body. No query parameters except the path parameter.

- Use `properties/0/metadata` to get only universal dimensions/metrics (no property-specific custom ones)

**Example response (abbreviated — real response has 200+ entries):**

```json
{
  "name": "properties/271773771/metadata",
  "dimensions": [
    {
      "apiName": "city",
      "uiName": "City",
      "description": "The city from which the user activity originated.",
      "category": "Geography"
    },
    {
      "apiName": "country",
      "uiName": "Country",
      "description": "The country from which the user activity originated.",
      "category": "Geography"
    },
    {
      "apiName": "sessionSource",
      "uiName": "Session source",
      "description": "The source that initiated a session.",
      "category": "Traffic source"
    },
    {
      "apiName": "sessionMedium",
      "uiName": "Session medium",
      "description": "The medium that initiated a session.",
      "category": "Traffic source"
    },
    {
      "apiName": "deviceCategory",
      "uiName": "Device category",
      "description": "The type of device: Desktop, Tablet, or Mobile.",
      "category": "Platform / Device"
    },
    {
      "apiName": "customEvent:branch",
      "uiName": "branch (custom event)",
      "description": "Custom event parameter 'branch'",
      "category": "Custom",
      "customDefinition": true
    }
  ],
  "metrics": [
    {
      "apiName": "activeUsers",
      "uiName": "Active users",
      "description": "The number of distinct users who visited your site or app.",
      "type": "TYPE_INTEGER",
      "category": "User"
    },
    {
      "apiName": "sessions",
      "uiName": "Sessions",
      "description": "The number of sessions that began on your site or app.",
      "type": "TYPE_INTEGER",
      "category": "Session"
    },
    {
      "apiName": "keyEvents",
      "uiName": "Key events",
      "description": "The number of times users triggered a key event.",
      "type": "TYPE_INTEGER",
      "category": "Conversions"
    },
    {
      "apiName": "keyEvents:purchase",
      "uiName": "Purchase key events",
      "description": "The number of times users triggered the 'purchase' key event.",
      "type": "TYPE_INTEGER",
      "category": "Conversions",
      "customDefinition": true
    },
    {
      "apiName": "keyEvents:whatsapp_click",
      "uiName": "whatsapp_click key events",
      "description": "The number of times users triggered the 'whatsapp_click' key event.",
      "type": "TYPE_INTEGER",
      "category": "Conversions",
      "customDefinition": true
    },
    {
      "apiName": "totalRevenue",
      "uiName": "Total revenue",
      "description": "The sum of revenue from purchases, subscriptions, and advertising.",
      "type": "TYPE_CURRENCY",
      "category": "Revenue"
    }
  ]
}
```

**Key notes:**
- `customDefinition: true` marks property-specific dimensions/metrics (custom events, key event metrics)
- Key event metrics have `apiName` prefix `keyEvents:` followed by the event name
- Custom event parameters have prefix `customEvent:` (event-scoped) or `customUser:` (user-scoped)
- Use this endpoint first to discover available dimension/metric names before building runReport requests
- No pagination — returns all entries in one call (can be large; cache it)

Source: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/getMetadata

---

### GET /v1alpha/properties/{pid}/keyEvents (list)

**Full HTTP request:**

```
GET https://analyticsadmin.googleapis.com/v1alpha/properties/271773771/keyEvents?pageSize=200
Authorization: Bearer ya29.a0ARrdaM...{token}
```

No request body. Query parameters:

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `pageSize` | integer | optional | Max 200 (default 50). The gads CLI uses `pageSize=200`. |
| `pageToken` | string | optional | Opaque token from previous response's `nextPageToken` |

**Example response:**

```json
{
  "keyEvents": [
    {
      "name": "properties/271773771/keyEvents/11111111",
      "eventName": "purchase",
      "createTime": "2024-03-15T08:22:14.000000Z",
      "deletable": true,
      "custom": false,
      "countingMethod": "ONCE_PER_EVENT",
      "defaultValue": {
        "numericValue": 0.0,
        "currencyCode": "AED"
      }
    },
    {
      "name": "properties/271773771/keyEvents/22222222",
      "eventName": "whatsapp_click",
      "createTime": "2024-06-01T11:45:00.000000Z",
      "deletable": true,
      "custom": true,
      "countingMethod": "ONCE_PER_EVENT"
    },
    {
      "name": "properties/271773771/keyEvents/33333333",
      "eventName": "begin_checkout",
      "createTime": "2024-06-01T11:45:01.000000Z",
      "deletable": true,
      "custom": false,
      "countingMethod": "ONCE_PER_SESSION"
    }
  ]
}
```

When there are more pages:
```json
{
  "keyEvents": [...],
  "nextPageToken": "Cg8KDXByb3BlcnRpZXMv..."
}
```

**Pagination pattern:**
```python
page_token = None
all_events = []
while True:
    params = {"pageSize": 200}
    if page_token:
        params["pageToken"] = page_token
    resp = requests.get(url, params=params, headers=headers).json()
    all_events.extend(resp.get("keyEvents", []))
    page_token = resp.get("nextPageToken")
    if not page_token:
        break
```

Source: https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents/list

---

### POST /v1alpha/properties/{pid}/keyEvents (create)

**Full HTTP request:**

```
POST https://analyticsadmin.googleapis.com/v1alpha/properties/271773771/keyEvents
Authorization: Bearer ya29.a0ARrdaM...{token}
Content-Type: application/json

{
  "eventName": "form_submit",
  "countingMethod": "ONCE_PER_EVENT"
}
```

**All request body fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `eventName` | string | **required** | GA4 event name exactly as tracked (e.g. `"form_submit"`, `"whatsapp_click"`). Immutable after creation. Must match an event that GA4 actually receives. |
| `countingMethod` | enum | **required** | `"ONCE_PER_EVENT"` or `"ONCE_PER_SESSION"` |
| `defaultValue.numericValue` | number | optional | Default monetary value for this key event |
| `defaultValue.currencyCode` | string | optional | ISO 4217 (e.g. `"AED"`) |

**Do NOT send:** `name`, `createTime`, `deletable`, `custom` — these are output-only and will be ignored or cause an error.

**Success response (201 Created):**

```json
{
  "name": "properties/271773771/keyEvents/44444444",
  "eventName": "form_submit",
  "createTime": "2026-06-23T10:30:00.000000Z",
  "deletable": true,
  "custom": true,
  "countingMethod": "ONCE_PER_EVENT"
}
```

**409 Conflict — event already exists as a key event:**

```json
{
  "error": {
    "code": 409,
    "message": "Key event already exists: form_submit",
    "status": "ALREADY_EXISTS",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.ResourceInfo",
        "resourceType": "analyticsadmin.googleapis.com/KeyEvent",
        "resourceName": "properties/271773771/keyEvents/44444444",
        "description": "A Key Event already exists with this event name."
      }
    ]
  }
}
```

**Handling 409 in the CLI:** The existing `ga4.py` code should treat 409 as "already exists — skip" for bulk operations, not as a fatal error.

Source: https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents

---

### DELETE /v1alpha/properties/{pid}/keyEvents/{keyEventId}

**Critical:** The path uses the **full resource name** from the `name` field of the KeyEvent object — NOT the `eventName` string. The `keyEventId` segment is the numeric ID from `name` (e.g. `"44444444"` from `"properties/271773771/keyEvents/44444444"`).

**Full HTTP request:**

```
DELETE https://analyticsadmin.googleapis.com/v1alpha/properties/271773771/keyEvents/44444444
Authorization: Bearer ya29.a0ARrdaM...{token}
```

No request body. No query parameters.

**Success response:** HTTP 200 with empty body `{}`

**404 — key event not found or wrong ID:**

```json
{
  "error": {
    "code": 404,
    "message": "Key event not found.",
    "status": "NOT_FOUND"
  }
}
```

**403 — wrong scope (analytics.readonly instead of analytics.edit):**

```json
{
  "error": {
    "code": 403,
    "message": "Request had insufficient authentication scopes.",
    "status": "PERMISSION_DENIED",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
        "reason": "ACCESS_TOKEN_SCOPE_INSUFFICIENT",
        "domain": "googleapis.com",
        "metadata": {
          "method": "google.analytics.admin.v1alpha.AnalyticsAdminService.DeleteKeyEvent",
          "service": "analyticsadmin.googleapis.com"
        }
      }
    ]
  }
}
```

**Pattern in gads CLI:** The CLI lists key events first (to get the `name` field), then calls delete using the `name`. The `eventName` string alone is NOT sufficient to delete — you must resolve it to a `name` first via list.

```python
# Correct delete pattern:
# 1. List to find name
events = list_key_events(pid)  # returns [{name: "properties/X/keyEvents/Y", eventName: "foo", ...}]
match = next((e for e in events if e["eventName"] == target_event_name), None)
if match:
    delete_url = f"https://analyticsadmin.googleapis.com/v1alpha/{match['name']}"
    requests.delete(delete_url, headers=headers)
```

Source: https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents

---

## Key Request/Response Fields — Reference

### runReport — complete field reference

**Request body** (`POST /v1beta/properties/{pid}:runReport`):

```json
{
  "dimensions": [{"name": "city"}],
  "metrics": [{"name": "totalUsers"}],
  "dateRanges": [{"startDate": "2025-01-01", "endDate": "today"}],
  "dimensionFilter": {
    "filter": {
      "fieldName": "country",
      "stringFilter": {"matchType": "EXACT", "value": "United Arab Emirates"}
    }
  },
  "metricFilter": {
    "filter": {
      "fieldName": "totalUsers",
      "numericFilter": {"operation": "GREATER_THAN", "value": {"int64Value": "100"}}
    }
  },
  "offset": 0,
  "limit": 10000,
  "orderBys": [{"metric": {"metricName": "totalUsers"}, "desc": true}],
  "metricAggregations": ["TOTAL", "MAXIMUM", "MINIMUM"],
  "keepEmptyRows": false,
  "returnPropertyQuota": true,
  "currencyCode": "AED",
  "comparisons": []
}
```

- `limit` default: 10,000; max: 250,000
- `offset` is 0-indexed (not pageToken-based)
- `dateRanges` supports up to 4 ranges; use `startDate`/`endDate` with values like `"today"`, `"yesterday"`, `"7daysAgo"`, or `"YYYY-MM-DD"`

**FilterExpression structures:**

```json
// Single filter
{"filter": {"fieldName": "city", "stringFilter": {"value": "Dubai"}}}

// AND of multiple filters
{"andGroup": {"expressions": [
  {"filter": {"fieldName": "country", "stringFilter": {"value": "United Arab Emirates"}}},
  {"filter": {"fieldName": "deviceCategory", "stringFilter": {"value": "mobile"}}}
]}}

// OR of multiple filters
{"orGroup": {"expressions": [...]}}

// NOT
{"notExpression": {"filter": {...}}}

// inListFilter (any of N values)
{"filter": {"fieldName": "city", "inListFilter": {"values": ["Dubai", "Abu Dhabi", "Sharjah"]}}}

// betweenFilter (numeric range)
{"filter": {"fieldName": "sessions", "betweenFilter": {
  "fromValue": {"int64Value": "10"},
  "toValue": {"int64Value": "100"}
}}}
```

**stringFilter matchType values:** `EXACT`, `BEGINS_WITH`, `ENDS_WITH`, `CONTAINS`, `FULL_REGEXP`, `PARTIAL_REGEXP`

Source: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport

---

### runRealtimeReport — field reference

**Request body** (`POST /v1beta/properties/{pid}:runRealtimeReport`):

```json
{
  "dimensions": [{"name": "country"}],
  "metrics": [{"name": "activeUsers"}],
  "minuteRanges": [{"startMinutesAgo": 29, "endMinutesAgo": 0}],
  "dimensionFilter": {},
  "metricFilter": {},
  "limit": 10000,
  "metricAggregations": ["TOTAL"],
  "orderBys": [],
  "returnPropertyQuota": true
}
```

- `minuteRanges` instead of `dateRanges`; default = last 30 minutes; max 2 ranges per request
- 360 properties: up to 60 minutes of realtime data
- No `offset`; no pagination — realtime is a snapshot
- `dateRanges` is NOT a valid field (realtime-only uses `minuteRanges`)

**Response body**: same shape as `runReport` but with `kind: "analyticsData#runRealtimeReport"` and `propertyQuota` reflects realtime quota.

Source: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runRealtimeReport

---

### getMetadata — field reference

**Request** (`GET /v1beta/properties/{pid}/metadata`):

- Path parameter `name` = `properties/{propertyId}/metadata`
- Use `properties/0/metadata` to get universal dimensions/metrics (excludes custom ones)
- Empty request body

**Response fields per dimension:**
- `apiName` — string to use in `dimensions[].name`
- `uiName` — human-readable label
- `description` — what it means
- `category` — grouping category
- `customDefinition` — boolean, true if property-specific
- `deprecatedApiNames[]` — old names (may be absent)
- `blockedReasons[]` — if access-controlled

**Response fields per metric:**
- `apiName`, `uiName`, `description`, `category` — same as dimensions
- `type` — `TYPE_INTEGER`, `TYPE_FLOAT`, `TYPE_CURRENCY`, `TYPE_SECONDS`, `TYPE_MINUTES`, `TYPE_HOURS`, `TYPE_STANDARD`, `TYPE_FEET`, `TYPE_MILES`, `TYPE_METERS`, `TYPE_KILOMETERS`
- `expression` — formula for calculated metrics
- `customDefinition` — boolean

Source: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/getMetadata

---

### keyEvents (Admin API) — field reference

**KeyEvent resource object:**

```json
{
  "name": "properties/271773771/keyEvents/44444444",
  "eventName": "purchase",
  "createTime": "2025-01-15T10:30:00.000000Z",
  "deletable": true,
  "custom": true,
  "countingMethod": "ONCE_PER_EVENT",
  "defaultValue": {
    "numericValue": 0.0,
    "currencyCode": "AED"
  }
}
```

**Field details:**

| Field | Type | R/W | Notes |
|-------|------|-----|-------|
| `name` | string | output-only | Full resource path: `properties/{property}/keyEvents/{keyEvent}` — use as the DELETE URL path |
| `eventName` | string | create-only (immutable) | GA4 event name — cannot be changed after creation; must match an event being tracked |
| `createTime` | string | output-only | RFC 3339 timestamp |
| `custom` | boolean | output-only | `false` for built-in GA4 events (purchase, first_visit, etc.), `true` for custom events |
| `deletable` | boolean | output-only | `false` for events that GA4 protects from deletion |
| `countingMethod` | enum | required on create; patchable | `ONCE_PER_EVENT` or `ONCE_PER_SESSION` |
| `defaultValue.numericValue` | number | optional | Default monetary value assigned when the event doesn't include a `value` parameter |
| `defaultValue.currencyCode` | string | optional | ISO 4217; required when `defaultValue.numericValue` is set |

**countingMethod:**
- `ONCE_PER_EVENT` — every event instance counts as a key event (e.g. each WhatsApp click counted separately)
- `ONCE_PER_SESSION` — at most one key event per session per user (e.g. if purchase fires 3× in one session, it only counts once)

**list request parameters:**
- `pageSize`: max 200, default 50 (gads CLI uses 200)
- `pageToken`: opaque token from previous `nextPageToken`
- `parent`: `properties/{propertyId}` (path param, not query param)

**list response:**
```json
{
  "keyEvents": [...],
  "nextPageToken": "Cg8KDXByb3BlcnRpZXMv..."
}
```
`nextPageToken` is omitted (not null) when there are no more pages.

Sources: https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents, https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents/list

---

## Error Responses — Common Patterns

### 400 — Invalid dimension or metric name

```json
{
  "error": {
    "code": 400,
    "message": "Field dimension[0] has unknown name 'sessions'. Did you mean metric[0] sessions?",
    "status": "INVALID_ARGUMENT",
    "details": [
      {
        "@type": "type.googleapis.com/google.analytics.data.v1beta.QuotaFailure"
      }
    ]
  }
}
```

Also occurs when trying to combine incompatible dimensions and metrics. Use `checkCompatibility` to pre-validate, or call `getMetadata` to verify `apiName` values.

### 403 — Missing analytics.edit scope (write operations)

```json
{
  "error": {
    "code": 403,
    "message": "Request had insufficient authentication scopes.",
    "status": "PERMISSION_DENIED",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
        "reason": "ACCESS_TOKEN_SCOPE_INSUFFICIENT",
        "domain": "googleapis.com",
        "metadata": {
          "method": "google.analytics.admin.v1alpha.AnalyticsAdminService.CreateKeyEvent",
          "service": "analyticsadmin.googleapis.com"
        }
      }
    ]
  }
}
```

**Fix:** Regenerate the OAuth token to include `analytics.edit` scope. The gads CLI's `generate_token.py` already includes it — if you see this, the token is stale.

### 403 — Wrong GA4 property ID or no access

```json
{
  "error": {
    "code": 403,
    "message": "The caller does not have permission",
    "status": "PERMISSION_DENIED"
  }
}
```

**Note:** A 403 for "no access to this property" looks identical to "insufficient scopes" — check both. The property ID in `GOOGLE_GA4_PROPERTY_ID` must be the numeric GA4 property ID, not the Measurement ID (`G-XXXXXXXX`).

### 404 — Wrong property ID format

If the Measurement ID (`G-XXXXXXXX`) is used instead of the numeric property ID, the API returns 404:

```json
{
  "error": {
    "code": 404,
    "message": "Property G-XXXXXXXX not found or it may not be a GA4 property.",
    "status": "NOT_FOUND"
  }
}
```

**Fix:** Use the numeric property ID found in GA4 Admin > Property Settings > Property ID (a 9-digit number like `271773771`).

### 429 — Quota exhausted

```json
{
  "error": {
    "code": 429,
    "message": "Quota exceeded for quota metric 'analyticsdata.googleapis.com/tokens' and limit 'Tokens per project per property per hour' of service 'analyticsdata.googleapis.com'.",
    "status": "RESOURCE_EXHAUSTED",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
        "violations": [
          {
            "subject": "project:my-gcp-project",
            "description": "Quota exceeded for quota metric 'analyticsdata.googleapis.com/tokens' and limit 'Tokens per project per property per hour' of service 'analyticsdata.googleapis.com'."
          }
        ]
      }
    ]
  }
}
```

**Fix:** Wait for hourly quota refresh (within ~60 minutes). Use `returnPropertyQuota: true` proactively to monitor remaining tokens before hitting the limit. For high-volume workloads, use `batchRunReports` to combine multiple report requests and reduce per-request overhead.

### 409 — Key event already exists

```json
{
  "error": {
    "code": 409,
    "message": "Key event already exists: whatsapp_click",
    "status": "ALREADY_EXISTS"
  }
}
```

Treat as success (idempotent) in bulk create operations.

---

## Pagination & Quotas

### Data API Pagination

- `runReport` and `runPivotReport` use **offset-based pagination** (`offset` + `limit`), NOT page tokens
- `batchRunReports`, `checkCompatibility` — same offset approach per report
- `audienceExports.list` — uses `pageToken` / `pageSize`
- `runRealtimeReport` — no pagination (snapshot; use `limit` to cap rows)
- `getMetadata` — no pagination (returns all dimensions/metrics in one call)

### Admin API Pagination

- `keyEvents.list`: `pageSize` (max 200), `pageToken` / `nextPageToken`

### Data API Quota Limits

Source: https://developers.google.com/analytics/devguides/reporting/data/v1/quotas

| Quota Category | Standard Property | Analytics 360 |
|---------------|-------------------|---------------|
| Tokens per day | 200,000 | 2,000,000 |
| Tokens per hour (property) | 40,000 | 400,000 |
| Tokens per hour (project, per property) | 14,000 | 140,000 |
| Concurrent requests | 10 | 50 |
| Server errors per hour | 10 | 50 |

- Token cost depends on row count, column count, date range span, filter complexity, and dimension cardinality
- Quota refreshes: daily at midnight PST; hourly within the hour (not necessarily on the hour boundary)
- Use `"returnPropertyQuota": true` in requests to get remaining quota in the response

---

## Gotchas

1. **v1beta vs v1alpha split**: Data API `v1beta` is stable for all standard reporting; only use `v1alpha` if you need funnel reports, async report tasks, or recurring audience lists. Admin API `v1beta` covers key events stably; `v1alpha` is needed for audiences, BigQuery links, channel groups, etc.

2. **Key Events vs Conversion Events naming**: GA4 renamed "conversion events" to "key events" in the UI and API. The Admin API resource is `keyEvents` (not `conversionEvents`). The old `conversionEvents` resource still exists in some API versions for backward compatibility but `keyEvents` is the current name. The gads CLI correctly uses "Key Events" terminology.

3. **Property ID format**: The `{property}` path parameter must be the **numeric GA4 Property ID** (e.g. `properties/271773771`), NOT the Measurement ID (e.g. `G-XXXXXXXXXX`). These are different identifiers. Using the wrong format produces a 403 or 404 depending on the endpoint.

4. **DELETE path uses `keyEvent.name`**: The delete endpoint takes the full resource name from the `name` field of a KeyEvent object (e.g. `properties/271773771/keyEvents/44444444`), not just the event name string. Always list first to resolve `eventName` → `name`.

5. **`eventName` is immutable**: After creating a key event, the `eventName` cannot be changed. To rename, you must delete and recreate.

6. **`analytics` scope vs `analytics.readonly`**: The broader `analytics` scope is also accepted by Data API read endpoints, but `analytics.edit` is specifically required for Admin API mutations (create/delete/patch key events). A 403 with `ACCESS_TOKEN_SCOPE_INSUFFICIENT` on write calls = missing `analytics.edit`.

7. **Realtime window**: Standard properties get 30 minutes of realtime data; 360 properties get up to 60 minutes. Attempting to specify `minuteRanges` beyond these limits returns an error.

8. **`offset` not `pageToken` for runReport**: Unlike many Google APIs, `runReport` uses integer `offset` for pagination, not a page token string. Check `rowCount` in response to know when you have all rows.

9. **`dateRanges` vs `minuteRanges`**: These are mutually exclusive by endpoint. `runReport` uses `dateRanges`. `runRealtimeReport` uses `minuteRanges`. Sending `dateRanges` to the realtime endpoint returns a 400.

10. **`nextPageToken` absent vs null**: Admin API list endpoints omit `nextPageToken` entirely (key not present) when there are no more pages — they do NOT return `"nextPageToken": null`. Code must check `resp.get("nextPageToken")`, not `resp["nextPageToken"] is None`.

11. **Metric values are always strings**: Even `TYPE_INTEGER` metrics come back as `"value": "1842"` (a JSON string). Always cast: `int(row["metricValues"][0]["value"])`.

12. **409 on bulk create is safe to ignore**: When bulk-creating key events, a 409 means the event is already a key event. Treat as success/skip, not fatal error.

---

## Coverage vs Current gads CLI

The gads CLI (`gads_lib/ga4.py`) currently uses:

| What | Status |
|------|--------|
| `GET /v1beta/properties/{pid}/metadata` | Used — dimension/metric catalog |
| `POST /v1beta/properties/{pid}:runReport` | Used — standard reports |
| `POST /v1beta/properties/{pid}:runRealtimeReport` | Used — realtime reports |
| `GET /v1alpha/properties/{pid}/keyEvents` | Used — list key events (pageSize=200) |
| `POST /v1alpha/properties/{pid}/keyEvents` | Used — create key event |
| `DELETE /v1alpha/{keyEvent.name}` | Used — delete key event |

**Gaps — endpoints not yet used by gads CLI:**

| Endpoint | Notes |
|----------|-------|
| `batchRunReports` | Useful for fetching multiple date ranges or campaigns in one call; reduces quota overhead |
| `runPivotReport` | Cross-tabulation reports; useful for campaign × device or source × medium breakdowns |
| `batchRunPivotReports` | Batch version of pivot |
| `checkCompatibility` | Validate dimension+metric combinations before sending a real report request |
| `audienceExports` (v1beta) | Export audience user lists for retargeting analysis |
| `runFunnelReport` (v1alpha) | Multi-step funnel analysis (checkout steps, etc.) |
| `reportTasks` (v1alpha) | Async large reports that exceed realtime API limits |
| Admin: `keyEvents.get` | Retrieve a single key event by name |
| Admin: `keyEvents.patch` | Update `countingMethod` or `defaultValue` without delete+recreate |
| Admin: Custom dimensions CRUD | `properties.customDimensions` — list/create/archive |
| Admin: Custom metrics CRUD | `properties.customMetrics` — list/create/archive |
| Admin: `accounts` / `properties` | Account-level listing and property provisioning |
| Admin: `runAccessReport` | Audit who accessed GA4 data |

**Migration opportunity:** Switch `key-events` commands from `v1alpha` Admin API to `v1beta` Admin API — same URL structure, just change the version segment. v1beta has stability guarantees that v1alpha does not.

---

## Sources

| URL | What It Documents |
|-----|-------------------|
| https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema | Data API dimensions/metrics catalog overview |
| https://developers.google.com/analytics/devguides/reporting/data/v1/rest | Data API full endpoint reference (v1beta + v1alpha) |
| https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport | runReport request/response shape |
| https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runRealtimeReport | runRealtimeReport request/response shape |
| https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/getMetadata | getMetadata request/response shape |
| https://developers.google.com/analytics/devguides/reporting/data/v1/quotas | Quota limits (tokens/day, tokens/hour, concurrency) |
| https://developers.google.com/analytics/devguides/config/admin/v1 | Admin API overview and version channels |
| https://developers.google.com/analytics/devguides/config/admin/v1/rest | Admin API endpoint reference (v1beta + v1alpha) |
| https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents | keyEvents resource (v1alpha) all methods |
| https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.keyEvents/list | keyEvents.list — pagination params and auth scopes |
| https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.keyEvents | keyEvents resource (v1beta) — confirms same methods available |
