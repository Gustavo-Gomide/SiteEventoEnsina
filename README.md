# Sistema de Gerenciamento de Eventos Acadêmicos

Este projeto é um gerenciador de eventos acadêmicos simples construído em Django. Ele permite:

- Cadastro e login de usuários (modelo custom `Usuario`).
- Criação de eventos por Professores/Organizadores.
- Listagem de eventos (qualquer um pode visualizar).
- Inscrição de alunos em eventos (quando logados).
- Perfil do usuário com upload de foto e envio de certificados.
- Exportação de lista de inscritos (CSV) para organizadores.


## Estrutura básica

- `instituicao_ensino/` - configurações do projeto, context processor, templates base.
- `usuarios/` - app que contém modelos de usuário custom (`Usuario`, `Perfil`, `Certificado`), formulários, views e templates.
- `eventos/` - app para gerenciar eventos e inscrições.


## Mudanças e decisões importantes

1. Autenticação
   - Atualmente o projeto usa um modelo de usuário custom (`usuarios.models.Usuario`) e autenticação simples baseada em sessão (armazena `usuario_id` em `request.session`).
   - Essa abordagem é intencional para simplicidade e compatibilidade com o que já existia.
   - Recomendação: migrar para `AUTH_USER_MODEL` (usar `AbstractBaseUser` ou OneToOne com `django.contrib.auth.User`) para poder usar recursos Django nativos (login/logout, decorators, permissões, admin, reset de senha).

2. Uploads de arquivos
   - Arquivos do usuário (foto de perfil e certificados) são armazenados em: `MEDIA_ROOT/usuarios/<nome_usuario>_<instituicao>/<tipo>/<arquivo>`.
   - Observe que se o `nome_usuario` ou `instituicao` mudar, os arquivos não são automaticamente movidos; apenas novos uploads seguirão o novo caminho. Para mover arquivos existentes, é necessário um script/management command para renomear diretórios.

3. Segurança e validações
   - Usar `csrf_token` nos formulários (já configurado).
   - Recomenda-se limitar tipos de arquivo e tamanho máximo de upload (não implementado como política global — pode ser adicionado via validators nos campos FileField/ImageField).
   - Senhas são armazenadas com `django.contrib.auth.hashers` (pbkdf2) pelo modelo `Usuario`.


## Como rodar (local)

1. Crie e ative um ambiente virtual (venv/conda).
2. Instale dependências (Django) — o `requirements.txt` já está no repositório:

```powershell
python -m pip install -r requirements.txt
```

3. Aplique migrações e crie dados iniciais:

```powershell
python manage.py makemigrations
python manage.py migrate
```

4. Crie tipos de usuário e dados de teste (pode usar Admin ou `manage.py shell`). Exemplo rápido no shell:

```python
from usuarios.models import TipoUsuario, Instituicao, DDD, Usuario
TipoUsuario.objects.get_or_create(tipo='Aluno')
TipoUsuario.objects.get_or_create(tipo='Professor')
Instituicao.objects.get_or_create(nome='Universidade Exemplo')
DDD.objects.get_or_create(codigo='+55')

# criar usuário exemplo
u=Usuario(nome='Aluno Teste', tipo=TipoUsuario.objects.get(tipo='Aluno'), instituicao=Instituicao.objects.first(), ddd=DDD.objects.first(), telefone='999999999', nome_usuario='aluno1', senha='senha123')
u.save()
```

5. Rodar servidor:

```powershell
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.


## Fluxo do usuário (visão geral)

- Visitante: pode ver home, sobre, galeria, eventos.
- Usuário registrado (aluno): pode fazer login, editar perfil, enviar certificados, inscrever-se em eventos.
- Usuário registrado (professor/organizador): pode criar eventos e visualizar inscritos; pode exportar lista em CSV.


## Próximos passos recomendados

- Migrar para `AUTH_USER_MODEL` (prioridade alta para segurança e compatibilidade).
- Implementar validação de upload (tipos e tamanho) e usar armazenamento seguro (S3) em produção.
- Adicionar testes unitários que cubram criação/inscrição/exportação de inscritos.
- Adicionar pagina de detalhe do evento e UI para gerenciamento (cancelamento, comunicação por e-mail).

## Novas funcionalidades (recente)

- Imagem padrão de perfil: o template exibirá `static/images/default_profile.png` quando o usuário não enviar foto de perfil. Adicione sua imagem padrão em `instituicao_ensino/static/images/default_profile.png`.
- Thumbs de evento: o modelo `Evento` agora tem um campo `thumb` (ImageField). Faça upload de imagens pelo admin ou no formulário de edição de evento para que apareçam na galeria/carousel.
- Galeria e carousel: a home agora mostra um carousel com eventos com thumb (`destaques`) e uma seção "Próximos Eventos" em grid.
- Gerenciar inscrições: organizadores podem acessar a área de gerenciamento do evento (`/eventos/gerenciar/<id>/`) para aprovar/reprovar inscrições. O modelo `InscricaoEvento` tem o campo `is_validated`.

## Observações sobre media e imagens

- As imagens de perfil e de eventos são salvas em `MEDIA_ROOT` (defina `MEDIA_ROOT` e `MEDIA_URL` no `settings.py` se ainda não estiver configurado). Exemplo no `settings.py`:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

- Ao trabalhar localmente, exponha `MEDIA_URL` durante o `runserver` adicionando as rotas `static()` nos `urls.py` (Django faz isso automaticamente em DEBUG True).

## Migrações

- Depois de atualizar o código, gere e aplique migrações locais:

```powershell
python manage.py makemigrations
python manage.py migrate

## Gerar certificados

Após instalar as dependências (Pillow, qrcode, reportlab) e aplicar as migrações, execute:

```powershell
python manage.py generate_certificates
```

O comando irá criar arquivos PNG e PDF para inscrições aprovadas em eventos já finalizados e armazená-los no modelo `Certificado`.
```


### Plano de migração para `AUTH_USER_MODEL` (passos sugeridos)

1. **Analisar modelo atual**
   - Verificar todos os lugares que usam `usuarios.Usuario` diretamente (views, forms, models, templates).

2. **Escolher estratégia**
   - Opção A: Fazer `Usuario` herdar de `AbstractBaseUser` e torná-lo `AUTH_USER_MODEL` — mais trabalho mas ideal.
   - Opção B: Criar `Django User` padrão e ter `Usuario` com OneToOne para dados extras — menos disruptivo.

3. **Criar plano de migração em desenvolvimento**
   - Implementar modelo novo em uma branch separada.
   - Atualizar forms e views para usar `django.contrib.auth` onde apropriado.
   - Criar scripts para migrar usuários existentes (copiar `nome_usuario`, password hash, e criar User vinculado).

4. **Migração de dados**
   - Fazer backup do DB.
   - Rodar script que cria `User` para cada `Usuario` existente e estabeleça relações (ex.: `Perfil.usuario -> Perfil.user`).

5. **Alterar `settings.AUTH_USER_MODEL`**
   - Apenas após validar scripts e testes locais.
   - Atualizar imports e referências (usar `get_user_model()` quando necessário).

6. **Testes**
   - Executar testes manuais e automatizados cobrindo: login, cadastro, criação de eventos, inscrições, upload de arquivos.

7. **Deploy**
   - Fazer deploy com downtime curto, verificar logs e integridade dos dados.

Observação: a migração é sensível (senha/ids). Posso escrever o script de migração e fazer a migração incremental com você se desejar.

### Como usar o utilitário de migração criado

1. Após garantir que as migrations foram aplicadas, execute o comando abaixo para criar `User` do Django para cada `Usuario` que ainda não tem vínculo:

```powershell
python manage.py migrate_to_django_user
```

2. Isso criará contas do Django com username igual a `nome_usuario` (quando possível) e marcará `Usuario.user` com o novo `User`.
3. Depois execute testes manuais de login: vá para `/usuarios/login/` e tente autenticar com `nome_usuario` e (se a senha não foi migrada) altere a senha via admin ou reset.

Nota: o script gera senhas aleatórias para users quando a senha não pode ser migrada diretamente do hash; recomenda-se forçar reset de senha dos usuários por email/admin em seguida.

## Observações finais

Implementei mudanças para: perfil do usuário (foto/biografia), upload de certificados, nav dinâmico, views para editar perfil, exportar inscritos, e melhorias em templates para controlar o acesso às ações.

Se quiser, eu posso:

- Fazer a migração para `AUTH_USER_MODEL` com plano de migração e execução.
- Adicionar validação de upload (tipos e tamanho) e testes automáticos.
- Criar páginas faltantes (galeria) e melhorar o visual.

Escolha o próximo passo e eu continuo.

---

## Notas e instruções adicionais (atualizado)

1) Criação automática do diretório de mídia

- O projeto foi atualizado para tentar criar `MEDIA_ROOT` automaticamente ao
   importar `settings.py`. Apesar disso é recomendável criar o diretório
   manualmente e garantir permissões corretas. No Windows PowerShell (na
   raiz do projeto):

```powershell
mkdir .\media
```

2) Dependências para geração de certificados

- As bibliotecas necessárias para gerar PNG/PDF/QR são opcionais. Se você
   quer que o site gere os arquivos binários automaticamente, instale:

```powershell
python -m pip install Pillow reportlab qrcode
```

- Se as bibliotecas não estiverem presentes, o sistema criará um arquivo
   HTML para cada certificado (visível pelo perfil do usuário). Isso
   permite que a aplicação funcione 100% via web sem executar comandos no
   terminal.

3) Passos para preparar o ambiente (PowerShell)

```powershell
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

4) Como testar fluxo de finalização e geração de certificado via web

- Crie um usuário organizador (tipo 'Professor' ou 'Organizador') e faça
   login.
- Crie um evento e inscreva alguns alunos (marque `is_validated=True`
   nas inscrições no painel de gerenciamento do evento).
- No painel do organizador clique em "Finalizar evento". O sistema irá
   tentar gerar os certificados; se libs estiverem ausentes, um certificado
   em HTML será criado e ficará visível no perfil do usuário.

5) Onde alterar comportamentos comuns

- Alterar campos de cadastro de usuário: `instituicao_ensino/usuarios/forms.py` e
   `instituicao_ensino/usuarios/models.py` (campo + validações).
- Adicionar um novo tipo de evento: atualizar `eventos/models.py` e criar as
   opções necessárias no banco (pelo admin ou via shell).
- Mudar local de armazenamento: `usuarios.models.user_directory_path`
   (também ver `Usuario.base_dir` generation).

6) Como depurar problemas com uploads e criação de pastas

- Os logs foram reforçados em pontos críticos. Veja os logs do servidor
   (console do runserver) para mensagens que começam com `Erro ao salvar
   perfil` ou `Erro criando diretorios de usuario`.
- Cheque se `MEDIA_ROOT` existe e é gravável pelo processo.

7) Documentação do código

- Cada módulo principal (`usuarios.models`, `usuarios.views`,
   `usuarios.utils`, `eventos.views`) contém comentários no topo explicando
   o propósito e decisões de implementação. Leia esses comentários para
   entender o porquê das escolhas e como modificar o comportamento.

---

Se quiser, prossigo com:
- rodar as migrações e criar um script de verificação automatizada (eu
   posso gerar os testes que façam chamadas às views principais),
- ou migrar para `AUTH_USER_MODEL` com um script de migração de dados.

## Documentação detalhada: Certificados (o núcleo do projeto)

O sistema agora gera certificados de forma controlada pelo organizador e
os disponibiliza no perfil do usuário. Principais pontos:

- Model `Certificado` (em `usuarios.models`) agora contém os campos:
   - `usuario` (FK) — proprietário do certificado
   - `evento` (FK) — evento relacionado (opcional)
   - `nome` — rótulo exibido no card de certificado
   - `pdf` / `png` / `arquivo` — arquivos gerados/armazenados
   - `qr_data` — string gravada (agora usamos a URL pública como qr_data)
   - `public_id` — identificador público (UUID) usado para validação via QR
   - `horas` — carga horária do certificado (decimal, em horas)

- Processo de geração (`usuarios.generator.generate_certificates_for_event`):
   1. Itera inscrições validadas (`is_validated=True`) do evento.
   2. Gera um `public_id` (UUID4) para cada certificado e grava no DB.
   3. Gera QR que codifica a URL pública de verificação: `SITE_URL/usuarios/certificado/<public_id>/`.
   4. Produz PNG e PDF (quando Pillow/reportlab/qrcode estão instalados). Caso contrário, o sistema criará um certificado em HTML (`certificado_base.html`) e o salvará no campo `arquivo`.

- Validação pública:
   - QR no certificado aponta para a view pública `certificado_publico` (rota: `/usuarios/certificado/<public_id>/`).
   - Essa página exibe metadados do certificado (nome, evento, data, horas) e fornece link para o PDF/PNG se existir.

- Campos do evento relacionados a certificados:
   - `Evento.horas` foi adicionado para armazenar a carga horária do evento (decimal). Quando o gerador cria o `Certificado`, ele copia `evento.horas` para `cert.horas`.

Como personalizar o visual do certificado (HTML/PDF):

1. Template HTML: `instituicao_ensino/templates/certificado_base.html` — usado pelo fallback HTML e também como base para o design do certificado.
    - Variáveis disponíveis no template: `nome_participante`, `nome_evento`, `data_inicio`, `data_fim`, `horas`, `qr_url`, `instituicao_nome`, `logo_url`.
2. Para ajustar texto e layout do PDF/PNG, edite `usuarios/generator.py` (ele desenha texto direto nas imagens/PDFs usando reportlab/Pillow). Mantive o código com comentários para facilitar ajustes de fontes e posições.

Como testar localmente o fluxo completo (passo a passo)

1. Assegure que `MEDIA_ROOT` existe e é gravável (veja nota acima).
2. Se quiser os arquivos PDF/PNG/QR reais, instale as dependências (recomendado):

```cmd
venv\Scripts\python.exe -m pip install pillow reportlab qrcode
```

3. Criar um organizador, criar um evento e definir `horas` (opcional). Inscrever alunos e validar as inscrições.
4. No painel do organizador, clique em "Finalizar evento". Isso chama o gerador no request/response (síncrono) e criará os certificados.
5. Verifique o perfil do aluno (`/usuarios/u/<nome_usuario>/certificados/`): cartões mostrarão botões para abrir PDF/PNG e um botão "Validar" que abre a página pública de validação.
6. Escanei o QR no certificado ou abra a URL pública `/usuarios/certificado/<public_id>/` para verificar os metadados.

Observações de segurança e produção

- O `public_id` permite validação sem autenticação; se lhe interessar restringir validação, mude a view `certificado_publico` para exigir algum token adicional.
- Em produção, sirva arquivos de mídia via Nginx/serviço estático e não use o servidor de desenvolvimento.

---

Se quiser, continuo com:
- Expandir a documentação linha-a-linha nos principais arquivos (`usuarios` e `eventos`).
- Implementar testes automatizados mais robustos para todo o fluxo de certificados e perfil.
- Refatorar `Usuario` para `AUTH_USER_MODEL` (opção maior).