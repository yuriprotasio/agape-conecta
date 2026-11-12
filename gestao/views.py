from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@login_required
def painel(request):
    return render(request, "gestao/painel.html")



@never_cache
def saude(request):
    """Verificação de saúde para o monitoramento: responde 200 se a aplicação e o banco estão no ar."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse({"status": "erro", "banco": "indisponivel"}, status=503)
    return JsonResponse({"status": "ok", "banco": "ok"})
