---

## Como Funciona o Projeto (por requisito do PDF)

Esta seção explica como cada funcionalidade do projeto atende aos requisitos do PDF e como testar cada uma delas:

### 1. Cadastro e autenticação de usuários
- O usuário pode se cadastrar pelo site, informando nome, e-mail, telefone e senha (com confirmação e validação de força).
- Após cadastro, recebe e-mail de confirmação (se configurado SMTP).
- Login pelo site ou via API (obtenção de token).

**Testar:**
1. Acesse `/usuarios/cadastro/` e preencha o formulário.
2. Confirme o e-mail (verifique caixa de entrada, se SMTP configurado).
3. Faça login pelo site ou obtenha token via API.

### 2. Gerenciamento de eventos
- Usuários autenticados podem visualizar eventos disponíveis, detalhes e se inscrever.
- Admins podem criar, editar e excluir eventos pelo Django Admin (`/admin/`).

**Testar:**
1. Acesse `/eventos/` para listar eventos.
2. Entre como admin em `/admin/` para gerenciar eventos.

### 3. Inscrição em eventos
- Usuário autenticado pode se inscrever em eventos via site ou API.
- Inscrição impede duplicidade e respeita limite de vagas.

**Testar:**
1. Faça login.
2. Clique em "Inscrever-se" em um evento ou use o endpoint `POST /api/events/register/`.

### 4. Edição de perfil e upload de foto
- Usuário pode editar dados pessoais e enviar foto de perfil.
- Máscara e validação de telefone no formulário.

**Testar:**
1. Acesse `/perfil/` após login.
2. Edite dados, envie foto e salve.

### 5. Emissão de certificados
- Após participação em evento, o usuário pode baixar certificado (PDF) se disponível.

**Testar:**
1. Após evento concluído, acesse área de certificados no perfil.

### 6. API REST para integração
- Endpoints para autenticação, listagem de eventos e inscrição.
- Throttling limita uso abusivo.

**Testar:**
1. Siga as instruções da seção "API REST e Testes com Postman".

### 7. Painel administrativo
- Acesse `/admin/` com usuário staff/superuser para gerenciar usuários, eventos, inscrições e certificados.

### 8. Notificações e fila de e-mails
- Sistema envia e-mails de confirmação, lembretes e notificações de inscrição.
- Fila de e-mails pode ser processada em background (ver `notifications/worker.py`).

**Testar:**
1. Realize ações que disparam e-mails (cadastro, inscrição, etc).
2. Verifique envio no e-mail configurado.

### 9. Segurança e validações
- Senhas validadas por força (mínimo, letra, número, especial).
- Telefone validado e normalizado.
- Proteção contra inscrições duplicadas e acesso não autorizado.

**Testar:**
1. Tente cadastrar senha fraca ou telefone inválido.
2. Tente se inscrever duas vezes no mesmo evento.

---
---

## API REST e Testes com Postman

O projeto possui uma API REST documentada e uma coleção pronta para o Postman (`postman_collection.json`).

### Fluxo de uso da API

1. **Obter token de autenticação**
   - Endpoint: `POST /api/auth/token/`
   - Body (x-www-form-urlencoded):
     - `username`: seu usuário
     - `password`: sua senha
   - Exemplo cURL:
     ```bash
     curl -X POST http://127.0.0.1:8000/api/auth/token/ -d "username=seu_usuario" -d "password=sua_senha"
     ```
   - Resposta esperada:
     ```json
     { "token": "<seu_token>" }
     ```

2. **Listar eventos**
   - Endpoint: `GET /api/events/`
   - Header:
     - `Authorization: Token <seu_token>`
   - Exemplo cURL:
     ```bash
     curl -H "Authorization: Token <seu_token>" http://127.0.0.1:8000/api/events/
     ```
   - Resposta esperada: lista de eventos em JSON.

3. **Inscrever-se em evento**
   - Endpoint: `POST /api/events/register/`
   - Header:
     - `Authorization: Token <seu_token>`
   - Body (JSON):
     ```json
     { "evento_id": <id_do_evento> }
     ```
   - Exemplo cURL:
     ```bash
     curl -X POST http://127.0.0.1:8000/api/events/register/ \
       -H "Authorization: Token <seu_token>" \
       -H "Content-Type: application/json" \
       -d '{"evento_id": 1}'
     ```
   - Resposta esperada: dados da inscrição ou mensagem de erro.

### Como importar e usar a coleção Postman

1. Abra o Postman e importe o arquivo `postman_collection.json` (raiz do projeto).
2. Configure a variável `base_url` como `http://127.0.0.1:8000/api`.
3. Siga a ordem das requisições:
   - `1 - Obter token`: preencha username e password no body (x-www-form-urlencoded). O token será salvo automaticamente na variável `{{token}}`.
   - `2 - Listar eventos`: já usa o token salvo no header.
   - `3 - Inscrever em evento`: envie o `evento_id` desejado no body JSON.

**Atenção:**
- Se receber erro de autenticação, confira se o token está correto e não expirou.
- Os endpoints possuem limites diários de uso (throttling): 20 requisições/dia para listar eventos, 50/dia para inscrição.

---


# 🎓 SiteEventoEnsina

Plataforma Django para gestão de eventos, inscrições, perfis e emissão de certificados para instituições de ensino.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Instalação e Configuração](#instalação-e-configuração)
- [Como Funciona o Projeto (por requisito)](#como-funciona-o-projeto-por-requisito)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [API REST e Testes com Postman](#api-rest-e-testes-com-postman)
- [Dicas, Observações e Segurança](#dicas-observações-e-segurança)
- [Autores](#autores)

---

## Visão Geral

O SiteEventoEnsina é um sistema web completo para:
- Cadastro e autenticação de usuários (com confirmação por e-mail)
- Gerenciamento de eventos, inscrições e certificados
- Edição de perfil, upload de foto, máscara e validação de telefone
- API REST para integração externa
- Painel administrativo (Django Admin)
- Fila de e-mails assíncrona para notificações

---

## Instalação e Configuração

1. **Clone o repositório:**
  ```bash
  git clone https://github.com/Gustavo-Gomide/SiteEventoEnsina.git
  cd SiteEventoEnsina/instituicao_ensino
  ```

2. **Crie e ative um ambiente virtual:**
  ```bash
  python -m venv venv
  # Windows:
  venv\Scripts\activate
  # Linux/Mac:
  source venv/bin/activate
  ```

3. **Instale as dependências:**
  ```bash
  python -m pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  ```

4. **Configure variáveis de ambiente:**
  - Copie `env.example` para `.env` e preencha com seus dados (e-mail SMTP, SITE_URL, etc).

5. **Aplique migrações e crie um superusuário:**
  ```bash
  python manage.py migrate
  python manage.py createsuperuser
  ```

6. **Inicie o servidor:**
  ```bash
  python manage.py runserver
  ```
  Acesse: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---
## 🗂️ Estrutura do Projeto

```
instituicao_ensino/
├── manage.py
├── requirements.txt
├── env.example / .env
├── instituicao_ensino/   # Configurações globais, templates, static, settings
├── eventos/              # App de eventos (modelos, views, API, admin)
├── usuarios/             # App de usuários (cadastro, login, perfil, certificados)
├── notifications/        # Sistema de notificações e fila de e-mails
├── static/               # CSS, JS, imagens
├── media/                # Uploads de usuários e certificados
└── ...
```

---

## 🔑 Configuração de Ambiente

1. **Variáveis sensíveis:**
   - Configure `.env` com dados SMTP, SITE_URL, etc. Nunca suba senhas ou chaves para o repositório.
2. **Banco de dados:**
   - Por padrão usa SQLite (`db.sqlite3`). Para produção, configure outro banco em `settings.py`.
3. **E-mail:**
   - SMTP Brevo (Sendinblue) já configurado no exemplo. Use sua API Key.

---

## 🧑‍💻 Funcionalidades Principais

- Cadastro e autenticação de usuários (com confirmação por e-mail)
- Gerenciamento de eventos, inscrições e certificados
- Edição de perfil, upload de foto, máscara e validação de telefone
- API REST (Django REST Framework) para integração externa
- Sistema de throttling (limite de requisições por usuário)
- Painel administrativo completo (Django Admin)
- Fila de e-mails assíncrona para notificações

---

## 🛠️ Comandos Úteis

- `python manage.py migrate` — aplica migrações do banco
- `python manage.py createsuperuser` — cria usuário admin
- `python manage.py runserver` — inicia o servidor local
- `python manage.py collectstatic` — coleta arquivos estáticos para produção

---

## 🔗 API REST (DRF)

Base: `http://127.0.0.1:8000/api/`

### Endpoints principais

- `POST /api/auth/token/` — obtém token de autenticação
- `GET /api/events/` — lista eventos (requer token)
- `POST /api/events/register/` — inscreve usuário autenticado em evento

**Autenticação:**
- Use o token retornado no header: `Authorization: Token <seu_token>`

**Throttling:**
- Limite de 20 requisições/dia para listar eventos
- Limite de 50 requisições/dia para inscrição em eventos

**Exemplo cURL:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ -d "username=seu_usuario" -d "password=sua_senha"
```

---

## 🧪 Testes com Postman

1. Importe `postman_collection.json` no Postman
2. Configure o `base_url` como `http://127.0.0.1:8000/api`
3. Siga a ordem: obter token → listar eventos → inscrever em evento

---

## 📝 Dicas e Observações

- Sempre ative o ambiente virtual antes de rodar comandos Python
- Se der erro de módulo (ex: `No module named 'rest_framework'`), instale as dependências
- Para produção, configure cache (Redis/Memcached) para throttling e use HTTPS
- Não exponha `.env` ou credenciais em repositórios públicos
- Para customizar templates, edite os arquivos em `instituicao_ensino/templates/`
- Para alterar regras de senha/telefone, veja `usuarios/forms.py` e `usuarios/models.py`

---

## 🛡️ Segurança

- Nunca suba senhas, chaves ou dados sensíveis para o repositório
- Use variáveis de ambiente para SMTP, tokens e segredos
- Habilite HTTPS e configure cabeçalhos de segurança em produção

---

## 👨‍💻 Autores

Desenvolvido por **Gustavo Gomide**, **Victor Ribeiro** e **Matheus Queiroz**.
