from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.cache import cache

MENSAGEM_GENERICA = "E-mail ou senha incorretos."
MENSAGEM_BLOQUEIO = "Muitas tentativas sem sucesso. Aguarde 15 minutos e tente novamente."


def _chave(email):
    return f"login-falhas:{email.strip().lower()}"


class LoginForm(forms.Form):
    email = forms.EmailField(label="E-mail", max_length=254, widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}))
    password = forms.CharField(label="Senha", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.usuario = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get("email")
        senha = self.cleaned_data.get("password")
        if not email or not senha:
            return self.cleaned_data
        chave = _chave(email)
        if cache.get(chave, 0) >= settings.LOGIN_MAX_TENTATIVAS:
            raise forms.ValidationError(MENSAGEM_BLOQUEIO)
        usuario = authenticate(self.request, username=email.lower(), password=senha)
        if usuario is None:
            cache.set(chave, cache.get(chave, 0) + 1, settings.LOGIN_JANELA_SEGUNDOS)
            raise forms.ValidationError(MENSAGEM_GENERICA)
        cache.delete(chave)
        self.usuario = usuario
        return self.cleaned_data
