from django.urls import path

from . import views, views_beneficiarios as benef, views_chamada as chamada, views_atendimentos as atend, views_relatorios as relatorios

app_name = "gestao"

urlpatterns = [
    path("", views.painel, name="painel"),
    path("beneficiarios/", benef.lista, name="beneficiarios"),
    path("beneficiarios/novo/", benef.novo, name="beneficiario_novo"),
    path("beneficiarios/<int:pk>/", benef.ficha, name="beneficiario_ficha"),
    path("beneficiarios/<int:pk>/editar/", benef.editar, name="beneficiario_editar"),
    path("chamada/", chamada.chamada, name="chamada"),
    path("chamada/<int:atividade_id>/resultado/", chamada.chamada_resultado, name="chamada_resultado"),
    path("atendimentos/novo/", atend.novo, name="atendimento_novo"),
    path("atendimentos/<int:pk>/editar/", atend.editar, name="atendimento_editar"),
    path("relatorios/frequencia/", relatorios.frequencia_mensal, name="relatorio_frequencia"),
]
