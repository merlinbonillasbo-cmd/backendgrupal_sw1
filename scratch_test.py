import psycopg2
import requests

def test():
    try:
        conn = psycopg2.connect(
            dbname="db_sof",
            user="postgres",
            password="1234",
            host="localhost",
            port="5432"
        )
        print("Connected to database successfully!")
        
        cur = conn.cursor()
        
        # 1. Fetch latest transcription
        cur.execute("SELECT id, texto_generado FROM transcripcion ORDER BY fecha_creado DESC LIMIT 1;")
        row = cur.fetchone()
        if not row:
            print("No transcriptions found in database!")
            return
        
        t_id, texto = row
        print(f"Latest transcription ID: {t_id}")
        print(f"Text snippet: {texto[:100]}...")
        
        # 2. Test Ollama embedding call
        print("Testing Ollama embedding call...")
        url = "http://localhost:11434/api/embeddings"
        payload = {
            "model": "nomic-embed-text",
            "prompt": "Hola mundo"
        }
        res = requests.post(url, json=payload, timeout=10)
        embedding = res.json()["embedding"]
        print(f"Embedding length: {len(embedding)}")
        
        # 3. Try to split and insert a fragment
        print("Attempting to insert a test fragment...")
        cur.execute("DELETE FROM fragmento_transcripcion WHERE id_transcripcion = %s;", (t_id,))
        
        vector_str = f"[{','.join(map(str, embedding))}]"
        cur.execute(
            """
            INSERT INTO fragmento_transcripcion (id_transcripcion, indice_fragmento, texto_fragmento, embedding)
            VALUES (%s, %s, %s, %s::vector);
            """,
            (t_id, 0, "Fragmento de prueba", vector_str)
        )
        conn.commit()
        print("Successfully inserted fragment into database!")
        
        # Verify
        cur.execute("SELECT count(*) FROM fragmento_transcripcion WHERE id_transcripcion = %s;", (t_id,))
        count = cur.fetchone()[0]
        print(f"Count of fragments in db for transcript {t_id}: {count}")
        
        conn.close()
    except Exception as e:
        print("Error during database test execution:", e)

if __name__ == "__main__":
    test()
