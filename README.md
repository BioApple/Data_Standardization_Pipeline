# Manufacturing Data Quality Framework

## Project Overview

This portfolio project demonstrates a controlled manufacturing data intake process. Incoming CSV and Excel files are validated before they are accepted into downstream workflows.

The focus is data quality, data governance, and operational data management rather than software complexity.

## Business Scenario

Manufacturing batch data arrives from operational teams or source systems. Before the data can be used for reporting, analytics, or regulated workflow steps, each file must pass basic quality controls.

Files that pass validation are moved to `data/accepted/`. Files that fail validation are moved to `data/rejected/`, and the reason is written to an audit-style validation report.

## Folder Structure

```text
manufacturing-data-quality-framework/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── incoming/
│   ├── accepted/
│   └── rejected/
├── reports/
│   └── validation_report.csv
└── src/
    └── validate_files.py
```

## Supported File Formats

- CSV files: `.csv`
- Excel files: `.xlsx`

JSON and XML are intentionally out of scope for MVP 1.

## Expected Data Schema

The default required columns are:

- `batch_id`
- `material_id`
- `production_date`
- `site`
- `status`
- `quantity`
- `unit`

These fields are defined in `src/validate_files.py` and can be modified as the project evolves.

## Validation Rules

The intake process checks each supported file for:

- Missing required columns
- Empty mandatory values
- Duplicate `batch_id` values within the file
- Invalid `production_date` values
- Invalid `status` values
- Non-numeric or non-positive `quantity` values
- Invalid `unit` values

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

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Place `.csv` or `.xlsx` files in:

```text
data/incoming/
```

3. Run the validation process:

```bash
python src/validate_files.py
```

## Output

The script displays progress in the console:

```text
Processing batch_001.csv...
PASS

Processing batch_002.xlsx...
FAIL - Missing required column: production_date
```

It also generates:

```text
reports/validation_report.csv
```

Report columns:

- `timestamp`
- `file_name`
- `status`
- `message`

## Portfolio Skills Demonstrated

- Data ingestion
- Data quality controls
- Validation logic
- Exception handling
- Audit-style reporting
- Operational workflow design
- Manufacturing data governance thinking
