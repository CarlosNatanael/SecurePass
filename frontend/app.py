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
from frontend.config import API_URL

# --- VARIÁVEIS GLOBAIS ---
sessao_atual = {
    "usuario": None,
    "chave": None,
    "dados": [],
    "indice_edicao": None
}

# ============ TEMA MODERNO ============
TEMA_MODERNO = {
    # Cores principais
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "secondary": "#64748b",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
    "warning": "#f59e0b",
    "success": "#10b981",
    "edit": "#fbbf24",
    
    # Fundos
    "bg_dark": "#0f172a",
    "bg_card": "#1e293b",
    "bg_input": "#334155",
    "bg_sidebar": "#1e293b",
    
    # Textos
    "text_primary": "#f8fafc",
    "text_secondary": "#cbd5e1",
    "text_muted": "#94a3b8",
    
    # Bordas
    "border": "#475569",
    "border_hover": "#64748b",
    
    # Efeitos
    "shadow": "0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)",
    "shadow_small": "0 1px 3px 0 rgba(0, 0, 0, 0.3)",
    
    # Fontes
    "font_family": "Segoe UI",
    "font_bold": ("Segoe UI", 10, "bold"),
    "font_title": ("Segoe UI", 14, "bold"),
    "font_subtitle": ("Segoe UI", 11, "bold"),
}

# ============ Funções de Criptografia & Nuvem ============
def derivar_chave(senha):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=b'salt_fixo_por_enquanto', iterations=5000,
    )
    return Fernet(base64.urlsafe_b64encode(kdf.derive(senha.encode())))

def sincronizar_upload():
    if not sessao_atual["usuario"] or not sessao_atual["chave"]:
        return

    try:
        dados_json = json.dumps(sessao_atual["dados"])
        blob_criptografado = sessao_atual["chave"].encrypt(dados_json.encode()).decode()
        payload = {"username": sessao_atual["usuario"], "blob_criptografado": blob_criptografado}
        
        res = requests.post(f"{API_URL}/salvar", json=payload)
        if res.status_code == 200:
            print("Sincronizado com sucesso!")
        else:
            messagebox.showerror("Erro Cloud", "Falha ao salvar na nuvem.")
    except Exception as e:
        messagebox.showerror("Erro de Conexão", f"Servidor offline: {e}")

def carregar_da_nuvem(usuario, senha_mestra):
    try:
        res = requests.get(f"{API_URL}/obter/{usuario}")
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

def salvar_ou_atualizar():
    servico = entrada_servico.get()
    usuario = entrada_usuario.get()
    senha = campo_senha.get()
    
    if not servico or not usuario or not senha:
        messagebox.showwarning("Campos Vazios", "Preencha todos os campos!")
        return
    
    idx_edicao = sessao_atual["indice_edicao"]
    
    novo_dado = {"servico": servico, "usuario": usuario, "senha": senha}
    
    if idx_edicao is not None:
        sessao_atual["dados"][idx_edicao] = novo_dado
        sessao_atual["indice_edicao"] = None
        
        btn_salvar.config(text="➕ Salvar Nova Senha", bg=TEMA_MODERNO["primary"])
        messagebox.showinfo("Atualizado", "Senha alterada com sucesso!")
    else:
        sessao_atual["dados"].append(novo_dado)
        messagebox.showinfo("Sucesso", "Nova senha salva!")
    
    entrada_servico.delete(0, tk.END)
    entrada_usuario.delete(0, tk.END)
    campo_senha.delete(0, tk.END)
    
    sincronizar_upload()
    atualizar_lista()

def editar_senha_selecionada():
    selecionado = tree.focus()
    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione uma senha para editar.")
        return

    item_tree = tree.item(selecionado)['values']
    servico_alvo, usuario_alvo = item_tree[0], item_tree[1]
    
    index_real = -1
    dado_encontrado = None
    
    for i, dado in enumerate(sessao_atual["dados"]):
        if dado["servico"] == servico_alvo and dado["usuario"] == usuario_alvo:
            index_real = i
            dado_encontrado = dado
            break
            
    if index_real != -1 and dado_encontrado:
        entrada_servico.delete(0, tk.END)
        entrada_servico.insert(0, dado_encontrado["servico"])
        
        entrada_usuario.delete(0, tk.END)
        entrada_usuario.insert(0, dado_encontrado["usuario"])
        
        campo_senha.delete(0, tk.END)
        campo_senha.insert(0, dado_encontrado["senha"])
        
        sessao_atual["indice_edicao"] = index_real
        
        btn_salvar.config(text="✓ Confirmar Edição", bg=TEMA_MODERNO["success"])
    else:
        messagebox.showerror("Erro", "Item não encontrado na memória.")

def excluir_senha_selecionada():
    selecionado = tree.focus()
    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione uma senha para excluir.")
        return

    item_tree = tree.item(selecionado)['values']
    servico_alvo, usuario_alvo = item_tree[0], item_tree[1]

    confirmacao = messagebox.askyesno("Confirmar Exclusão", 
                                      f"Tem certeza que deseja apagar a senha de:\n{servico_alvo} ({usuario_alvo})?")
    
    if confirmacao:
        nova_lista = []
        encontrou = False
        for dado in sessao_atual["dados"]:
            if not encontrou and dado["servico"] == servico_alvo and dado["usuario"] == usuario_alvo:
                encontrou = True
                continue 
            nova_lista.append(dado)
        
        sessao_atual["dados"] = nova_lista
        sessao_atual["indice_edicao"] = None
        btn_salvar.config(text="➕ Salvar Nova Senha", bg=TEMA_MODERNO["primary"])
        
        sincronizar_upload()
        atualizar_lista()
        messagebox.showinfo("Excluído", "Senha removida com sucesso!")

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

# ============ Funções de Estilização ============
def criar_botao_moderno(parent, text, command, **kwargs):
    bg = kwargs.get('bg', TEMA_MODERNO["primary"])
    fg = kwargs.get('fg', TEMA_MODERNO["text_primary"])
    width = kwargs.get('width', 12)
    height = kwargs.get('height', 1)
    
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        font=TEMA_MODERNO["font_bold"],
        width=width,
        height=height,
        relief="flat",
        bd=0,
        cursor="hand2",
        activebackground=kwargs.get('active_bg', bg),
        activeforeground=fg
    )
    
    # Adiciona efeito hover
    def on_enter(e):
        btn['bg'] = kwargs.get('hover_bg', TEMA_MODERNO.get(f"{bg.split('_')[0]}_hover", bg))
    
    def on_leave(e):
        btn['bg'] = bg
    
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn

def criar_entry_moderno(parent, **kwargs):
    """Função simplificada - retorna apenas o Entry"""
    entry = tk.Entry(
        parent,
        bg=TEMA_MODERNO["bg_input"],
        fg=TEMA_MODERNO["text_primary"],
        insertbackground=TEMA_MODERNO["text_primary"],
        relief="flat",
        bd=0,
        font=(TEMA_MODERNO["font_family"], 10),
        highlightthickness=1,
        highlightbackground=TEMA_MODERNO["border"],
        highlightcolor=TEMA_MODERNO["primary"]
    )
    
    return entry

def criar_label_moderno(parent, text, **kwargs):
    font = kwargs.get('font', (TEMA_MODERNO["font_family"], 10))
    bg = kwargs.get('bg', TEMA_MODERNO["bg_dark"])
    fg = kwargs.get('fg', TEMA_MODERNO["text_secondary"])
    
    return tk.Label(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        font=font
    )

# ============ Janela Principal ============
def abrir_janela_principal():
    global janela_principal, entrada_servico, entrada_usuario, campo_senha, tree, entrada_busca, btn_salvar
    
    janela_principal = tk.Tk()
    janela_principal.title(f"🔐 SecurePass Cloud - {sessao_atual['usuario']}")
    janela_principal.geometry("900x650")
    janela_principal.config(bg=TEMA_MODERNO["bg_dark"])
    janela_principal.resizable(True, True)
    
    # Container principal
    main_container = tk.Frame(janela_principal, bg=TEMA_MODERNO["bg_dark"])
    main_container.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Cabeçalho
    header_frame = tk.Frame(main_container, bg=TEMA_MODERNO["bg_dark"])
    header_frame.pack(fill="x", pady=(0, 20))
    
    criar_label_moderno(
        header_frame,
        f"Bem-vindo, {sessao_atual['usuario']}",
        font=TEMA_MODERNO["font_title"],
        fg=TEMA_MODERNO["text_primary"]
    ).pack(side="left")
    
    # Frame de adição de senhas
    form_card = tk.Frame(main_container, bg=TEMA_MODERNO["bg_card"])
    form_card.pack(fill="x", pady=(0, 20))
    
    # Título do card
    tk.Label(
        form_card,
        text="➕ Adicionar/Editar Senha",
        bg=TEMA_MODERNO["bg_card"],
        fg=TEMA_MODERNO["text_primary"],
        font=TEMA_MODERNO["font_subtitle"]
    ).pack(anchor="w", padx=20, pady=(15, 10))
    
    # Campos do formulário
    form_content = tk.Frame(form_card, bg=TEMA_MODERNO["bg_card"])
    form_content.pack(fill="x", padx=20, pady=(0, 15))
    
    # Linha 1: Serviço e Usuário
    linha1 = tk.Frame(form_content, bg=TEMA_MODERNO["bg_card"])
    linha1.pack(fill="x", pady=(0, 10))
    
    criar_label_moderno(linha1, "Serviço:", bg=TEMA_MODERNO["bg_card"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
    entrada_servico = criar_entry_moderno(linha1)
    entrada_servico.grid(row=0, column=1, padx=(0, 20), ipady=3, ipadx=5)
    
    criar_label_moderno(linha1, "Usuário:", bg=TEMA_MODERNO["bg_card"]).grid(row=0, column=2, sticky="w", padx=(0, 5))
    entrada_usuario = criar_entry_moderno(linha1)
    entrada_usuario.grid(row=0, column=3, padx=(0, 20), ipady=3, ipadx=5)
    
    # Linha 2: Senha e Botões
    linha2 = tk.Frame(form_content, bg=TEMA_MODERNO["bg_card"])
    linha2.pack(fill="x", pady=(0, 10))
    
    criar_label_moderno(linha2, "Senha:", bg=TEMA_MODERNO["bg_card"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
    campo_senha = criar_entry_moderno(linha2)
    campo_senha.config(show="•")
    campo_senha.grid(row=0, column=1, padx=(0, 10), ipady=3, ipadx=5)
    
    # Botão gerar senha
    btn_gerar = criar_botao_moderno(
        linha2,
        "🎲 Gerar Senha",
        inserir_senha_gerada,
        bg=TEMA_MODERNO["warning"],
        hover_bg="#e69e00",
        width=15
    )
    btn_gerar.grid(row=0, column=2, padx=(10, 20))
    
    # Botão salvar
    btn_salvar = criar_botao_moderno(
        linha2,
        "➕ Salvar Nova Senha",
        salvar_ou_atualizar,
        bg=TEMA_MODERNO["primary"],
        hover_bg=TEMA_MODERNO["primary_hover"],
        width=20
    )
    btn_salvar.grid(row=0, column=3)
    
    # Frame da lista de senhas
    lista_card = tk.Frame(main_container, bg=TEMA_MODERNO["bg_card"])
    lista_card.pack(fill="both", expand=True)
    
    # Cabeçalho da lista
    lista_header = tk.Frame(lista_card, bg=TEMA_MODERNO["bg_card"])
    lista_header.pack(fill="x", padx=20, pady=15)
    
    criar_label_moderno(
        lista_header,
        "📋 Suas Senhas Salvas",
        font=TEMA_MODERNO["font_subtitle"],
        fg=TEMA_MODERNO["text_primary"],
        bg=TEMA_MODERNO["bg_card"]
    ).pack(side="left")
    
    # Campo de busca
    busca_frame = tk.Frame(lista_header, bg=TEMA_MODERNO["bg_card"])
    busca_frame.pack(side="right")
    
    criar_label_moderno(busca_frame, "🔍", bg=TEMA_MODERNO["bg_card"]).pack(side="left", padx=(0, 5))
    entrada_busca = criar_entry_moderno(busca_frame)
    entrada_busca.config(width=25)
    entrada_busca.pack(side="left", ipady=3, ipadx=5)
    entrada_busca.bind("<KeyRelease>", lambda e: atualizar_lista())
    
    # Treeview com scrollbar
    tree_frame = tk.Frame(lista_card, bg=TEMA_MODERNO["bg_card"])
    tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame)
    scrollbar.pack(side="right", fill="y")
    
    # Configurar estilo da treeview
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview",
        background=TEMA_MODERNO["bg_input"],
        foreground=TEMA_MODERNO["text_primary"],
        fieldbackground=TEMA_MODERNO["bg_input"],
        borderwidth=0,
        font=(TEMA_MODERNO["font_family"], 10)
    )
    style.configure(
        "Treeview.Heading",
        background=TEMA_MODERNO["bg_input"],
        foreground=TEMA_MODERNO["text_secondary"],
        font=(TEMA_MODERNO["font_family"], 10, "bold"),
        relief="flat"
    )
    style.map(
        "Treeview",
        background=[('selected', TEMA_MODERNO["primary"])],
        foreground=[('selected', TEMA_MODERNO["text_primary"])]
    )
    
    colunas = ("Serviço", "Usuário", "Senha")
    tree = ttk.Treeview(tree_frame, columns=colunas, show="headings", yscrollcommand=scrollbar.set)
    
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=200 if col != "Senha" else 100)
    
    tree.pack(fill="both", expand=True, side="left")
    scrollbar.config(command=tree.yview)
    
    # Botões de ação
    botoes_frame = tk.Frame(lista_card, bg=TEMA_MODERNO["bg_card"])
    botoes_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    # Botão Copiar
    btn_copiar = criar_botao_moderno(
        botoes_frame,
        "📋 Copiar Senha",
        copiar_senha_selecionada,
        bg=TEMA_MODERNO["secondary"],
        hover_bg="#4b5563",
        width=15
    )
    btn_copiar.pack(side="left", padx=(0, 10))
    
    # Botão Editar
    btn_editar = criar_botao_moderno(
        botoes_frame,
        "✏️ Editar",
        editar_senha_selecionada,
        bg=TEMA_MODERNO["edit"],
        fg="#000000",
        hover_bg="#e6b400",
        width=15
    )
    btn_editar.pack(side="left", padx=(0, 10))
    
    # Botão Excluir
    btn_excluir = criar_botao_moderno(
        botoes_frame,
        "🗑️ Excluir",
        excluir_senha_selecionada,
        bg=TEMA_MODERNO["danger"],
        hover_bg=TEMA_MODERNO["danger_hover"],
        width=15
    )
    btn_excluir.pack(side="right")
    
    atualizar_lista()
    janela_principal.mainloop()

# ============ TELA DE LOGIN ============
janela_login = tk.Tk()
janela_login.title("🔐 SecurePass Cloud - Login")
janela_login.geometry("400x500")
janela_login.config(bg=TEMA_MODERNO["bg_dark"])
janela_login.resizable(False, False)

# Centralizar janela
janela_login.eval('tk::PlaceWindow . center')

# Container do login
login_container = tk.Frame(janela_login, bg=TEMA_MODERNO["bg_dark"])
login_container.pack(expand=True, padx=40, pady=40)

# Logo/Title
tk.Label(
    login_container,
    text="🔐",
    font=("Segoe UI", 30),
    bg=TEMA_MODERNO["bg_dark"],
    fg=TEMA_MODERNO["primary"]
).pack(pady=(0, 5))

tk.Label(
    login_container,
    text="SecurePass Cloud",
    font=("Segoe UI", 24, "bold"),
    bg=TEMA_MODERNO["bg_dark"],
    fg=TEMA_MODERNO["text_primary"]
).pack(pady=(0, 30))

# Formulário de login
login_form = tk.Frame(login_container, bg=TEMA_MODERNO["bg_dark"])
login_form.pack(fill="x")

# Campo usuário
criar_label_moderno(
    login_form,
    "Usuário",
    font=("Segoe UI", 11)
).pack(anchor="w", pady=(0, 5))
ent_login_user = criar_entry_moderno(login_form)
ent_login_user.pack(fill="x", pady=(0, 15), ipady=5)

# Campo senha
criar_label_moderno(
    login_form,
    "Senha Mestra",
    font=("Segoe UI", 11)
).pack(anchor="w", pady=(0, 5))
ent_login_pass = criar_entry_moderno(login_form)
ent_login_pass.config(show="•")
ent_login_pass.pack(fill="x", pady=(0, 30), ipady=5)

# Botão de login
btn_login = criar_botao_moderno(
    login_form,
    "→ ENTRAR",
    acao_login,
    bg=TEMA_MODERNO["primary"],
    hover_bg=TEMA_MODERNO["primary_hover"],
    width=20,
    height=2
)
btn_login.pack()

# Footer
tk.Label(
    login_container,
    text="© 2024 SecurePass Cloud",
    font=("Segoe UI", 9),
    bg=TEMA_MODERNO["bg_dark"],
    fg=TEMA_MODERNO["text_muted"]
).pack(side="bottom", pady=(20, 0))

janela_login.mainloop()