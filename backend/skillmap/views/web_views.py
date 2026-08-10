from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login as django_login,
    logout as django_logout,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST


def login_page(request):
    if request.user.is_authenticated:
        return redirect("my-profile")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(
            request,
            email=email,
            password=password,
        )

        if user is None or not user.is_active:
            messages.error(request, "Неверная почта или пароль")
        else:
            django_login(request, user)
            return redirect("my-profile")

    return render(request, "login.html")


@require_POST
@login_required
def logout_page(request):
    django_logout(request)
    return redirect("login")
