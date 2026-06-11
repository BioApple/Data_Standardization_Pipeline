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
ADMET_OUTPUT_PATH = PROCESSED_DIR / "standardized_admet_results.csv"

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
EXCEL_EXTENSIONS = {".xlsx", ".xls"}

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

ALLOWED_CROS = {"GVK", "Aragen"}
ALLOWED_SPECIES = {"Human", "Mouse", "Rat", "Dog", "Monkey"}

ADMET_PARAMETER_MAP = {
    "Hepatocyte Stability": {
        "concentration_uM": ("concentration", "uM", "numeric"),
        "timepoint_min": ("timepoint", "min", "numeric"),
        "remaining_percent": ("remaining_percent", "%", "percent"),
        "half_life_min": ("half_life", "min", "numeric"),
    },
    "Microsome Stability": {
        "concentration_uM": ("concentration", "uM", "numeric"),
        "timepoint_min": ("timepoint", "min", "numeric"),
        "remaining_percent": ("remaining_percent", "%", "percent"),
        "clint_uL_min_mg": ("intrinsic_clearance", "uL/min/mg", "numeric"),
    },
    "Plasma Stability": {
        "concentration_uM": ("concentration", "uM", "numeric"),
        "timepoint_min": ("timepoint", "min", "numeric"),
        "remaining_percent": ("remaining_percent", "%", "percent"),
        "matrix": ("matrix", "text", "text"),
    },
    "Solubility": {
        "nominal_concentration_uM": ("nominal_concentration", "uM", "numeric"),
        "pH": ("pH", "unitless", "numeric"),
        "solubility_uM": ("solubility", "uM", "numeric"),
        "result_flag": ("result_flag", "text", "text"),
    },
    "Protein Binding": {
        "concentration_uM": ("concentration", "uM", "numeric"),
        "matrix": ("matrix", "text", "text"),
        "fraction_unbound_percent": ("fraction_unbound", "%", "percent"),
        "bound_percent": ("bound", "%", "percent"),
    },
    "Permeability Caco2": {
        "concentration_uM": ("concentration", "uM", "numeric"),
        "papp_ab_10_6_cm_s": ("papp_ab", "10^-6 cm/s", "numeric"),
        "papp_ba_10_6_cm_s": ("papp_ba", "10^-6 cm/s", "numeric"),
        "efflux_ratio": ("efflux_ratio", "unitless", "numeric"),
    },
    "CYP Inhibition": {
        "concentration_uM": ("concentration", "uM", "numeric"),
        "cyp_isoform": ("cyp_isoform", "text", "text"),
        "inhibition_percent": ("inhibition", "%", "percent"),
        "ic50_uM": ("ic50", "uM", "numeric"),
    },
}

ADMET_TARGET_SCHEMA = [
    "compound_id",
    "exp_date",
    "cro",
    "species",
    "assay_name",
    "study_id",
    "parameter",
    "value",
    "unit",
    "source_file",
    "processed_at",
    "source_measurement",
]


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


def is_admet_file(file_path):
    return file_path.suffix.lower() in EXCEL_EXTENSIONS and "STUDY-ADMET" in file_path.stem


def parse_admet_filename(file_path):
    parts = file_path.stem.split("_")

    if len(parts) < 5:
        raise ValueError("Filename does not match expected ADMET pattern")

    date_text, cro, species = parts[0], parts[1], parts[2]
    study_start = next((index for index, part in enumerate(parts) if part.startswith("STUDY-")), None)

    if study_start is None or study_start <= 3:
        raise ValueError("Filename does not contain assay name and study ID")

    exp_date = datetime.strptime(date_text, "%Y%m%d").strftime("%Y-%m-%d")
    assay_name = " ".join(parts[3:study_start])
    study_id = "_".join(parts[study_start:])

    if cro not in ALLOWED_CROS:
        raise ValueError(f"Unsupported CRO: {cro}")

    if species not in ALLOWED_SPECIES:
        raise ValueError(f"Unsupported species: {species}")

    if assay_name not in ADMET_PARAMETER_MAP:
        raise ValueError(f"Unsupported assay name: {assay_name}")

    return {
        "exp_date": exp_date,
        "cro": cro,
        "species": species,
        "assay_name": assay_name,
        "study_id": study_id,
        "source_file": file_path.name,
    }


def read_admet_report_table(file_path):
    engine = "openpyxl" if file_path.suffix.lower() == ".xlsx" else "xlrd"
    workbook = pd.ExcelFile(file_path, engine=engine)

    if "Report" not in workbook.sheet_names:
        raise ValueError("Workbook does not contain a Report sheet")

    raw_df = pd.read_excel(file_path, sheet_name="Report", header=None, engine=engine)
    header_row_index = None

    for index, row in raw_df.iterrows():
        values = [str(value).strip().lower() for value in row.tolist() if pd.notna(value)]
        if "compound_id" in values:
            header_row_index = index
            break

    if header_row_index is None:
        raise ValueError("Result table header with compound_id was not found")

    headers = [str(value).strip() if pd.notna(value) else "" for value in raw_df.iloc[header_row_index]]
    table_df = raw_df.iloc[header_row_index + 1 :].copy()
    table_df.columns = headers
    table_df = table_df.loc[:, [column for column in table_df.columns if column]]
    table_df = table_df.dropna(how="all")

    return table_df


def validate_admet_table(df, assay_name):
    if "compound_id" not in df.columns:
        return False, "Result table must contain compound_id"

    mapping = ADMET_PARAMETER_MAP[assay_name]
    missing_columns = [column for column in mapping if column not in df.columns]
    if missing_columns:
        return False, f"Missing assay-specific column: {', '.join(missing_columns)}"

    if is_empty(df["compound_id"]).any():
        return False, "compound_id must not be empty"

    for column, (_, _, value_type) in mapping.items():
        if value_type == "text":
            continue

        values = pd.to_numeric(df[column], errors="coerce")
        if values.isna().any():
            return False, f"{column} contains invalid numeric values"

        if (values < 0).any():
            return False, f"{column} contains negative values"

        if value_type == "percent" and ((values < 0) | (values > 100)).any():
            return False, f"{column} contains percentage values outside 0-100"

    return True, "ADMET report validated"


def standardize_admet_table(df, metadata, processed_at):
    output_rows = []
    mapping = ADMET_PARAMETER_MAP[metadata["assay_name"]]

    for _, row in df.iterrows():
        compound_id = row["compound_id"]

        for source_measurement, (parameter, unit, value_type) in mapping.items():
            value = row[source_measurement]
            if value_type in {"numeric", "percent"}:
                value = pd.to_numeric(value)

            output_rows.append(
                {
                    "compound_id": compound_id,
                    "exp_date": metadata["exp_date"],
                    "cro": metadata["cro"],
                    "species": metadata["species"],
                    "assay_name": metadata["assay_name"],
                    "study_id": metadata["study_id"],
                    "parameter": parameter,
                    "value": value,
                    "unit": unit,
                    "source_file": metadata["source_file"],
                    "processed_at": processed_at,
                    "source_measurement": source_measurement,
                }
            )

    return pd.DataFrame(output_rows, columns=ADMET_TARGET_SCHEMA)


def process_manufacturing_file(file_path):
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


def process_admet_file(file_path, processed_at):
    print(f"Processing {file_path.name}...")

    try:
        metadata = parse_admet_filename(file_path)
        df = read_admet_report_table(file_path)
        passed, message = validate_admet_table(df, metadata["assay_name"])

        if passed:
            standardized_df = standardize_admet_table(df, metadata, processed_at)
            print("PASS - ADMET report standardized")
            status = "accepted"
            move_file(file_path, status)
            print()
            return build_report_row(file_path.name, status, message), standardized_df
    except Exception as error:
        message = str(error)

    print(f"FAIL - {message}")
    status = "rejected"
    move_file(file_path, status)
    print()
    return build_report_row(file_path.name, status, message), None


def consolidate_accepted_files():
    print("Only accepted files are eligible for consolidation.")

    accepted_files = sorted(
        file_path
        for file_path in ACCEPTED_DIR.iterdir()
        if file_path.is_file()
        and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not is_admet_file(file_path)
    )

    if not accepted_files:
        print("No accepted manufacturing files found. Consolidated output was not created.")
        return

    print("Creating consolidated output from accepted manufacturing files...")

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
        print("No accepted manufacturing files could be consolidated.")
        return

    combined_df = pd.concat(dataframes, ignore_index=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(CONSOLIDATED_OUTPUT_PATH, index=False)

    relative_output_path = CONSOLIDATED_OUTPUT_PATH.relative_to(BASE_DIR)
    print(f"Consolidated file created: {relative_output_path}")
    print(f"Rows written: {len(combined_df)}")


def write_admet_output(admet_dataframes):
    if not admet_dataframes:
        return 0

    combined_df = pd.concat(admet_dataframes, ignore_index=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(ADMET_OUTPUT_PATH, index=False)

    return len(combined_df)


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

    report_rows = []
    admet_dataframes = []
    processed_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not files:
        print("No supported files found in data/incoming/.")
    else:
        for file_path in files:
            if is_admet_file(file_path):
                report_row, standardized_df = process_admet_file(file_path, processed_at)
                report_rows.append(report_row)

                if standardized_df is not None:
                    admet_dataframes.append(standardized_df)
            else:
                report_rows.append(process_manufacturing_file(file_path))

        write_validation_report(report_rows)

        accepted_count = sum(row["status"] == "accepted" for row in report_rows)
        rejected_count = sum(row["status"] == "rejected" for row in report_rows)

        print("Validation complete.")
        print(f"Accepted files: {accepted_count}")
        print(f"Rejected files: {rejected_count}")
        print(f"Validation report generated: {REPORT_PATH}")
        print()

    consolidate_accepted_files()

    admet_rows_written = write_admet_output(admet_dataframes)
    if admet_dataframes:
        print()
        print("ADMET standardization complete.")
        print(f"Rows written: {admet_rows_written}")
        print(f"Output: {ADMET_OUTPUT_PATH.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
