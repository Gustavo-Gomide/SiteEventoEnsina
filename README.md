# 🎓 SiteEventoEnsina

O **SiteEventoEnsina** é uma aplicação web desenvolvida em **Django**, voltada para instituições de ensino que desejam **gerenciar eventos**, **inscrições de usuários**, e **interações entre participantes** de forma centralizada.
O projeto foi estruturado para ser didático e modular, facilitando manutenção e expansão.

---

## 🚀 Instalação e Configuração

### 1. Clonar o Repositório

```bash
git clone https://github.com/Gustavo-Gomide/SiteEventoEnsina.git
cd SiteEventoEnsina/instituicao_ensino
```

### 2. Criar e Ativar um Ambiente Virtual

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Aplicar Migrações e Executar o Servidor

```bash
python manage.py migrate
python manage.py runserver
```

O servidor será iniciado em `http://127.0.0.1:8000/`.

---

## 🧠 Estrutura do Projeto

```
instituicao_ensino/
│
├── manage.py                # Script principal para rodar comandos Django
├── requirements.txt         # Dependências do projeto
│
├── instituicao_ensino/      # Diretório raiz do projeto (configurações principais)
│   ├── settings.py          # Configurações globais: apps, banco, paths, etc.
│   ├── urls.py              # Rotas principais do sistema
│   ├── templates/           # Templates base do projeto
│   │   └── base/            # Templates de layout e estrutura HTML
│   ├── static/              # Arquivos CSS/JS compartilhados
│   └── ...
│
├── eventos/                 # App responsável pelo gerenciamento de eventos
│   ├── models.py            # Modelos (Event, Categoria, Inscrição...)
│   ├── views.py             # Lógica das páginas (criação, edição, listagem)
"""
SiteEventoEnsina - README

Este arquivo documenta a instalação, execução e as alterações recentes deste projeto
(API REST, validações de senha/telefone, máscara no front e mecanismos de segurança).

"""

# 🎓 SiteEventoEnsina

Aplicação web em Django para gerenciar eventos, inscrições e perfis de usuários. Este README foi
atualizado para documentar as alterações recentes (API REST, validações, máscaras e melhorias de
segurança) e para orientar execução e testes locais.

---

## Sumário

- [Instalação rápida](#instalação-rápida)
- [Execução e migrações](#execução-e-migrações)
- [API REST (DRF)](#api-rest-drf)
- [Testes com Postman](#testes-com-postman)
- [Mudanças e validações importantes](#mudanças-e-validações-importantes)
- [Notas de segurança e implantação](#notas-de-segurança-e-implantação)

---

## Instalação rápida

1. Clone o repositório e entre na pasta do projeto:

```powershell
git clone https://github.com/Gustavo-Gomide/SiteEventoEnsina.git
cd SiteEventoEnsina/instituicao_ensino
```

2. Crie e ative um ambiente virtual (Windows PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Instale as dependências:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

4. Aplique migrações e crie um superuser (opcional):

```powershell
python manage.py migrate
python manage.py createsuperuser
```

5. Inicie o servidor:

```powershell
python manage.py runserver
```

A aplicação estará disponível em `http://127.0.0.1:8000/`.

---

## Execução e migrações

- Rode `python manage.py migrate` sempre que alterar modelos.
- Para criar dados de teste, use o admin em `http://127.0.0.1:8000/admin/`.

---

## API REST (DRF)

O projeto inclui uma API REST construída com Django REST Framework para consulta de eventos e
inscrição de participantes.

Base URL (local): `http://127.0.0.1:8000/api/`

Endpoints principais:

- `POST /api/auth/token/` — obtém token por `username` e `password` (form data) — retorna
  `{ "token": "..." }`.
- `GET  /api/events/` — lista eventos (requer header `Authorization: Token <token>`). Limitado a
  20 requisições por dia por usuário.
- `POST /api/events/register/` — inscreve o usuário autenticado em evento; body JSON:
  `{ "evento_id": <id> }`. Limitado a 50 requisições por dia por usuário.

Autenticação e permissões:

- A API usa `TokenAuthentication` (DRF). Gere um token via `POST /api/auth/token/` ou pelo admin.
- As views exigem autenticação (`IsAuthenticated`). O endpoint de token é público (exige
  credenciais para gerar token).

Throttling (limites):

- `event_list` (GET /api/events/) → `20/day` por usuário.
- `event_register` (POST /api/events/register/) → `50/day` por usuário.

Como obter token (exemplo cURL):

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -d "username=seu_usuario" -d "password=sua_senha"
```

Usar token nas chamadas subsequentes:

```
Authorization: Token <SEU_TOKEN>
```

---

## Testes com Postman

Uma coleção Postman foi adicionada ao repositório: `postman_collection.json`.

Instruções:

1. Abra Postman → `File → Import` → selecione `postman_collection.json` na raiz do projeto.
2. Defina o Environment `base_url` como `http://127.0.0.1:8000/api`.
3. Execute as requisições na sequência:
   - `1 - Obter token` (preencha username e password no body urlencoded). O teste salva
     `{{token}}` automaticamente.
   - `2 - Listar eventos` (usa `Authorization: Token {{token}}`).
   - `3 - Inscrever em evento` (ajuste `evento_id` no body JSON).

Também há exemplos cURL nas descrições das requisições.

---

## Mudanças e validações importantes

Resumo das alterações implementadas:

- API REST com DRF e `rest_framework.authtoken` para autenticação por token.
- Coleção Postman pronta (`postman_collection.json`).
- Throttling configurado em `settings.py` (20/day e 50/day).
- Validação de senha no formulário de cadastro e edição:
  - Mínimo 8 caracteres
  - Ao menos uma letra
  - Ao menos um número
  - Ao menos um caractere especial
  Mensagens de erro aparecem no formulário quando regras não são cumpridas.
- Campo `senha_confirm` adicionado ao formulário de cadastro (`usuarios/forms.py`) e template
  `usuarios/templates/cadastro.html` atualizado com instruções fixas de senha.
- Normalização de telefone no modelo `usuarios.Usuario` e validação no formulário: formato
  armazenado como `+CC (DD) NNNNN-NNNN` (padrão Brasil `+55` quando país não informado). Há máscara
  JS no front (`telefone_mask.js`) e validação server-side.
- Hash de senha: PBKDF2-SHA256 customizado para reforçar a criptografia (mantendo compatibilidade
  com hashes Django antigos). Ver função de hashing em `usuarios/models.py`.
- Fluxo de confirmação de e-mail (quando ativado): geração de token de confirmação com expiração
  curta (2 minutos) e templates em `usuarios/templates/emails/`.

Observações sobre inscrição via API:

- A inscrição (`InscricaoEvento`) exige que o usuário Django autenticado possua um `Usuario`
  vinculado via `User.profile` (campo `Usuario.user` com `related_name='profile'`). Se não houver
  perfil, a API retorna 400.
- A API impede inscrições duplicadas e respeita `quantidade_participantes` salvo se
  `sem_limites=True`.

---

## Notas de segurança e implantação

- Não deixe credenciais (SMTP, chaves, etc.) em `settings.py` no repositório. Use variáveis de
  ambiente.
- Para produção, configure um cache compartilhado (Redis/Memcached) para que o throttling funcione
  corretamente entre múltiplos processos/instâncias.
- Habilite HTTPS e configure cabeçalhos de segurança (HSTS, CSP) no servidor de produção.

---

## Diagnóstico rápido

- Se ao iniciar o servidor aparecer `ModuleNotFoundError: No module named 'rest_framework'`:
  1. Ative o venv: `.\venv\Scripts\Activate.ps1` (PowerShell).
  2. Instale dependências: `python -m pip install -r requirements.txt`.
  3. Verifique: `python -c "import rest_framework; print(rest_framework.__version__)"`.

- Se receber `{"detail":"Método \"GET\" não é permitido."}` no Postman: verifique que está
  usando o método correto para o endpoint (por exemplo `POST /api/events/register/` para
  inscrições).

---

## Arquivos úteis no repositório

- `postman_collection.json` — coleção Postman para teste da API.
- `requirements.txt` — dependências (DRF já adicionado).
- `eventos/serializers.py`, `eventos/api_views.py`, `eventos/urls_api.py` — implementação da API.

---

## Próximos passos (opcionais)

- Adicionar documentação OpenAPI/Swagger (ex: `drf-yasg` ou `drf-spectacular`).
- Criar testes automatizados para endpoints da API (pytest + Django) e para validações de senha/
  telefone.
- Adicionar monitoramento de taxa de erro e métricas (Sentry, Prometheus).

---

## Autor

Desenvolvido por **Gustavo Gomide**.

---

Se quiser, eu também:
- gero um `postman_environment.json` com `base_url` e `token` para importar;
- crio um pequeno script `scripts/api_check.py` que executa token → list → register localmente e
  imprime os resultados.
Diga qual prefere que eu adicione ao repositório.
