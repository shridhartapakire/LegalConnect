from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from apps.accounts.models import User


P = ParamSpec("P")
R = TypeVar("R", bound=HttpResponse)


def role_required(role: User.PrimaryRole) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Require an authenticated user with the supplied primary service role.

    A forbidden response, rather than a redirect to another dashboard, avoids
    accidentally implying that a user has access to a protected area.
    """

    def decorator(view_func: Callable[P, R]) -> Callable[P, R]:
        @login_required
        @wraps(view_func)
        def wrapped(request: HttpRequest, *args: P.args, **kwargs: P.kwargs) -> R:
            if request.user.primary_role != role:
                raise PermissionDenied("You do not have permission to access this area.")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
