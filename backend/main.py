from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

app = FastAPI()

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DIRETORIO_ATUAL, "db_usuarios.json")

class DadosUsuario(BaseModel):
    username: str
    blob_criptografado: str

def carregar_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def salvar_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

@app.get("/")
def home():
    return {"status": "SecurePass Server Online", "db_path": DB_FILE}

@app.get("/obter/{username}")
def obter_dados(username: str):
    db = carregar_db()
    if username in db:
        return {"blob": db[username]}
    return {"blob": ""}

@app.post("/salvar")
def salvar_dados(dados: DadosUsuario):
    db = carregar_db()
    db[dados.username] = dados.blob_criptografado
    salvar_db(db)
    return {"status": "Sucesso", "mensagem": "Dados sincronizados na nuvem"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)