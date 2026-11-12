from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def validar_data_nao_futura(valor):
    if isinstance(valor, datetime):
        if valor > timezone.now():
            raise ValidationError("A data e a hora não podem ser futuras.")
        return
    if valor > timezone.localdate():
        raise ValidationError("A data não pode ser futura. Informe a data de hoje ou uma data anterior.")


def validar_cpf(valor):
    numeros = "".join(c for c in valor if c.isdigit())
    if len(numeros) != 11 or numeros == numeros[0] * 11:
        raise ValidationError("CPF inválido. Informe os 11 números.")
    for tamanho in (9, 10):
        soma = sum(int(numeros[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11 % 10
        if digito != int(numeros[tamanho]):
            raise ValidationError("CPF inválido. Confira os números digitados.")


class Atividade(models.Model):
    """Turma ou oficina em que a frequência é registrada."""

    nome = models.CharField(max_length=120, unique=True)
    descricao = models.TextField("descrição", blank=True, max_length=1000)
    dias_semana = models.CharField("dias da semana", max_length=60)
    horario = models.TimeField("horário")
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Beneficiario(models.Model):
    """Pessoa atendida pela associação. Não é excluída: é inativada para preservar o histórico."""

    class Situacao(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        INATIVO = "inativo", "Inativo"

    nome_completo = models.CharField("nome completo", max_length=150)
    data_nascimento = models.DateField("data de nascimento", validators=[validar_data_nao_futura])
    cpf = models.CharField("CPF", max_length=14, blank=True, null=True, unique=True, validators=[validar_cpf])
    nome_responsavel = models.CharField("nome do responsável", max_length=150, blank=True)
    telefone_responsavel = models.CharField("telefone do responsável", max_length=20)
    necessidades_apoio = models.TextField(
        "necessidades de apoio",
        blank=True,
        max_length=1000,
        help_text="Adaptações práticas de que a pessoa precisa. Não registre diagnóstico ou CID.",
    )
    situacao = models.CharField("situação", max_length=10, choices=Situacao.choices, default=Situacao.ATIVO)
    atividades = models.ManyToManyField(Atividade, related_name="beneficiarios", blank=True)
    data_cadastro = models.DateField("data de cadastro", auto_now_add=True)

    class Meta:
        ordering = ["nome_completo"]
        verbose_name = "beneficiário"

    def __str__(self):
        return self.nome_completo

    @property
    def idade(self):
        hoje = timezone.localdate()
        n = self.data_nascimento
        return hoje.year - n.year - ((hoje.month, hoje.day) < (n.month, n.day))

    @property
    def menor_de_idade(self):
        return self.idade < 18

    def clean(self):
        if self.cpf:
            self.cpf = "".join(c for c in self.cpf if c.isdigit())
        else:
            self.cpf = None
        if self.data_nascimento and self.data_nascimento <= timezone.localdate() and self.menor_de_idade and not self.nome_responsavel:
            raise ValidationError({"nome_responsavel": "Informe o responsável, pois o beneficiário é menor de idade."})

    def faltas_consecutivas(self, atividade):
        """Conta faltas sem justificativa seguidas, da chamada mais recente para trás."""
        total = 0
        for registro in self.frequencias.filter(atividade=atividade).order_by("-data"):
            if registro.presente or registro.justificativa:
                break
            total += 1
        return total


class Frequencia(models.Model):
    """Presença ou ausência de um beneficiário em uma atividade, em uma data."""

    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.PROTECT, related_name="frequencias")
    atividade = models.ForeignKey(Atividade, on_delete=models.PROTECT, related_name="frequencias")
    data = models.DateField(validators=[validar_data_nao_futura])
    presente = models.BooleanField()
    justificativa = models.CharField(max_length=200, blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="frequencias")
    registrado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data"]
        verbose_name = "frequência"
        constraints = [
            models.UniqueConstraint(fields=["beneficiario", "atividade", "data"], name="frequencia_unica_por_dia"),
        ]
        indexes = [models.Index(fields=["atividade", "data"])]

    def __str__(self):
        estado = "Presente" if self.presente else "Ausente"
        return f"{self.beneficiario} · {self.atividade} · {self.data:%d/%m/%Y} · {estado}"


class Atendimento(models.Model):
    """Atendimento individual registrado por um profissional da equipe."""

    class Tipo(models.TextChoices):
        PEDAGOGICO = "pedagogico", "Pedagógico"
        PSICOLOGICO = "psicologico", "Psicológico"
        SOCIAL = "social", "Social"
        OUTRO = "outro", "Outro"

    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.PROTECT, related_name="atendimentos")
    profissional = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="atendimentos")
    data_hora = models.DateTimeField("data e hora", validators=[validar_data_nao_futura])
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    descricao = models.TextField("descrição", max_length=3000)
    encaminhamento = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-data_hora"]

    def __str__(self):
        return f"{self.beneficiario} · {self.get_tipo_display()} · {self.data_hora:%d/%m/%Y}"

    def pode_editar(self, usuario):
        return usuario.eh_administrador or usuario.pk == self.profissional_id
