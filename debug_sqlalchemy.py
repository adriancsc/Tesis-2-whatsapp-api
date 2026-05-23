from sqlalchemy import create_engine
import urllib.parse
import sys

server = 'LAPTOP-QUKF9S4T'
database = 'MAS_CIS_DB'
driver = 'ODBC Driver 17 for SQL Server'
port = 1433

print(f"TESTING DRIVER: {driver}")

try:
    connection_string = f"DRIVER={{{driver}}};SERVER={server},{port};DATABASE={database};Trusted_Connection=yes;"
    params = urllib.parse.quote_plus(connection_string)
    url = f"mssql+pyodbc:///?odbc_connect={params}"
    
    print(f"URL: {url}")
    engine = create_engine(url)
    conn = engine.connect()
    print("SUCCESS")
    conn.close()
except Exception as e:
    print(f"FAILED: {e}")
