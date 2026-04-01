# Installation

## Requirements

- Python 3.11 or later
- An EdStem account with API access

## Install the package

=== "pip"

    ```bash
    pip install ed-api
    ```

=== "uv"

    ```bash
    uv add ed-api
    ```

=== "uv (dev dependency)"

    ```bash
    uv add --dev ed-api
    ```

## Set up your API token

ed-api needs your EdStem API token to authenticate. Obtain it from your EdStem account settings page.

### Option 1: Environment variable (recommended for CI/scripts)

```bash
export ED_API_TOKEN=your_token_here
```

### Option 2: `.env` file (recommended for local development)

Create a `.env` file in your project directory:

```ini title=".env"
ED_API_TOKEN=your_token_here
```

ed-api automatically loads `.env` files via `python-dotenv` — no extra setup needed.

!!! warning "Keep your token secret"
    Never commit your `.env` file or hardcode your token in source code. Add `.env` to your `.gitignore`.

### Option 3: Constructor argument

```python
from ed_api import EdClient

client = EdClient(token="your_token_here")
```

This is useful for short scripts but not recommended for production code.

## Region configuration

EdStem has multiple regions. By default, ed-api connects to the US region (`us.edstem.org`). If your institution uses a different region, configure it:

```bash
export ED_REGION=au   # Australia
```

Or pass it to the constructor:

```python
client = EdClient(region="au")
```

Supported values: `us`, `au`.

## Verify installation

```bash
ed-api auth check
```

If your token is valid, you will see:

```
Token valid. Logged in as Your Name
```

## Dependencies

ed-api installs these packages automatically:

| Package | Purpose |
|---|---|
| `httpx` | HTTP client |
| `typer` | CLI framework |
| `rich` | Terminal formatting |
| `python-dotenv` | `.env` file loading |
| `beautifulsoup4` | Ed XML parsing |
| `lxml` | XML parser backend |
