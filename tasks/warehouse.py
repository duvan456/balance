import pyodbc
from django.conf import settings


def get_connection():
    connection_string = (
        f"DRIVER={{{settings.FABRIC_WAREHOUSE_ODBC_DRIVER}}};"
        f"SERVER={settings.FABRIC_WAREHOUSE_SERVER};"
        f"DATABASE={settings.FABRIC_WAREHOUSE_DATABASE};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        f"Authentication={settings.FABRIC_WAREHOUSE_AUTHENTICATION};"
    )
    return pyodbc.connect(connection_string, timeout=15)


def fetch_rows(query):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]