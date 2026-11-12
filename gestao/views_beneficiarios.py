from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BeneficiarioForm
from .models import Beneficiario, normalizar
from .permissoes import somente_administrador


@login_required
def lista(request):
    termo = request.GET.get("q", "").strip()[:100]
    beneficiarios = Beneficiario.objects.all()
    if termo:
        # O ORM gera consulta parametrizada; o termo nunca é concatenado ao SQL.
        beneficiarios = beneficiarios.filter(nome_busca__contains=normalizar(termo))
    return render(request, "gestao/beneficiarios/lista.html", {"beneficiarios": beneficiarios, "termo": termo})


@login_required
def ficha(request, pk):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)
    historico = []
    for f in beneficiario.frequencias.select_related("atividade"):
        historico.append({"quando": f.data, "tipo": "frequencia", "item": f})
    for a in beneficiario.atendimentos.select_related("profissional"):
        historico.append({"quando": timezone.localtime(a.data_hora).date(), "tipo": "atendimento", "item": a})
    historico.sort(key=lambda h: h["quando"], reverse=True)
    alertas = [
        (atividade, total)
        for atividade in beneficiario.atividades.all()
        if (total := beneficiario.faltas_consecutivas(atividade)) >= 3
    ]
    return render(
        request,
        "gestao/beneficiarios/ficha.html",
        {"b": beneficiario, "historico": historico, "alertas": alertas},
    )


@somente_administrador
def novo(request):
    form = BeneficiarioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        b = form.save()
        messages.success(request, f"Beneficiário {b.nome_completo} cadastrado.")
        return redirect("gestao:beneficiario_ficha", pk=b.pk)
    return render(request, "gestao/beneficiarios/form.html", {"form": form, "titulo": "Novo beneficiário"})


@somente_administrador
def editar(request, pk):
    b = get_object_or_404(Beneficiario, pk=pk)
    form = BeneficiarioForm(request.POST or None, instance=b)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cadastro atualizado.")
        return redirect("gestao:beneficiario_ficha", pk=b.pk)
    return render(request, "gestao/beneficiarios/form.html", {"form": form, "titulo": f"Editar {b.nome_completo}"})
