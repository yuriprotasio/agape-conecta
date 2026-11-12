"""Regras de negócio do MVP, isoladas das Views para facilitar os testes."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Beneficiario, Frequencia

LIMITE_FALTAS_CONSECUTIVAS = 3


def beneficiarios_da_chamada(atividade):
    return atividade.beneficiarios.filter(situacao=Beneficiario.Situacao.ATIVO).order_by("nome_completo")


@transaction.atomic
def registrar_chamada(atividade, data, marcacoes, usuario):
    """Grava a chamada inteira em uma transação.

    marcacoes: {beneficiario_id: (presente: bool, justificativa: str)}
    Se já existir chamada para a atividade e a data, os registros são atualizados, sem duplicar.
    """
    if not atividade.ativa:
        raise ValidationError("Esta atividade está inativa e não aceita novas chamadas.")
    if data > timezone.localdate():
        raise ValidationError("A data não pode ser futura. Informe a data de hoje ou uma data anterior.")
    inscritos = {b.pk: b for b in beneficiarios_da_chamada(atividade)}
    estranhos = set(marcacoes) - set(inscritos)
    if estranhos:
        raise ValidationError("Há beneficiários que não estão inscritos nesta atividade.")
    faltando = set(inscritos) - set(marcacoes)
    if faltando:
        nomes = ", ".join(sorted(inscritos[i].nome_completo for i in faltando))
        raise ValidationError(f"Marque presente ou ausente para: {nomes}.")

    presentes = ausentes = 0
    for beneficiario_id, (presente, justificativa) in marcacoes.items():
        Frequencia.objects.update_or_create(
            beneficiario_id=beneficiario_id,
            atividade=atividade,
            data=data,
            defaults={
                "presente": presente,
                "justificativa": "" if presente else justificativa.strip()[:200],
                "registrado_por": usuario,
            },
        )
        if presente:
            presentes += 1
        else:
            ausentes += 1
    return presentes, ausentes


def alertas_de_faltas(atividade):
    """Beneficiários da atividade com faltas consecutivas sem justificativa (RF08)."""
    alertas = []
    for b in beneficiarios_da_chamada(atividade):
        total = b.faltas_consecutivas(atividade)
        if total >= LIMITE_FALTAS_CONSECUTIVAS:
            alertas.append((b, total))
    return alertas
