from datetime import date

from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from .models import Atividade, Beneficiario
from .permissoes import somente_administrador


def _mes(texto):
    try:
        ano, mes = (int(p) for p in texto.split("-"))
        return date(ano, mes, 1)
    except (AttributeError, ValueError):
        hoje = timezone.localdate()
        return date(hoje.year, hoje.month, 1)


@somente_administrador
def frequencia_mensal(request):
    atividades = Atividade.objects.all()
    inicio = _mes(request.GET.get("mes"))
    fim = date(inicio.year + (inicio.month == 12), inicio.month % 12 + 1, 1)
    atividade = None
    linhas = []
    atividade_id = request.GET.get("atividade", "")
    if atividade_id.isdigit():
        atividade = atividades.filter(pk=atividade_id).first()
    if atividade:
        periodo = Q(frequencias__atividade=atividade, frequencias__data__gte=inicio, frequencias__data__lt=fim)
        consulta = (
            Beneficiario.objects.filter(periodo)
            .annotate(
                presencas=Count("frequencias", filter=periodo & Q(frequencias__presente=True)),
                faltas=Count("frequencias", filter=periodo & Q(frequencias__presente=False)),
            )
            .distinct()
            .order_by("nome_completo")
        )
        for b in consulta:
            total = b.presencas + b.faltas
            linhas.append({
                "nome": b.nome_completo,
                "presencas": b.presencas,
                "faltas": b.faltas,
                "percentual": round(100 * b.presencas / total) if total else 0,
            })
    return render(request, "gestao/relatorio_frequencia.html", {
        "atividades": atividades, "atividade": atividade, "inicio": inicio, "linhas": linhas,
    })
