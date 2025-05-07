import psycopg2
print(f"Connecting to the database...")
conn = psycopg2.connect(
    database = "taippa",
    host="magmostafa-4523.postgres.pythonanywhere-services.com",
    user="super",
    password="drowsapp_2025",
    port="14523"
)
cursor = conn.cursor()
cursor.execute("INSERT INTO dummy VALUES ('test');")
conn.commit()
cursor.close()
conn.close()
