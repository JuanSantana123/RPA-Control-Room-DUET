# Autenticação — RPA Control Room

## 1. Objetivo

O RPA Control Room utiliza autenticação para controlar o acesso à interface
web e às APIs do sistema.

A arquitetura de autenticação será dividida em dois cenários:

1. Usuários acessando a interface web.
2. Sistemas externos consumindo as APIs.

Cada cenário possui um mecanismo de autenticação próprio.

---

# 2. Autenticação da Interface Web

Para usuários acessando o Frontend React, será utilizada uma sessão
gerenciada pelo Backend.

O fluxo será:

```text
Usuário
   │
   │ username + senha
   ▼
Frontend React
   │
   │ POST /auth/login
   ▼
FastAPI
   │
   ├── Localiza usuário
   ├── Verifica senha
   ├── Cria sessão
   │
   ▼
Banco de dados
   │
   │ session_id
   ▼
FastAPI
   │
   │ Cookie HttpOnly
   ▼
Navegador