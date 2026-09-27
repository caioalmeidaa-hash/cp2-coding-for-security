import os
from flask import Flask, request, jsonify
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
COLUNAS = {"data": "criado_em", "sev": "severidade", "ip": "ip_origem"}
ORDEM = {"asc": "ASC", "desc": "DESC"}

def db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "seguranca"),
    )

def preparar():
    con = db(); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS eventos(
        id INT AUTO_INCREMENT PRIMARY KEY,
        ip_origem VARCHAR(45) NOT NULL,
        severidade VARCHAR(20) NOT NULL,
        descricao VARCHAR(150) NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("SELECT COUNT(*) FROM eventos")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO eventos(ip_origem,severidade,descricao) VALUES(%s,%s,%s)",
            [
                ("10.0.0.5","alta","Múltiplas falhas de login"),
                ("192.168.1.22","media","Varredura de portas"),
                ("172.16.0.8","baixa","Acesso fora do horário"),
            ],
        )
    con.commit(); cur.close(); con.close()

@app.get("/api/eventos")
def listar():
    campo = request.args.get("ordenar_por", "data")
    ordem = request.args.get("ordem", "asc")
    if campo not in COLUNAS:
        return jsonify(erro="campo de ordenação inválido"), 400
    if ordem not in ORDEM:
        return jsonify(erro="ordem deve ser asc ou desc"), 400
    try:
        tamanho = int(request.args.get("tamanho", "20"))
    except ValueError:
        return jsonify(erro="tamanho deve ser inteiro"), 400
    if tamanho < 1:
        return jsonify(erro="tamanho deve ser maior que zero"), 400
    tamanho = min(tamanho, 100)

    con = db(); cur = con.cursor(dictionary=True)
    # Nome de coluna e ASC/DESC são identificadores SQL, não dados — o driver
    # não sabe colocar aspas neles com segurança, então %s não os protege ali.
    # LIMIT recebe um valor (um número), por isso %s funciona normalmente nele.
    # Por isso identificador só pode vir de whitelist fechada; dado pode vir do usuário via %s.
    sql = f"SELECT id,ip_origem,severidade,descricao,criado_em FROM eventos ORDER BY {COLUNAS[campo]} {ORDEM[ordem]} LIMIT %s"
    cur.execute(sql, (tamanho,))
    dados = cur.fetchall()
    cur.close(); con.close()
    return jsonify(dados)

if __name__ == "__main__":
    preparar()
    app.run(host="127.0.0.1", debug=False)
