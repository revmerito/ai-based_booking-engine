
import sqlite3
import os

db_path = "d:/booking engine/ai-based-booking-engine-for-hotels-/backend/app.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(integration_settings)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    conn.close()
else:
    print("Database not found at", db_path)
