import sqlalchemy as sa
import pandas as pd
import pathlib

from espn_fantasy.utils.creds import get
from espn_fantasy.utils.aws import fetch_and_unzip_s3
from espn_fantasy.utils.os import get_os


INSTANT_CLIENT_VERSIONS = {
    "macos-arm64": "instantclient_23_3",
    "windows-x64": "instantclient_23_8",
    "linux-x86_64": "instantclient_23_8"
}

def create_engine() -> sa.engine :
    base_dir = pathlib.Path.cwd()
    
    # first check for wallet folder
    folder = base_dir / "wallet"
    if not folder.is_dir() :
        print(f"Wallet credentials don't exist on your local machine! Downloading them from s3.")
        fetch_and_unzip_s3(s3_path="creds/wallet.zip")
    
    # then check for instant client
    os = get_os()
    instant_client = INSTANT_CLIENT_VERSIONS.get(os)

    folder = base_dir / instant_client
    if not folder.is_dir() :
        print(f"Instantclient credentials don't exist on your local machine! Downloading them from s3.")
        s3_path = f"instantclient/{os}/{instant_client}.zip"
        fetch_and_unzip_s3(s3_path=s3_path)

    engine = sa.create_engine(
        f"oracle+oracledb://{get('oracle_user')}:{get('oracle_pw')}@{get('oracle_dsn')}",
        thick_mode={
            "config_dir": str(base_dir / "wallet"),
            "lib_dir": str(base_dir / instant_client),
        }
    )

    return engine


def read_oracle_query(query: str, engine: sa.engine, **kwargs) -> pd.DataFrame :
    df = pd.read_sql(
        query, engine, params=kwargs
    )

    return df


def read_sql_file(filename):
    base_dir = pathlib.Path.cwd()

    with open(f"{base_dir}/espn_fantasy/sql/queries/{filename}.sql", "r") as f:
        return f.read()
