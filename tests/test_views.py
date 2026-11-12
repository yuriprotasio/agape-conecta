"""Testes de integração: requisições HTTP passando por URLs, Views, templates e banco."""

from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from gestao.models import Atendimento, Beneficiario, Frequencia
from tests.conftest import SENHA

pytestmark = pytest.mark.django_db


# --- Autenticação e acesso (RF01, RNF01, RNF02) ---

def test_pagina_protegida_redireciona_para_login(client):
    resposta = client.get(reverse("gestao:painel"))
    assert resposta.status_code == 302
    assert reverse("contas:login") in resposta.url


def test_login_valido_abre_o_painel(client, colaborador):
    resposta = client.post(reverse("contas:login"), {"email": "CARLA@exemplo.org", "password": SENHA}, follow=True)
    assert "Olá, Carla" in resposta.content.decode()


def test_login_invalido_mostra_mensagem_generica(client, colaborador):
    resposta = client.post(reverse("contas:login"), {"email": "carla@exemplo.org", "password": "errada"})
    assert "E-mail ou senha incorretos." in resposta.content.decode()


def test_bloqueio_apos_cinco_tentativas(client, colaborador):
    for _ in range(5):
        client.post(reverse("contas:login"), {"email": "carla@exemplo.org", "password": "errada"})
    resposta = client.post(reverse("contas:login"), {"email": "carla@exemplo.org", "password": SENHA})
    assert "Muitas tentativas" in resposta.content.decode()
    assert "_auth_user_id" not in client.session


def test_sair_encerra_a_sessao(cliente_colaborador):
    cliente_colaborador.post(reverse("contas:logout"))
    assert cliente_colaborador.get(reverse("gestao:painel")).status_code == 302


def test_colaborador_nao_ve_nem_acessa_relatorios(cliente_colaborador):
    painel = cliente_colaborador.get(reverse("gestao:painel")).content.decode()
    assert "Relatórios" not in painel
    assert cliente_colaborador.get(reverse("gestao:relatorio_frequencia")).status_code == 403


def test_colaborador_nao_cadastra_beneficiario(cliente_colaborador):
    assert cliente_colaborador.get(reverse("gestao:beneficiario_novo")).status_code == 403


def test_cabecalho_csp_presente(cliente_colaborador):
    resposta = cliente_colaborador.get(reverse("gestao:painel"))
    assert "script-src 'self'" in resposta["Content-Security-Policy"]


# --- Beneficiários (RF02, RF03) ---

def test_admin_cadastra_beneficiario(cliente_admin, atividade):
    dados = {"nome_completo": "Mariana Ávila", "data_nascimento": "2001-03-01", "telefone_responsavel": "12999990000",
             "situacao": "ativo", "atividades": [atividade.pk]}
    resposta = cliente_admin.post(reverse("gestao:beneficiario_novo"), dados)
    assert resposta.status_code == 302
    assert Beneficiario.objects.get().atividades.count() == 1


def test_cpf_repetido_nao_e_gravado(cliente_admin):
    base = {"data_nascimento": "2001-03-01", "telefone_responsavel": "1", "situacao": "ativo", "cpf": "529.982.247-25"}
    cliente_admin.post(reverse("gestao:beneficiario_novo"), {**base, "nome_completo": "Primeira"})
    resposta = cliente_admin.post(reverse("gestao:beneficiario_novo"), {**base, "nome_completo": "Segunda"})
    assert resposta.status_code == 200
    assert Beneficiario.objects.count() == 1


def test_busca_ignora_acentos_e_maiusculas(cliente_colaborador, turma):
    Beneficiario.objects.create(nome_completo="Mariana Ávila", data_nascimento="2000-01-01", telefone_responsavel="1")
    conteudo = cliente_colaborador.get(reverse("gestao:beneficiarios"), {"q": "ANA"}).content.decode()
    assert "Ana Souza" in conteudo and "Mariana Ávila" in conteudo and "Bruno Lima" not in conteudo


def test_busca_com_texto_de_injecao_sql_nao_retorna_todos(cliente_colaborador, turma):
    resposta = cliente_colaborador.get(reverse("gestao:beneficiarios"), {"q": "' OR 1=1 --"})
    assert resposta.status_code == 200
    assert "Ana Souza" not in resposta.content.decode()


def test_texto_com_script_e_exibido_escapado(cliente_colaborador, turma, colaborador):
    Atendimento.objects.create(beneficiario=turma[0], profissional=colaborador, data_hora=timezone.now(),
                               tipo="pedagogico", descricao="<script>alert(1)</script>")
    conteudo = cliente_colaborador.get(reverse("gestao:beneficiario_ficha", args=[turma[0].pk])).content.decode()
    assert "<script>alert(1)</script>" not in conteudo
    assert "&lt;script&gt;" in conteudo


# --- Chamada de frequência (RF04, RF08) ---

def _dados_chamada(atividade, turma, dia, ausentes=()):
    dados = {"atividade": atividade.pk, "data": dia.isoformat()}
    for b in turma:
        dados[f"estado_{b.pk}"] = "ausente" if b.nome_completo in ausentes else "presente"
    return dados


def test_chamada_completa_redireciona_com_confirmacao(cliente_colaborador, atividade, turma):
    dados = _dados_chamada(atividade, turma, date(2026, 11, 10), ausentes=["Bruno Lima", "Daniela Rocha"])
    resposta = cliente_colaborador.post(reverse("gestao:chamada"), dados, follow=True)
    assert "Frequência registrada: 2 presentes, 2 ausentes." in resposta.content.decode()
    assert Frequencia.objects.count() == 4


def test_chamada_repetida_nao_duplica(cliente_colaborador, atividade, turma):
    dados = _dados_chamada(atividade, turma, date(2026, 11, 10))
    cliente_colaborador.post(reverse("gestao:chamada"), dados)
    cliente_colaborador.post(reverse("gestao:chamada"), dados)
    assert Frequencia.objects.count() == 4


def test_chamada_com_data_futura_mostra_correcao(cliente_colaborador, atividade, turma):
    dados = _dados_chamada(atividade, turma, timezone.localdate() + timedelta(days=2))
    conteudo = cliente_colaborador.post(reverse("gestao:chamada"), dados).content.decode()
    assert "Informe a data de hoje ou uma data anterior." in conteudo
    assert Frequencia.objects.count() == 0


def test_chamada_sem_csrf_e_recusada(colaborador, atividade, turma):
    from django.test import Client

    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(colaborador)
    resposta = cliente.post(reverse("gestao:chamada"), _dados_chamada(atividade, turma, date(2026, 11, 10)))
    assert resposta.status_code == 403


def test_resultado_mostra_alerta_de_faltas(cliente_colaborador, atividade, turma):
    for dia in (date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 10)):
        cliente_colaborador.post(reverse("gestao:chamada"), _dados_chamada(atividade, turma, dia, ausentes=["Bruno Lima"]))
    url = reverse("gestao:chamada_resultado", args=[atividade.pk]) + "?data=2026-11-10"
    conteudo = cliente_colaborador.get(url).content.decode()
    assert "Faltas consecutivas: 3" in conteudo and "Bruno Lima" in conteudo


# --- Atendimentos (RF05) e relatório (RF06) ---

def test_atendimento_registrado_com_o_profissional_logado(cliente_colaborador, turma, colaborador):
    dados = {"beneficiario": turma[0].pk, "data_hora": "2026-11-10T10:00", "tipo": "pedagogico", "descricao": "Leitura"}
    cliente_colaborador.post(reverse("gestao:atendimento_novo"), dados)
    assert Atendimento.objects.get().profissional == colaborador


def test_outro_profissional_nao_edita_atendimento(client, turma, admin, colaborador):
    from contas.models import Usuario

    atendimento = Atendimento.objects.create(beneficiario=turma[0], profissional=colaborador,
                                             data_hora=timezone.now(), tipo="social", descricao="x")
    outro = Usuario.objects.create_user("outro@exemplo.org", SENHA, nome="Outro")
    client.force_login(outro)
    assert client.get(reverse("gestao:atendimento_editar", args=[atendimento.pk])).status_code == 403


def test_relatorio_calcula_percentual(cliente_admin, atividade, turma, admin):
    for dia, presente in [(6, True), (13, True), (20, False), (27, True)]:
        Frequencia.objects.create(beneficiario=turma[0], atividade=atividade, data=date(2026, 10, dia),
                                  presente=presente, registrado_por=admin)
    url = reverse("gestao:relatorio_frequencia")
    conteudo = cliente_admin.get(url, {"atividade": atividade.pk, "mes": "2026-10"}).content.decode()
    assert "<td>Ana Souza</td><td>3</td><td>1</td><td>75%</td>" in conteudo
    assert "12900000000" not in conteudo  # relatório não expõe telefone
