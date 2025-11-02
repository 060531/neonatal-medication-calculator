# analyze_logs.py

import os
from sqlalchemy import create_engine, text
import pandas as pd

# 1) กำหนด path ไปยังไฟล์ app.db
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'app.db')
DB_URI   = f"sqlite:///{DB_PATH}"

# 2) สร้าง SQLAlchemy engine
engine = create_engine(DB_URI, echo=False, future=True)

# 3) ตัวอย่าง: อ่านข้อมูลทั้งตาราง access_logs เป็น DataFrame
df_logs = pd.read_sql_table(
    table_name='access_logs',
    con=engine
)

print("=== ตัวอย่าง 10 แถวแรก ===")
print(df_logs.head(10))

# 4) สรุปจำนวนเข้าชม (visits) ตามวัน
#    แปลงคอลัมน์ timestamp เป็น datetime ก่อน
df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
df_logs['day']       = df_logs['timestamp'].dt.date

summary = (
    df_logs
    .groupby('day')
    .size()
    .reset_index(name='visits')
    .sort_values(by='day', ascending=False)
)

print("\n=== Visits per day (ย้อนหลัง 30 วัน) ===")
print(summary.head(30).to_string(index=False))

# 5) (ถ้าต้องการ) รัน query ตรงด้วย text SQL
sql = text("""
    SELECT endpoint, COUNT(*) AS cnt
    FROM access_logs
    GROUP BY endpoint
    ORDER BY cnt DESC
    LIMIT 10
""")
df_top = pd.read_sql_query(sql, engine)
print("\n=== Top 10 endpoints by request count ===")
print(df_top.to_string(index=False))
