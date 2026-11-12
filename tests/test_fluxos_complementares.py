"""Testes de integração complementares: edição, comando de demonstração e casos de erro."""

from datetime import date

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from contas.models import Usuario
from gestao.models import Atendimento, Beneficiario, Frequencia

pytestmark = pytest.mark.django_db


def test_admin_edita_e_inativa_beneficiario(cliente_admin, turma):
    b = turma[0]
    dados = {"nome_completo": "Ana Souza Lima", "data_nascimento": "2000-05-10",
             "telefone_responsavel": "12900000000", "situacao": "inativo"}
    resposta = cliente_admin.post(reverse("gestao:beneficiario_editar", args=[b.pk]), dados)
    assert resposta.status_code == 302
    b.refresh_from_db()
    assert b.nome_completo == "Ana Souza Lima" and b.situacao == "inativo"


def test_ficha_exibe_alerta_e_historico(cliente_colaborador, atividade, turma, colaborador):
    bruno = turma[1]
    for dia in (6, 13, 20):
        Frequencia.objects.create(beneficiario=bruno, atividade=atividade, data=date(2026, 10, dia),
                                  presente=False, registrado_por=colaborador)
    conteudo = cliente_colaborador.get(reverse("gestao:beneficiario_ficha", args=[bruno.pk])).content.decode()
    assert "Faltas consecutivas: 3" in conteudo and "20/10/2026" in conteudo


def test_autor_edita_o_proprio_atendimento(cliente_colaborador, turma, colaborador):
    atendimento = Atendimento.objects.create(beneficiario=turma[0], profissional=colaborador,
                                             data_hora=timezone.now(), tipo="social", descricao="Antes")
    url = reverse("gestao:atendimento_editar", args=[atendimento.pk])
    assert cliente_colaborador.get(url).status_code == 200
    dados = {"beneficiario": turma[0].pk, "data_hora": "2026-11-10T09:30", "tipo": "social", "descricao": "Depois"}
    cliente_colaborador.post(url, dados)
    atendimento.refresh_from_db()
    assert atendimento.descricao == "Depois"


def test_formulario_de_atendimento_preenche_beneficiario(cliente_colaborador, turma):
    resposta = cliente_colaborador.get(reverse("gestao:atendimento_novo"), {"beneficiario": turma[0].pk})
    assert resposta.context["form"].initial["beneficiario"] == turma[0].pk


def test_chamada_com_data_invalida_e_tratada(cliente_colaborador, atividade, turma):
    resposta = cliente_colaborador.get(reverse("gestao:chamada"), {"atividade": atividade.pk, "data": "31/02"})
    assert "Informe uma data válida." in resposta.content.decode()


def test_chamada_incompleta_lista_quem_falta_marcar(cliente_colaborador, atividade, turma):
    dados = {"atividade": atividade.pk, "data": "2026-11-10", f"estado_{turma[0].pk}": "presente"}
    conteudo = cliente_colaborador.post(reverse("gestao:chamada"), dados).content.decode()
    assert "Marque presente ou ausente para" in conteudo and "Bruno Lima" in conteudo
    assert Frequencia.objects.count() == 0


def test_relatorio_com_mes_invalido_usa_mes_atual(cliente_admin, atividade):
    resposta = cliente_admin.get(reverse("gestao:relatorio_frequencia"), {"atividade": atividade.pk, "mes": "abc"})
    assert resposta.context["inicio"].month == timezone.localdate().month


def test_usuario_logado_que_abre_login_vai_ao_painel(cliente_colaborador):
    resposta = cliente_colaborador.get(reverse("contas:login"))
    assert resposta.status_code == 302


def test_comando_carregar_demo_cria_dados_ficticios():
    call_command("carregar_demo", senha="senha-demo-segura")
    assert Beneficiario.objects.count() == 20
    assert Usuario.objects.get(email="gestora@exemplo.org").eh_administrador
    bruno = Beneficiario.objects.get(nome_completo="Bruno Lima")
    assert bruno.frequencias.filter(presente=False).count() == 3


def test_chamada_carrega_script_do_contador_da_propria_origem(cliente_colaborador, atividade, turma):
    conteudo = cliente_colaborador.get(reverse("gestao:chamada"), {"atividade": atividade.pk, "data": "2026-11-10"}).content.decode()
    assert 'id="contador-chamada"' in conteudo and 'aria-live="polite"' in conteudo
    assert "/static/js/chamada.js" in conteudo
