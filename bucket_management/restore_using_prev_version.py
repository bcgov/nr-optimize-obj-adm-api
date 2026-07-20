import os
import argparse
from datetime import datetime
from urllib.parse import quote
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import pandas as pd

"""
restore_using_prev_version_xlsx.py

Restores objects by copying a specified PreviousVersionId over the same key,
creating a new current version.

Inputs
------
- .env: ACCESS_KEY, SECRET_KEY, S3_ENDPOINT, S3_BUCKET_NAME (optional), OUTPUT_PATH (optional)
- XLSX: default 'restore_input.xlsx' with columns:
      Required: Key, PreviousVersionId
      Optional: Bucket (overrides .env bucket per row)

Usage
-----
# Dry-run first (recommended)
python restore_using_prev_version_xlsx.py --dry-run

# Real run with default input file (restore_input.xlsx, first sheet)
python restore_using_prev_version_xlsx.py

# Use a custom input XLSX, specific sheet, and custom output report path
python restore_using_prev_version_xlsx.py --input my_items.xlsx --sheet Items --output my_restore_report.xlsx

Notes
-----
- Accepted header variants (case-insensitive):
  * Key -> "key"
  * PreviousVersionId -> "previousversionid", "versionid", "version", "prevversionid"
  * Bucket -> "bucket"
- If S3_BUCKET_NAME is omitted in .env, you must provide a Bucket value per row.
- If OUTPUT_PATH is set in .env and --output is not provided, the report will be written to that folder.
"""

def load_env():
    load_dotenv()
    cfg = {
        "ACCESS_KEY": os.getenv("ACCESS_KEY"),
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "S3_ENDPOINT": os.getenv("S3_ENDPOINT"),
        "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME"),
        "OUTPUT_PATH": os.getenv("OUTPUT_PATH"),
    }

    # Only these are strictly required; bucket and output path are optional
    required_keys = ["ACCESS_KEY", "SECRET_KEY", "S3_ENDPOINT"]
    missing = [k for k in required_keys if not cfg.get(k)]
    if missing:
        raise ValueError("Missing required AWS environment variables in .env: " + ", ".join(missing))

    return cfg

def get_s3_client(cfg):
    return boto3.client(
        "s3",
        aws_access_key_id=cfg["ACCESS_KEY"],
        aws_secret_access_key=cfg["SECRET_KEY"],
        endpoint_url=cfg["S3_ENDPOINT"],
    )

def encode_copy_source(bucket, key, version_id):
    # URL-encode key but keep path separators (not strictly needed when using dict CopySource)
    encoded_key = quote(key, safe="/")
    return {"Bucket": bucket, "Key": key, "VersionId": version_id}, f"{bucket}/{encoded_key}?versionId={version_id}"

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize column headers: strip, lowercase, remove BOM
    mapping = {}
    for col in df.columns:
        norm = str(col).replace("\ufeff", "").strip().lower()
        mapping[col] = norm
    df.columns = [mapping[c] for c in df.columns]
    return df

def resolve_header(df: pd.DataFrame, required_name: str, aliases=None):
    """Find a column by normalized name or aliases; returns the normalized column name present in df."""
    aliases = aliases or []
    cols = list(df.columns)
    if required_name in cols:
        return required_name
    for a in aliases:
        if a in cols:
            return a
    return None

def _safe_str(val: object) -> str:
    # Convert value to string, treating NaN/None as empty string
    if pd.isna(val):
        return ""
    return str(val)

def restore_from_xlsx(s3, cfg, input_xlsx, output_xlsx, input_sheet=None, report_sheet="Report", dry_run=False):
    restored = []
    skipped = []

    if not os.path.exists(input_xlsx):
        raise FileNotFoundError(f"Input XLSX not found: {input_xlsx}")

    # Read Excel
    try:
        # Use first sheet by default when no sheet is specified
        sheet_arg = input_sheet if (input_sheet not in (None, "", "None")) else 0
        df = pd.read_excel(input_xlsx, sheet_name=sheet_arg, engine="openpyxl")
    except Exception as e:
        raise ValueError(
            f"Failed to read Excel file '{input_xlsx}' (sheet='{input_sheet or 'first'}'): {e}"
        )

    if df.empty or df.columns.size == 0:
        raise ValueError("Input Excel appears empty or has no header row.")

    # Normalize headers
    df = normalize_headers(df)

    # Resolve required headers
    key_col = resolve_header(df, "key")
    prev_col = resolve_header(df, "previousversionid", aliases=["versionid", "version", "prevversionid"])
    bucket_col = resolve_header(df, "bucket")

    if not key_col or not prev_col:
        present = ", ".join(df.columns)
        raise ValueError(
            "Input Excel must include 'Key' and 'PreviousVersionId' headers (case-insensitive). "
            "Accepted variants for PreviousVersionId: previousversionid, versionid, version, prevversionid. "
            f"Headers found: [{present}]"
        )

    # Iterate rows
    for idx, row in df.iterrows():
        key = _safe_str(row.get(key_col)).strip()
        prev_id = _safe_str(row.get(prev_col)).strip()
        row_bucket = _safe_str(row.get(bucket_col)).strip() if bucket_col else ""

        bucket = row_bucket or cfg.get("S3_BUCKET_NAME", "")

        if not bucket:
            skipped.append((key, "Skipped", "Missing bucket (not in .env and no Bucket column)"))
            continue
        if not key:
            skipped.append(("", "Skipped", "Missing Key"))
            continue
        if not prev_id:
            skipped.append((key, "Skipped", "Missing PreviousVersionId"))
            continue

        # Validate the version exists
        try:
            s3.head_object(Bucket=bucket, Key=key, VersionId=prev_id)
        except ClientError as e:
            skipped.append((key, "Skipped", f"NoSuchVersion or not accessible: {e}"))
            continue

        # Perform restore by copying specified version to same key
        try:
            if dry_run:
                status = "DryRun"
                detail = f"Would restore version {prev_id}"
            else:
                s3.copy_object(
                    Bucket=bucket,
                    Key=key,
                    CopySource={"Bucket": bucket, "Key": key, "VersionId": prev_id},
                )
                status = "Restored"
                detail = f"Version {prev_id}"
            restored.append((key, status, detail))
        except ClientError as e:
            skipped.append((key, "Skipped", f"Restore failed: {e}"))

    # Build DataFrame for report and write to Excel
    report_rows = restored + skipped
    report_df = pd.DataFrame(report_rows, columns=["Key", "Status", "Detail"])

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_xlsx) or ".", exist_ok=True)

    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        report_df.to_excel(writer, index=False, sheet_name=report_sheet)

        # Optional: add a small summary sheet
        summary = {
            "Restored": [len(restored)],
            "Skipped": [len(skipped)],
            "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "InputFile": [os.path.abspath(input_xlsx)],
        }
        pd.DataFrame(summary).to_excel(writer, index=False, sheet_name="Summary")

    return restored, skipped

def main():
    parser = argparse.ArgumentParser(description="Restore objects using PreviousVersionId (copy specific version over same key) from XLSX.")
    parser.add_argument("--input", default="restore_input.xlsx", help="Path to input XLSX (Key, PreviousVersionId[, Bucket])")
    parser.add_argument("--sheet", default=None, help="Worksheet name in input XLSX (default: first sheet)")
    parser.add_argument("--output", help="Path to output XLSX report (default: restore_report_<timestamp>.xlsx or OUTPUT_PATH/.env)")
    parser.add_argument("--report-sheet", default="Report", help="Worksheet name for the report (default: 'Report')")
    parser.add_argument("--dry-run", action="store_true", help="Validate and report without performing copy")
    args = parser.parse_args()

    cfg = load_env()
    s3 = get_s3_client(cfg)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build default output file path respecting OUTPUT_PATH if present
    if args.output:
        output_xlsx = args.output
    else:
        base = f"restore_report_{ts}.xlsx"
        output_base = cfg.get("OUTPUT_PATH")
        if output_base:
            output_xlsx = os.path.join(output_base, base)
        else:
            output_xlsx = base

    restored, skipped = restore_from_xlsx(
        s3=s3,
        cfg=cfg,
        input_xlsx=args.input,
        output_xlsx=output_xlsx,
        input_sheet=args.sheet,
        report_sheet=args.report_sheet,
        dry_run=args.dry_run,
    )

    print("Restore Summary:")
    print(f"  Restored ({len(restored)}): {[k for k, _, _ in restored]}")
    print(f"  Skipped  ({len(skipped)}):  {[k for k, _, _ in skipped]}")
    print(f"Report written to: {output_xlsx}")

if __name__ == "__main__":
    main()
