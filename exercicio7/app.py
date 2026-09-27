import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask,render_template,request
from pymongo import MongoClient
from markupsafe import Markup
app=Flask(__name__)
mongo=MongoClient(os.getenv("MONGO_URI","mongodb://localhost:27017/"))
col=mongo.cp2.incidentes_xss
p1="<script>alert('xss1')</script>"
p2='x" onerror="alert(\'xss2\')'
col.delete_many({});col.insert_many([{"titulo":p1,"ativo":"srv-01"},{"titulo":"Teste atributo","ativo":p2}])

@app.after_request
def headers(r):
 r.headers["Content-Security-Policy"]="default-src 'self'"
 return r

@app.get("/dashboard")
def dashboard():
 return render_template("dashboard.html",incidentes=list(col.find({},{"_id":0})))

@app.get("/dashboard-inseguro")
def inseguro():
 # Somente comparação local solicitada pelo exercício.
 linhas="".join(f'<tr><td>{x["titulo"]}</td><td><img src="/icone.png" alt="{x["ativo"]}"></td></tr>' for x in col.find())
 return "<h1>INSEGURO - LAB LOCAL</h1><table>"+linhas+"</table>"
if __name__=="__main__":app.run(debug=False)
