# Google Merchant API

## Status & Versions

| Version | Status | Notes |
|---------|--------|-------|
| v1 | **GA (stable)** | Current production version. Use this. |
| v1beta | **Discontinued** | Shut down February 28, 2026. Do not use. |
| v1alpha | Experimental | Unstable surface; not for production. |

The Merchant API is a redesign of the legacy Content API for Shopping.

- **Content API for Shopping (v2.1) sunset date: August 18, 2026**
  (Source: https://developers.google.com/shopping-content/guides/quickstart — "Content API for Shopping will be sunset on August 18, 2026")
- **v1beta discontinued: February 28, 2026**
  (Source: https://developers.google.com/merchant/api/overview — "Merchant API v1beta was discontinued and shut down on February 28, 2026")

Sources:
- https://developers.google.com/merchant/api/overview
- https://developers.google.com/merchant/api/reference/rest
- https://developers.google.com/shopping-content/guides/quickstart


## Base URL(s)

The Merchant API uses **per-sub-API versioned hosts** — each sub-API has its own path prefix and version segment:

```
https://merchantapi.googleapis.com/{sub-api}/{version}/{resource-path}
```

| Sub-API | Base URL | Notes |
|---------|----------|-------|
| Accounts | `https://merchantapi.googleapis.com/accounts/v1` | Account mgmt, shipping, return policies, issues |
| Products | `https://merchantapi.googleapis.com/products/v1` | Product inputs + processed products |
| Data Sources | `https://merchantapi.googleapis.com/datasources/v1` | Feed / data source management |
| Inventories | `https://merchantapi.googleapis.com/inventories/v1` | Local + regional inventory |
| Reports | `https://merchantapi.googleapis.com/reports/v1` | SQL-like reporting |
| Promotions | `https://merchantapi.googleapis.com/promotions/v1` | Promotions management |
| Conversions | `https://merchantapi.googleapis.com/conversions/v1` | Conversion sources |
| Notifications | `https://merchantapi.googleapis.com/notifications/v1` | Event subscriptions |
| Order Tracking | `https://merchantapi.googleapis.com/ordertracking/v1` | Order fulfillment signals |
| Issue Resolution | `https://merchantapi.googleapis.com/issueresolution/v1` | Product issue resolution |
| LFP | `https://merchantapi.googleapis.com/lfp/v1` | Local Feeds Partnership |
| Quota | `https://merchantapi.googleapis.com/quota/v1` | API usage monitoring |

Source: https://merchantapi.googleapis.com/$discovery/rest?version=accounts_v1 (and equivalent per sub-API)


## Auth / OAuth Scopes

**Required scope:** `https://www.googleapis.com/auth/content`

Description: "Manage your product listings and accounts for Google Shopping"

This is the **same scope** used by the legacy Content API v2.1. No scope change is needed when migrating.

In the gads CLI the bearer token is obtained via `get_bearer_headers(creds)` in `gads_lib/http.py` — the same credential object used for all other Google services.

Source: discovery documents at `https://merchantapi.googleapis.com/$discovery/rest?version=accounts_v1`, `products_v1`, `datasources_v1`, `inventories_v1`, `reports_v1`


## Sub-APIs Overview

| Sub-API | Host Version | v1 GA? | v1alpha? | Purpose |
|---------|--------------|--------|----------|---------|
| Accounts | accounts/v1 | Yes | Yes | Account config, users, shipping, return policies, regions, issues |
| Products | products/v1 | Yes | No | Product inputs (write) + processed products (read) |
| Data Sources | datasources/v1 | Yes | No | Feed management (primary, supplemental, local, regional, promotion, review) |
| Inventories | inventories/v1 | Yes | No | Local + regional per-product inventory |
| Reports | reports/v1 | Yes | Yes | SQL-like performance + product reporting |
| Promotions | promotions/v1 | Yes | No | Promotions |
| Conversions | conversions/v1 | Yes | No | Conversion sources |
| Notifications | notifications/v1 | Yes | No | Event notifications |
| Order Tracking | ordertracking/v1 | Yes | No | Order signals |
| Issue Resolution | issueresolution/v1 | Yes | No | Account/product issue resolution |
| LFP | lfp/v1 | Yes | No | Local Feeds Partnership |
| Quota | quota/v1 | Yes | No | Quota monitoring |
| Reviews | reviews/v1beta | No (beta) | Yes | Merchant + product reviews |
| Loyalty Customers | — | No | Yes (alpha) | Loyalty program customers |
| Product Studio | — | No | Yes (alpha) | AI image/text generation |
| YouTube Shopping | — | No | beta/alpha | YouTube commerce |

Source: https://developers.google.com/merchant/api/reference/rest


## Resources & Endpoints

### Accounts Sub-API (`accounts/v1`)

| Resource | Method | HTTP | Path | Purpose |
|----------|--------|------|------|---------|
| accounts | get | GET | `accounts/v1/accounts/{account}` | Get single account details |
| accounts | list | GET | `accounts/v1/accounts` | List accessible accounts |
| accounts | create | POST | `accounts/v1/accounts` | Create new merchant account |
| accounts | patch | PATCH | `accounts/v1/accounts/{account}` | Update account settings |
| accounts | delete | DELETE | `accounts/v1/accounts/{account}` | Delete account |
| accounts.issues | list | GET | `accounts/v1/accounts/{account}/issues` | List account-level policy issues |
| accounts.shippingSettings | get | GET | `accounts/v1/accounts/{account}/shippingSettings` | Get shipping configuration |
| accounts.shippingSettings | insert | POST | `accounts/v1/accounts/{account}/shippingSettings` | Replace full shipping config |
| accounts.onlineReturnPolicies | get | GET | `accounts/v1/accounts/{account}/onlineReturnPolicies/{policy}` | Get specific return policy |
| accounts.onlineReturnPolicies | list | GET | `accounts/v1/accounts/{account}/onlineReturnPolicies` | List all return policies |
| accounts.onlineReturnPolicies | create | POST | `accounts/v1/accounts/{account}/onlineReturnPolicies` | Create return policy |
| accounts.onlineReturnPolicies | patch | PATCH | `accounts/v1/accounts/{account}/onlineReturnPolicies/{policy}` | Update return policy |
| accounts.onlineReturnPolicies | delete | DELETE | `accounts/v1/accounts/{account}/onlineReturnPolicies/{policy}` | Delete return policy |
| accounts.users | list | GET | `accounts/v1/accounts/{account}/users` | List account users |
| accounts.users | get | GET | `accounts/v1/accounts/{account}/users/{email}` | Get user |
| accounts.users | create | POST | `accounts/v1/accounts/{account}/users` | Add user |
| accounts.users | patch | PATCH | `accounts/v1/accounts/{account}/users/{email}` | Update user access |
| accounts.users | delete | DELETE | `accounts/v1/accounts/{account}/users/{email}` | Remove user |
| accounts.regions | list | GET | `accounts/v1/accounts/{account}/regions` | List shipping regions |
| accounts.regions | get | GET | `accounts/v1/accounts/{account}/regions/{region}` | Get region |
| accounts.regions | create | POST | `accounts/v1/accounts/{account}/regions` | Create region |
| accounts.regions | patch | PATCH | `accounts/v1/accounts/{account}/regions/{region}` | Update region |
| accounts.regions | delete | DELETE | `accounts/v1/accounts/{account}/regions/{region}` | Delete region |
| accounts.homepage | get | GET | `accounts/v1/accounts/{account}/homepage` | Get homepage (store URL) |
| accounts.homepage | claim | POST | `accounts/v1/accounts/{account}/homepage:claim` | Claim homepage ownership |
| accounts.homepage | unclaim | POST | `accounts/v1/accounts/{account}/homepage:unclaim` | Release homepage claim |

Source: discovery doc `https://merchantapi.googleapis.com/$discovery/rest?version=accounts_v1`

### Products Sub-API (`products/v1`)

| Resource | Method | HTTP | Path | Purpose |
|----------|--------|------|------|---------|
| accounts.products | list | GET | `products/v1/accounts/{account}/products` | List processed products (read-only) |
| accounts.products | get | GET | `products/v1/accounts/{account}/products/{product}` | Get single processed product |
| accounts.productInputs | insert | POST | `products/v1/accounts/{account}/productInputs:insert` | Upload/replace a product |
| accounts.productInputs | patch | PATCH | `products/v1/accounts/{account}/productInputs/{product}` | Partial update a product |
| accounts.productInputs | delete | DELETE | `products/v1/accounts/{account}/productInputs/{product}` | Delete a product input |

**Notes on Products vs ProductInputs:**
- `productInputs` = what you write (raw submitted data, per data source)
- `products` = what you read (processed/merged result; read-only)
- `insert` on `productInputs` requires `?dataSource=accounts/{account}/dataSources/{datasource}` query param
- `patch` requires `?dataSource=...` and `?updateMask=field1,field2` query params

Source: discovery doc `https://merchantapi.googleapis.com/$discovery/rest?version=products_v1`

### Data Sources Sub-API (`datasources/v1`)

| Resource | Method | HTTP | Path | Purpose |
|----------|--------|------|------|---------|
| accounts.dataSources | list | GET | `datasources/v1/accounts/{account}/dataSources` | List all data sources |
| accounts.dataSources | get | GET | `datasources/v1/accounts/{account}/dataSources/{dataSource}` | Get single data source |
| accounts.dataSources | create | POST | `datasources/v1/accounts/{account}/dataSources` | Create new data source |
| accounts.dataSources | patch | PATCH | `datasources/v1/accounts/{account}/dataSources/{dataSource}` | Update data source config |
| accounts.dataSources | delete | DELETE | `datasources/v1/accounts/{account}/dataSources/{dataSource}` | Delete data source |
| accounts.dataSources | fetch | POST | `datasources/v1/accounts/{account}/dataSources/{dataSource}:fetch` | Trigger immediate file fetch |
| accounts.dataSources.fileUploads | get | GET | `datasources/v1/accounts/{account}/dataSources/{dataSource}/fileUploads/latest` | Get latest file upload status |

Source: discovery doc `https://merchantapi.googleapis.com/$discovery/rest?version=datasources_v1`

### Inventories Sub-API (`inventories/v1`)

| Resource | Method | HTTP | Path | Purpose |
|----------|--------|------|------|---------|
| accounts.products.localInventories | list | GET | `inventories/v1/accounts/{account}/products/{product}/localInventories` | List local inventory for product |
| accounts.products.localInventories | insert | POST | `inventories/v1/accounts/{account}/products/{product}/localInventories:insert` | Set local inventory at a store |
| accounts.products.localInventories | delete | DELETE | `inventories/v1/accounts/{account}/products/{product}/localInventories/{storeCode}` | Remove local inventory |
| accounts.products.regionalInventories | list | GET | `inventories/v1/accounts/{account}/products/{product}/regionalInventories` | List regional inventory |
| accounts.products.regionalInventories | insert | POST | `inventories/v1/accounts/{account}/products/{product}/regionalInventories:insert` | Set regional inventory |
| accounts.products.regionalInventories | delete | DELETE | `inventories/v1/accounts/{account}/products/{product}/regionalInventories/{region}` | Remove regional inventory |

Source: discovery doc `https://merchantapi.googleapis.com/$discovery/rest?version=inventories_v1`

### Reports Sub-API (`reports/v1`)

| Resource | Method | HTTP | Path | Purpose |
|----------|--------|------|------|---------|
| accounts.reports | search | POST | `reports/v1/accounts/{account}/reports:search` | Run SQL-like report query |

**Available report tables:**

| Table | Description |
|-------|-------------|
| `product_view` | Current inventory products with status and issues |
| `product_performance_view` | Clicks, impressions, conversions |
| `price_competitiveness_product_view` | Price benchmarking vs. competitors |
| `price_insights_product_view` | AI-driven price suggestions |
| `competitive_visibility_top_merchant_view` | Top-ranking competitor domains |
| `competitive_visibility_benchmark_view` | Category-level benchmarks |
| `competitive_visibility_competitor_view` | Similar businesses analysis |
| `best_sellers_brand_view` | Popular brands by category/country |
| `best_sellers_product_cluster_view` | Popular product groupings |
| `non_product_performance_view` | Image and link performance metrics |

Source: discovery doc `https://merchantapi.googleapis.com/$discovery/rest?version=reports_v1`


---

## Concrete Request/Response Examples

This section documents every endpoint used by gads-cli (plus priority gap endpoints) with exact HTTP details, typed parameters, and realistic example payloads. Use these as the implementation reference when building new subcommands.

### Conventions

- `{merchantId}` — numeric string, e.g. `"355285634"`. In path it appears as the bare number, not as a resource name prefix.
- `{account}` — the full resource name form used in some discovery docs: `accounts/{merchantId}`.
- The gads CLI uses the numeric form directly: `MA_ACCOUNTS + "/accounts/" + MERCHANT_CENTER_ID`.
- All request headers must include `Authorization: Bearer {token}`. Write operations also need `Content-Type: application/json`.
- `pageSize` defaults vary by endpoint; always supply it explicitly to avoid surprises.

---

### GET /accounts/v1/accounts/{merchantId}

**Purpose:** Fetch basic account info — name, timezone, language, test flag.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | e.g. `"355285634"` |

**Example request:**

```http
GET https://merchantapi.googleapis.com/accounts/v1/accounts/355285634
Authorization: Bearer ya29.a0AfB_byC...
```

**Example response (200 OK):**

```json
{
  "name": "accounts/355285634",
  "accountId": "355285634",
  "accountName": "Talas Auto Parts",
  "testAccount": false,
  "timeZone": {
    "id": "Asia/Dubai",
    "version": "2024b"
  },
  "languageCode": "en",
  "adultContent": false
}
```

**Error cases:**

```json
// 403 — wrong scope or token expired
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
          "service": "merchantapi.googleapis.com",
          "method": "google.shopping.merchant.accounts.v1.AccountsService.GetAccount"
        }
      }
    ]
  }
}

// 404 — account not found or no access
{
  "error": {
    "code": 404,
    "message": "Account '999999999' not found or caller does not have access.",
    "status": "NOT_FOUND"
  }
}
```

---

### GET /accounts/v1/accounts/{merchantId}/issues

**Purpose:** List account-level policy issues (disapprovals, warnings, suggestions). Used by `mc_get_account_status()` in gads-cli.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | |
| `pageSize` | query | int | no | Recommended: 50. Max unspecified; use 50 for safety. |
| `pageToken` | query | string | no | Pagination cursor from previous response |
| `languageCode` | query | string | no | BCP-47; localises `title` and `detail` fields |

**Example request:**

```http
GET https://merchantapi.googleapis.com/accounts/v1/accounts/355285634/issues?pageSize=50
Authorization: Bearer ya29.a0AfB_byC...
```

**Example response (200 OK — one CRITICAL issue):**

```json
{
  "accountIssues": [
    {
      "name": "accounts/355285634/issues/missing_return_policy",
      "title": "Missing return policy",
      "severity": "CRITICAL",
      "impactedDestinations": [
        {
          "impacts": [
            {
              "regionCode": "AE",
              "severity": "CRITICAL",
              "impactedRanking": [
                {
                  "type": "SHOPPING_ADS",
                  "region": "AE",
                  "rank": "SEVERELY_IMPACTED"
                }
              ]
            }
          ],
          "destination": "Shopping ads"
        }
      ],
      "detail": "Your account is missing a return policy for the United Arab Emirates. Ads for products in AE may be disapproved.",
      "documentationUri": "https://support.google.com/merchants/answer/7538732"
    },
    {
      "name": "accounts/355285634/issues/phone_verification_required",
      "title": "Phone number verification required",
      "severity": "ERROR",
      "impactedDestinations": [],
      "detail": "Verify your business phone number to improve trust signals.",
      "documentationUri": "https://support.google.com/merchants/answer/176793"
    }
  ],
  "nextPageToken": "CjQKMgoubWlzc2luZ19yZXR1cm5fcG9saWN5EiJhY2NvdW50cy8zNTUyODU2MzQ..."
}
```

**Severity enum values:** `CRITICAL`, `ERROR`, `SUGGESTION`

**Notes:**
- `nextPageToken` absent means last page.
- `impactedDestinations[].impacts[].rank` values: `SEVERELY_IMPACTED`, `DEMOTED`, `UNKNOWN`.
- When `accountIssues` is an empty array, the account is issue-free.

---

### GET /products/v1/accounts/{merchantId}/products

**Purpose:** List processed (read-only) products with their attributes and status. Used by both `mc_list_products()` and `mc_list_product_statuses()` in gads-cli.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | |
| `pageSize` | query | int | no | Default 25, max 1000 |
| `pageToken` | query | string | no | Pagination cursor |

**Example request:**

```http
GET https://merchantapi.googleapis.com/products/v1/accounts/355285634/products?pageSize=50
Authorization: Bearer ya29.a0AfB_byC...
```

**Example response (200 OK — one product fully expanded):**

```json
{
  "products": [
    {
      "name": "accounts/355285634/products/ZW4tQUUtVGVzbGFNb2RlbDNSZWFyQnVtcGVy",
      "offerId": "TeslaModel3RearBumper",
      "contentLanguage": "en",
      "feedLabel": "AE",
      "dataSource": "accounts/355285634/dataSources/7823401256",
      "versionNumber": "1714567890123",
      "archived": false,
      "productAttributes": {
        "title": "Tesla Model 3 Rear Bumper Cover — Used OEM",
        "description": "Original Tesla Model 3 rear bumper cover in good condition, minor scuffs. Fits 2017-2022 Model 3. No installation included — parts only.",
        "link": "https://shop.talas.ae/products/tesla-model3-rear-bumper?branch=QZ3",
        "imageLink": "https://cdn.talas.ae/images/tesla-m3-rear-bumper-001.jpg",
        "additionalImageLinks": [
          "https://cdn.talas.ae/images/tesla-m3-rear-bumper-002.jpg",
          "https://cdn.talas.ae/images/tesla-m3-rear-bumper-003.jpg"
        ],
        "brand": "Tesla",
        "condition": "used",
        "availability": "in_stock",
        "price": {
          "amountMicros": "450000000",
          "currencyCode": "AED"
        },
        "googleProductCategory": "5613",
        "productTypes": [
          "Auto Parts > Body Parts > Bumpers",
          "Tesla Parts > Model 3"
        ],
        "gtins": [],
        "mpn": "1084665-00-E",
        "itemGroupId": "tesla-model3-bumpers",
        "shipping": [
          {
            "country": "AE",
            "service": "Standard",
            "price": {
              "amountMicros": "0",
              "currencyCode": "AED"
            }
          }
        ]
      },
      "productStatus": {
        "destinationStatuses": [
          {
            "destination": "Shopping ads",
            "approvedCountries": ["AE"],
            "pendingCountries": [],
            "disapprovedCountries": []
          },
          {
            "destination": "Buy on Google listings",
            "approvedCountries": [],
            "pendingCountries": [],
            "disapprovedCountries": ["AE"]
          }
        ],
        "itemLevelIssues": [
          {
            "code": "missing_gtin",
            "severity": "SUGGESTION",
            "resolution": "merchant_action",
            "attribute": "gtin",
            "destination": "Shopping ads",
            "description": "Missing value [gtin]",
            "detail": "Add a GTIN to improve your product's performance in shopping ads.",
            "documentation": "https://support.google.com/merchants/answer/160161"
          }
        ]
      }
    }
  ],
  "nextPageToken": "CiQKIgogYWNjb3VudHMvMzU1Mjg1NjM0L3Byb2R1Y3RzL2VuLUFFL..."
}
```

**Product ID encoding note:**
The `{product}` path segment in `products/{product}` is the unpadded base64url of `contentLanguage~feedLabel~offerId`.
- `en~AE~TeslaModel3RearBumper` → `ZW4tQUUtVGVzbGFNb2RlbDNSZWFyQnVtcGVy`
- Python: `base64.urlsafe_b64encode(b"en~AE~TeslaModel3RearBumper").rstrip(b"=").decode()`

**`productStatus.itemLevelIssues[].severity` values:** `ERROR`, `SUGGESTION`
**`productStatus.itemLevelIssues[].resolution` values:** `merchant_action`, `pending_processing`

---

### GET /datasources/v1/accounts/{merchantId}/dataSources

**Purpose:** List all data sources (feeds) in the account. Used by `mc_list_datafeeds()` in gads-cli.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | |
| `pageSize` | query | int | no | Max 1000 |
| `pageToken` | query | string | no | Pagination cursor |

**Example request:**

```http
GET https://merchantapi.googleapis.com/datasources/v1/accounts/355285634/dataSources?pageSize=50
Authorization: Bearer ya29.a0AfB_byC...
```

**Example response (200 OK):**

```json
{
  "dataSources": [
    {
      "name": "accounts/355285634/dataSources/7823401256",
      "dataSourceId": "7823401256",
      "displayName": "Talas Shop — Primary Feed (AE)",
      "input": "FILE",
      "primaryProductDataSource": {
        "feedLabel": "AE",
        "contentLanguage": "en",
        "countries": ["AE"],
        "destinations": [
          {
            "destination": "Shopping ads",
            "state": "ENABLED"
          }
        ]
      },
      "fileInput": {
        "fileInputType": "FETCH",
        "fetchSettings": {
          "frequency": "DAILY",
          "fetchUri": "https://shop.talas.ae/feeds/google-shopping.xml",
          "enabled": true,
          "timeOfDay": {
            "hours": 2,
            "minutes": 0,
            "seconds": 0,
            "nanos": 0
          },
          "timeZone": "Asia/Dubai"
        }
      }
    },
    {
      "name": "accounts/355285634/dataSources/7823401999",
      "dataSourceId": "7823401999",
      "displayName": "API Direct Upload",
      "input": "API",
      "primaryProductDataSource": {
        "feedLabel": "AE",
        "contentLanguage": "en",
        "countries": ["AE"]
      }
    }
  ]
}
```

**`input` enum values:** `API`, `FILE`, `UI`, `AUTOFEED` (read-only — reflects how the data source receives data)

---

### GET /accounts/v1/accounts/{merchantId}/shippingSettings

**Purpose:** Fetch full shipping configuration. Used by `mc_get_shipping()` in gads-cli.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | |

**Example request:**

```http
GET https://merchantapi.googleapis.com/accounts/v1/accounts/355285634/shippingSettings
Authorization: Bearer ya29.a0AfB_byC...
```

**Example response (200 OK):**

```json
{
  "name": "accounts/355285634/shippingSettings",
  "services": [
    {
      "serviceName": "UAE Standard Delivery",
      "active": true,
      "deliveryCountries": ["AE"],
      "currencyCode": "AED",
      "deliveryTime": {
        "minHandlingDays": 0,
        "maxHandlingDays": 1,
        "minTransitDays": 2,
        "maxTransitDays": 5,
        "transitTimeTable": null
      },
      "rateGroups": [
        {
          "singleValue": {
            "flatRate": {
              "amountMicros": "0",
              "currencyCode": "AED"
            }
          },
          "name": "Free Shipping AE"
        }
      ],
      "shipmentType": "DELIVERY"
    }
  ],
  "warehouses": [
    {
      "name": "QZ3 Warehouse",
      "shippingAddress": {
        "streetAddress": "Al Quoz Industrial Area 3",
        "city": "Dubai",
        "administrativeArea": "DU",
        "postalCode": "00000",
        "regionCode": "AE"
      },
      "cutoffTime": {
        "hours": 14,
        "minutes": 0
      },
      "handlingDays": 1,
      "businessDaysConfig": {
        "businessDays": ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"]
      }
    }
  ],
  "etag": "\"AbCdEfGhIjKlMnOp12345\""
}
```

**Critical:** Store the `etag` when you GET. You must include it when calling `shippingSettings:insert` (POST) to prevent concurrent-write conflicts. If your etag is stale the API returns 409 Conflict.

---

### GET /accounts/v1/accounts/{merchantId}/onlineReturnPolicies

**Purpose:** List all online return policies. Used by `mc_get_return_policy()` in gads-cli.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | |
| `pageSize` | query | int | no | gads-cli uses 10 |

**Example request:**

```http
GET https://merchantapi.googleapis.com/accounts/v1/accounts/355285634/onlineReturnPolicies?pageSize=10
Authorization: Bearer ya29.a0AfB_byC...
```

**Example response (200 OK):**

```json
{
  "onlineReturnPolicies": [
    {
      "name": "accounts/355285634/onlineReturnPolicies/return_policy_AE_default",
      "returnPolicyId": "return_policy_AE_default",
      "label": "default",
      "countries": ["AE"],
      "policy": {
        "type": "NUMBER_OF_DAYS_AFTER_DELIVERY",
        "days": 14
      },
      "restockingFee": {
        "fixedFee": {
          "amountMicros": "0",
          "currencyCode": "AED"
        }
      },
      "returnMethods": ["BY_MAIL"],
      "itemConditions": ["NEW", "USED"],
      "returnShippingFee": {
        "type": "FREE",
        "fixedFee": null
      }
    }
  ]
}
```

**`policy.type` enum values:** `NUMBER_OF_DAYS_AFTER_DELIVERY`, `NO_RETURNS`, `LIFETIME_RETURNS`

---

## ProductInputs Write Path

These endpoints are **not yet implemented in gads-cli** but are documented here implementation-ready for future subcommands (e.g. `gads merchant product-insert`, `gads merchant product-patch`, `gads merchant product-delete`).

### POST /products/v1/accounts/{merchantId}/productInputs:insert

**Purpose:** Upload a new product or fully replace an existing one in a specific data source. Idempotent on `(contentLanguage, feedLabel, offerId, dataSource)` tuple.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | |
| `dataSource` | query | string | yes | Full resource name: `accounts/{merchantId}/dataSources/{dataSourceId}`. The data source must have `input=API`. |

**Request headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request body — ProductInput object:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | no | Ignored on insert; auto-assigned |
| `product` | string | no | Read-only; do not supply |
| `offerId` | string | yes | Your SKU; must be stable across updates |
| `contentLanguage` | string | yes | ISO 639-1, e.g. `"en"` |
| `feedLabel` | string | yes | Country/feed label ≤20 chars, e.g. `"AE"` |
| `productAttributes` | object | yes | See fields below |
| `customAttributes` | array | no | Key-value pairs for custom data |
| `versionNumber` | int64 | no | If set, insert is rejected if existing versionNumber is higher (freshness guard) |

**`productAttributes` key fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | yes | Max 150 chars |
| `description` | string | yes | Max 5000 chars |
| `link` | string | yes | Must include `?branch=` for Talas |
| `imageLink` | string | yes | HTTPS, min 100×100px |
| `brand` | string | recommended | |
| `condition` | string | yes | `"new"`, `"used"`, `"refurbished"` |
| `availability` | string | yes | `"in_stock"`, `"out_of_stock"`, `"preorder"` |
| `price` | object | yes | `{"amountMicros": int64, "currencyCode": "AED"}` |
| `googleProductCategory` | string | recommended | Numeric or string category |
| `gtins` | string[] | recommended | Improves matching; can be empty array |
| `mpn` | string | recommended | Manufacturer part number |

**Example request:**

```http
POST https://merchantapi.googleapis.com/products/v1/accounts/355285634/productInputs:insert?dataSource=accounts%2F355285634%2FdataSources%2F7823401999
Authorization: Bearer ya29.a0AfB_byC...
Content-Type: application/json

{
  "offerId": "TeslaModel3FrontBumper-Used-001",
  "contentLanguage": "en",
  "feedLabel": "AE",
  "productAttributes": {
    "title": "Tesla Model 3 Front Bumper Cover — Used OEM",
    "description": "Original Tesla Model 3 front bumper in good condition. Fits 2017-2022 models. Parts only — no installation.",
    "link": "https://shop.talas.ae/products/tesla-model3-front-bumper-001?branch=QZ3",
    "imageLink": "https://cdn.talas.ae/images/tesla-m3-front-bumper-001.jpg",
    "brand": "Tesla",
    "condition": "used",
    "availability": "in_stock",
    "price": {
      "amountMicros": "380000000",
      "currencyCode": "AED"
    },
    "googleProductCategory": "5613",
    "mpn": "1059186-00-E",
    "gtins": []
  }
}
```

**Example response (200 OK — returns the ProductInput as stored):**

```json
{
  "name": "accounts/355285634/productInputs/ZW4tQUUtVGVzbGFNb2RlbDNGcm9udEJ1bXBlci1Vc2VkLTAwMQ",
  "product": "accounts/355285634/products/ZW4tQUUtVGVzbGFNb2RlbDNGcm9udEJ1bXBlci1Vc2VkLTAwMQ",
  "offerId": "TeslaModel3FrontBumper-Used-001",
  "contentLanguage": "en",
  "feedLabel": "AE",
  "versionNumber": "1714599000000",
  "productAttributes": {
    "title": "Tesla Model 3 Front Bumper Cover — Used OEM",
    "description": "Original Tesla Model 3 front bumper in good condition. Fits 2017-2022 models. Parts only — no installation.",
    "link": "https://shop.talas.ae/products/tesla-model3-front-bumper-001?branch=QZ3",
    "imageLink": "https://cdn.talas.ae/images/tesla-m3-front-bumper-001.jpg",
    "brand": "Tesla",
    "condition": "used",
    "availability": "in_stock",
    "price": {
      "amountMicros": "380000000",
      "currencyCode": "AED"
    },
    "googleProductCategory": "5613",
    "mpn": "1059186-00-E",
    "gtins": []
  }
}
```

**Note:** The processed `products` resource will not reflect this insert for several minutes. Check via `GET /products/v1/.../products/{encodedId}`.

---

### PATCH /products/v1/accounts/{merchantId}/productInputs/{productInputId}

**Purpose:** Partial update — change only specific fields of an existing product input.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | |
| `productInputId` | path | string | yes | Encoded product input name (base64url of `contentLanguage~feedLabel~offerId`) |
| `dataSource` | query | string | yes | `accounts/{merchantId}/dataSources/{dataSourceId}` |
| `updateMask` | query | string | yes | Comma-separated field paths to update, e.g. `productAttributes.price,productAttributes.availability` |

**Example request — price update only:**

```http
PATCH https://merchantapi.googleapis.com/products/v1/accounts/355285634/productInputs/ZW4tQUUtVGVzbGFNb2RlbDNGcm9udEJ1bXBlci1Vc2VkLTAwMQ?dataSource=accounts%2F355285634%2FdataSources%2F7823401999&updateMask=productAttributes.price
Authorization: Bearer ya29.a0AfB_byC...
Content-Type: application/json

{
  "productAttributes": {
    "price": {
      "amountMicros": "350000000",
      "currencyCode": "AED"
    }
  }
}
```

**Example response (200 OK):** Returns the full updated ProductInput (same shape as insert response).

**Important:** `updateMask` must exactly match the fields in the body — unmasked fields in the body are silently ignored, and masked fields not in the body are set to null.

---

### DELETE /products/v1/accounts/{merchantId}/productInputs/{productInputId}

**Purpose:** Remove a product from the catalog.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | |
| `productInputId` | path | string | yes | Encoded product ID |
| `dataSource` | query | string | yes | `accounts/{merchantId}/dataSources/{dataSourceId}` |

**Example request:**

```http
DELETE https://merchantapi.googleapis.com/products/v1/accounts/355285634/productInputs/ZW4tQUUtVGVzbGFNb2RlbDNGcm9udEJ1bXBlci1Vc2VkLTAwMQ?dataSource=accounts%2F355285634%2FdataSources%2F7823401999
Authorization: Bearer ya29.a0AfB_byC...
```

**Example response (200 OK):**

```json
{}
```

(Empty object — standard Google API "Empty" response.)

**Note:** Deletion is not immediate. The product may remain visible in `GET /products` for several minutes.

---

## Reports Sub-API — Implementation Reference

### POST /reports/v1/accounts/{merchantId}/reports:search

**Purpose:** Execute a SQL-like query against Merchant Center data. This is the Merchant API equivalent of a GAQL query — one endpoint, many report types.

**Parameters:**

| Name | In | Type | Required | Notes |
|------|----|------|----------|-------|
| `merchantId` | path | string (numeric) | yes | |

**Request headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request body:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `query` | string | yes | SQL-like query — see syntax below |
| `pageSize` | int | no | Default 1000, max 100000 |
| `pageToken` | string | no | Pagination cursor |

**Query syntax:**

```sql
SELECT field1, field2, ...
FROM table_name
WHERE condition
ORDER BY field ASC|DESC
LIMIT n
```

Supported `WHERE` operators: `=`, `!=`, `<`, `>`, `<=`, `>=`, `IN`, `NOT IN`, `LIKE`, `IS NULL`, `IS NOT NULL`, `AND`, `OR`.

---

#### Example 1 — product_view: disapproved products

```http
POST https://merchantapi.googleapis.com/reports/v1/accounts/355285634/reports:search
Authorization: Bearer ya29.a0AfB_byC...
Content-Type: application/json

{
  "query": "SELECT id, title, brand, availability, price_micros, currency_code, feed_label, item_issues FROM product_view WHERE channel = 'ONLINE' AND item_issues IS NOT NULL LIMIT 100",
  "pageSize": 100
}
```

**Example response (200 OK):**

```json
{
  "results": [
    {
      "productView": {
        "id": "online:en:AE:TeslaModel3FrontBumper-Used-001",
        "title": "Tesla Model 3 Front Bumper Cover — Used OEM",
        "brand": "Tesla",
        "availability": "IN_STOCK",
        "priceMicros": "380000000",
        "currencyCode": "AED",
        "feedLabel": "AE",
        "itemIssues": [
          {
            "type": {
              "code": "missing_gtin",
              "canonicalAttribute": "gtin",
              "resolution": "MERCHANT_ACTION"
            },
            "severity": {
              "severityPerDestination": [
                {
                  "destination": "SHOPPING_ADS",
                  "demotionImpact": "DEMOTED",
                  "approvalStatus": "APPROVED_LIMITED"
                }
              ],
              "aggregatedSeverity": "DISAPPROVED"
            }
          }
        ]
      }
    }
  ],
  "nextPageToken": null
}
```

---

#### Example 2 — product_performance_view: clicks and impressions last 30 days

```http
POST https://merchantapi.googleapis.com/reports/v1/accounts/355285634/reports:search
Authorization: Bearer ya29.a0AfB_byC...
Content-Type: application/json

{
  "query": "SELECT offer_id, title, clicks, impressions, click_through_rate FROM product_performance_view WHERE date BETWEEN '2026-05-24' AND '2026-06-22' ORDER BY clicks DESC LIMIT 50",
  "pageSize": 50
}
```

**Example response (200 OK):**

```json
{
  "results": [
    {
      "productPerformanceView": {
        "offerId": "TeslaModel3RearBumper",
        "title": "Tesla Model 3 Rear Bumper Cover — Used OEM",
        "clicks": "42",
        "impressions": "1834",
        "clickThroughRate": 0.022900
      }
    },
    {
      "productPerformanceView": {
        "offerId": "TeslaModel3FrontBumper-Used-001",
        "title": "Tesla Model 3 Front Bumper Cover — Used OEM",
        "clicks": "18",
        "impressions": "921",
        "clickThroughRate": 0.019500
      }
    }
  ]
}
```

---

#### Example 3 — product_view: all products with aggregated approval status

```http
POST https://merchantapi.googleapis.com/reports/v1/accounts/355285634/reports:search
Authorization: Bearer ya29.a0AfB_byC...
Content-Type: application/json

{
  "query": "SELECT id, title, aggregated_destination_status, item_issues FROM product_view WHERE channel = 'ONLINE' ORDER BY aggregated_destination_status LIMIT 200",
  "pageSize": 200
}
```

**`aggregatedDestinationStatus` enum values:**
- `NOT_ELIGIBLE_OR_DISAPPROVED` — blocked from all surfaces
- `NOT_ELIGIBLE` — not eligible but no active disapproval
- `ELIGIBLE_LIMITED` — approved with restrictions (e.g. missing GTIN)
- `ELIGIBLE` — fully approved

---

## Key Request/Response Fields

### Account Object (`accounts/v1`)

```json
{
  "name": "accounts/{accountId}",
  "accountId": "string (numeric)",
  "accountName": "string (display name)",
  "testAccount": false,
  "timeZone": { "id": "string", "version": "string" },
  "languageCode": "string (BCP-47)",
  "adultContent": false
}
```

### AccountIssue Object (`accounts/{id}/issues`)

```json
{
  "name": "string (resource name)",
  "title": "string (human-readable)",
  "severity": "CRITICAL | ERROR | SUGGESTION",
  "impactedDestinations": ["array of destination strings"],
  "detail": "string",
  "documentationUri": "string (URL to help docs)"
}
```

### Product Object (read-only, from `products/v1/.../products`)

```json
{
  "name": "accounts/{account}/products/{product}",
  "offerId": "string (merchant-assigned SKU)",
  "contentLanguage": "string (ISO 639-1)",
  "feedLabel": "string (country/feed label, max 20 chars)",
  "dataSource": "string (resource name of primary data source)",
  "versionNumber": "int64 (freshness identifier, read-only)",
  "archived": "boolean",
  "productAttributes": {
    "title": "string",
    "description": "string",
    "link": "string (canonical URL)",
    "brand": "string",
    "condition": "string enum",
    "availability": "string enum",
    "gtins": ["string array"],
    "price": {
      "amountMicros": "int64 (price × 1,000,000)",
      "currencyCode": "string (ISO 4217)"
    },
    "imageLink": "string",
    "additionalImageLinks": ["string array"],
    "googleProductCategory": "string",
    "productTypes": ["string array"],
    "shipping": ["shipping overrides"],
    "mpn": "string",
    "itemGroupId": "string"
  },
  "productStatus": {
    "destinationStatuses": [
      {
        "destination": "string",
        "approvedCountries": ["string array"],
        "pendingCountries": ["string array"],
        "disapprovedCountries": ["string array"]
      }
    ],
    "itemLevelIssues": [
      {
        "code": "string",
        "severity": "string",
        "resolution": "string",
        "attribute": "string",
        "destination": "string",
        "description": "string",
        "detail": "string",
        "documentation": "string (URL)"
      }
    ]
  }
}
```

**Product ID encoding:** Product IDs use tilde-separated `contentLanguage~feedLabel~offerId`.
For offerId values with special characters (slashes, etc.), use unpadded base64url encoding.
Example: `en~US~sku/123` encodes to `ZW5-VVN-c2t1LzEyMw`.

### DataSource Object

```json
{
  "name": "accounts/{account}/dataSources/{dataSourceId}",
  "dataSourceId": "int64 (read-only)",
  "displayName": "string (required)",
  "input": "API | FILE | UI | AUTOFEED (read-only)",
  "primaryProductDataSource": {
    "feedLabel": "string (immutable, ≤20 chars)",
    "contentLanguage": "string (immutable, ISO 639-1)",
    "countries": ["CLDR territory codes"],
    "destinations": ["marketing method selections"],
    "defaultRule": {}
  },
  "supplementalProductDataSource": {},
  "localInventoryDataSource": {},
  "regionalInventoryDataSource": {},
  "promotionDataSource": {},
  "productReviewDataSource": {},
  "merchantReviewDataSource": {},
  "fileInput": {
    "fileInputType": "UPLOAD | FETCH | GOOGLE_SHEETS (read-only)",
    "fileName": "string (required for UPLOAD)",
    "fetchSettings": {
      "frequency": "DAILY | WEEKLY | MONTHLY",
      "fetchUri": "string",
      "enabled": "boolean",
      "timeOfDay": {},
      "dayOfWeek": "MONDAY..SUNDAY",
      "dayOfMonth": "int32 1-31",
      "timeZone": "string (CLDR, default UTC)",
      "username": "string",
      "password": "string"
    }
  }
}
```

### ShippingSettings Object

```json
{
  "name": "accounts/{account}/shippingSettings",
  "services": [
    {
      "serviceName": "string",
      "active": "boolean",
      "deliveryCountries": ["string array"],
      "currencyCode": "string (ISO 4217)",
      "deliveryTime": { "minTransitDays": "int", "maxTransitDays": "int" },
      "rateGroups": ["RateGroup objects"],
      "shipmentType": "string enum",
      "storeConfig": {}
    }
  ],
  "warehouses": [
    {
      "name": "string",
      "shippingAddress": {},
      "cutoffTime": {},
      "handlingDays": "int32",
      "businessDaysConfig": {}
    }
  ],
  "etag": "string (concurrency token)"
}
```

**Important:** `shippingSettings:insert` (POST) is a full-replace — NULL or missing fields will null out existing values. Always GET first and include the `etag`.

### OnlineReturnPolicy Object

```json
{
  "name": "accounts/{account}/onlineReturnPolicies/{returnPolicyId}",
  "returnPolicyId": "string",
  "label": "string",
  "countries": ["string array (country codes)"],
  "policy": {
    "type": "string enum",
    "days": "int32"
  }
}
```


## Pagination & Quotas

### Pagination

All list methods use cursor-based pagination with `pageToken`:

```
GET ...?pageSize=100&pageToken={nextPageToken}

Response:
{
  "items": [...],
  "nextPageToken": "string | absent when last page"
}
```

| Sub-API | Collection field | Default pageSize | Max pageSize |
|---------|-----------------|-----------------|-------------|
| Products (list) | `products` | 25 | 1000 |
| DataSources (list) | `dataSources` | unspecified | 1000 |
| Issues (list) | `accountIssues` | unspecified | 50 (recommended) |
| LocalInventories | `localInventories` | 25000 | 25000 |
| RegionalInventories | `regionalInventories` | 25000 | 100000 |
| Reports (search) | `results` | 1000 | 100000 |

When `nextPageToken` is absent from a response, you have reached the last page.

**Python pagination helper pattern:**

```python
def paginate(fetch_fn, collection_key, **kwargs):
    """Generic paginator. fetch_fn(page_token=None, **kwargs) -> dict."""
    items = []
    page_token = None
    while True:
        resp = fetch_fn(page_token=page_token, **kwargs)
        items.extend(resp.get(collection_key, []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items
```

### Quotas

The Merchant API has a **Quota sub-API** (`quota/v1`) for monitoring usage. Specific QPS/QPD limits are account-dependent. Use `GET quota/v1/accounts/{account}/quotas` to inspect current limits.

**429 quota exceeded response:**

```json
{
  "error": {
    "code": 429,
    "message": "Quota exceeded for quota metric 'merchantapi.googleapis.com/default' and limit 'DEFAULT-LIMIT' of service 'merchantapi.googleapis.com'.",
    "status": "RESOURCE_EXHAUSTED",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
        "violations": [
          {
            "subject": "merchantapiuser:355285634",
            "description": "Quota exceeded for quota metric 'merchantapi.googleapis.com/default'"
          }
        ]
      }
    ]
  }
}
```

**Retry strategy:** Exponential backoff starting at 1s. Merchant API is not high-QPS — typical scripts hit quota only if looping without pagination delay.

Source: https://developers.google.com/merchant/api/reference/rest


## Error Reference

### Common Error Shapes

All errors use the standard Google API error envelope:

```json
{
  "error": {
    "code": 403,
    "message": "string",
    "status": "PERMISSION_DENIED | NOT_FOUND | INVALID_ARGUMENT | RESOURCE_EXHAUSTED | ALREADY_EXISTS | FAILED_PRECONDITION | INTERNAL",
    "details": [...]
  }
}
```

| HTTP code | `status` string | Typical cause |
|-----------|----------------|---------------|
| 400 | `INVALID_ARGUMENT` | Bad field value, missing required field, wrong enum string |
| 401 | `UNAUTHENTICATED` | Token expired or missing |
| 403 | `PERMISSION_DENIED` | Wrong scope, wrong account, or no access |
| 404 | `NOT_FOUND` | Account ID wrong, resource doesn't exist |
| 409 | `ABORTED` | ETag conflict on shippingSettings insert |
| 429 | `RESOURCE_EXHAUSTED` | Quota exceeded |
| 500 | `INTERNAL` | Google-side error; retry with backoff |

### 400 INVALID_ARGUMENT — missing required query param

```json
{
  "error": {
    "code": 400,
    "message": "Request is missing required query parameter 'dataSource'.",
    "status": "INVALID_ARGUMENT"
  }
}
```

Trigger: calling `productInputs:insert` without `?dataSource=` query param.

### 403 PERMISSION_DENIED — insufficient scope

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
        "domain": "googleapis.com"
      }
    ]
  }
}
```

**Fix:** Ensure the OAuth token includes `https://www.googleapis.com/auth/content`. Re-run `python generate_token.py` if the stored token predates scope additions.

### 404 NOT_FOUND — account doesn't exist or no access

```json
{
  "error": {
    "code": 404,
    "message": "Account '999999999' not found or caller does not have access.",
    "status": "NOT_FOUND"
  }
}
```


## Migration Notes: Content API v2.1 → Merchant API

### Timeline

| Event | Date |
|-------|------|
| Merchant API v1beta discontinued | February 28, 2026 |
| Content API v2.1 sunset | **August 18, 2026** |

Source: https://developers.google.com/shopping-content/guides/quickstart, https://developers.google.com/merchant/api/overview

### Key Structural Changes

| Area | Content API v2.1 | Merchant API v1 |
|------|-----------------|-----------------|
| Base URL | `https://shoppingcontent.googleapis.com/content/v2.1/` | `https://merchantapi.googleapis.com/{sub-api}/v1/` |
| Merchant ID param | Path: `/{merchantId}/products` | Path: `accounts/{account}/products` |
| Account ID format | Numeric string in path | `accounts/{id}` resource name |
| OAuth scope | `https://www.googleapis.com/auth/content` | **Same scope — no change** |
| Product status | Separate `productstatuses` resource | Folded into `products` resource under `productStatus.*` |
| Data sources | `datafeeds` resource | `dataSources` sub-API at `datasources/v1/` |
| Write vs read products | Same resource | Split: `productInputs` (write) vs `products` (read) |
| Shipping settings | `shippingsettings` resource | `accounts/{id}/shippingSettings` under accounts sub-API |
| Return policies | `returnpolicy` resource | `accounts/{id}/onlineReturnPolicies` under accounts sub-API |

### Field Renames

| Content API field | Merchant API field |
|------------------|--------------------|
| `merchant_id` | `name` (resource name string) |
| `product.id` | `product.offerId` |
| `productStatus.productId` | (embedded in product `name`) |
| `datafeed.id` | `dataSource.dataSourceId` |
| `price.value` (string) | `price.amountMicros` (int64, ×1,000,000) |
| `price.currency` | `price.currencyCode` |

### Removed / No-Longer-Separate Endpoints

- `productstatuses.list` / `productstatuses.get` — status is now embedded in the `products` resource under `productStatus.*`
- `accounts.authinfo` — replaced by the accounts sub-API methods
- Batch-insert for products — must now insert one at a time via `productInputs:insert`, or use file data sources

### Authentication

No OAuth scope change. Still uses `https://www.googleapis.com/auth/content`.
Service account approach is the same.


## Gotchas

1. **v1beta is dead.** The gads CLI correctly uses `v1` paths (`/accounts/v1`, `/products/v1`, `/datasources/v1`). Any code referencing `v1beta` paths will 404 as of February 28, 2026.

2. **productInputs vs products confusion.** You cannot write to `products` (it's read-only processed output). All writes go to `productInputs:insert` or `productInputs:patch`. The CLI's `mc_list_product_statuses` correctly delegates to the `products` list endpoint since status is embedded there.

3. **shippingSettings:insert is destructive.** The `INSERT` (POST) method replaces the entire shipping config. Missing fields are nulled. Always GET → modify → INSERT with the etag. (Source: https://developers.google.com/merchant/api/guides/shipping-settings/overview)

4. **dataSource required for productInput writes.** Both `insert` and `patch` on `productInputs` require a `?dataSource=accounts/{account}/dataSources/{id}` query parameter. The data source must have `input=API` type.

5. **Price is in micros.** `price.amountMicros` is the price multiplied by 1,000,000. AED 99.00 = `99000000`.

6. **Product ID encoding.** For offer IDs containing `/`, `~`, or other special characters, the product resource name uses unpadded base64url of `contentLanguage~feedLabel~offerId`. The CLI must handle this when constructing GET paths for individual products.

7. **Processing lag.** Product inserts/patches/deletes take "several minutes" to reflect in the `products` read endpoint.

8. **API data source prerequisite.** Before using `productInputs:insert`, at least one data source with `input=API` must exist in the account.

9. **Issues list, not a single status object.** `accounts/{id}/issues` returns a paginated list of `AccountIssue` objects — not a single status field. The CLI fetches with `pageSize=50`.

10. **fileUploads only accepts `latest` alias.** To get the most recent upload status: `GET datasources/v1/.../fileUploads/latest`. There is no `list` method for file uploads.

11. **Reports date format.** In `reports:search` queries, dates must be quoted strings in `'YYYY-MM-DD'` format. The `BETWEEN` operator is inclusive on both ends. Do not use `TODAY` or relative keywords — use explicit dates computed in Python.

12. **updateMask is required for PATCH.** A `productInputs:patch` without `?updateMask=` will return 400. The mask must exactly list the dotted field paths to update.

13. **ETag on shippingSettings.** The `etag` field is a quoted string (includes the surrounding double-quotes in the value). Pass it verbatim in the `If-Match` header or in the body when calling insert: `"etag": "\"AbCdEfGhIjKlMnOp12345\""`.


## Coverage vs Current gads CLI

### Currently Used (gads_lib/merchant.py)

| Function | Endpoint | Status |
|----------|----------|--------|
| `mc_get_account` | `GET accounts/v1/accounts/{id}` | Correct v1 path |
| `mc_get_account_status` | `GET accounts/v1/accounts/{id}/issues` | Correct — issues list |
| `mc_list_products` | `GET products/v1/accounts/{id}/products` | Correct |
| `mc_list_product_statuses` | `GET products/v1/accounts/{id}/products` | Correct — delegates to products (status embedded) |
| `mc_list_datafeeds` | `GET datasources/v1/accounts/{id}/dataSources` | Correct v1 path |
| `mc_get_shipping` | `GET accounts/v1/accounts/{id}/shippingSettings` | Correct |
| `mc_get_return_policy` | `GET accounts/v1/accounts/{id}/onlineReturnPolicies` | Correct |

### Gaps — Available But Not Implemented

| Capability | Sub-API | Endpoint |
|------------|---------|----------|
| Write products | products/v1 | `productInputs:insert`, `productInputs:patch`, `productInputs:delete` |
| Get single product | products/v1 | `GET .../products/{product}` |
| Create/update data source | datasources/v1 | `POST .../dataSources`, `PATCH .../dataSources/{id}` |
| Trigger file fetch | datasources/v1 | `POST .../dataSources/{id}:fetch` |
| Check file upload status | datasources/v1 | `GET .../dataSources/{id}/fileUploads/latest` |
| Local inventory | inventories/v1 | `localInventories` insert/list/delete |
| Regional inventory | inventories/v1 | `regionalInventories` insert/list/delete |
| Performance reports | reports/v1 | `reports:search` (product_performance_view, etc.) |
| Product view report | reports/v1 | `reports:search` with `product_view` table |
| Promotions | promotions/v1 | Full promotions sub-API |
| Users management | accounts/v1 | `accounts/{id}/users` |
| Regions management | accounts/v1 | `accounts/{id}/regions` |
| Homepage claim | accounts/v1 | `homepage:claim`, `homepage:unclaim` |
| Business identity | accounts/v1 | Business identity attributes |
| Quota monitoring | quota/v1 | `quotas` list |

### Priority Gaps for Talas Use Case

1. **Reports** (`reports/v1`) — `product_view` for disapproved products, `product_performance_view` for clicks/impressions. High value for monitoring.
2. **Product writes** (`productInputs`) — needed to fix disapproved products programmatically.
3. **File upload status** — to monitor feed health after data source fetch.


## Sources

All claims in this document are sourced from the following URLs, fetched 2026-06-23:

| Source | URL |
|--------|-----|
| Merchant API overview (version, v1beta shutdown) | https://developers.google.com/merchant/api/overview |
| Merchant API reference index (sub-APIs, versions) | https://developers.google.com/merchant/api/reference/rest |
| Content API sunset date (Aug 18, 2026) | https://developers.google.com/shopping-content/guides/quickstart |
| Accounts sub-API: shipping settings guide | https://developers.google.com/merchant/api/guides/shipping-settings/overview |
| Accounts sub-API: accounts overview | https://developers.google.com/merchant/api/guides/accounts/overview |
| Products sub-API: overview | https://developers.google.com/merchant/api/guides/products/overview |
| Data sources sub-API: overview | https://developers.google.com/merchant/api/guides/data-sources/overview |
| Discovery doc: accounts_v1 (auth, schemas, methods) | https://merchantapi.googleapis.com/$discovery/rest?version=accounts_v1 |
| Discovery doc: products_v1 (methods, product schema) | https://merchantapi.googleapis.com/$discovery/rest?version=products_v1 |
| Discovery doc: datasources_v1 (methods, DataSource schema) | https://merchantapi.googleapis.com/$discovery/rest?version=datasources_v1 |
| Discovery doc: inventories_v1 (methods, schemas) | https://merchantapi.googleapis.com/$discovery/rest?version=inventories_v1 |
| Discovery doc: reports_v1 (search method, report tables) | https://merchantapi.googleapis.com/$discovery/rest?version=reports_v1 |

### Unverified Claims (doc fetch failed)

- Specific Content API v2.1 migration field-rename details (migration guide URL 404d) — field renames table above is based on discovery doc comparison and overview doc, not a dedicated migration guide.
- Exact `onlineReturnPolicies` object shape — full schema not fetched (404); shape above derived from accounts_v1 discovery doc summary.
- Exact `issues` response field names (specifically `impactedDestinations` nesting depth) — primary source is CLI source code docstring + accounts overview; dedicated issues reference page 404d.
- Reports query field names in `product_view` and `product_performance_view` (e.g. `price_micros`, `item_issues`) — derived from discovery doc table names and overview content; the exact field lists require the full reports discovery doc schema.
