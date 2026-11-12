import pytest
from django.core.cache import cache

from contas.models import Usuario
from gestao.models import Atividade, Beneficiario

SENHA = "senha-de-teste-123"


@pytest.fixture(autouse=True)
def limpar_cache():
    cache.clear()


@pytest.fixture
def admin(db):
    return Usuario.objects.create_user("gestora@exemplo.org", SENHA, nome="Gestora", perfil=Usuario.Perfil.ADMINISTRADOR)


@pytest.fixture
def colaborador(db):
    return Usuario.objects.create_user("carla@exemplo.org", SENHA, nome="Carla")


@pytest.fixture
def atividade(db):
    return Atividade.objects.create(nome="Oficina de Artes", dias_semana="terça", horario="14:00")


@pytest.fixture
def turma(atividade):
    nomes = ["Ana Souza", "Bruno Lima", "Carlos Pereira", "Daniela Rocha"]
    alunos = []
    for nome in nomes:
        b = Beneficiario.objects.create(
            nome_completo=nome, data_nascimento="2000-05-10", telefone_responsavel="12900000000"
        )
        b.atividades.add(atividade)
        alunos.append(b)
    return alunos


@pytest.fixture
def cliente_admin(client, admin):
    client.force_login(admin)
    return client


@pytest.fixture
def cliente_colaborador(client, colaborador):
    client.force_login(colaborador)
    return client
