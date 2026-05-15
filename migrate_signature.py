import sqlite3

def migrate():
    conn = sqlite3.connect('kicau.db')
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN tanda_tangan TEXT')
        print("Column 'tanda_tangan' added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("Column 'tanda_tangan' already exists.")
        else:
            print(f"Error: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
