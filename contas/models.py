from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _criar(self, email, password, **campos):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        usuario = self.model(email=self.normalize_email(email).lower(), **campos)
        usuario.set_password(password)  # grava apenas o hash Argon2
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **campos):
        campos.setdefault("perfil", Usuario.Perfil.COLABORADOR)
        return self._criar(email, password, **campos)

    def create_superuser(self, email, password=None, **campos):
        campos.update(perfil=Usuario.Perfil.ADMINISTRADOR, is_staff=True, is_superuser=True)
        return self._criar(email, password, **campos)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Pessoa da equipe que acessa o sistema. A senha fica apenas como hash (campo password)."""

    class Perfil(models.TextChoices):
        ADMINISTRADOR = "administrador", "Administrador"
        COLABORADOR = "colaborador", "Colaborador"

    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    perfil = models.CharField(max_length=20, choices=Perfil.choices, default=Perfil.COLABORADOR)
    is_active = models.BooleanField("ativo", default=True)
    is_staff = models.BooleanField("acesso ao painel técnico", default=False)
    criado_em = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["nome"]

    def __str__(self):
        return self.nome or self.email

    @property
    def eh_administrador(self):
        return self.perfil == self.Perfil.ADMINISTRADOR or self.is_superuser
