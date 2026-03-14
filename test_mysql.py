import pymysql

conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='1234',
    charset='utf8mb4'
)
cursor = conn.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS irrigation_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.execute("USE irrigation_db")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        prenom     VARCHAR(100) NOT NULL,
        nom        VARCHAR(100) NOT NULL,
        dob        DATE NOT NULL,
        telephone  VARCHAR(20),
        email      VARCHAR(150) NOT NULL UNIQUE,
        password   VARCHAR(64)  NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.commit()
conn.close()
print("✅ Table 'users' créée avec succès !")