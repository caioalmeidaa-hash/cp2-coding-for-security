import os
from flask import Flask, request, jsonify
import mysql.connector
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

def db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST","localhost"), user=os.getenv("MYSQL_USER","root"),
        password=os.getenv("MYSQL_PASSWORD"), database=os.getenv("MYSQL_DATABASE","seguranca")
    )

def preparar():
    con=db(); cur=con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS analistas(
      id INT PRIMARY KEY, nome VARCHAR(60), nivel INT NOT NULL, api_key VARCHAR(100) UNIQUE NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS incidentes(
      id INT PRIMARY KEY, titulo VARCHAR(120), severidade VARCHAR(20), dono_id INT NOT NULL,
      FOREIGN KEY(dono_id) REFERENCES analistas(id))""")
    cur.executemany("INSERT IGNORE INTO analistas VALUES(%s,%s,%s,%s)",[
        (1,"Ana",5,"key-admin-lab"), (2,"Bruno",2,"key-bruno-lab")
    ])
    cur.executemany("INSERT IGNORE INTO incidentes VALUES(%s,%s,%s,%s)",[
        (1,"Brute force no servidor","alta",1),
        (2,"Phishing recebido","media",2),
        (3,"Tentativa de enumeração","baixa",2)
    ])
    con.commit();cur.close();con.close()

def autenticar():
    key=request.headers.get("X-API-Key")
    if not key: return None
    con=db();cur=con.cursor(dictionary=True)
    cur.execute("SELECT id,nome,nivel FROM analistas WHERE api_key=%s",(key,))
    u=cur.fetchone();cur.close();con.close()
    return u

@app.get("/api/incidentes")
def listar():
    u=autenticar()
    if not u:return jsonify(erro="não autenticado"),401
    con=db();cur=con.cursor(dictionary=True)
    cur.execute("SELECT id,titulo,severidade,dono_id FROM incidentes WHERE dono_id=%s",(u["id"],))
    dados=cur.fetchall();cur.close();con.close()
    return jsonify(dados)

@app.get("/api/incidentes/<int:incidente_id>")
def detalhe(incidente_id):
    u=autenticar()
    if not u:return jsonify(erro="não autenticado"),401
    con=db();cur=con.cursor(dictionary=True)
    cur.execute("SELECT id,titulo,severidade,dono_id FROM incidentes WHERE id=%s",(incidente_id,))
    inc=cur.fetchone();cur.close();con.close()
    if inc is None:return jsonify(erro="não encontrado"),404
    if inc["dono_id"] != u["id"] and u["nivel"] < 5:
        # Não devolvemos conteúdo do incidente de outro usuário.
        return jsonify(erro="acesso negado"),403
    return jsonify(inc)

@app.delete("/api/incidentes/<int:incidente_id>")
def remover(incidente_id):
    u=autenticar()
    if not u:return jsonify(erro="não autenticado"),401
    if u["nivel"] < 5:return jsonify(erro="acesso negado"),403
    con=db();cur=con.cursor()
    cur.execute("DELETE FROM incidentes WHERE id=%s",(incidente_id,))
    if cur.rowcount == 0:
        con.rollback();cur.close();con.close()
        return jsonify(erro="não encontrado"),404
    con.commit();cur.close();con.close()
    return jsonify(removido=incidente_id)

if __name__=="__main__":
    preparar()
    app.run(host="127.0.0.1",debug=False)
