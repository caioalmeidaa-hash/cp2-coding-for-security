import os
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import random

random.seed(42)
client = MongoClient(os.getenv("MONGO_URI","mongodb://localhost:27017/"))
eventos = client.cp2.eventos
eventos.delete_many({})
eventos.create_index("timestamp", expireAfterSeconds=604800)

agora = datetime.now(timezone.utc)
docs=[]
for i in range(200):
    docs.append({"tipo":"FAIL","timestamp":agora-timedelta(seconds=random.randint(0,86399))})
eventos.insert_many(docs)

pipeline=[
 {"$match":{"tipo":"FAIL","timestamp":{"$gte":agora-timedelta(hours=24)}}},
 {"$group":{"_id":{"$hour":"$timestamp"},"total":{"$sum":1}}},
 {"$sort":{"_id":1}}
]
resultado=list(eventos.aggregate(pipeline))
print("=== Falhas por hora (últimas 24h) ===")
for r in resultado:
    print(f'{r["_id"]:02d}h | {"█"*r["total"]} {r["total"]}')
pico=max(resultado,key=lambda x:x["total"])
print(f'Hora de pico: {pico["_id"]:02d}h ({pico["total"]} falhas)')
print("Índice TTL ativo: eventos com mais de 7 dias serão removidos automaticamente.")
print("TTL também reduz exposição: dados sensíveis antigos deixam de permanecer disponíveis indefinidamente.")
client.close()
