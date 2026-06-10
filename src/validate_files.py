from datetime import datetime
from pathlib import Path
import shutil

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INCOMING_DIR = BASE_DIR / "data" / "incoming"
ACCEPTED_DIR = BASE_DIR / "data" / "accepted"
REJECTED_DIR = BASE_DIR / "data" / "rejected"
REPORT_PATH = BASE_DIR / "reports" / "validation_report.csv"

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}

REQUIRED_COLUMNS = [
    "batch_id",
    "material_id",
    "production_date",
    "site",
    "status",
    "quantity",
    "unit",
]

ALLOWED_STATUSES = {"Released", "In Progress", "Rejected"}
ALLOWED_UNITS = {"mg", "g", "kg", "mL", "L"}


def read_input_file(file_path):
    if file_path.suffix.lower() == ".csv":
        return pd.read_csv(file_path)

    if file_path.suffix.lower() == ".xlsx":
        return pd.read_excel(file_path, engine="openpyxl")

    raise ValueError(f"Unsupported file format: {file_path.suffix}")


def is_empty(series):
    return series.isna() | (series.astype(str).str.strip() == "")


def validate_dataframe(df):
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        return False, f"Missing required column: {', '.join(missing_columns)}"

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


def append_report_row(file_name, status, message):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    report_row = pd.DataFrame(
        [
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "file_name": file_name,
                "status": status,
                "message": message,
            }
        ]
    )

    report_exists = REPORT_PATH.exists()
    report_row.to_csv(REPORT_PATH, mode="a", index=False, header=not report_exists)


def move_file(file_path, destination_dir):
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / file_path.name

    if destination_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination_path = destination_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

    shutil.move(str(file_path), str(destination_path))


def process_file(file_path):
    print(f"Processing {file_path.name}...")

    try:
        df = read_input_file(file_path)
        passed, message = validate_dataframe(df)
    except Exception as error:
        passed = False
        message = f"File could not be processed: {error}"

    if passed:
        print("PASS")
        move_file(file_path, ACCEPTED_DIR)
        append_report_row(file_path.name, "accepted", message)
    else:
        print(f"FAIL - {message}")
        move_file(file_path, REJECTED_DIR)
        append_report_row(file_path.name, "rejected", message)

    print()


def main():
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    ACCEPTED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(
        file_path
        for file_path in INCOMING_DIR.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print("No supported files found in data/incoming/.")
        return

    for file_path in files:
        process_file(file_path)

    print(f"Validation report generated: {REPORT_PATH}")


if __name__ == "__main__":
    main()
