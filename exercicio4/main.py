import os
from datetime import datetime, timezone
import mysql.connector
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

USUARIOS = [
    (1, "ana", "ana@x.com", 5),
    (2, "bruno", "bruno@x.com", 2),
    (3, "caio", "caio@x.com", 1),
]

def db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "seguranca"),
    )

mongo = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
auditoria = mongo.cp2.auditoria

con = db()
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS usuarios(
    id INT PRIMARY KEY,
    nome VARCHAR(60) NOT NULL,
    email VARCHAR(100) NOT NULL,
    nivel_acesso INT NOT NULL
)""")
cur.executemany(
    """INSERT INTO usuarios(id,nome,email,nivel_acesso) VALUES(%s,%s,%s,%s)
       ON DUPLICATE KEY UPDATE nome=VALUES(nome), email=VALUES(email),
                               nivel_acesso=VALUES(nivel_acesso)""",
    USUARIOS,
)
con.commit()
cur.close()
con.close()
auditoria.delete_many({})

def alterar_nivel(admin_id, alvo_id, novo_nivel):
    con = db()
    cur = con.cursor(dictionary=True)
    anterior = None
    resultado = "RECUSADO"
    nome_alvo = None
    try:
        con.start_transaction()

        cur.execute("SELECT nome,nivel_acesso FROM usuarios WHERE id=%s FOR UPDATE", (admin_id,))
        admin = cur.fetchone()
        cur.execute("SELECT nome,nivel_acesso FROM usuarios WHERE id=%s FOR UPDATE", (alvo_id,))
        alvo = cur.fetchone()

        if alvo:
            anterior = alvo["nivel_acesso"]
            nome_alvo = alvo["nome"].capitalize()

        if not admin or admin["nivel_acesso"] < 5:
            raise PermissionError("admin sem privilégio")
        if admin_id == alvo_id:
            raise PermissionError("auto-promoção")
        if not alvo:
            raise LookupError("alvo inexistente")
        if not isinstance(novo_nivel, int) or not 0 <= novo_nivel <= 9:
            raise ValueError("nível inválido")

        cur.execute("UPDATE usuarios SET nivel_acesso=%s WHERE id=%s", (novo_nivel, alvo_id))
        con.commit()
        resultado = "OK"
        print(f"OK. commit. {nome_alvo}: {anterior} -> {novo_nivel}")
    except Exception as e:
        con.rollback()
        estado = f" {nome_alvo}: {anterior}" if nome_alvo else ""
        print(f"RECUSADO ({e}). rollback.{estado}")
    finally:
        auditoria.insert_one({
            "quem": admin_id,
            "alvo": alvo_id,
            "nivel_anterior": anterior,
            "nivel_novo": novo_nivel,
            "resultado": resultado,
            "timestamp": datetime.now(timezone.utc),
        })
        cur.close()
        con.close()

alterar_nivel(1, 2, 4)
alterar_nivel(2, 3, 5)
alterar_nivel(1, 1, 9)
alterar_nivel(1, 99, 3)

total = auditoria.count_documents({})
recusadas = auditoria.count_documents({"resultado": "RECUSADO"})
sucessos = total - recusadas
print(f"Trilha de auditoria ao final: {total} documentos ({sucessos} sucesso, {recusadas} recusas)")
print(f'db.auditoria.count_documents({{"resultado":"RECUSADO"}}) -> {recusadas}')
mongo.close()
