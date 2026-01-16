# 🔐 SecurePass Cloud

> Um gerenciador de senhas multiplataforma (Desktop & Mobile) com arquitetura "Zero-Knowledge", sincronização em nuvem e criptografia de ponta a ponta.

![Status do Projeto](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![React Native](https://img.shields.io/badge/React_Native-Expo-violet)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)

## Sobre o Projeto

O **SecurePass Cloud** é uma solução completa para gerenciamento de credenciais. O diferencial deste projeto é a segurança: as senhas são criptografadas no dispositivo do cliente (PC ou Celular) usando uma **Senha Mestra** que nunca é enviada ao servidor. O Backend armazena apenas o "blob" criptografado, garantindo que nem mesmo o administrador do servidor tenha acesso aos dados.

## Funcionalidades

* **Multiplataforma:** Cliente Desktop (Tkinter) e Mobile (React Native) totalmente sincronizados.
* **Criptografia Zero-Knowledge:** Usa AES (Fernet) e PBKDF2HMAC. A descriptografia ocorre apenas localmente.
* **CRUD Completo:** Adicionar, Visualizar, Editar e Excluir senhas.
* **Gerador de Senhas Fortes:** Criação automática de senhas seguras (letras, números e símbolos).
* **Copiar com um Toque:** Facilidade para copiar senhas para a área de transferência.
* **Modo Offline:** O app mobile armazena o último estado conhecido (planejado).

## Tecnologias Utilizadas

### Backend (API)
* **Python**
* **FastAPI:** Framework moderno e rápido para APIs.
* **Uvicorn:** Servidor ASGI.
* **Hospedagem:** Compatível com PythonAnywhere (WSGI via a2wsgi).

### Cliente Desktop
* **Python & Tkinter:** Interface gráfica nativa.
* **Cryptography (Fernet):** Biblioteca robusta para segurança.

### Cliente Mobile
* **React Native (Expo):** Desenvolvimento híbrido ágil.
* **Crypto-JS:** Implementação de criptografia compatível com o Python no JS.
* **Axios:** Comunicação HTTP.

---

## Como Executar o Projeto

### Pré-requisitos
> [!NOTE]
>* `Python 3.10+` instalado.
>* `Node.js` instalado.
>* `Expo Go` instalado no celular (para testar o mobile).

### 1️⃣ Configurando o Backend

O backend é o coração da sincronização.

```bash
# Entre na pasta do backend
cd backend

# Crie um ambiente virtual (recomendado)
python -m venv venv
# Ative o venv (Windows: venv\Scripts\activate | Linux/Mac: source venv/bin/activate)

# Instale as dependências
pip install fastapi uvicorn pydantic a2wsgi

# Inicie o servidor
uvicorn main:app --reload --host 0.0.0.0

```

> O servidor rodará em `http://localhost:8000` (ou no seu IP local).

### 2️⃣ Executando o Cliente Desktop

```bash
# Entre na pasta do frontend desktop
cd frontend_desktop

# Instale as dependências
pip install requests cryptography

# Configure o IP do servidor no código se necessário
# Execute o app
python app_tkinter_cloud.py

```

### 3️⃣ Executando o App Mobile

```bash
# Entre na pasta mobile
cd securepass-mobile

# Instale as dependências
npm install

# ⚠️ CONFIGURAÇÃO IMPORTANTE:
# Crie um arquivo chamado 'config.js' na raiz da pasta mobile
# Conteúdo do config.js:
# export const API_URL = "http://SEU_IP_DO_PC:8000";

# Inicie o Expo
npx expo start
```

> Escaneie o QR Code com o app **Expo Go** no seu celular.

---

##  Arquitetura de Segurança

O sistema utiliza uma abordagem híbrida para garantir compatibilidade entre Python e JavaScript:

1. **Derivação de Chave:** A Senha Mestra do usuário passa por um algoritmo **PBKDF2** (com SHA256 e 5.000 iterações) para gerar uma chave criptográfica de 32 bytes.
2. **Criptografia:** Os dados (JSON) são criptografados usando **AES-128-CBC** (padrão Fernet), gerando um token que contém Timestamp, IV (Vetor de Inicialização) e Assinatura HMAC.
3. **Transmissão:** Apenas o token criptografado trafega pela rede.

##  Contribuição

Este é um projeto de portfólio e estudos. Sinta-se à vontade para fazer um fork e submeter Pull Requests!