from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DIRETORIO_ATUAL, "db_usuarios.json")

def carregar_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def salvar_db(db):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(db, f)
    except Exception as e:
        print(f"Erro ao salvar: {e}")

@app.route('/')
def home():
    return jsonify({"status": "SecurePass (Flask) Online", "db_local": DB_FILE})

@app.route('/obter/<username>', methods=['GET'])
def obter_dados(username):
    db = carregar_db()
    if username in db:
        return jsonify({"blob": db[username]})
    return jsonify({"blob": ""})

@app.route('/salvar', methods=['POST'])
def salvar_dados():
    dados = request.get_json()
    
    if not dados:
        return jsonify({"erro": "Sem dados"}), 400
        
    usuario = dados.get("username")
    blob = dados.get("blob_criptografado")
    
    if not usuario or not blob:
        return jsonify({"erro": "Dados incompletos"}), 400

    db = carregar_db()
    db[usuario] = blob
    salvar_db(db)
    return jsonify({"status": "Sucesso", "mensagem": "Dados sincronizados via Flask"})