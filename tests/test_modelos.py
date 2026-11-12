"""Testes unitários das regras dos modelos e dos serviços."""

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from gestao.models import Beneficiario, Frequencia, normalizar, validar_cpf
from gestao.servicos import alertas_de_faltas, registrar_chamada


def test_normalizar_remove_acentos_e_maiusculas():
    assert normalizar("  Mariana ÁVILA  ") == "mariana avila"


@pytest.mark.parametrize("cpf", ["529.982.247-25", "52998224725"])
def test_cpf_valido(cpf):
    validar_cpf(cpf)


@pytest.mark.parametrize("cpf", ["111.111.111-11", "123", "529.982.247-24"])
def test_cpf_invalido(cpf):
    with pytest.raises(ValidationError):
        validar_cpf(cpf)


@pytest.mark.django_db
def test_senha_armazenada_somente_como_hash_argon2(colaborador):
    assert colaborador.password.startswith("argon2$argon2id$")
    assert "senha-de-teste-123" not in colaborador.password


@pytest.mark.django_db
def test_data_de_nascimento_futura_e_rejeitada():
    b = Beneficiario(nome_completo="Teste", data_nascimento=timezone.localdate() + timedelta(days=1), telefone_responsavel="1")
    with pytest.raises(ValidationError):
        b.full_clean()


@pytest.mark.django_db
def test_menor_de_idade_exige_responsavel():
    b = Beneficiario(nome_completo="Criança", data_nascimento=date(2018, 1, 1), telefone_responsavel="1")
    with pytest.raises(ValidationError) as erro:
        b.full_clean()
    assert "nome_responsavel" in erro.value.message_dict


@pytest.mark.django_db
def test_frequencia_duplicada_e_bloqueada_pelo_banco(turma, atividade, colaborador):
    dados = dict(beneficiario=turma[0], atividade=atividade, data=date(2026, 11, 10), registrado_por=colaborador)
    Frequencia.objects.create(presente=True, **dados)
    with pytest.raises(IntegrityError):
        Frequencia.objects.create(presente=False, **dados)


@pytest.mark.django_db
def test_registrar_chamada_conta_presentes_e_ausentes(turma, atividade, colaborador):
    marcacoes = {b.pk: (b.nome_completo != "Bruno Lima", "") for b in turma}
    assert registrar_chamada(atividade, date(2026, 11, 10), marcacoes, colaborador) == (3, 1)
    assert Frequencia.objects.count() == 4


@pytest.mark.django_db
def test_repetir_chamada_atualiza_sem_duplicar(turma, atividade, colaborador):
    dia = date(2026, 11, 10)
    registrar_chamada(atividade, dia, {b.pk: (True, "") for b in turma}, colaborador)
    registrar_chamada(atividade, dia, {b.pk: (False, "") for b in turma}, colaborador)
    assert Frequencia.objects.count() == 4
    assert not Frequencia.objects.filter(presente=True).exists()


@pytest.mark.django_db
def test_chamada_com_data_futura_e_rejeitada(turma, atividade, colaborador):
    with pytest.raises(ValidationError):
        registrar_chamada(atividade, timezone.localdate() + timedelta(days=1), {b.pk: (True, "") for b in turma}, colaborador)
    assert Frequencia.objects.count() == 0


@pytest.mark.django_db
def test_chamada_incompleta_e_rejeitada_sem_gravar(turma, atividade, colaborador):
    with pytest.raises(ValidationError):
        registrar_chamada(atividade, date(2026, 11, 10), {turma[0].pk: (True, "")}, colaborador)
    assert Frequencia.objects.count() == 0


@pytest.mark.django_db
def test_beneficiario_inativo_nao_entra_na_chamada(turma, atividade, colaborador):
    turma[3].situacao = Beneficiario.Situacao.INATIVO
    turma[3].save()
    marcacoes = {b.pk: (True, "") for b in turma}
    with pytest.raises(ValidationError):
        registrar_chamada(atividade, date(2026, 11, 10), marcacoes, colaborador)


@pytest.mark.django_db
def test_alerta_de_tres_faltas_consecutivas_sem_justificativa(turma, atividade, colaborador):
    bruno = turma[1]
    for dia, presente, justificativa in [(6, True, ""), (13, False, "consulta médica"), (20, False, ""), (27, False, "")]:
        Frequencia.objects.create(beneficiario=bruno, atividade=atividade, data=date(2026, 10, dia),
                                  presente=presente, justificativa=justificativa, registrado_por=colaborador)
    assert bruno.faltas_consecutivas(atividade) == 2  # a falta justificada interrompe a sequência
    Frequencia.objects.create(beneficiario=bruno, atividade=atividade, data=date(2026, 11, 3), presente=False, registrado_por=colaborador)
    assert alertas_de_faltas(atividade) == [(bruno, 3)]
