import pyodbc
import sys
import socket
from sqlalchemy import create_engine

print("🔍 Checking ODBC Drivers...")
drivers = pyodbc.drivers()
for d in drivers:
    print(f"   - {d}")

hostname = socket.gethostname()
servers_to_try = ['localhost', '.', hostname, f'{hostname}\\SQLEXPRESS']
database = 'MAS_CIS_DB'
driver = 'ODBC Driver 17 for SQL Server'

if driver not in drivers:
    print(f"\n⚠️  Warning: '{driver}' not found.")
    if drivers:
        driver = drivers[0]
        print(f"   Using fallback: '{driver}'")
    else:
        print("❌ No ODBC drivers found!")
        sys.exit(1)

print(f"\nUsing Driver: {driver}")

for server in servers_to_try:
    conn_str = f'mssql+pyodbc://@{server}/{database}?driver={driver}&trusted_connection=yes'
    print(f"\n🔌 Testing: {server}")
    
    try:
        engine = create_engine(conn_str)
        connection = engine.connect()
        print(f"   ✅ SUCCESS! Connected to {server}")
        connection.close()
        
        # Update .env with working server
        print(f"   📝 Updating .env with DB_SERVER={server}")
        # We can't easily update .env from here without parsing, but we can print instructions
        sys.exit(0)
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:100]}...") # Truncate error to avoid noise
