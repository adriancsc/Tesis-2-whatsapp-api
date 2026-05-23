import os

log_dir = "logs"
files = sorted([f for f in os.listdir(log_dir) if f.startswith("mas_cis_")], reverse=True)
if not files:
    print("No logs found")
else:
    latest_log = os.path.join(log_dir, files[0])
    print(f"Reading {latest_log}...")
    try:
        with open(latest_log, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        with open("latest_log_content.txt", "w", encoding="utf-8") as out:
            out.write("".join(lines[-200:])) # Last 200 lines
            
        print("Log extracted to latest_log_content.txt")
    except Exception as e:
        print(f"Error reading log: {e}")
