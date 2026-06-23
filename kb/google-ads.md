# Google Ads REST API

> Implementation-grade reference for building new gads-cli subcommands.
> Every concrete request/response example is derived from the live `gads_lib/ads.py`
> implementation + official doc pages fetched 2026-06-23.

---

## Status & Versions

| Version | Release Date | Status |
|---------|-------------|--------|
| v24.2   | ~2026-06 (announced, not yet released) | Announced |
| v24.1   | 2026-05-13 | GA |
| v24     | 2026-04-22 | GA |
| v23.2   | 2026-03-25 | GA |
| v23.1   | 2026-02-25 | GA |
| v23     | 2026-01-28 | GA |
| v22.1   | 2026-02-25 | GA |
| v22     | 2025-10-15 | GA |
| v21.1   | 2026-02-25 | GA |
| v21     | 2025-08-06 | GA |

**Current gads-cli default:** `v24` (env var `GOOGLE_ADS_API_VERSION`, falls back to `"v24"` in `config.py`).

**Sunset schedule:** Explicit per-version sunset dates were not extractable from the doc fetch (page exists at `https://developers.google.com/google-ads/api/docs/sunset-dates` but the table content was not returned). Google typically sunsets a version ~12 months after a newer major version ships. (unverified — doc fetch returned navigation only, not the dates table)

**Sources:**
- Release notes: https://developers.google.com/google-ads/api/docs/release-notes (fetched 2026-06-23)
- Introduction: https://developers.google.com/google-ads/api/docs/get-started/introduction (fetched 2026-06-23)
- Sunset dates: https://developers.google.com/google-ads/api/docs/sunset-dates (fetched 2026-06-23 — page exists, dates table not extracted)


---

## Base URL

```
https://googleads.googleapis.com/{API_VERSION: string}/customers/{CUSTOMER_ID: 10-digit-string}/
```

**Two path patterns — do not mix them:**

| Pattern | Example | Used for |
|---------|---------|---------|
| `customers/{CID}/{resource}:{method}` | `customers/3552856345/campaigns:mutate` | Resource-scoped operations |
| `customers/{CID}:{method}` | `customers/3552856345:generateKeywordIdeas` | Customer-level operations |

The `offlineUserDataJobs/{job_id}:addOperations` and `:run` paths are **not** prefixed with `customers/` — the full resource name returned from `:create` is used verbatim:

```
https://googleads.googleapis.com/v24/{job_resource_name}:addOperations
# e.g. https://googleads.googleapis.com/v24/customers/3552856345/offlineUserDataJobs/12345:addOperations
```

Source: confirmed from `gads_lib/ads.py` + introduction page.


---

## Auth / OAuth Scopes

| Scope | Services | How to pass |
|-------|---------|-------------|
| `https://www.googleapis.com/auth/adwords` | All Google Ads API endpoints | `Authorization: Bearer {token}` header |

### Required HTTP Headers (ALL Google Ads REST calls)

| Header | Type | Required? | Value |
|--------|------|-----------|-------|
| `Authorization` | string | Always | `Bearer {oauth2_access_token}` |
| `developer-token` | string | Always | 22-char alphanumeric from API Center |
| `login-customer-id` | string (10 digits) | When using MCC | Manager account ID, no dashes |
| `Content-Type` | string | Always for POST | `application/json` |

**Example headers block (used in every request below):**
```http
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json
```

### Developer Token Access Levels

| Level | Environments | Keyword Planner / Forecast |
|-------|-------------|---------------------------|
| Test Account | Test accounts only | No |
| Explorer | Production, some restrictions | No |
| Basic | Production | No |
| Standard | Production | Yes — required for `:generateKeywordIdeas` and `:generateKeywordForecastMetrics` |

Source:
- Developer token: https://developers.google.com/google-ads/api/docs/get-started/dev-token (fetched 2026-06-23)
- Account hierarchy / login-customer-id: https://developers.google.com/google-ads/api/docs/account-management/get-account-hierarchy (fetched 2026-06-23)
- `gads-cli/CLAUDE.md` confirms `adwords` scope and Standard Access requirement


---

## Endpoint Reference

Quick index:

| # | Endpoint | gads-cli function |
|---|----------|-------------------|
| 1 | `googleAds:searchStream` | `run_gaql()` |
| 2 | `googleAds:search` | `ads_search()` |
| 3 | `googleAds:mutate` (batch) | `ads_batch_mutate()` |
| 4 | `{resource}:mutate` (single) | `ads_mutate()` |
| 5 | `offlineUserDataJobs:create` | `audience_upload_csv()` |
| 6 | `{job}:addOperations` | `audience_upload_csv()` |
| 7 | `{job}:run` | `audience_upload_csv()` |
| 8 | `userLists:mutate` | `audience_create_list()` |
| 9 | `:generateKeywordIdeas` | `generate_keyword_ideas()` |
| 10 | `:generateKeywordForecastMetrics` | `generate_keyword_forecast()` |
| 11 | `:uploadClickConversions` | `ads_upload_click_conversions()` |


---

### 1. `googleAds:searchStream` — GAQL Streaming Query

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}/googleAds:searchStream`

**When to use:** Bulk data pull — all matching rows returned in a single HTTP response body as an array of batch objects. No pagination. Faster than `search` for complete datasets. Used by `run_gaql()` throughout the CLI.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | GAQL query string |

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/googleAds:searchStream
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "query": "SELECT campaign.id, campaign.name, campaign.status, metrics.clicks, metrics.cost_micros, metrics.conversions FROM campaign WHERE segments.date DURING LAST_7_DAYS ORDER BY metrics.cost_micros DESC"
}
```

#### Response

The response is a **JSON array** of batch objects. Each batch has a `results` array and a `fieldMask`. Typically a single batch for normal result sets.

```json
[
  {
    "results": [
      {
        "campaign": {
          "resourceName": "customers/3552856345/campaigns/123456789",
          "id": "123456789",
          "name": "Search - Tesla Parts - QZ3",
          "status": "ENABLED"
        },
        "metrics": {
          "clicks": "142",
          "costMicros": "185340000",
          "conversions": 3.0
        }
      },
      {
        "campaign": {
          "resourceName": "customers/3552856345/campaigns/987654321",
          "id": "987654321",
          "name": "PMax - Tesla - IND4",
          "status": "ENABLED"
        },
        "metrics": {
          "clicks": "98",
          "costMicros": "112000000",
          "conversions": 1.0
        }
      }
    ],
    "fieldMask": "campaign.id,campaign.name,campaign.status,metrics.clicks,metrics.costMicros,metrics.conversions"
  }
]
```

**Important field conventions:**
- Numbers are returned as **strings** for integer IDs (e.g. `"id": "123456789"`)
- `cost_micros` in GAQL becomes `costMicros` in JSON response (camelCase)
- `metrics.cost_micros` value is in **micros** — divide by 1,000,000 for AED/USD amount
- `metrics.conversions` is a float, not a string

#### Python access pattern

```python
results = run_gaql(creds, query)
# results is already the flat list from all batch["results"]
for row in results:
    name = row["campaign"]["name"]
    cost_aed = int(row["metrics"].get("costMicros", 0)) / 1_000_000
```

#### Error Response

```json
{
  "error": {
    "code": 400,
    "message": "Request contains an invalid argument.",
    "status": "INVALID_ARGUMENT",
    "details": [
      {
        "@type": "type.googleapis.com/google.ads.googleads.v24.errors.GoogleAdsFailure",
        "errors": [
          {
            "errorCode": {
              "queryError": "UNRECOGNIZED_FIELD"
            },
            "message": "Unrecognized field in the query: 'campaign.foo'.",
            "location": {
              "fieldPathElements": [{"fieldName": "query"}]
            }
          }
        ]
      }
    ]
  }
}
```

---

### 2. `googleAds:search` — Paginated GAQL Query

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}/googleAds:search`

**When to use:** Large result sets requiring pagination, or when you need `returnTotalResultsCount`. Used by `ads_search()`.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | GAQL query string |
| `pageToken` | string | No | Token from previous response's `nextPageToken` for subsequent pages |
| `returnTotalResultsCount` | bool | No | Include `totalResultsCount` in response |
| `validateOnly` | bool | No | Validate query without executing |

**Page size is fixed at 10,000 rows** (since v19). The `page_size` field was removed — do not send it.

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/googleAds:search
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "query": "SELECT keyword_view.resource_name, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, metrics.impressions, metrics.clicks FROM keyword_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.impressions DESC"
}
```

**Second page request** (add `pageToken` from previous response):
```json
{
  "query": "SELECT keyword_view.resource_name, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, metrics.impressions, metrics.clicks FROM keyword_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.impressions DESC",
  "pageToken": "CiQIABAAGAIiHQoZZ29vZ2xl..."
}
```

#### Response

```json
{
  "results": [
    {
      "keywordView": {
        "resourceName": "customers/3552856345/keywordViews/111~222"
      },
      "adGroupCriterion": {
        "keyword": {
          "text": "tesla model 3 parts",
          "matchType": "BROAD"
        }
      },
      "metrics": {
        "impressions": "4200",
        "clicks": "310"
      }
    }
  ],
  "nextPageToken": "CiQIABAAGAIiHQoZZ29vZ2xl...",
  "fieldMask": "keywordView.resourceName,adGroupCriterion.keyword.text,adGroupCriterion.keyword.matchType,metrics.impressions,metrics.clicks"
}
```

**Final page** — `nextPageToken` is absent or empty string:
```json
{
  "results": [ /* ... last batch ... */ ],
  "fieldMask": "..."
}
```

#### Pagination Loop Pattern

```python
page_token = None
results = []
while True:
    payload = {"query": query}
    if page_token:
        payload["pageToken"] = page_token
    resp = requests.post(url, headers=headers, json=payload)
    data = resp.json()
    results.extend(data.get("results", []))
    page_token = data.get("nextPageToken")
    if not page_token:
        break
```

**Rule:** The query string must be **byte-for-byte identical** across page requests to use the server-side cache and keep the result stable.

---

### 3. `googleAds:mutate` — Cross-Resource Batch Mutate

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}/googleAds:mutate`

**When to use:** Creating or modifying multiple different resource types in a single atomic call (e.g., campaign + budget + ad group together). Uses **`mutateOperations`** key (plural). Used by `ads_batch_mutate()`.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mutateOperations` | array | Yes | Array of typed operation objects |
| `partialFailure` | bool | No | If true, successful ops commit even if others fail |
| `validateOnly` | bool | No | Validate without executing; useful for dry-run |
| `responseContentType` | string | No | `MUTABLE_RESOURCE` or `RESOURCE_NAME_ONLY` (default) |

Each element of `mutateOperations` is a **typed wrapper**: `{"{resourceType}Operation": {"create"|"update"|"remove": ...}}`.

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/googleAds:mutate
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "mutateOperations": [
    {
      "campaignBudgetOperation": {
        "create": {
          "name": "Tesla Parts Budget - QZ3 - 2026-06",
          "amountMicros": "35000000",
          "deliveryMethod": "STANDARD"
        }
      }
    },
    {
      "campaignOperation": {
        "update": {
          "resourceName": "customers/3552856345/campaigns/123456789",
          "campaignBudget": "customers/3552856345/campaignBudgets/-1"
        },
        "updateMask": "campaignBudget"
      }
    }
  ],
  "partialFailure": false
}
```

Note: Temporary resource names like `"-1"` can be used to reference resources created earlier in the same `mutateOperations` array.

#### Response

```json
{
  "mutateOperationResponses": [
    {
      "campaignBudgetResult": {
        "resourceName": "customers/3552856345/campaignBudgets/987654"
      }
    },
    {
      "campaignResult": {
        "resourceName": "customers/3552856345/campaigns/123456789"
      }
    }
  ]
}
```

**Operation type key names** (common ones):

| Resource | Operation key in mutateOperations |
|----------|----------------------------------|
| campaign | `campaignOperation` |
| campaign budget | `campaignBudgetOperation` |
| ad group | `adGroupOperation` |
| ad group ad | `adGroupAdOperation` |
| ad group criterion (keyword) | `adGroupCriterionOperation` |
| campaign criterion | `campaignCriterionOperation` |
| asset | `assetOperation` |
| campaign asset | `campaignAssetOperation` |
| conversion action | `conversionActionOperation` |

---

### 4. `{resource}:mutate` — Single-Resource Mutate

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}/{resource}:mutate`

**When to use:** Mutating a single resource type — simpler shape than cross-resource batch. Uses **`operations`** key (singular). Used by `ads_mutate()`.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operations` | array | Yes | Array of `create`/`update`/`remove` ops |
| `partialFailure` | bool | No | Allow partial success |
| `validateOnly` | bool | No | Dry-run validation |

**Example: Enable an ad group (update)**

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/adGroups:mutate
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "operations": [
    {
      "update": {
        "resourceName": "customers/3552856345/adGroups/111222333",
        "status": "ENABLED"
      },
      "updateMask": "status"
    }
  ],
  "partialFailure": false
}
```

**Example: Remove a keyword (negative)**

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/adGroupCriteria:mutate
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "operations": [
    {
      "remove": "customers/3552856345/adGroupCriteria/111222333~444555666"
    }
  ]
}
```

**Example: Create a campaign-level negative keyword**

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/campaignCriteria:mutate
Content-Type: application/json
...

{
  "operations": [
    {
      "create": {
        "campaign": "customers/3552856345/campaigns/123456789",
        "keyword": {
          "text": "repair",
          "matchType": "BROAD"
        },
        "negative": true
      }
    }
  ]
}
```

#### Response

```json
{
  "results": [
    {
      "resourceName": "customers/3552856345/adGroups/111222333"
    }
  ]
}
```

**Partial failure response** (when `partialFailure: true` and some ops fail):
```json
{
  "results": [
    { "resourceName": "customers/3552856345/adGroups/111222333" },
    {}
  ],
  "partialFailureError": {
    "code": 3,
    "message": "Multiple errors in response",
    "details": [
      {
        "@type": "type.googleapis.com/google.ads.googleads.v24.errors.GoogleAdsFailure",
        "errors": [
          {
            "errorCode": { "criterionError": "INVALID_KEYWORD_TEXT" },
            "message": "Keyword text is invalid.",
            "location": {
              "fieldPathElements": [
                { "fieldName": "operations", "index": 1 },
                { "fieldName": "create" }
              ]
            }
          }
        ]
      }
    ]
  }
}
```

---

### 5. `offlineUserDataJobs:create` — Create Customer Match Job

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}/offlineUserDataJobs:create`

**When to use:** Step 1 of Customer Match upload. Creates the job, returns a `resourceName` used for subsequent `addOperations` and `run` calls.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job.type` | string | Yes | `CUSTOMER_MATCH_USER_LIST` |
| `job.customerMatchUserListMetadata.userList` | string | Yes | Resource name of the target user list |
| `job.customerMatchUserListMetadata.consent.adUserData` | string | Yes (post-2024) | `GRANTED` or `DENIED` |
| `job.customerMatchUserListMetadata.consent.adPersonalization` | string | Yes (post-2024) | `GRANTED` or `DENIED` |

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/offlineUserDataJobs:create
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "job": {
    "type": "CUSTOMER_MATCH_USER_LIST",
    "customerMatchUserListMetadata": {
      "userList": "customers/3552856345/userLists/7654321",
      "consent": {
        "adUserData": "GRANTED",
        "adPersonalization": "GRANTED"
      }
    }
  }
}
```

#### Response

```json
{
  "resourceName": "customers/3552856345/offlineUserDataJobs/12345678"
}
```

Store this `resourceName` — it becomes the base path for steps 2 and 3.

---

### 6. `{job}:addOperations` — Upload Hashed PII

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/{job_resource_name}:addOperations`

Note: the full job resource name already contains `customers/{CID}/offlineUserDataJobs/{id}`, so the URL is:
```
https://googleads.googleapis.com/v24/customers/3552856345/offlineUserDataJobs/12345678:addOperations
```

**Batch in chunks of 100** (as used in `audience_upload_csv()`). Max documented limit is 100,000 per job total.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operations` | array | Yes | Array of `create` user data ops |
| `enableWarnings` | bool | No | Return warnings for skipped records |

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/offlineUserDataJobs/12345678:addOperations
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "operations": [
    {
      "create": {
        "userIdentifiers": [
          {
            "hashedEmail": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
          },
          {
            "hashedPhoneNumber": "8f14e45fceea167a5a36dedd4bea2543380e7a6a602c6b3ba61b56f6718c5d07"
          },
          {
            "addressInfo": {
              "hashedFirstName": "2c624232cdd221771294dfbb310acbc8f27fac24b34beaccb8c77e4752dba689",
              "hashedLastName": "19581e27de7ced00ff1ce50b2047e7a567c76b1cbaebabe5ef03f7c3017bb5b7",
              "countryCode": "AE"
            }
          }
        ]
      }
    }
  ],
  "enableWarnings": true
}
```

#### PII Hashing Rules (MANDATORY — violations cause silent drops or API errors)

| Identifier | Pre-processing | Hash |
|-----------|----------------|------|
| Email | `email.strip().lower()` | SHA-256 hex |
| Phone | Normalize to E.164 (`+971XXXXXXXXX`), then `.strip()` | SHA-256 hex |
| First name | `name.strip().lower()` | SHA-256 hex |
| Last name | `name.strip().lower()` | SHA-256 hex |
| Country code | ISO-3166 two-letter (e.g. `"AE"`) | **NOT hashed** |

**Phone E.164 normalization rules** (from `ads.py`):
- `00971...` → `+971...`
- `05XXXXXXXX` (10 digits) → `+9715XXXXXXXX`
- `5XXXXXXXX` (9 digits) → `+9715XXXXXXXX`
- `971...` (no plus) → `+971...`
- Must have at least 8 digits after stripping non-digits

**Name validation rules** (from `_is_valid_name()` in `ads.py`):
- Must be non-empty after strip
- Max 30 characters
- No special chars: `* ( ) , [ ] { } | / \`
- No digits
- Max 4 space-separated tokens (words)
- If either first or last name fails validation, `addressInfo` is omitted entirely

#### Response

```json
{}
```

Empty 200 response on success. Rate-limited responses return `429` — use exponential backoff.

---

### 7. `{job}:run` — Kick Off Processing

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/{job_resource_name}:run`

Triggers async processing of uploaded user data. Processing is fire-and-forget — poll the job status separately via GAQL on `offline_user_data_job` if needed.

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/offlineUserDataJobs/12345678:run
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{}
```

#### Response

```json
{
  "name": "customers/3552856345/operations/1234567890",
  "done": false
}
```

The returned `name` is a long-running operation resource name. To poll completion:
```gaql
SELECT offline_user_data_job.resource_name,
       offline_user_data_job.id,
       offline_user_data_job.status,
       offline_user_data_job.type,
       offline_user_data_job.failure_reason
FROM offline_user_data_job
WHERE offline_user_data_job.resource_name = 'customers/3552856345/offlineUserDataJobs/12345678'
```
Job `status` values: `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`.

---

### 8. `userLists:mutate` — Manage Customer Match Lists

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}/userLists:mutate`

**Create a CRM-based list:**

```http
POST https://googleads.googleapis.com/v24/customers/3552856345/userLists:mutate
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "operations": [
    {
      "create": {
        "name": "Talas CRM - All Customers 2026-Q2",
        "description": "All CRM contacts uploaded from Talas ERP",
        "membershipStatus": "OPEN",
        "membershipLifeSpan": 540,
        "crmBasedUserList": {
          "uploadKeyType": "CONTACT_INFO",
          "dataSourceType": "FIRST_PARTY"
        }
      }
    }
  ]
}
```

#### Response

```json
{
  "results": [
    {
      "resourceName": "customers/3552856345/userLists/7654321"
    }
  ]
}
```

**Find list by name** (GAQL via `run_gaql`):
```sql
SELECT user_list.resource_name, user_list.name, user_list.member_count
FROM user_list
WHERE user_list.name = 'Talas CRM - All Customers 2026-Q2'
```

---

### 9. `:generateKeywordIdeas` — Keyword Research

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}:generateKeywordIdeas`

**Access level required:** Standard (not available with Explorer or Basic tokens).

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keywordSeed.keywords` | string[] | One of the seeds required | Keywords describing your product/service |
| `urlSeed.url` | string | One of the seeds required | Landing page URL for content analysis |
| `keywordAndUrlSeed` | object | One of the seeds required | Combined keywords + URL |
| `siteSeed.site` | string | One of the seeds required | Domain, up to 250k keyword ideas |
| `languageId` | string | Yes | Language constant ID (e.g. `"1000"` = English) |
| `geoTargetConstants` | object[] | No | Array of `{"resourceName": "geoTargetConstants/{id}"}` |
| `keywordPlanNetwork` | string | No | `GOOGLE_SEARCH` or `GOOGLE_SEARCH_AND_PARTNERS` |
| `includeAdultKeywords` | bool | No | Default false |

**Common language IDs:** `1000` = English, `1019` = Arabic. **Common geo IDs:** `2784` = UAE, `2840` = USA, `2682` = Saudi Arabia.

**Keyword sanitization required** before sending (remove `! @ % , * '`).

```http
POST https://googleads.googleapis.com/v24/customers/3552856345:generateKeywordIdeas
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "keywordSeed": {
    "keywords": ["tesla parts", "tesla body parts", "model 3 bumper"]
  },
  "languageId": "1000",
  "geoTargetConstants": [
    {"resourceName": "geoTargetConstants/2784"}
  ],
  "keywordPlanNetwork": "GOOGLE_SEARCH"
}
```

#### Response

```json
{
  "results": [
    {
      "text": "tesla model 3 parts",
      "keywordIdeaMetrics": {
        "competition": "LOW",
        "avgMonthlySearches": "1000",
        "monthlySearchVolumes": [
          {"year": 2026, "month": "MAY", "monthlySearches": "880"},
          {"year": 2026, "month": "APRIL", "monthlySearches": "1100"}
        ],
        "competitionIndex": "12"
      }
    },
    {
      "text": "tesla parts uae",
      "keywordIdeaMetrics": {
        "competition": "MEDIUM",
        "avgMonthlySearches": "320",
        "competitionIndex": "45"
      }
    }
  ]
}
```

Source: https://developers.google.com/google-ads/api/docs/keyword-planning/generate-keyword-ideas (fetched 2026-06-23)

---

### 10. `:generateKeywordForecastMetrics` — Budget Forecasting

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}:generateKeywordForecastMetrics`

**Access level required:** Standard.

```http
POST https://googleads.googleapis.com/v24/customers/3552856345:generateKeywordForecastMetrics
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "campaignToForecast": {
    "keywordPlanKeywords": [
      {"keyword": "tesla parts"},
      {"keyword": "tesla body parts dubai"}
    ],
    "keywordPlanNetwork": "GOOGLE_SEARCH",
    "languageConstants": ["languageConstants/1000"],
    "geoTargetConstants": ["geoTargetConstants/2784"]
  }
}
```

#### Response

```json
{
  "campaignForecastMetrics": {
    "impressions": 4500.0,
    "clicks": 310.0,
    "averageCpc": {
      "amountMicros": "1850000",
      "currencyCode": "AED"
    },
    "costMicros": "573500000",
    "conversions": 8.4,
    "conversionRate": 0.027
  }
}
```

---

### 11. `:uploadClickConversions` — Offline Conversion Upload

**Method:** `POST`
**Full path:** `https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}:uploadClickConversions`

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conversions` | array | Yes | Array of `ClickConversion` objects |
| `conversions[].gclid` | string | Yes | Google Click ID from landing page URL |
| `conversions[].conversionAction` | string | Yes | Resource name: `customers/{CID}/conversionActions/{id}` |
| `conversions[].conversionDateTime` | string | Yes | `"YYYY-MM-DD HH:MM:SS+TZ"` format |
| `conversions[].conversionValue` | float | No | Conversion value in `currencyCode` currency |
| `conversions[].currencyCode` | string | No | ISO 4217, e.g. `"AED"` |
| `partialFailure` | bool | No | Allow partial success across conversions |

```http
POST https://googleads.googleapis.com/v24/customers/3552856345:uploadClickConversions
Authorization: Bearer ya29.A0AfH6SMBxxxxxxxx
developer-token: ABcDeFgHiJkLmNoPqRsTuV
login-customer-id: 6706955825
Content-Type: application/json

{
  "conversions": [
    {
      "gclid": "EAIaIQobChMI3pHX5r7N7AIVxxxxxx",
      "conversionAction": "customers/3552856345/conversionActions/987654321",
      "conversionDateTime": "2026-06-20 14:32:00+04:00",
      "conversionValue": 350.0,
      "currencyCode": "AED"
    }
  ],
  "partialFailure": true
}
```

#### Response (success)

```json
{
  "results": [
    {
      "gclid": "EAIaIQobChMI3pHX5r7N7AIVxxxxxx",
      "conversionAction": "customers/3552856345/conversionActions/987654321",
      "conversionDateTime": "2026-06-20 14:32:00+04:00"
    }
  ]
}
```

---

## GAQL Reference

### Syntax

```sql
SELECT field1, field2, ...
FROM resource_name
WHERE condition1 AND condition2
ORDER BY field ASC|DESC
LIMIT N
```

All clauses except `SELECT` and `FROM` are optional. No `JOIN` — implicit joins via attributed resources.

### Supported Resources (queryable FROM)

| Resource | Contains | Key fields |
|----------|---------|-----------|
| `campaign` | Campaign config + budget + bidding | `campaign.id`, `campaign.name`, `campaign.status`, `campaign.advertising_channel_type`, `campaign.target_cpa`, `campaign.target_roas` |
| `ad_group` | Ad group config | `ad_group.id`, `ad_group.name`, `ad_group.status`, `ad_group.campaign`, `ad_group.cpc_bid_micros` |
| `ad_group_ad` | Individual ads | `ad_group_ad.ad.id`, `ad_group_ad.ad.type`, `ad_group_ad.status`, `ad_group_ad.ad.responsive_search_ad` |
| `ad_group_criterion` | Keywords, audiences, criteria | `ad_group_criterion.keyword.text`, `ad_group_criterion.keyword.match_type`, `ad_group_criterion.status`, `ad_group_criterion.negative` |
| `keyword_view` | Keyword-level metrics | Use with `ad_group_criterion.*` fields for keyword text |
| `campaign_criterion` | Campaign-level criteria | `campaign_criterion.keyword.text`, `campaign_criterion.negative` |
| `user_list` | Audience lists | `user_list.name`, `user_list.resource_name`, `user_list.member_count`, `user_list.type` |
| `conversion_action` | Conversion action definitions | `conversion_action.name`, `conversion_action.type`, `conversion_action.status` |
| `offline_user_data_job` | Customer Match job status | `offline_user_data_job.status`, `offline_user_data_job.failure_reason` |
| `search_term_view` | Search terms that triggered ads | `search_term_view.search_term`, `search_term_view.status` |
| `geo_target_constant` | Geographic constants | `geo_target_constant.name`, `geo_target_constant.country_code` |

### Segment vs Resource Field Rules

Segments split metric rows by dimension. Key restrictions:

1. **Only one segmenting date field** — can use `segments.date`, `segments.week`, `segments.month`, or `segments.year` but not more than one time segment simultaneously.
2. **Segments and metrics must be compatible** — not all fields can appear together. Check `selectable_with` via `GoogleAdsFieldService` for unusual combos.
3. **Metrics require a reportable resource** — cannot select `metrics.*` from non-reportable resources like `geo_target_constant`.
4. **Attributed resources** — you can select fields from related resources (e.g. `campaign.name` in a query `FROM ad_group`) without explicit joins.

```sql
-- VALID: one date segment with metrics
SELECT campaign.name, segments.date, metrics.clicks, metrics.cost_micros
FROM campaign
WHERE segments.date DURING LAST_7_DAYS

-- INVALID: cannot mix segments.date and segments.week
-- SELECT campaign.name, segments.date, segments.week FROM campaign  ← ERROR

-- VALID: segment by device
SELECT campaign.name, segments.device, metrics.impressions
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
```

### Date Filtering

**Using date macros (DURING keyword):**
```sql
WHERE segments.date DURING LAST_7_DAYS
WHERE segments.date DURING LAST_30_DAYS
WHERE segments.date DURING THIS_MONTH
WHERE segments.date DURING LAST_MONTH
WHERE segments.date DURING YESTERDAY
```

**Available date macros:** `TODAY`, `YESTERDAY`, `LAST_7_DAYS`, `LAST_14_DAYS`, `LAST_30_DAYS`, `THIS_WEEK_SUN_TODAY`, `THIS_WEEK_MON_TODAY`, `LAST_WEEK_SUN_SAT`, `LAST_WEEK_MON_SUN`, `THIS_MONTH`, `LAST_MONTH`, `LAST_BUSINESS_WEEK`

**Using explicit date range (BETWEEN):**
```sql
WHERE segments.date BETWEEN '2026-06-01' AND '2026-06-22'
```

**Using exact date:**
```sql
WHERE segments.date = '2026-06-22'
```

**Never use TODAY for performance analysis** — 24-48h attribution lag means today's data is incomplete. Always use `YESTERDAY` or earlier.

### WHERE Operators

| Operator | Types | Example |
|----------|-------|---------|
| `=`, `!=` | string, enum, int, bool | `campaign.status = 'ENABLED'` |
| `>`, `>=`, `<`, `<=` | int, float | `metrics.clicks > 100` |
| `IN`, `NOT IN` | list | `campaign.status IN ('ENABLED', 'PAUSED')` |
| `CONTAINS ANY` | repeated field | (for multi-value fields) |
| `LIKE`, `NOT LIKE` | string | `campaign.name LIKE '%Tesla%'` |
| `REGEXP_MATCH` | string | `campaign.name REGEXP_MATCH '.*Tesla.*'` (RE2 syntax) |
| `IS NULL`, `IS NOT NULL` | any | `campaign.target_cpa IS NOT NULL` |
| `DURING` | date | `segments.date DURING LAST_30_DAYS` |
| `BETWEEN` | date, int | `segments.date BETWEEN '2026-01-01' AND '2026-06-01'` |

**Enum values** use unquoted uppercase strings in some contexts but quoted strings in others. When in doubt, use quoted: `campaign.status = 'ENABLED'`.

Source: https://developers.google.com/google-ads/api/docs/query/grammar (fetched 2026-06-23)

### Common GAQL Patterns

```sql
-- Campaign performance with cost in AED
SELECT campaign.name, campaign.status,
       metrics.clicks, metrics.impressions, metrics.cost_micros,
       metrics.conversions, metrics.cost_per_conversion
FROM campaign
WHERE segments.date DURING LAST_7_DAYS
  AND campaign.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC

-- Keywords with search volume
SELECT ad_group_criterion.keyword.text,
       ad_group_criterion.keyword.match_type,
       ad_group_criterion.status,
       metrics.impressions, metrics.clicks, metrics.ctr,
       metrics.average_cpc, metrics.cost_micros
FROM keyword_view
WHERE segments.date DURING LAST_30_DAYS
  AND ad_group_criterion.status != 'REMOVED'

-- Search terms (what users actually typed)
SELECT search_term_view.search_term,
       search_term_view.status,
       metrics.impressions, metrics.clicks, metrics.conversions
FROM search_term_view
WHERE segments.date DURING LAST_14_DAYS
ORDER BY metrics.impressions DESC
LIMIT 200

-- Ad performance
SELECT ad_group_ad.ad.id,
       ad_group_ad.ad.responsive_search_ad.headlines,
       ad_group_ad.status,
       metrics.clicks, metrics.impressions, metrics.ctr, metrics.conversions
FROM ad_group_ad
WHERE segments.date DURING LAST_30_DAYS
  AND ad_group_ad.status = 'ENABLED'

-- Audience (user list) inventory
SELECT user_list.resource_name, user_list.name,
       user_list.member_count, user_list.type,
       user_list.membership_status
FROM user_list

-- Conversion actions
SELECT conversion_action.name, conversion_action.status,
       conversion_action.type, conversion_action.id,
       conversion_action.counting_type
FROM conversion_action
WHERE conversion_action.status = 'ENABLED'
```


---

## Pagination & Quotas

### Pagination (`googleAds:search`)

- Page size: **fixed at 10,000 rows** since v19. `page_size` field removed — do not send.
- Use `nextPageToken` from response body → pass as `pageToken` in next request.
- Final page has no `nextPageToken` key (or it is an empty string).
- Query must be **byte-for-byte identical** across all page requests for server-side cache to hold.

### Rate Limits & Quotas

Specific numeric limits (operations/day, RPS) are not extractable from the docs (the quotas page returned HTTP 404). Confirmed behavior:

- Quotas are **per developer token**, not per customer account.
- Access level determines ceiling: Standard > Basic > Explorer > Test.
- Rate-limited responses: **HTTP 429**. gads-cli backoff: `delay = 10 * (attempt + 1)` sec, up to 5 retries.
- Batch efficiently: prefer ~500 operations per mutate request rather than individual calls.
- `addOperations` is most likely to hit 429 for large CSV uploads — retry with backoff.

Source: https://developers.google.com/google-ads/api/docs/best-practices/overview (fetched 2026-06-23)


---

## Error Reference

### HTTP Status Codes

| Status | Meaning | Common cause |
|--------|---------|-------------|
| 200 | Success | — |
| 400 | INVALID_ARGUMENT | Bad GAQL, wrong field name, invalid enum, missing required field |
| 401 | UNAUTHENTICATED | Expired or invalid OAuth token |
| 403 | PERMISSION_DENIED | Missing `login-customer-id` for MCC; wrong customer access; Basic token on Standard-only endpoint |
| 404 | NOT_FOUND | Wrong resource name, tilde vs slash in criterion path |
| 429 | RESOURCE_EXHAUSTED | Rate limit hit — backoff and retry |
| 500 | INTERNAL | Transient server error — retry with backoff |
| 503 | UNAVAILABLE | Service temporarily down — retry |

### Error Response Shape

All Google Ads API errors return the same envelope:

```json
{
  "error": {
    "code": 400,
    "message": "Human-readable summary",
    "status": "INVALID_ARGUMENT",
    "details": [
      {
        "@type": "type.googleapis.com/google.ads.googleads.v24.errors.GoogleAdsFailure",
        "errors": [
          {
            "errorCode": {
              "{errorDomain}Error": "{ERROR_ENUM_VALUE}"
            },
            "message": "Detailed error message",
            "location": {
              "fieldPathElements": [
                { "fieldName": "operations", "index": 0 },
                { "fieldName": "create" }
              ]
            }
          }
        ],
        "requestId": "abc123xyz"
      }
    ]
  }
}
```

### Common Error Codes

| `errorCode` key | Value | Cause |
|----------------|-------|-------|
| `queryError` | `UNRECOGNIZED_FIELD` | Field name typo in GAQL |
| `queryError` | `PROHIBITED_FIELD_COMBINATION` | Incompatible fields selected together |
| `queryError` | `INVALID_VALUE` | Bad enum or filter value |
| `criterionError` | `INVALID_KEYWORD_TEXT` | Keyword contains invalid chars or too long |
| `criterionError` | `KEYWORD_HAS_TOO_MANY_WORDS` | Google Ads keyword word limit exceeded |
| `authorizationError` | `DEVELOPER_TOKEN_NOT_APPROVED` | Token not approved for production |
| `authorizationError` | `USER_PERMISSION_DENIED` | Account access issue |
| `resourceCountLimitExceededException` | — | Too many operations in one mutate |
| `internalError` | `TRANSIENT_ERROR` | Retry-able server-side error |

### Extracting Error Details in Python

```python
resp = requests.post(url, headers=headers, json=payload)
if resp.status_code != 200:
    try:
        err = resp.json()["error"]
        for detail in err.get("details", []):
            for gads_err in detail.get("errors", []):
                print(gads_err["message"])
                print(gads_err.get("errorCode"))
                print(gads_err.get("location"))
    except Exception:
        pass
    raise SystemExit(1)
```


---

## Gotchas

1. **`mutateOperations` vs `operations` key** — cross-resource batch mutate uses `mutateOperations`; single-resource mutate uses `operations`. Mixing causes 400. See gads-cli CLAUDE.md.

2. **Tilde `~` in ad group criterion resource names** — format is `customers/{CID}/adGroupCriteria/{adGroupId}~{criterionId}`. Slash instead of tilde → 404.

3. **Fixed page size of 10,000** — `page_size` was removed in v19. Sending it causes errors or is silently ignored. Source: paging docs (fetched 2026-06-23).

4. **No same-day data** — 24-48h attribution lag. Never use `TODAY` for performance analysis. Use `YESTERDAY` or earlier.

5. **Customer Match consent fields required** — `consent.adUserData` and `consent.adPersonalization` must be `"GRANTED"`. Missing these causes upload failure. Required post-2024.

6. **OfflineUserDataJobService April 2026 note** — starting April 1, 2026, uploads may fail if the token has no prior successful Customer Match history. Pre-upload or migrate to Data Manager API.

7. **Keyword special characters** — `generateKeywordIdeas` and `generateKeywordForecastMetrics` reject `! @ % , * '`. Sanitize: `re.sub(r'[!@%,*\']', '', keyword)`.

8. **Asset creation is two-step** — create asset via `assets:mutate`, then link via `campaignAssets:mutate`. Cannot be combined in one call.

9. **sitelink finalUrls placement** — `finalUrls` at the top level of the create object, NOT nested inside `sitelinkAsset`. Nesting causes silent URL drops.

10. **Standard Access required for Keyword Planner / Forecast** — Explorer/Basic tokens → 403 PERMISSION_DENIED on these endpoints.

11. **`login-customer-id` header** — must be the MCC manager account ID. Without it when accessing a client account → PERMISSION_DENIED.

12. **`addressInfo` with empty names in Customer Match** — `{"addressInfo": {"countryCode": "AE"}}` with no hashed names is silently dropped. Validate both names are present and pass `_is_valid_name()` before including.

13. **GAQL segment compatibility** — not all field combinations are valid. Use `GoogleAdsFieldService` to check `selectable_with` constraints.

14. **`offlineUserDataJobs/{job}:addOperations` path** — uses the full resource name returned from `:create`, which already includes `customers/{CID}/`. Do not prepend the customer prefix again.

15. **Temporary resource names in batch mutate** — use `"-1"`, `"-2"`, etc. as resource names within the same `mutateOperations` array to reference just-created resources. Google resolves them in order.

16. **`updateMask` required for update ops** — when using `update` in any mutate operation, `updateMask` must list the fields being changed (comma-separated, camelCase). Omitting it may result in no change or 400.

17. **cost_micros arithmetic** — all cost values from the API are in micros (1/1,000,000 of the currency unit). `185340000 micros = 185.34 AED`. Always divide by `1_000_000`.

18. **camelCase in responses, snake_case in GAQL** — GAQL uses `metrics.cost_micros` but the JSON response uses `"costMicros"`. Field names transform on output.

Sources: gads-cli CLAUDE.md + `gads_lib/ads.py` + doc pages fetched 2026-06-23.


---

## Coverage vs Current gads-cli

### Endpoints Currently Used

| Endpoint | gads-cli function | CLI commands |
|---|---|---|
| `googleAds:searchStream` | `run_gaql()` | `query`, `campaign list/status/perf`, `adgroup`, `ad`, `keyword list/search-terms`, `report`, `audience list`, `conversion list/perf` |
| `googleAds:search` | `ads_search()` | Paginated queries |
| `googleAds:mutate` (batch) | `ads_batch_mutate()` | `batch-mutate`, two-step asset flows |
| `{resource}:mutate` | `ads_mutate()` | `campaign budget`, `keyword add/remove/negative`, `ad`, `asset`, `conversion create`, `audience create` |
| `offlineUserDataJobs:create` | `audience_upload_csv()` | `audience upload` |
| `{job}:addOperations` | `audience_upload_csv()` | `audience upload` |
| `{job}:run` | `audience_upload_csv()` | `audience upload` |
| `userLists:mutate` | `audience_create_list()` | `audience create` |
| `:generateKeywordIdeas` | `generate_keyword_ideas()` | `keyword ideas` |
| `:generateKeywordForecastMetrics` | `generate_keyword_forecast()` | `keyword forecast` |
| `:uploadClickConversions` | `ads_upload_click_conversions()` | `conversion upload` |

### Gaps / Not Yet Implemented

| Endpoint / Service | Purpose | Notes |
|---|---|---|
| `:uploadCallConversions` | Upload offline call conversions | Parallel to `:uploadClickConversions`; uses same pattern |
| `ConversionAdjustmentUploadService` | Restate/retract uploaded conversions | Correcting post-attribution conversion values |
| `offlineUserDataJobs` status poll | Check job completion | Currently fire-and-forget; poll via GAQL on `offline_user_data_job` |
| `BiddingStrategyService` | Portfolio bid strategies | Only inline campaign-level tCPA/tROAS handled |
| Shared budget management | `campaignBudgets:mutate` (shared) | Budget mutate works but no shared-budget workflow |
| `adSchedules:mutate` | Ad schedule criteria | Removal done via snapshot replay; no dedicated CLI command |
| `AssetGroupService` | PMax asset group management | No PMax asset group create/update commands |
| `AssetGroupListingGroupFilterService` | PMax product partitions | Not implemented |
| `AudienceService` | Audience definition (not user lists) | Different from `userLists`; segments management |
| `GoogleAdsFieldService` | Field metadata / `selectable_with` checks | Useful for GAQL field compatibility debugging |
| `LocalServicesLeadService` | Local Services Ads lead management | Not applicable to current account type |
| `SmartCampaignService` | Smart campaign management | Not implemented |


---

## Sources

All URLs fetched on 2026-06-23:

1. https://developers.google.com/google-ads/api/docs/get-started/introduction — API overview, v24.2 announced
2. https://developers.google.com/google-ads/api/docs/release-notes — Version timeline (v21–v24.1), release dates
3. https://developers.google.com/google-ads/api/rest/reference/rest — REST reference structure (v22, v23, v24 shown)
4. https://developers.google.com/google-ads/api/docs/query/grammar — GAQL grammar, operators, date macros
5. https://developers.google.com/google-ads/api/docs/reporting/paging — Pagination, 10,000-row fixed page size (v19+)
6. https://developers.google.com/google-ads/api/docs/keyword-planning/generate-keyword-ideas — KeywordPlanIdeaService, request shape, response fields
7. https://developers.google.com/google-ads/api/docs/best-practices/overview — Batch operations, error handling, development best practices
8. https://developers.google.com/google-ads/api/docs/get-started/dev-token — Developer token, access levels, `developer-token` header
9. https://developers.google.com/google-ads/api/docs/account-management/get-account-hierarchy — login-customer-id header, manager vs client account access
10. https://developers.google.com/google-ads/api/docs/sunset-dates — Sunset dates page exists; table content not extracted
11. https://developers.google.com/google-ads/api/docs/concepts/quotas — HTTP 404 at this URL
12. https://developers.google.com/google-ads/api/docs/query/overview — GAQL overview, resource types
13. `/home/talas9/talas-ads/gads-cli/gads_lib/ads.py` — Primary source for all endpoint paths, request shapes, response handling, PII hashing
14. `/home/talas9/talas-ads/gads-cli/gads_lib/config.py` — API_VERSION default (`v24`), env var names
15. `/home/talas9/talas-ads/gads-cli/CLAUDE.md` — Command taxonomy, auth requirements per service, known gotchas
