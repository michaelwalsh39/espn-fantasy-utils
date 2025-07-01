from setuptools import setup, find_packages

setup(
    name="espn-fantasy-utils",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas==2.3.0",
        "numpy==2.3.1",
        "awswrangler==3.12.1",
        "oracledb==3.2.0",
        "sqlalchemy==2.0.41",
        "boto3==1.38.45"
    ],
)
