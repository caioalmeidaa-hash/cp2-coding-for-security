import os
from dotenv import load_dotenv
load_dotenv()

import mysql.connector
from pymongo import MongoClient

def mysql_conn():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST","localhost"), user=os.getenv("MYSQL_USER","root"),
        password=os.getenv("MYSQL_PASSWORD"), database=os.getenv("MYSQL_DATABASE","seguranca")
    )

con = mysql_conn()
cur = con.cursor(dictionary=True)
cur.execute("""CREATE TABLE IF NOT EXISTS ativos(
 id INT PRIMARY KEY, nome VARCHAR(80), ip VARCHAR(45) UNIQUE,
 criticidade ENUM('baixa','media','alta'))""")
cur.execute("""CREATE TABLE IF NOT EXISTS alertas(
 id INT PRIMARY KEY, ativo_id INT, tipo VARCHAR(50), severidade VARCHAR(20),
 criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(ativo_id) REFERENCES ativos(id))""")
cur.executemany("INSERT IGNORE INTO ativos(id,nome,ip,criticidade) VALUES(%s,%s,%s,%s)",
 [(1,"SRV-WEB01","192.168.1.10","alta"),(2,"PC-RH03","192.168.1.45","baixa")])
cur.executemany("INSERT IGNORE INTO alertas(id,ativo_id,tipo,severidade) VALUES(%s,%s,%s,%s)",
 [(1,1,"BRUTE_FORCE","critica"),(2,1,"PORT_SCAN","alta"),(3,2,"XSS","media")])
con.commit()

cur.execute("""SELECT al.tipo, al.severidade, a.nome, a.ip, a.criticidade
 FROM alertas al JOIN ativos a ON a.id=al.ativo_id""")
rows = cur.fetchall()
docs = [{"tipo":r["tipo"],"severidade":r["severidade"],
         "ativo":{"nome":r["nome"],"ip":r["ip"],"criticidade":r["criticidade"]}} for r in rows]

mongo = MongoClient(os.getenv("MONGO_URI","mongodb://localhost:27017/"))
col = mongo.cp2.alertas
col.delete_many({})
if docs: col.insert_many(docs)

cur.execute("SELECT COUNT(*) total FROM alertas")
n_sql = cur.fetchone()["total"]
n_mongo = col.count_documents({})
print(f"MySQL: {n_sql} alertas | MongoDB: {n_mongo} documentos ->", "MIGRAÇÃO ÍNTEGRA" if n_sql==n_mongo else "ERRO")

n_alta = col.count_documents({"ativo.criticidade":"alta"})
print(f'Consulta sem JOIN: db.alertas.find({{"ativo.criticidade":"alta"}}) -> {n_alta} documentos')

print("Ganho: leitura do alerta com o ativo sem JOIN.")
print("Perda: há duplicação; renomear um ativo exige atualizar vários documentos.")
cur.close(); con.close(); mongo.close()
