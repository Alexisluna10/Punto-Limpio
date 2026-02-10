from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
# Importamos tu formulario personalizado
from .forms import RegistroUsuarioForm
from django.contrib import messages
from usuarios.models import Usuario


def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == 'POST':
        # 1. Recibir los datos del formulario HTML
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # 2. VALIDACIONES DE SEGURIDAD

        # A) Que las contraseñas coincidan
        if password != confirm_password:
            messages.error(request, '❌ Las contraseñas no coinciden.')
            return render(request, 'signup.html')

        # B) Que el teléfono no exista ya (IMPORTANTE)
        if Usuario.objects.filter(telefono=telefono).exists():
            messages.error(
                request, '⚠️ Este teléfono ya está registrado. Por favor inicia sesión.')
            return redirect('signin')  # Lo mandamos al login si ya existe

        # C) Que el correo no exista ya
        if Usuario.objects.filter(email=email).exists():
            messages.error(
                request, '⚠️ Ese correo electrónico ya está en uso.')
            return render(request, 'signup.html')

        # 3. CREAR EL USUARIO
        try:
            # Aquí ocurre la magia: Usamos el telefono como username
            user = Usuario.objects.create_user(
                username=telefono,  # <--- EL TELÉFONO ES EL USUARIO
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Guardamos datos extra y rol
            user.telefono = telefono
            user.rol = 'cliente'
            user.save()

            # 4. ÉXITO
            messages.success(
                request, '✅ ¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
            return redirect('signin')

        except Exception as e:
            # Si pasa algo raro en la base de datos
            messages.error(request, f'Error al crear la cuenta: {str(e)}')
            return render(request, 'signup.html')

    # Si es GET (cuando entra a la página), muestra el formulario vacío
    return render(request, 'signup.html')


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
