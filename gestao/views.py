from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def painel(request):
    return render(request, "gestao/painel.html")


@login_required
def em_breve(request):
    return render(request, "gestao/em_breve.html")
