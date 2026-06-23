import psycopg2

try:
    conn = psycopg2.connect(
        dbname="db_sof",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432",
        sslmode="disable"  # 👈 Cambiado a disable para desarrollo local
    )
    print("✅ Conexión exitosa")
    conn.close()
except Exception as e:
    print("❌ Error de conexión:", e)