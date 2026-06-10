# Manufacturing Data Quality Framework

## Project Overview

This portfolio project demonstrates a controlled manufacturing data intake process. Incoming CSV and Excel files are validated, routed, reported, and consolidated before they are used in downstream workflows.

The focus is data quality, data governance, and operational data management rather than software complexity.

## Business Scenario

Manufacturing batch data arrives from operational teams or source systems. Before the data can be used for reporting, analytics, or regulated workflow steps, each file must pass basic quality controls.

The framework validates incoming manufacturing data files, routes accepted and rejected files, records validation outcomes in a structured report, and consolidates only accepted datasets into a standardized output with source-file traceability. Rejected files remain unprocessed in the rejected folder for review.

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

## Supported File Formats

- CSV files: `.csv`
- Excel files: `.xlsx`
- Legacy Excel files: `.xls`

JSON and XML are intentionally out of scope for MVP 2.

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

## Consolidated Output

After validation is complete, accepted files are standardized and combined into one consolidated dataset:

```text
data/processed/consolidated_manufacturing_data.csv
```

The consolidated output uses this target schema:

- `batch_id`
- `material_id`
- `production_date`
- `site`
- `status`
- `quantity`
- `unit`
- `source_file`
- `processed_at`

`source_file` records the accepted file each row came from. `processed_at` records when the consolidation process ran.

## How To Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Place `.csv`, `.xlsx`, or `.xls` files in:

```text
data/incoming/
```

3. Run the validation and consolidation process:

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

It also generates a validation report:

```text
reports/validation_report.csv
```

Report columns:

- `timestamp`
- `file_name`
- `status`
- `message`

Only accepted files are consolidated into:

```text
data/processed/consolidated_manufacturing_data.csv
```

## Portfolio Skills Demonstrated

- Data ingestion
- Data quality controls
- Validation logic
- Exception handling
- Audit-style reporting
- Standardized data consolidation
- Source-file traceability
- Operational workflow design
- Manufacturing data governance thinking
