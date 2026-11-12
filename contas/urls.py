from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("entrar/", views.entrar, name="login"),
    path("sair/", views.sair, name="logout"),
]
