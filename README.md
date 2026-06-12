# Scientific Data Quality Framework

A lightweight data quality pipeline for checking incoming scientific data files before they are used downstream.

The current workflow focuses on ADMET CRO Excel reports. It validates incoming files, routes accepted and rejected files, records validation results, and standardizes accepted ADMET reports into a long-format output.

Rejected files are not processed further. They stay in `data/rejected/` for review.

## Folder Structure

```text
scientific-data-quality-framework/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   └── admet_mapping_config.xlsx
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

## Supported Input

ADMET CRO reports in Excel format:

- `.xlsx`
- `.xls`

The expected filename pattern is:

```text
YYYYMMDD_CRO_Species_Assay_STUDY-ID.xlsx
```

Example:

```text
20260615_GVK_Human_Hepatocyte_Stability_STUDY-ADMET-001.xlsx
```

## What The Pipeline Checks

The pipeline checks that:

- the filename contains the expected metadata
- the CRO, species, and assay name are supported
- the workbook contains a `Report` sheet
- the result table can be detected
- `compound_id` is present and not empty
- required assay-specific columns are present
- numeric values are valid
- percentages are between 0 and 100
- negative values are rejected where they do not make sense

## Configuration-Driven Mapping

The framework uses an external assay mapping configuration file:

```text
config/admet_mapping_config.xlsx
```

This file controls how source measurements are standardized into target parameters, units, and value types. Mapping rules can be added or changed in the config file without editing the Python code.

The config includes:

- `assay_name`
- `source_measurement`
- `parameter`
- `unit`
- `value_type`
- `include_in_output`

Use `include_in_output = no` when a source measurement is allowed in an input file but should not be written to the standardized output.

## How To Run

Install dependencies:

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

Accepted ADMET reports are standardized into:

```text
data/processed/standardized_admet_results.csv
```

The standardized output uses one row per compound measurement:

- `compound_id`
- `exp_date`
- `cro`
- `species`
- `assay_name`
- `study_id`
- `parameter`
- `value`
- `unit`
- `source_file`
- `processed_at`
- `original_column`
