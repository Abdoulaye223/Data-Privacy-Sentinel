"""Validate and pseudonymize customer data before export.

The output uses HMAC-SHA-256 for deterministic email pseudonyms. This is
pseudonymization, not anonymization: the secret must remain private.
"""
import argparse
import hashlib
import hmac
import math
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

EXPECTED_COLUMNS = [
    "order_id",
    "customer_name",
    "email",
    "ip_address",
    "total_spent",
    "purchase_date",
]


def validate_schema(df: pd.DataFrame) -> None:
    """Reject duplicate, missing, or unexpected input columns."""
    if df.columns.duplicated().any():
        duplicates = df.columns[df.columns.duplicated()].tolist()
        raise ValueError(f"Duplicate columns are not allowed: {duplicates}")

    actual = set(df.columns)
    expected = set(EXPECTED_COLUMNS)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)

    if missing or unknown:
        problems = []
        if missing:
            problems.append(f"missing required columns: {missing}")
        if unknown:
            problems.append(f"unapproved columns: {unknown}")
        raise ValueError("CSV schema rejected (" + "; ".join(problems) + ").")


def pseudonymize_email(email, secret: str):
    """Return a keyed, stable pseudonym; preserve missing/blank values."""
    if pd.isna(email) or not str(email).strip():
        return pd.NA
    if not secret or not secret.strip():
        raise ValueError(
            "SECRET_SALT is required. Set it in your environment or .env file."
        )

    normalized = str(email).strip().lower().encode("utf-8")
    return hmac.new(secret.encode("utf-8"), normalized, hashlib.sha256).hexdigest()


def mask_customer_name(value):
    """Mask a name for display; this is not a guarantee of anonymity."""
    if pd.isna(value):
        return pd.NA
    normalized = str(value).strip()
    if not normalized:
        return ""
    return normalized[0] + "***"


def resolve_input_path(input_file: str) -> Path:
    """Resolve paths relative to the current directory or this source file."""
    path = Path(input_file).expanduser()
    if path.is_absolute() and path.is_file():
        return path.resolve()

    if path.is_file():
        return path.resolve()

    script_dir = Path(__file__).resolve().parent
    candidates = [script_dir / path, script_dir / "data" / path]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    return path.resolve()


def protect_data(input_file: str, output_file: str, secret: str | None = None):
    """Validate, pseudonymize, and write a sanitized CSV; return its DataFrame."""
    input_path = resolve_input_path(input_file)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    output_path = Path(output_file).expanduser().resolve()
    if input_path == output_path:
        raise ValueError("Input and output paths must be different.")

    key = secret if secret is not None else os.getenv("SECRET_SALT", "")
    if not key or not key.strip():
        raise ValueError(
            "SECRET_SALT is required. Set it in your environment or .env file."
        )

    df = pd.read_csv(input_path)
    validate_schema(df)

    if df["order_id"].isna().any() or df["order_id"].astype(str).str.strip().eq("").any():
        raise ValueError("order_id must not be empty.")

    amounts = pd.to_numeric(df["total_spent"], errors="raise")
    if amounts.isna().any() or not amounts.map(lambda value: math.isfinite(float(value))).all():
        raise ValueError("total_spent must contain finite numeric values.")

    dates = pd.to_datetime(df["purchase_date"], errors="raise")
    if dates.isna().any():
        raise ValueError("purchase_date must not be empty.")

    df_clean = df.copy()
    df_clean["email_hash"] = df_clean["email"].apply(
        lambda value: pseudonymize_email(value, key)
    )
    df_clean["customer_name"] = df_clean["customer_name"].apply(mask_customer_name)
    df_clean["total_spent"] = amounts
    df_clean["purchase_date"] = dates.dt.strftime("%Y-%m-%d")

    # Remove direct identifiers before writing the export.
    df_clean = df_clean.drop(columns=["email", "ip_address"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    print(f"Secure export written to: {output_path}")
    return df_clean


def main() -> int:
    parser = argparse.ArgumentParser(description="Privacy-first data gateway")
    parser.add_argument(
        "--input", "-i", default="data/raw_customers.csv",
        help="Path to the input CSV",
    )
    parser.add_argument(
        "--output", "-o", default="clean_data_export.csv",
        help="Path for the sanitized output CSV",
    )
    args = parser.parse_args()

    try:
        protect_data(args.input, args.output)
    except (FileNotFoundError, ValueError, pd.errors.ParserError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
