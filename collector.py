from pyarrow import csv,parquet
import boto3
import os
import pyarrow as pa
import csv as std_csv
import requests
import zipfile
import shutil
from botocore.exceptions import ClientError

BUCKET = "bronze"
PREFIX = "bts_ontime"

def build_paths(year, month):
    name = f"{PREFIX}_{year}_{month:02d}"
    zip_path     = f"data/landing/{PREFIX}/{name}.zip"
    csv_path     = f"data/landing/{PREFIX}/{name}.csv"
    parquet_path     = f"data/bronze_local/{name}.parquet"
    object_key = f"{PREFIX}/year={year}/month={month:02d}/{name}.parquet"
    return zip_path, csv_path, parquet_path, object_key

def convert_to_parquet(csv_path, parquet_path):
        with open(csv_path, newline="") as file:
           header = next(std_csv.reader(file))
        columns = [column for column in header if column != '']
         
        convert_options = csv.ConvertOptions(column_types = {column : pa.string() for column in columns},
                                             include_columns = columns)

        flights_table = csv.read_csv(csv_path, convert_options = convert_options)    

        with open(csv_path, "rb") as csv_file:
            csv_row_count  = sum (1 for _ in csv_file) -1

        if flights_table.num_rows != csv_row_count:
            raise ValueError(f"Row count mismatch: CSV {csv_row_count}, Parquet {flights_table.num_rows}")

        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        parquet.write_table(flights_table, parquet_path)

        print("Successful")


def download_zip(year, month, zip_path):
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with requests.get(f"https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip", stream=True, timeout=(10, 60)) as response:
     response.raise_for_status()
     with open(zip_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            file.write(chunk)

def extract_csv(zip_path, csv_path):
    with zipfile.ZipFile(zip_path) as zip_file:
        csv_members = [name for name in zip_file.namelist() if name.lower().endswith(".csv")]
        if len(csv_members) != 1:
            raise ValueError(f"Expected exactly one CSV in the zip, found: {csv_members}")

        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        with zip_file.open(csv_members[0]) as source_file, open(csv_path, "wb") as target_file:
            shutil.copyfileobj(source_file, target_file)

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    )

def object_exists(bucket, object_key):
    s3_client = get_s3_client()
    try:
        s3_client.head_object(Bucket=bucket, Key=object_key)
        return True
    except ClientError as error:
        if error.response["Error"]["Code"] == "404":
            return False
        raise 

   
def upload_file(local_path, bucket, object_key):
    """Upload a local file to an S3 bucket (MinIO).

    :param local_path: path of the file to upload
    :param bucket: target bucket
    :param object_key: object name in the bucket
    """
    s3_client = get_s3_client()
    s3_client.upload_file(local_path, bucket, object_key)

def collect_month(year, month, force=False):
    zip_path ,csv_path, parquet_path, object_key = build_paths(year, month)

    if not force and object_exists(BUCKET, object_key):
        print(f"{year}-{month:02d} already in MinIO, skipping")
        return

    download_zip(year, month, zip_path)
    extract_csv(zip_path, csv_path)
    convert_to_parquet(csv_path, parquet_path)
    upload_file(parquet_path, BUCKET, object_key)

    if not object_exists(BUCKET, object_key):
        raise RuntimeError(f"Upload check failed: {object_key}")

    os.remove(zip_path)
    os.remove(csv_path)

    print(f"{year}-{month:02d} loaded")

def main():
        for year, month in [
        (2023, 8)
    ]:
         collect_month(year, month)
if __name__ == "__main__":
    main()