from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import Atividade, Frequencia
from .servicos import alertas_de_faltas, beneficiarios_da_chamada, registrar_chamada


def _ler_data(texto):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


@login_required
def chamada(request):
    atividades = Atividade.objects.filter(ativa=True)
    hoje = timezone.localdate()
    atividade = None
    atividade_id = request.POST.get("atividade") or request.GET.get("atividade")
    if atividade_id and str(atividade_id).isdigit():
        atividade = get_object_or_404(Atividade, pk=atividade_id, ativa=True)
    texto_data = request.POST.get("data") or request.GET.get("data")
    data = _ler_data(texto_data) if texto_data else hoje
    erro_data = None
    if data is None:
        erro_data, data = "Informe uma data válida.", hoje
    elif data > hoje:
        erro_data = "A data não pode ser futura. Informe a data de hoje ou uma data anterior."

    linhas = []
    erro = None
    if atividade:
        existentes = {f.beneficiario_id: f for f in Frequencia.objects.filter(atividade=atividade, data=data)}
        for b in beneficiarios_da_chamada(atividade):
            anterior = existentes.get(b.pk)
            if request.method == "POST":
                estado = request.POST.get(f"estado_{b.pk}", "")
                justificativa = request.POST.get(f"justificativa_{b.pk}", "")
            else:
                estado = "" if anterior is None else ("presente" if anterior.presente else "ausente")
                justificativa = anterior.justificativa if anterior else ""
            linhas.append({"b": b, "estado": estado, "justificativa": justificativa})

        if request.method == "POST" and not erro_data:
            marcacoes = {}
            for linha in linhas:
                if linha["estado"] in ("presente", "ausente"):
                    marcacoes[linha["b"].pk] = (linha["estado"] == "presente", linha["justificativa"])
            try:
                presentes, ausentes = registrar_chamada(atividade, data, marcacoes, request.user)
            except ValidationError as e:
                erro = " ".join(e.messages)
            else:
                messages.success(request, f"Frequência registrada: {presentes} presentes, {ausentes} ausentes.")
                url = reverse("gestao:chamada_resultado", args=[atividade.pk])
                return redirect(f"{url}?data={data.isoformat()}")

    contagem = {
        "total": len(linhas),
        "presentes": sum(1 for l in linhas if l["estado"] == "presente"),
        "ausentes": sum(1 for l in linhas if l["estado"] == "ausente"),
    }
    return render(request, "gestao/chamada.html", {
        "atividades": atividades, "atividade": atividade, "data": data, "hoje": hoje,
        "linhas": linhas, "contagem": contagem, "erro": erro, "erro_data": erro_data,
    })


@login_required
def chamada_resultado(request, atividade_id):
    atividade = get_object_or_404(Atividade, pk=atividade_id)
    data = _ler_data(request.GET.get("data")) or timezone.localdate()
    return render(request, "gestao/chamada_resultado.html", {
        "atividade": atividade, "data": data, "alertas": alertas_de_faltas(atividade),
    })
