"""Cria dados fictícios para demonstração e testes de usabilidade (nenhum dado real)."""

from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from contas.models import Usuario
from gestao.models import Atividade, Beneficiario, Frequencia

NOMES = [
    "Ana Souza", "Bruno Lima", "Carlos Pereira", "Daniela Rocha", "Eduardo Alves", "Fernanda Dias",
    "Gabriel Costa", "Helena Martins", "Igor Ribeiro", "Joana Freitas", "Lucas Teixeira", "Marina Lopes",
    "Nicolas Barros", "Olívia Ramos", "Paulo Nunes", "Rafaela Moreira", "Samuel Pinto", "Tatiane Cardoso",
    "Vítor Mendes", "Yasmin Araújo",
]


class Command(BaseCommand):
    help = "Carrega usuários, uma atividade e 20 beneficiários fictícios."

    def add_arguments(self, parser):
        parser.add_argument("--senha", required=True, help="Senha dos usuários de demonstração (mín. 10 caracteres).")

    @transaction.atomic
    def handle(self, *args, senha, **opcoes):
        gestora, _ = Usuario.objects.get_or_create(
            email="gestora@exemplo.org", defaults={"nome": "Gestora Demo", "perfil": Usuario.Perfil.ADMINISTRADOR}
        )
        carla, _ = Usuario.objects.get_or_create(email="carla@exemplo.org", defaults={"nome": "Carla"})
        for u in (gestora, carla):
            u.set_password(senha)
            u.save()
        oficina, _ = Atividade.objects.get_or_create(
            nome="Oficina de Artes", defaults={"dias_semana": "terça", "horario": "14:00"}
        )
        for i, nome in enumerate(NOMES):
            b, _ = Beneficiario.objects.get_or_create(
                nome_completo=nome,
                defaults={
                    "data_nascimento": date(2005 + i % 12, i % 12 + 1, 10),
                    "nome_responsavel": f"Responsável de {nome.split()[0]}",
                    "telefone_responsavel": "(12) 90000-0000",
                },
            )
            b.atividades.add(oficina)
        bruno = Beneficiario.objects.get(nome_completo="Bruno Lima")
        ultima_terca = date.today() - timedelta(days=(date.today().weekday() - 1) % 7 or 7)
        for semanas in (1, 2, 3):
            Frequencia.objects.update_or_create(
                beneficiario=bruno, atividade=oficina, data=ultima_terca - timedelta(weeks=semanas),
                defaults={"presente": False, "registrado_por": carla},
            )
        self.stdout.write(self.style.SUCCESS("Dados fictícios carregados: gestora@exemplo.org e carla@exemplo.org."))
