# Authentication

ed-api uses Bearer token authentication against the EdStem API.

## Obtaining your token

1. Log in to [edstem.org](https://edstem.org)
2. Go to your account settings
3. Copy the API key from the API section

## Token resolution order

`EdClient` resolves your token from three sources, in priority order:

1. **Constructor argument** — `EdClient(token="...")`
2. **Environment variable** — `ED_API_TOKEN`
3. **`.env` file** — `ED_API_TOKEN=...` in a `.env` file in the working directory

If no token is found, `EdClient` raises `ValueError` immediately.

## Constructor argument

```python
from ed_api import EdClient

client = EdClient(token="your_token_here")
```

Useful for one-off scripts. Not recommended for code that will be shared or committed.

## Environment variable

```bash
export ED_API_TOKEN=your_token_here
python your_script.py
```

```python
# No token argument needed — reads from environment
client = EdClient()
```

## `.env` file

Create `.env` in your project root:

```ini title=".env"
ED_API_TOKEN=your_token_here
ED_REGION=us
```

ed-api calls `load_dotenv(find_dotenv(usecwd=True))` on construction, so it picks up `.env` files relative to the working directory.

!!! tip "`.gitignore` your `.env`"
    ```gitignore
    .env
    .env.*
    ```

## Region configuration

EdStem has regional deployments. The region affects both the API base URL and the static file URL for uploads.

| Region | API base |
|---|---|
| `us` (default) | `https://us.edstem.org/api/` |
| `au` | `https://au.edstem.org/api/` |

Set the region:

```bash
export ED_REGION=au
```

Or in the constructor:

```python
client = EdClient(region="au")
```

Or in `.env`:

```ini
ED_REGION=au
```

## Rate limiting

The `rate_limit` parameter controls requests per second (default: `5.0`):

```python
# Slower — for scripts running alongside heavy course activity
client = EdClient(rate_limit=2.0)

# Faster — if you know your account has higher limits
client = EdClient(rate_limit=10.0)
```

The HTTP client enforces the rate limit with a simple token bucket and automatically retries 429 responses with exponential backoff (up to 3 attempts by default).

## Verifying your token

```python
from ed_api import EdClient

client = EdClient()
info = client.user.info()
print(f"Authenticated as: {info.user.name} <{info.user.email}>")
```

Or from the CLI:

```bash
ed-api auth check
ed-api auth whoami
```

## Exception handling

Authentication errors raise `EdAuthError` (HTTP 401):

```python
from ed_api import EdClient
from ed_api.exceptions import EdAuthError

try:
    client = EdClient(token="bad_token")
    client.user.info()
except EdAuthError as e:
    print(f"Auth failed: {e}")
    print(f"Status: {e.status_code}")
```
