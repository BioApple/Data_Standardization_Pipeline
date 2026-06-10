from datetime import datetime
from pathlib import Path
import shutil

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INCOMING_DIR = BASE_DIR / "data" / "incoming"
ACCEPTED_DIR = BASE_DIR / "data" / "accepted"
REJECTED_DIR = BASE_DIR / "data" / "rejected"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_PATH = BASE_DIR / "reports" / "validation_report.csv"
CONSOLIDATED_OUTPUT_PATH = PROCESSED_DIR / "consolidated_manufacturing_data.csv"

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

REQUIRED_COLUMNS = [
    "batch_id",
    "material_id",
    "production_date",
    "site",
    "status",
    "quantity",
    "unit",
]

TARGET_SCHEMA = REQUIRED_COLUMNS + ["source_file", "processed_at"]

ALLOWED_STATUSES = {"Released", "In Progress", "Rejected"}
ALLOWED_UNITS = {"mg", "g", "kg", "mL", "L"}


def read_file(file_path):
    if file_path.suffix.lower() == ".csv":
        return pd.read_csv(file_path)

    if file_path.suffix.lower() == ".xlsx":
        return pd.read_excel(file_path, engine="openpyxl")

    if file_path.suffix.lower() == ".xls":
        return pd.read_excel(file_path, engine="xlrd")

    raise ValueError(f"Unsupported file format: {file_path.suffix}")


def is_empty(series):
    return series.isna() | (series.astype(str).str.strip() == "")


def validate_schema(df):
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        return False, f"Missing required column: {', '.join(missing_columns)}"

    return True, "Schema validation passed"


def validate_business_rules(df):
    for column in REQUIRED_COLUMNS:
        if is_empty(df[column]).any():
            return False, f"Empty mandatory value detected in column: {column}"

    if df["batch_id"].duplicated().any():
        return False, "Duplicate batch_id values detected"

    parsed_dates = pd.to_datetime(df["production_date"], errors="coerce")
    if parsed_dates.isna().any():
        return False, "Invalid production_date values detected"

    invalid_statuses = ~df["status"].isin(ALLOWED_STATUSES)
    if invalid_statuses.any():
        values = sorted(df.loc[invalid_statuses, "status"].astype(str).unique())
        return False, f"Invalid status values detected: {', '.join(values)}"

    quantities = pd.to_numeric(df["quantity"], errors="coerce")
    if quantities.isna().any():
        return False, "Quantity must be numeric"

    if (quantities <= 0).any():
        return False, "Quantity must be greater than zero"

    invalid_units = ~df["unit"].isin(ALLOWED_UNITS)
    if invalid_units.any():
        values = sorted(df.loc[invalid_units, "unit"].astype(str).unique())
        return False, f"Invalid unit values detected: {', '.join(values)}"

    return True, "Validation passed"


def validate_dataframe(df):
    schema_is_valid, schema_message = validate_schema(df)
    if not schema_is_valid:
        return False, schema_message

    return validate_business_rules(df)


def build_report_row(file_name, status, message):
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "file_name": file_name,
        "status": status,
        "message": message,
    }


def write_validation_report(report_rows):
    if not report_rows:
        return

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    report_df = pd.DataFrame(report_rows)
    report_exists = REPORT_PATH.exists()
    report_df.to_csv(REPORT_PATH, mode="a", index=False, header=not report_exists)


def move_file(file_path, status):
    if status == "accepted":
        destination_dir = ACCEPTED_DIR
    elif status == "rejected":
        destination_dir = REJECTED_DIR
    else:
        raise ValueError(f"Unknown file status: {status}")

    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / file_path.name

    shutil.move(str(file_path), str(destination_path))


def process_file(file_path):
    print(f"Processing {file_path.name}...")

    try:
        df = read_file(file_path)
        passed, message = validate_dataframe(df)
    except Exception as error:
        passed = False
        message = f"File could not be processed: {error}"

    if passed:
        print("PASS")
        status = "accepted"
        move_file(file_path, status)
    else:
        print(f"FAIL - {message}")
        status = "rejected"
        move_file(file_path, status)

    print()
    return build_report_row(file_path.name, status, message)


def consolidate_accepted_files():
    print("Only accepted files are eligible for consolidation.")

    accepted_files = sorted(
        file_path
        for file_path in ACCEPTED_DIR.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not accepted_files:
        print("No accepted files found. Consolidated output was not created.")
        return

    print("Creating consolidated output from accepted files...")

    processed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    dataframes = []

    for file_path in accepted_files:
        df = read_file(file_path)
        schema_is_valid, schema_message = validate_schema(df)

        if not schema_is_valid:
            print(f"Skipping {file_path.name} - {schema_message}")
            continue

        standardized_df = df[REQUIRED_COLUMNS].copy()
        standardized_df["source_file"] = file_path.name
        standardized_df["processed_at"] = processed_at
        standardized_df = standardized_df[TARGET_SCHEMA]
        dataframes.append(standardized_df)

    if not dataframes:
        print("No accepted files could be consolidated.")
        return

    combined_df = pd.concat(dataframes, ignore_index=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(CONSOLIDATED_OUTPUT_PATH, index=False)

    relative_output_path = CONSOLIDATED_OUTPUT_PATH.relative_to(BASE_DIR)
    print(f"Consolidated file created: {relative_output_path}")
    print(f"Rows written: {len(combined_df)}")


def main():
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    ACCEPTED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(
        file_path
        for file_path in INCOMING_DIR.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print("No supported files found in data/incoming/.")
    else:
        report_rows = []

        for file_path in files:
            report_rows.append(process_file(file_path))

        write_validation_report(report_rows)

        accepted_count = sum(row["status"] == "accepted" for row in report_rows)
        rejected_count = sum(row["status"] == "rejected" for row in report_rows)

        print("Validation complete.")
        print(f"Accepted files: {accepted_count}")
        print(f"Rejected files: {rejected_count}")
        print(f"Validation report generated: {REPORT_PATH}")
        print()

    consolidate_accepted_files()


if __name__ == "__main__":
    main()
