import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import base64
import random
import string
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# --- CONFIGURAÇÃO DA NUVEM ---
SERVER_URL = "http://127.0.0.1:8000"

# --- VARIÁVEIS GLOBAIS ---
sessao_atual = {
    "usuario": None,
    "chave": None,
    "dados": []
}

# ============ Configurações de Tema ============
tema_atual = {
    "bg": "#2b2b2b", "fg": "#e0e0e0", "entry_bg": "#424242", "entry_fg": "#ffffff",
    "btn_bg": "#2b83a1", "btn_fg": "#ffffff", "btn_hover": "#0b495e",
    "frame_bg": "#424242", "highlight": "#0D47A1"
}

# ============ Funções de Criptografia & Nuvem ============
def derivar_chave(senha):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=b'salt_fixo_por_enquanto', iterations=100000,
    )
    return Fernet(base64.urlsafe_b64encode(kdf.derive(senha.encode())))

def sincronizar_upload():
    if not sessao_atual["usuario"] or not sessao_atual["chave"]:
        return

    try:
        dados_json = json.dumps(sessao_atual["dados"])
        blob_criptografado = sessao_atual["chave"].encrypt(dados_json.encode()).decode()
        payload = {"username": sessao_atual["usuario"], "blob_criptografado": blob_criptografado}
        
        res = requests.post(f"{SERVER_URL}/salvar", json=payload)
        if res.status_code == 200:
            print("Sincronizado com sucesso!")
        else:
            messagebox.showerror("Erro Cloud", "Falha ao salvar na nuvem.")
    except Exception as e:
        messagebox.showerror("Erro de Conexão", f"Servidor offline: {e}")

def carregar_da_nuvem(usuario, senha_mestra):
    try:
        res = requests.get(f"{SERVER_URL}/obter/{usuario}")
        if res.status_code == 200:
            resposta = res.json()
            blob = resposta.get("blob", "")
            chave_temp = derivar_chave(senha_mestra)
            
            if blob:
                try:
                    json_decifrado = chave_temp.decrypt(blob.encode()).decode()
                    dados = json.loads(json_decifrado)
                    return True, chave_temp, dados
                except:
                    return False, None, [] 
            else:
                return True, chave_temp, [] 
        return False, None, []
    except Exception as e:
        messagebox.showerror("Erro", f"Erro de conexão: {e}")
        return False, None, []

# ============ Funções do Gerador de Senhas ============
def gerar_senha_segura(tamanho=16):
    caracteres = string.ascii_letters + string.digits + string.punctuation
    senha = ''.join(random.choice(caracteres) for _ in range(tamanho))
    return senha

def inserir_senha_gerada():
    nova_senha = gerar_senha_segura()
    campo_senha.delete(0, tk.END)
    campo_senha.insert(0, nova_senha)

# ============ Funções da Interface ============
def acao_login():
    user = ent_login_user.get()
    senha = ent_login_pass.get()
    
    if not user or not senha:
        messagebox.showwarning("Aviso", "Preencha usuário e senha!")
        return
        
    sucesso, chave, dados = carregar_da_nuvem(user, senha)
    
    if sucesso:
        sessao_atual["usuario"] = user
        sessao_atual["chave"] = chave
        sessao_atual["dados"] = dados
        janela_login.destroy()
        abrir_janela_principal()
    else:
        messagebox.showerror("Login Falhou", "Senha incorreta ou erro de conexão.")

def salvar_senha_nova():
    servico = entrada_servico.get()
    usuario = entrada_usuario.get()
    senha = campo_senha.get()
    
    if not servico or not usuario or not senha:
        messagebox.showwarning("Campos Vazios", "Preencha todos os campos!")
        return
    
    sessao_atual["dados"].append({"servico": servico, "usuario": usuario, "senha": senha})
    
    entrada_servico.delete(0, tk.END)
    entrada_usuario.delete(0, tk.END)
    campo_senha.delete(0, tk.END)
    
    sincronizar_upload()
    messagebox.showinfo("Sucesso", "Senha salva e sincronizada!")
    atualizar_lista()

def atualizar_lista():
    for item in tree.get_children():
        tree.delete(item)
    filtro = entrada_busca.get().lower()
    for item in sessao_atual["dados"]:
        if filtro in item["servico"].lower():
            tree.insert("", "end", values=(item["servico"], item["usuario"], "••••••••"))

def copiar_senha_selecionada():
    selecionado = tree.focus()
    if selecionado:
        item_tree = tree.item(selecionado)['values']
        servico, usuario = item_tree[0], item_tree[1]
        
        for dado in sessao_atual["dados"]:
            if dado["servico"] == servico and dado["usuario"] == usuario:
                janela_principal.clipboard_clear()
                janela_principal.clipboard_append(dado["senha"])
                messagebox.showinfo("Copiado", "Senha copiada para área de transferência!")
                return

# ============ Janela Principal ============
def abrir_janela_principal():
    global janela_principal, entrada_servico, entrada_usuario, campo_senha, tree, entrada_busca
    
    janela_principal = tk.Tk()
    janela_principal.title(f"SecurePass Cloud - {sessao_atual['usuario']}")
    janela_principal.geometry("650x500")
    janela_principal.config(bg=tema_atual["bg"])
    
    # --- Área de Cadastro ---
    frame_form = tk.Frame(janela_principal, bg=tema_atual["bg"], pady=10)
    frame_form.pack(fill="x", padx=10)
    
    # Grid Layout para o formulário
    tk.Label(frame_form, text="Serviço:", bg=tema_atual["bg"], fg=tema_atual["fg"]).grid(row=0, column=0, sticky="w")
    entrada_servico = tk.Entry(frame_form, width=20, bg=tema_atual["entry_bg"], fg=tema_atual["entry_fg"])
    entrada_servico.grid(row=0, column=1, padx=5)
    
    tk.Label(frame_form, text="User:", bg=tema_atual["bg"], fg=tema_atual["fg"]).grid(row=0, column=2, sticky="w")
    entrada_usuario = tk.Entry(frame_form, width=20, bg=tema_atual["entry_bg"], fg=tema_atual["entry_fg"])
    entrada_usuario.grid(row=0, column=3, padx=5)
    
    tk.Label(frame_form, text="Senha:", bg=tema_atual["bg"], fg=tema_atual["fg"]).grid(row=1, column=0, sticky="w", pady=10)
    campo_senha = tk.Entry(frame_form, width=20, bg=tema_atual["entry_bg"], fg=tema_atual["entry_fg"])
    campo_senha.grid(row=1, column=1, padx=5, pady=10)
    
    # Botão GERAR (O retorno do rei)
    btn_gerar = tk.Button(frame_form, text="🎲 Gerar", command=inserir_senha_gerada, 
                         bg="#FF9800", fg="white", font=("Arial", 8, "bold"), width=10)
    btn_gerar.grid(row=1, column=2, sticky="w", padx=5)
    
    # Botão SALVAR
    btn_salvar = tk.Button(frame_form, text="Salvar na Nuvem", command=salvar_senha_nova, 
                          bg=tema_atual["btn_bg"], fg="white", width=20)
    btn_salvar.grid(row=2, column=0, columnspan=4, pady=10)

    # --- Área de Lista ---
    frame_lista = tk.Frame(janela_principal, bg=tema_atual["bg"])
    frame_lista.pack(fill="both", expand=True, padx=10, pady=10)
    
    tk.Label(frame_lista, text="Buscar:", bg=tema_atual["bg"], fg=tema_atual["fg"]).pack(anchor="w")
    entrada_busca = tk.Entry(frame_lista, bg=tema_atual["entry_bg"], fg=tema_atual["entry_fg"])
    entrada_busca.pack(fill="x", pady=(0, 5))
    entrada_busca.bind("<KeyRelease>", lambda e: atualizar_lista())
    
    colunas = ("Serviço", "Usuário", "Senha")
    tree = ttk.Treeview(frame_lista, columns=colunas, show="headings")
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill="both", expand=True)
    
    btn_copiar = tk.Button(frame_lista, text="Copiar Senha Selecionada", command=copiar_senha_selecionada, 
                          bg="#4CAF50", fg="white", pady=5)
    btn_copiar.pack(fill="x", pady=5)
    
    atualizar_lista()
    janela_principal.mainloop()

# ============ TELA DE LOGIN ============
janela_login = tk.Tk()
janela_login.title("Login SecurePass Cloud")
janela_login.geometry("300x250")
janela_login.config(bg=tema_atual["bg"])

tk.Label(janela_login, text="SecurePass Cloud", font=("Arial", 14, "bold"), 
         bg=tema_atual["bg"], fg=tema_atual["fg"]).pack(pady=20)

tk.Label(janela_login, text="Usuário:", bg=tema_atual["bg"], fg=tema_atual["fg"]).pack()
ent_login_user = tk.Entry(janela_login)
ent_login_user.pack(pady=5)

tk.Label(janela_login, text="Senha Mestra:", bg=tema_atual["bg"], fg=tema_atual["fg"]).pack()
ent_login_pass = tk.Entry(janela_login, show="*")
ent_login_pass.pack(pady=5)

tk.Button(janela_login, text="ENTRAR", command=acao_login, 
          bg=tema_atual["btn_bg"], fg="white", width=15, height=2).pack(pady=20)

janela_login.mainloop()