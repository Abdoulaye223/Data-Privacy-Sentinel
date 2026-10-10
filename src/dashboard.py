"""Create a revenue chart only from the expected sanitized export."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

EXPECTED_EXPORT_COLUMNS = {
    "order_id",
    "customer_name",
    "total_spent",
    "purchase_date",
    "email_hash",
}


def generate_secure_report(data_file="clean_data_export.csv", output_image="secure_revenue_report.png"):
    """Validate the sanitized export and save a daily revenue chart."""
    input_path = Path(data_file).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(
            f"Sanitized export not found: {input_path}. Run gateway.py first."
        )

    df = pd.read_csv(input_path)

    if df.columns.duplicated().any():
        raise ValueError("Sanitized export contains duplicate column names.")

    actual_columns = set(df.columns)
    if actual_columns != EXPECTED_EXPORT_COLUMNS:
        missing = sorted(EXPECTED_EXPORT_COLUMNS - actual_columns)
        unexpected = sorted(actual_columns - EXPECTED_EXPORT_COLUMNS)
        raise ValueError(
            "Sanitized export schema rejected. "
            f"Missing columns: {missing}; unexpected columns: {unexpected}."
        )

    amounts = pd.to_numeric(df["total_spent"], errors="raise")
    if amounts.isna().any():
        raise ValueError("total_spent contains missing values.")

    dates = pd.to_datetime(df["purchase_date"], errors="raise")
    if dates.isna().any():
        raise ValueError("purchase_date contains missing values.")

    if df.empty:
        raise ValueError("Sanitized export contains no rows.")

    report_df = pd.DataFrame({
        "purchase_date": dates.dt.strftime("%Y-%m-%d"),
        "total_spent": amounts,
    })
    daily_revenue = (
        report_df.groupby("purchase_date", as_index=False)["total_spent"]
        .sum()
        .sort_values("purchase_date")
    )

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        x="purchase_date",
        y="total_spent",
        data=daily_revenue,
        ax=ax,
        color="steelblue",
    )
    ax.set_title("Daily Revenue (Sanitized Data)", fontsize=16, pad=20)
    ax.set_xlabel("Transaction Date", fontsize=12)
    ax.set_ylabel("Revenue (source currency)", fontsize=12)

    for patch in ax.patches:
        ax.annotate(
            f"{patch.get_height():.2f}",
            (patch.get_x() + patch.get_width() / 2, patch.get_height()),
            ha="center",
            va="center",
            xytext=(0, 9),
            textcoords="offset points",
        )

    fig.tight_layout()
    output_path = Path(output_image).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Revenue report saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_secure_report()
