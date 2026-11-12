from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm


def entrar(request):
    if request.user.is_authenticated:
        return redirect("gestao:painel")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.usuario)  # o Django gera um novo identificador de sessão
        return redirect("gestao:painel")
    return render(request, "contas/login.html", {"form": form})


@require_POST
def sair(request):
    logout(request)  # encerra a sessão no servidor
    return redirect("contas:login")
