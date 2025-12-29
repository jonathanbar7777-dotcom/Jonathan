import mysql.connector

def reset_table():
    print("Connecting to database...")
    try:
        # התחברות ישירה עם הפרטים שהופיעו בקוד שלך
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Jb240108",
            database="mysql"
        )
        
        cursor = conn.cursor()
        
        # 1. מחיקת הטבלה הישנה
        print("Dropping old 'clients' table...")
        cursor.execute("DROP TABLE IF EXISTS clients")
        
        # 2. מחיקת טבלת הקבצים (למקרה שצריך לרענן גם אותה)
        # cursor.execute("DROP TABLE IF EXISTS files") 
        
        conn.commit()
        print("✅ Success! The table 'clients' has been deleted.")
        print("Now run your server or create_tables.py to recreate it with the new structure.")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")

if __name__ == "__main__":
    reset_table()