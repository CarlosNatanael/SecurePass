from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import flet as ft
import requests
import base64
import json
import os

SERVER_URL = "http://127.0.0.1:8000"

def main(page: ft.Page):
    page.title = "SecurePass Cloud"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 700
    state = {
        "usuario": "",
        "senha_mestra": "",
        "chave_fernet": None,
        "dados_decifrados": []
    }

    # --- FUNÇÕES DE SEGURANÇA ---
    def derivar_chave(senha: str, salt: bytes = b'salt_fixo_por_enquanto'):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(senha.encode()))
        return Fernet(key)

    def criptografar_tudo():
        dados_json = json.dumps(state["dados_decifrados"])
        token = state["chave_fernet"].encrypt(dados_json.encode())
        return token.decode()

    def descriptografar_tudo(token_criptografado):
        try:
            dados_json = state["chave_fernet"].decrypt(token_criptografado.encode()).decode()
            return json.loads(dados_json)
        except Exception as e:
            return []

    # --- COMUNICAÇÃO COM API ---
    def sincronizar_dados(e=None):
        try:
            blob = criptografar_tudo()
            payload = {"username": state["usuario"], "blob_criptografado": blob}
            res = requests.post(f"{SERVER_URL}/salvar", json=payload)
            if res.status_code == 200:
                page.snack_bar = ft.SnackBar(ft.Text("Dados salvos na nuvem!"))
                page.snack_bar.open = True
                page.update()
        except Exception as erro:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro de conexão: {erro}"))
            page.snack_bar.open = True
            page.update()

    # --- INTERFACE ---
    def mostrar_dashboard():
        page.clean()
        lista_senhas = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        def renderizar_lista():
            lista_senhas.controls.clear()
            for item in state["dados_decifrados"]:
                lista_senhas.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Row([
                                ft.Icon(ft.icons.LOCK, color="blue"),
                                ft.Column([
                                    ft.Text(item['servico'], weight="bold"),
                                    ft.Text(item['usuario'], size=12, color="grey"),
                                ], expand=True),
                                ft.IconButton(
                                    icon=ft.icons.COPY,
                                    tooltip="Copiar Senha",
                                    on_click=lambda _, s=item['senha']: page.set_clipboard(s)
                                )
                            ])
                        )
                    )
                )
            page.update()
        txt_servico = ft.TextField(label="Serviço")
        txt_login = ft.TextField(label="Login/Email")
        txt_senha_nova = ft.TextField(label="Senha", password=True, can_reveal_password=True)

        def adicionar_senha(e):
            if txt_servico.value and txt_senha_nova.value:
                state["dados_decifrados"].append({
                    "servico": txt_servico.value,
                    "usuario": txt_login.value,
                    "senha": txt_senha_nova.value
                })
                txt_servico.value = ""
                txt_login.value = ""
                txt_senha_nova.value = ""
                renderizar_lista()
                sincronizar_dados()
                dlg_add.open = False
                page.update()
        dlg_add = ft.AlertDialog(
            title=ft.Text("Nova Senha"),
            content=ft.Column([txt_servico, txt_login, txt_senha_nova], height=200),
            actions=[ft.TextButton("Salvar", on_click=adicionar_senha)]
        )
        page.add(
            ft.AppBar(title=ft.Text(f"Cofre de {state['usuario']}"), actions=[
                ft.IconButton(ft.icons.SYNC, on_click=sincronizar_dados),
                ft.IconButton(ft.icons.ADD, on_click=lambda _: page.open(dlg_add))
            ]),
            lista_senhas
        )
        renderizar_lista()

    # Tela de Login
    def tela_login():
        txt_user = ft.TextField(label="Usuário", width=300)
        txt_pass = ft.TextField(label="Senha Mestra", password=True, width=300)
        
        def tentar_login(e):
            if not txt_user.value or not txt_pass.value:
                return
            state["usuario"] = txt_user.value
            state["senha_mestra"] = txt_pass.value
            state["chave_fernet"] = derivar_chave(txt_pass.value)
            try:
                res = requests.get(f"{SERVER_URL}/obter/{txt_user.value}")
                if res.status_code == 200:
                    dados = res.json()
                    blob = dados.get("blob", "")
                    if blob:
                        try:
                            state["dados_decifrados"] = descriptografar_tudo(blob)
                            mostrar_dashboard()
                        except:
                            page.snack_bar = ft.SnackBar(ft.Text("Senha Mestra Incorreta (Não foi possível descriptografar)"))
                            page.snack_bar.open = True
                            page.update()
                    else:
                        state["dados_decifrados"] = []
                        mostrar_dashboard()
            except Exception as erro:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao conectar no servidor: {erro}"))
                page.snack_bar.open = True
                page.update()

        page.add(
            ft.Column([
                ft.Icon(ft.icons.SECURITY, size=100, color="blue"),
                ft.Text("SecurePass Cloud", size=30, weight="bold"),
                txt_user,
                txt_pass,
                ft.ElevatedButton("Entrar / Criar", on_click=tentar_login)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        )
    tela_login()
    
ft.app(target=main)