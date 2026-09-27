import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask,request,jsonify
from pymongo import MongoClient
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score,recall_score,f1_score,confusion_matrix
from datetime import datetime,timezone
import numpy as np
app=Flask(__name__)
rng=np.random.default_rng(42)
X=[];y=[]
for _ in range(500):
 f=[int(rng.integers(0,20)),int(rng.integers(1,15)),int(rng.integers(500,120000)),int(rng.integers(0,24))]
 X.append(f);y.append(int(f[0]>=8 or f[1]>=6 or f[2]>=60000))
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
modelo=RandomForestClassifier(n_estimators=150,random_state=42).fit(Xtr,ytr)
pred=modelo.predict(Xte)
metricas={"precisao":round(precision_score(yte,pred),3),"recall":round(recall_score(yte,pred),3),
 "f1":round(f1_score(yte,pred),3),"matriz":confusion_matrix(yte,pred).tolist(),
 "aviso":"A acurácia foi omitida porque pode esconder desempenho ruim em classes desbalanceadas."}
mongo=MongoClient(os.getenv("MONGO_URI","mongodb://localhost:27017/"));col=mongo.cp2.previsoes
col.delete_many({})

@app.post("/api/triagem")
def triagem():
 data=request.get_json(silent=True)
 if not data or "features" not in data:return jsonify(erro="corpo JSON com features é obrigatório"),400
 f=data["features"]
 if not isinstance(f,list):return jsonify(erro="features deve ser uma lista"),400
 if len(f)!=4:return jsonify(erro=f"esperadas 4 features, recebidas {len(f)}"),400
 if any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in f):return jsonify(erro="features devem ser numéricas"),400
 p=int(modelo.predict([f])[0]);conf=float(max(modelo.predict_proba([f])[0]))
 saida={"risco":"alto" if p else "baixo","confianca":round(conf,3)}
 col.insert_one({"entrada":f,"saida":saida["risco"],"confianca":saida["confianca"],"timestamp":datetime.now(timezone.utc)})
 return jsonify(saida)
@app.get("/api/modelo/metricas")
def met():return jsonify(metricas)
if __name__=="__main__":app.run(debug=False)
