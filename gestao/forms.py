from django import forms
from django.utils import timezone

from .models import Atendimento, Atividade, Beneficiario


class DataInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%d", **kwargs)


class BeneficiarioForm(forms.ModelForm):
    class Meta:
        model = Beneficiario
        fields = [
            "nome_completo", "data_nascimento", "cpf", "nome_responsavel",
            "telefone_responsavel", "necessidades_apoio", "atividades", "situacao",
        ]
        widgets = {
            "data_nascimento": DataInput(),
            "atividades": forms.CheckboxSelectMultiple(),
            "necessidades_apoio": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["atividades"].queryset = Atividade.objects.filter(ativa=True)
        self.fields["data_nascimento"].widget.attrs["max"] = timezone.localdate().isoformat()


class AtendimentoForm(forms.ModelForm):
    class Meta:
        model = Atendimento
        fields = ["beneficiario", "data_hora", "tipo", "descricao", "encaminhamento"]
        widgets = {
            "data_hora": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "descricao": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["beneficiario"].queryset = Beneficiario.objects.filter(situacao=Beneficiario.Situacao.ATIVO)
        self.fields["data_hora"].input_formats = ["%Y-%m-%dT%H:%M"]
        if not self.instance.pk and not self.initial.get("data_hora"):
            self.initial["data_hora"] = timezone.localtime().replace(second=0, microsecond=0)
