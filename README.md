# 🎓 SiteEventoEnsina

O **SiteEventoEnsina** é uma aplicação web desenvolvida em **Django**, voltada para instituições de ensino que desejam **gerenciar eventos**, **inscrições de usuários**, e **interações entre participantes** de forma centralizada.
O projeto foi estruturado para ser didático e modular, facilitando manutenção e expansão.

---

## 🚀 Instalação e Configuração

### 1. Clonar o Repositório

```bash
git clone https://github.com/SEU_USUARIO/SiteEventoEnsina.git
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
│   ├── templates/eventos/   # Páginas HTML específicas de eventos
│   ├── static/              # CSS e JS específicos de eventos
│   └── urls.py              # Rotas próprias do app de eventos
│
├── usuarios/                # App de autenticação e perfil de usuários
│   ├── models.py            # Modelos de usuário, organizador, aluno etc.
│   ├── views.py             # Lógica de login, cadastro e perfil
│   ├── templates/usuarios/  # Páginas HTML do módulo de usuários
│   └── urls.py              # Rotas específicas de usuários
│
└── media/                   # Uploads (imagens de eventos e usuários)
```

---

## 🧩 Organização e Funcionamento

### **Apps Principais**

* **eventos/**:
  Gerencia todo o ciclo de vida dos eventos — criação, edição, exclusão, listagem e exibição detalhada.
  Os dados são definidos nos `models.py` e exibidos via `views.py`, que enviam o contexto para os templates HTML.

* **usuarios/**:
  Responsável pelo cadastro e autenticação de usuários, com diferenciação de perfis (aluno, organizador, etc.).
  Usa os templates em `usuarios/templates/usuarios/` para renderizar as páginas de login, registro e perfil.

* **commands/**:
  Contém scripts de manutenção ou geração de dados (como comandos personalizados do Django).

---

## 🎨 Templates e Customização

### Estrutura de Templates

Os templates seguem uma hierarquia lógica baseada na app:

```
eventos/templates/eventos/
usuarios/templates/usuarios/
instituicao_ensino/templates/base/
```

O arquivo base (`base.html`) contém o layout principal (navbar, rodapé e blocos de conteúdo).
Cada página específica herda esse template e substitui blocos (`{% block content %}`) para renderizar seu conteúdo.

Para alterar o design:

* Edite os arquivos em `static/` ou `static/styles/` para modificar CSS.
* Ajuste os blocos HTML dentro de cada template.
* Substitua imagens e ícones em `media/` conforme necessário.

---

## ⚙️ Lógica das Views

O projeto utiliza **Function-Based Views (FBV)**.
Cada view em `views.py` é uma função que:

1. Processa a requisição (`request`)
2. Interage com o modelo (`models.py`)
3. Retorna um template (`render(request, 'caminho/template.html', contexto)`)

Isso facilita a leitura e a modificação de comportamentos específicos de cada página.

---

## 📦 Models (Banco de Dados)

Os modelos estão definidos em cada app:

* `eventos/models.py` → Tabelas relacionadas a eventos (ex: `Evento`, `Categoria`, `Inscricao`).
* `usuarios/models.py` → Tabelas relacionadas a perfis de usuário e permissões.

Caso queira adicionar novos campos:

1. Edite o `models.py` correspondente.
2. Rode `python manage.py makemigrations` e `python manage.py migrate`.

---

## 🧱 Static e Media

* **`static/`** → contém os arquivos estáticos (CSS, JS, imagens de design).
* **`media/`** → armazena arquivos enviados pelos usuários (como imagens de perfil ou banners de evento).

Esses diretórios podem ser configurados em `settings.py` nas variáveis `STATIC_URL`, `MEDIA_URL` e `MEDIA_ROOT`.

---

## 🧪 Como Personalizar Funcionalidades

* Para **mudar o comportamento** de uma página: edite o `views.py` correspondente.
* Para **mudar o design**: altere o HTML em `templates/` ou o CSS em `static/`.
* Para **mudar os dados exibidos**: edite o `context` enviado nas views ou os modelos em `models.py`.

Exemplo: se quiser adicionar um novo campo “Palestrante” no evento:

1. Abra `eventos/models.py` e adicione o campo.
2. Faça migrações.
3. Atualize o template `detalhes_evento.html` para exibir o novo campo.

---

## 🧰 Tecnologias Utilizadas

* **Python 3.x**
* **Django 4.x**
* **SQLite** (padrão, pode ser trocado por PostgreSQL)
* **HTML5 / CSS3 / JavaScript**
* **Bootstrap (opcional para estilização)**

---

## 🧑‍💻 Autor

Desenvolvido por ***Gustavo Gomide***, como parte de um estudo sobre Django, arquitetura de aplicações web e boas práticas de organização de código.