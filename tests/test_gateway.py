import pandas as pd
import pytest

from src.gateway import (
    EXPECTED_COLUMNS,
    mask_customer_name,
    protect_data,
    pseudonymize_email,
    validate_schema,
)


def sample_df():
    return pd.DataFrame({
        "order_id": ["A-100", "A-101"],
        "customer_name": ["Awa Traore", "  "],
        "email": ["AWA@example.com", None],
        "ip_address": ["192.0.2.10", "192.0.2.11"],
        "total_spent": [12.5, 0],
        "purchase_date": ["2026-01-02", "2026-01-03"],
    })


def test_schema_accepts_expected_columns():
    validate_schema(sample_df())


def test_schema_rejects_missing_column():
    with pytest.raises(ValueError, match="missing required columns"):
        validate_schema(sample_df().drop(columns=["ip_address"]))


def test_schema_rejects_unapproved_column():
    df = sample_df()
    df["phone_number"] = "123"
    with pytest.raises(ValueError, match="unapproved columns"):
        validate_schema(df)


def test_schema_rejects_duplicate_column_names():
    df = sample_df()
    df.columns = EXPECTED_COLUMNS[:-1] + ["email"]
    with pytest.raises(ValueError, match="Duplicate columns"):
        validate_schema(df)


def test_pseudonym_is_stable_and_keyed():
    first = pseudonymize_email(" AWA@example.com ", "test-secret")
    assert first == pseudonymize_email("awa@example.com", "test-secret")
    assert first != pseudonymize_email("awa@example.com", "different-secret")


def test_missing_email_stays_missing():
    assert pd.isna(pseudonymize_email(None, "test-secret"))
    assert pd.isna(pseudonymize_email("   ", "test-secret"))


def test_pseudonymization_requires_secret_for_nonempty_email():
    with pytest.raises(ValueError, match="SECRET_SALT is required"):
        pseudonymize_email("awa@example.com", "")


def test_name_mask_handles_blank_and_missing_values():
    assert mask_customer_name("Awa Traore") == "A***"
    assert mask_customer_name("  ") == ""
    assert pd.isna(mask_customer_name(None))


def test_protect_data_removes_direct_identifiers(tmp_path):
    input_path = tmp_path / "raw.csv"
    output_path = tmp_path / "clean.csv"
    sample_df().to_csv(input_path, index=False)

    result = protect_data(str(input_path), str(output_path), secret="test-secret")
    written = pd.read_csv(output_path)

    assert "email" not in result.columns
    assert "ip_address" not in result.columns
    assert "email" not in written.columns
    assert "ip_address" not in written.columns
    assert "email_hash" in written.columns
    assert written.loc[0, "email_hash"] == pseudonymize_email(
        "awa@example.com", "test-secret"
    )


def test_protect_data_rejects_invalid_amount(tmp_path):
    input_path = tmp_path / "raw.csv"
    sample_df().assign(total_spent=["not-a-number", 0]).to_csv(input_path, index=False)

    with pytest.raises((ValueError, TypeError)):
        protect_data(str(input_path), str(tmp_path / "clean.csv"), secret="test-secret")


def test_protect_data_rejects_same_input_and_output_path(tmp_path):
    input_path = tmp_path / "raw.csv"
    sample_df().to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="must be different"):
        protect_data(str(input_path), str(input_path), secret="test-secret")
