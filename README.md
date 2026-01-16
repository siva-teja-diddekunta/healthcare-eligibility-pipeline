# Healthcare Eligibility Pipeline

A configuration-driven data pipeline for processing healthcare eligibility files from multiple partners.

## Overview

This pipeline solves the problem of receiving eligibility data from different healthcare partners who each use different file formats and column structures. Instead of hardcoding logic for each partner, I built a config-driven system where partner details live in a YAML file.

**Key idea:** Add new partners by updating config, not code.

## Quick Start

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the pipeline:
```bash
python eligibility_pipeline.py
```

Output will be saved to `output/unified_eligibility.csv`

## What It Does

Takes files like:
- **Acme Health** (pipe-delimited): `MBI|FNAME|LNAME|DOB|...`
- **Better Care** (CSV): `subscriber_id,first_name,last_name,...`

And produces one unified CSV with standardized format:
- Names in Title Case
- Dates in YYYY-MM-DD format  
- Phones as XXX-XXX-XXXX
- Emails in lowercase

## Project Structure

```
config/         Partner configurations
data/           Input files from partners
output/         Generated unified file
tests/          Basic unit tests
```

## How It Works

1. **Reads config** - Gets partner details from `config/partners.yaml`
2. **Processes each partner** - Reads their file using their specific format
3. **Transforms data** - Standardizes names, dates, phones, emails
4. **Validates** - Checks for required fields (external_id, DOB)
5. **Combines** - Merges all partner data into one file

## Adding a New Partner

Edit `config/partners.yaml` and add your partner:

```yaml
new_partner:
  partner_code: "NEWP"
  file_path: "data/newpartner.csv"
  delimiter: ","
  date_format: "%Y-%m-%d"
  column_mapping:
    external_id: "member_id"
    first_name: "fname"
    last_name: "lname"
    dob: "birth_date"
    email: "email"
    phone: "phone_number"
```

Then run the pipeline again. No code changes needed.

### Config Parameters

- `partner_code` - Short identifier for the partner (shows up in output)
- `file_path` - Where their file is located
- `delimiter` - What separates fields (`,` or `|` or `\t` etc)
- `date_format` - How they format dates (Python strptime format)
- `column_mapping` - Maps their column names to our standard fields

### Date Format Examples

| Their Format | Example | Config Value |
|-------------|---------|-------------|
| MM/DD/YYYY | 03/15/1955 | `"%m/%d/%Y"` |
| YYYY-MM-DD | 1955-03-15 | `"%Y-%m-%d"` |
| DD-MM-YYYY | 15-03-1955 | `"%d-%m-%Y"` |

## Output Schema

| Field | Description |
|-------|-------------|
| external_id | Partner's unique ID for the member |
| first_name | First name (Title Case) |
| last_name | Last name (Title Case) |
| dob | Date of birth (YYYY-MM-DD) |
| email | Email address (lowercase) |
| phone | Phone number (XXX-XXX-XXXX) |
| partner_code | Which partner this record came from |

## Validation

The pipeline validates that each record has:
- An external_id (required)
- A valid date of birth (required)

Invalid records get logged and excluded from the output.

## Error Handling

If one partner's file fails to process, the pipeline logs the error and continues with other partners. This way one bad file doesn't break the whole pipeline.

## Testing

Run the tests:
```bash
pytest tests/ -v
```

Tests cover:
- Phone number formatting (handles different input formats)
- Date conversion (different date formats)
- Validation logic

## Technical Details

**Built with:**
- Python 3.8+
- Pandas for data processing
- YAML for configuration
- Pytest for testing

**Design approach:**
- Configuration-driven (no hardcoded partner logic)
- Fail-safe (errors don't stop processing)
- Logged (track what happened)
- Validated (ensure data quality)

## Sample Data

The repo includes sample data from two partners:
- `data/acme.txt` - Acme Health (pipe-delimited)
- `data/bettercare.csv` - Better Care (CSV)

Run the pipeline to see how they get combined.

## Notes

See `notes.txt` for development notes and decisions made along the way.

---

**Last updated:** January 2025# healthcare-eligibility-pipeline
