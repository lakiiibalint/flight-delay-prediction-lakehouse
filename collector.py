from pyarrow import csv,parquet
import logging
import boto3
import os
from botocore.exceptions import ClientError
import pyarrow as pa
import csv as std_csv

source = "data/landing/bts_ontime/bts_ontime_2026_07.csv"
output = "data/bronze_local/bts_ontime_2026_07.parquet"
object_key = "bts_ontime/year=2026/month=07/bts_ontime_2026_07.parquet"

# Remove the unwanted last row from the data
header = next(std_csv.reader(open(source)))
header = [column for column in header if column != '']


convert_options = csv.ConvertOptions(column_types = {column: pa.string() for column in header},  include_columns=header)

table = csv.read_csv(source, convert_options=convert_options)

os.makedirs(os.path.dirname(output), exist_ok=True)
parquet.write_table(table, output)

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client(
        "s3",
        endpoint_url = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id = os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key = os.environ["MINIO_ROOT_PASSWORD"]
    )
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

print(upload_file(output, "bronze", object_key))



