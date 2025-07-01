import smtplib
import sqlalchemy as sa
from email.mime.multipart import MIMEMultipart

from espn_fantasy.utils.creds import get
from espn_fantasy.utils.database import read_oracle_query


def send_email(msg: MIMEMultipart) :
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(get("email_user"), get("email_pw"))
        server.send_message(msg)


def get_email_list(engine: sa.engine, is_test: bool=False) -> list:
    if is_test :
        clause = " AND is_test_email = 1"
    else :
        clause = ""

    df = read_oracle_query(
        f"""
        SELECT email
        FROM email_list
        WHERE is_active = 1
        {clause}
        """, engine
    )

    email_list = df["email"].to_list()
    email_list = ";".join(i for i in email_list)

    return email_list
