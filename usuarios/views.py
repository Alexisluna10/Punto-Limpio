from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
# Importamos tu formulario personalizado
from .forms import RegistroUsuarioForm


def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('tasks')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'signup.html', {
        'form': form
    })


def tasks(request):
    return render(request, 'tasks.html')


def signout(request):
    logout(request)
    return redirect('home')


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm()
        })
    else:
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is None:
            return render(request, 'signin.html', {
                'form': AuthenticationForm(),
                'error': 'Usuario o contraseña incorrectos'
            })
        else:
            login(request, user)
            return redirect('tasks')


def forgotpassword(request):
    return render(request, 'forgotpassword.html')
