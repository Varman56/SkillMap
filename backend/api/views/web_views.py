from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login
from django.contrib import messages

def login_page(request):
    # Если пользователь уже авторизован, сразу кидаем его на матрицу, 
    # чтобы он не логинился дважды
    if request.user.is_authenticated:
        return redirect('matrix')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Проверяем пользователя через твой кастомный бэкенд
        user = authenticate(request, email=email, password=password)

        if user is not None:
            # Встроенная функция авторизации Django для сессий
            django_login(request, user)
            return redirect('matrix') 
        else:
            messages.error(request, 'Неверный email или пароль')

    # Для GET-запроса просто показываем страницу с формой
    return render(request, 'login.html')