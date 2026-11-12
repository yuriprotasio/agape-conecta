from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AtendimentoForm
from .models import Atendimento


@login_required
def novo(request):
    inicial = {}
    beneficiario_id = request.GET.get("beneficiario", "")
    if beneficiario_id.isdigit():
        inicial["beneficiario"] = int(beneficiario_id)
    form = AtendimentoForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        atendimento = form.save(commit=False)
        atendimento.profissional = request.user  # autoria definida no servidor, nunca pelo formulário
        atendimento.save()
        messages.success(request, "Atendimento registrado.")
        return redirect("gestao:beneficiario_ficha", pk=atendimento.beneficiario_id)
    return render(request, "gestao/atendimento_form.html", {"form": form, "titulo": "Registrar atendimento"})


@login_required
def editar(request, pk):
    atendimento = get_object_or_404(Atendimento, pk=pk)
    if not atendimento.pode_editar(request.user):
        raise PermissionDenied
    form = AtendimentoForm(request.POST or None, instance=atendimento)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Atendimento atualizado.")
        return redirect("gestao:beneficiario_ficha", pk=atendimento.beneficiario_id)
    return render(request, "gestao/atendimento_form.html", {"form": form, "titulo": "Editar atendimento"})
