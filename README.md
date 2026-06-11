# Manufacturing Data Quality Framework

This is a small data pipeline for checking incoming manufacturing batch files before they are used downstream.

The pipeline reads files from `data/incoming/`, validates them, moves good files to `data/accepted/`, moves failed files to `data/rejected/`, writes a validation report, and consolidates accepted files into one standardized output.

Rejected files are not consolidated. They stay in `data/rejected/` so they can be reviewed separately.

## Folder Structure

```text
manufacturing-data-quality-framework/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── incoming/
│   ├── accepted/
│   ├── rejected/
│   └── processed/
├── reports/
│   └── validation_report.csv
└── src/
    └── validate_files.py
```

## Supported Files

- `.csv`
- `.xlsx`
- `.xls`

JSON and XML are not included yet.

## Expected Columns

Input files should contain these columns:

- `batch_id`
- `material_id`
- `production_date`
- `site`
- `status`
- `quantity`
- `unit`

The required columns are defined near the top of `src/validate_files.py`, so they can be changed later if the data model changes.

## Checks Performed

The pipeline checks for:

- missing required columns
- empty required values
- duplicate `batch_id` values
- invalid production dates
- invalid status values
- non-numeric or non-positive quantities
- invalid units

Allowed `status` values:

- `Released`
- `In Progress`
- `Rejected`

Allowed `unit` values:

- `mg`
- `g`
- `kg`
- `mL`
- `L`

## How To Run

Install the required packages:

```bash
pip install -r requirements.txt
```

Put input files into:

```text
data/incoming/
```

Run the pipeline:

```bash
python src/validate_files.py
```

## Outputs

Validation results are written to:

```text
reports/validation_report.csv
```

Accepted files are consolidated into:

```text
data/processed/consolidated_manufacturing_data.csv
```

The consolidated file uses this schema:

- `batch_id`
- `material_id`
- `production_date`
- `site`
- `status`
- `quantity`
- `unit`
- `source_file`
- `processed_at`

`source_file` shows which accepted file the row came from. `processed_at` shows when the consolidation was created.

## Example Console Output

```text
Processing batch_001.csv...
PASS

Processing batch_002.xlsx...
FAIL - Missing required column: production_date

Validation complete.
Accepted files: 1
Rejected files: 1

Only accepted files are eligible for consolidation.
Creating consolidated output from accepted files...
Consolidated file created: data/processed/consolidated_manufacturing_data.csv
Rows written: 3
```
