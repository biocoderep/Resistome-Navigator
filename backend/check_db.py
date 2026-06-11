import sqlite3

conn = sqlite3.connect('amr_mvp.db')
tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print(f"Tables in amr_mvp.db: {tables}")
conn.close()
