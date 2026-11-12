# Ágape Conecta

Sistema web de gestão de beneficiários, atendimentos e frequência para a Associação Ágape para Educação Especial (São José dos Campos, SP). MVP desenvolvido na disciplina de Projeto de Software do curso de Análise e Desenvolvimento de Sistemas.

## Problema

Os registros de beneficiários, atendimentos e frequência ficam espalhados em planilhas, documentos e controles manuais. Isso toma tempo da equipe, dificulta consultar o histórico de cada pessoa e aumenta o risco de dados duplicados ou perdidos. O projeto está alinhado ao ODS 10 (Redução das Desigualdades), meta 10.2.

## Funcionalidades do MVP

| Requisito | Funcionalidade | Perfil |
|---|---|---|
| RF01 | Login por e-mail e senha, com perfis administrador e colaborador | Todos |
| RF02 | Cadastro e edição de beneficiários (inativação em vez de exclusão) | Administrador |
| RF03 | Busca por nome (ignora acentos e maiúsculas) e ficha com histórico cronológico | Todos |
| RF04 | Chamada de frequência por atividade em uma única tela, sem duplicidade | Todos |
| RF05 | Registro e edição de atendimentos individuais | Todos (edição: autor ou administrador) |
| RF06 | Relatório mensal de frequência por atividade | Administrador |
| RF08 | Alerta de 3 ou mais faltas consecutivas sem justificativa | Todos |

## Tecnologias

- Python 3.12+ e Django 5.2 LTS (arquitetura monolítica em camadas, padrão MVT)
- PostgreSQL em produção (SQLite apenas no desenvolvimento local)
- Argon2id para hash de senhas (`argon2-cffi`)
- WhiteNoise para arquivos estáticos e Gunicorn como servidor de aplicação
- pytest e pytest-django para testes automatizados

## Estrutura

```
config/      configurações, URLs e middleware de segurança (CSP)
contas/      modelo de usuário, login com bloqueio de tentativas e logout
gestao/      modelos, regras de negócio (servicos.py), views e templates do MVP
templates/   layout base, componentes de formulário e páginas de erro
static/css/  estilos acessíveis (contraste AA, foco visível, alvos de 44 px)
tests/       testes unitários (test_modelos.py) e de integração (test_views.py)
```

## Como executar localmente

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # ajuste os valores se quiser
export DEBUG=True                  # Windows (PowerShell): $env:DEBUG="True"
python manage.py migrate
python manage.py carregar_demo --senha "escolha-uma-senha-forte"
python manage.py runserver
```

Acesse http://127.0.0.1:8000 e entre com `gestora@exemplo.org` (administradora) ou `carla@exemplo.org` (colaboradora), usando a senha escolhida. Todos os dados de demonstração são fictícios.

## Testes

```bash
pytest
```

A suíte cobre regras de negócio (CPF, datas futuras, chamada sem duplicidade, faltas consecutivas) e fluxos completos pelas telas, incluindo verificações de segurança: hash Argon2, bloqueio de login, controle de acesso por perfil, CSRF, cabeçalho CSP, tentativa de injeção de SQL e escape de scripts (XSS).

## Variáveis de ambiente (produção)

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta longa e aleatória (obrigatória) |
| `DATABASE_URL` | Conexão PostgreSQL, por exemplo `postgres://usuario:senha@host:5432/agape?sslmode=require` |
| `ALLOWED_HOSTS` | Domínios permitidos, separados por vírgula |
| `CSRF_TRUSTED_ORIGINS` | Origens HTTPS confiáveis, por exemplo `https://agape-conecta.onrender.com` |
| `DEBUG` | Deve ficar ausente ou `False` em produção |

Antes de publicar:

```bash
python manage.py check --deploy
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi
```

## Segurança e privacidade

- Senhas guardadas apenas como hash Argon2id, nunca em texto ou com MD5/SHA-1.
- Bloqueio de 15 minutos após 5 tentativas de login inválidas; mensagem de erro genérica.
- Autorização verificada no servidor em cada operação; sessão expira após 30 minutos sem uso.
- Consultas somente pelo ORM (parametrizadas), escape automático nos templates e CSP restrita à própria origem.
- Minimização de dados: o sistema não armazena laudo médico, CID ou renda familiar.

## Licença

MIT
