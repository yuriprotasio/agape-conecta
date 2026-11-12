"""Controle de acesso por perfil, verificado no servidor em cada View (OWASP A01)."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def somente_administrador(view):
    @login_required
    @wraps(view)
    def interna(request, *args, **kwargs):
        if not request.user.eh_administrador:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return interna
