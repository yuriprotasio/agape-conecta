from django.urls import path

from . import views, views_beneficiarios as benef

app_name = "gestao"

urlpatterns = [
    path("", views.painel, name="painel"),
    path("beneficiarios/", benef.lista, name="beneficiarios"),
    path("beneficiarios/novo/", benef.novo, name="beneficiario_novo"),
    path("beneficiarios/<int:pk>/", benef.ficha, name="beneficiario_ficha"),
    path("beneficiarios/<int:pk>/editar/", benef.editar, name="beneficiario_editar"),
    path("atendimentos/novo/", views.em_breve, name="atendimento_novo"),
]
