# src/quality/validation.py
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite

def build_patient_expectation_suite() -> ExpectationSuite:
    """
    TODO: Tạo expectation suite cho anonymized patient data.
    """
    context = gx.get_context()
    suite = context.add_expectation_suite("patient_data_suite")

    # Lấy validator
    df = pd.read_csv("data/raw/patients_raw.csv")
    validator = context.sources.pandas_default.read_dataframe(df)

    # --- TASK: Thêm các expectations ---

    # 1. patient_id không được null
    validator.expect_column_values_to_not_be_null("patient_id")

    validator.expect_column_value_lengths_to_equal(
        column= "cccd",
        value=12
    )

    validator.expect_column_values_to_be_between(
        column="ket_qua_xet_nghiem",
        min_value=0,
        max_value=50
    )

    # 4. TODO: benh phải thuộc danh sách hợp lệ
    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
    validator.expect_column_values_to_be_in_set(
        column="benh",
        value_set=valid_conditions
    )

    # 5. TODO: email phải match regex pattern
    validator.expect_column_values_to_match_regex(
        column="email",
        regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    # 6. TODO: Không được có duplicate patient_id
    validator.expect_column_values_to_be_unique(column="patient_id")

    validator.save_expectation_suite()
    return suite


def validate_anonymized_data(filepath: str) -> dict:
    """
    TODO: Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: Không còn CCCD gốc xuất hiện trong anonymized data
    try:
        original_df = pd.read_csv("data/raw/patients_raw.csv")
        original_cccds = set(original_df["cccd"].astype(str))
        leaked = set(df["cccd"].astype(str)) & original_cccds
        if leaked:
            results["success"] = False
            results["failed_checks"].append(f"Original CCCDs still present: {leaked}")
    except FileNotFoundError:
        pass

    # Check 2: Không có null values trong các cột quan trọng
    for col in ["patient_id", "cccd", "email"]:
        if df[col].isnull().any():
            results["success"] = False
            results["failed_checks"].append(f"Null values found in column: {col}")

    # Check 3: Số rows phải bằng original
    original_df = pd.read_csv("data/raw/patients_raw.csv")
    if len(df) != len(original_df):
        results["success"] = False
        results["failed_checks"].append(f"Row count mismatch: {len(df)} vs {len(original_df)}")

    return results
