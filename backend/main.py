from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

app = FastAPI()

DB_FILE = "db_usuarios.json"

class DadosUsuarios(BaseModel):
    username = str
    blob_criptografado: str

def carregar_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open (DB_FILE, "r") as f:
        return json.load(f)

def salvar_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

@app.get("/")
def home():
    return {"status": "SecurePass Server Online"}

@app.get("/obter/{username}")
def obter_dados(username: str):
    db = carregar_db()
    if username in db:
        return {"blob": db[username]}
    return {"blob": ""}

@app.get("/Salvar")
def salvar_dados(dados: DadosUsuarios):
    db = carregar_db()
    db[dados.username] = dados.blob_criptografado
    salvar_dados(db)
    return {"status": "Sucesso", "mensagem": "Dados sincronizados na nuvem"}