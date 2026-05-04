import sqlite3
conn = sqlite3.connect('reg.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(users)")
print('COLUMNS:')
for r in cur.fetchall():
    print(r)
cur.execute('SELECT username, role, is_active FROM users ORDER BY id')
print('\nUSERS:')
for r in cur.fetchall():
    print(r)
conn.close()