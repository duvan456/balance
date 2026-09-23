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


def execute_query(query, params=None):
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return rows
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def fetch_rows(query):
    return execute_query(query)