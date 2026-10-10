# Data Privacy Sentinel

A small Python project demonstrating a privacy-conscious CSV export workflow: validate an input schema, pseudonymize email addresses, remove direct identifiers, and generate a revenue chart from the sanitized export.

> **Scope:** This is a learning/portfolio project, not a certified compliance solution or production-ready privacy platform. The code does not by itself establish GDPR/CCPA compliance.

## Workflow

1. **Validate the input schema.** The gateway rejects missing required columns, unexpected columns, and duplicate column names.
2. **Validate key fields.** Transaction IDs must be present, amounts must be finite numeric values, and purchase dates must be parseable.
3. **Pseudonymize emails.** Email addresses are normalized and processed with HMAC-SHA-256 using a secret key.
4. **Minimize exported data.** The raw `email` and `ip_address` columns are removed. The customer name is masked for display.
5. **Generate a report.** The dashboard accepts only the expected sanitized-export schema and creates a daily revenue chart.

## Privacy notes and limitations

- **Pseudonymization is not anonymization.** HMAC values remain linkable across datasets when the same secret is used and may still be personal data.
- Keep `SECRET_SALT` private. Do not commit it to Git, include it in logs, or share it with the exported dataset. Use a strong, randomly generated secret and store it in a local `.env` file or environment variable.
- Masking a name to its first character plus `***` is a display mask, not a robust anonymization method.
- Schema validation only checks column names and the validations implemented in this code. It does not prove that all sensitive information has been found or removed from arbitrary datasets.
- No independent compliance audit or measured percentage reduction in personal-data exposure is claimed.

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Configuration

Create a local `.env` file (do not commit it) with a strong secret:

```dotenv
SECRET_SALT=replace-with-a-long-random-secret
```

The variable name `SECRET_SALT` is retained for compatibility, but the value is used as an HMAC key.

## Run the pipeline

From the repository root:

```bash
python src/gateway.py --input data/raw_customers.csv --output clean_data_export.csv
python src/dashboard.py
```

The input CSV must contain exactly these columns:

- `order_id`
- `customer_name`
- `email`
- `ip_address`
- `total_spent`
- `purchase_date`

The dashboard expects the gateway output file `clean_data_export.csv` in the current working directory. It writes `secure_revenue_report.png`.

## Tests

Run the automated gateway tests from the repository root:

```bash
python -m pytest -q
```

The tests cover schema validation, required-secret handling, deterministic keyed pseudonyms, masking behavior, removal of direct identifiers, invalid amounts, and input/output path safety.
