import psycopg2

try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="Software_1_2_3_4",
        host="db.pqqvoeybcarrrechvxzu.supabase.co",
        port="5432",
        sslmode="require"
    )
    print("✅ Conexión exitosa")
    conn.close()
except Exception as e:
    print("❌ Error de conexión:", e)
