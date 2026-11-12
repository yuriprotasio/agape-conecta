from django.contrib import admin

from .models import Atendimento, Atividade, Beneficiario, Frequencia


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ["nome", "dias_semana", "horario", "ativa"]
    list_filter = ["ativa"]


@admin.register(Beneficiario)
class BeneficiarioAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "data_nascimento", "situacao"]
    list_filter = ["situacao", "atividades"]
    search_fields = ["nome_completo"]
    filter_horizontal = ["atividades"]

    def has_delete_permission(self, request, obj=None):
        return False  # beneficiários são inativados, nunca excluídos


@admin.register(Frequencia)
class FrequenciaAdmin(admin.ModelAdmin):
    list_display = ["beneficiario", "atividade", "data", "presente"]
    list_filter = ["atividade", "presente"]


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):
    list_display = ["beneficiario", "tipo", "data_hora", "profissional"]
    list_filter = ["tipo"]
