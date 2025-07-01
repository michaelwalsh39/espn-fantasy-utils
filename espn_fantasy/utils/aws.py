import boto3
import pathlib
import zipfile

from espn_fantasy.utils.creds import get


BUCKET_NAME = "espn-fantasy"

def fetch_and_unzip_s3(s3_path: str) :
    # set path to download credentials into
    download_name = s3_path.split("/")[-1]
    base_dir = pathlib.Path.cwd()
    zip_path = base_dir / download_name

    s3 = boto3.client(
        "s3",
        aws_access_key_id=get("aws_access_key"),
        aws_secret_access_key=get("aws_access_secret")        
    )

    print(f"Downloading {s3_path}...")
    s3.download_file(BUCKET_NAME, s3_path, str(zip_path))
    print("Download complete.")

    print(f"Unzipping to {base_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            zip_ref.extract(member, base_dir)

    zip_path.unlink()
    print("Unzipped and cleaned up.")    
