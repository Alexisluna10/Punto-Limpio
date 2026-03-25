from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistroUsuarioForm
from django.contrib import messages
from .models import Usuario
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
import json
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from apps.core.decorators import solo_admin, solo_cliente, solo_trabajador
from apps.usuarios.models import Usuario
from apps.usuarios.forms import RegistroUsuarioAdminForm
from apps.servicios.models import Pedido # Para ver historial en perfil


def home(request):
    return render(request, 'usuarios/home.html')


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
            return render(request, 'usuarios/signup.html')

        # B) Que el teléfono no exista ya (IMPORTANTE)
        if Usuario.objects.filter(telefono=telefono).exists():
            messages.error(
                request, '⚠️ Este teléfono ya está registrado. Por favor inicia sesión.')
            return redirect('usuarios:signin')  # Lo mandamos al login si ya existe

        # C) Que el correo no exista ya
        if Usuario.objects.filter(email=email).exists():
            messages.error(
                request, '⚠️ Ese correo electrónico ya está en uso.')
            return render(request, 'usuarios/signup.html')

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
            return redirect('usuarios:signin')

        except Exception as e:
            # Si pasa algo raro en la base de datos
            messages.error(request, f'Error al crear la cuenta: {str(e)}')
            return render(request, 'usuarios/signup.html')

    # Si es GET (cuando entra a la página), muestra el formulario vacío
    return render(request, 'usuarios/signup.html')


def tasks(request):
    return render(request, 'usuarios/tasks.html')


def signout(request):
    logout(request)
    return redirect('usuarios:home')


def signin(request):
    if request.method == 'GET':
        return render(request, 'usuarios/signin.html', {
            'form': AuthenticationForm()
        })
    else:
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is None:
            return render(request, 'usuarios/signin.html', {
                'form': AuthenticationForm(),
                'error': 'Usuario o contraseña incorrectos'
            })
        else:
            login(request, user)
            return redirect('usuarios:tasks')


def forgotpassword(request):
    return render(request, 'usuarios/forgotpassword.html')


@solo_admin
def admin_usuarios(request):
    trabajadores = Usuario.objects.filter(rol__in=['operador', 'admin'])
    clientes = Usuario.objects.filter(rol='cliente')
    tab = request.GET.get('tab', 'clientes')

    context = {
        'trabajadores': trabajadores,
        'clientes': clientes,
        'tab': tab,
        'total_trabajadores': trabajadores.count(),
        'total_clientes': clientes.count(),
    }
    return render(request, 'admin/usuarios/usuarios.html', context)

@solo_admin
def admin_nuevo_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioAdminForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            rol = form.cleaned_data['rol']
            user.rol = rol
            user.save()

            if rol == 'admin':
                grupo, created = Group.objects.get_or_create(
                    name='Administrador')
                user.groups.add(grupo)
            elif rol == 'operador':
                grupo, created = Group.objects.get_or_create(name='Trabajador')
                user.groups.add(grupo)

            messages.success(request, 'Usuario registrado exitosamente.')
            return redirect('usuarios:admin_usuarios')
    else:
        form = RegistroUsuarioAdminForm()

    return render(request, 'admin/usuarios/nuevo_usuario.html', {'form': form})

@solo_admin
def admin_eliminar_usuario(request, usuario_id):
    try:
        usuario = Usuario.objects.get(id=usuario_id)
        if usuario != request.user:
            usuario.delete()
            messages.success(request, 'Usuario eliminado exitosamente.')
        else:
            messages.error(request, 'No puedes eliminarte a ti mismo.')
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')

    return redirect('usuarios:admin_usuarios')

@solo_admin
def admin_editar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.telefono = telefono if telefono else None
        usuario.email = email

        if password:
            usuario.set_password(password)

        usuario.save()

        MovimientoOperador.objects.create(
            operador=request.user,
            accion='actualizo',
            detalles=f'Editó datos del usuario: {usuario.username}'
        )

        messages.success(request, f'Usuario "{usuario.username}" actualizado exitosamente.')
        return redirect('usuarios:admin_usuarios')

    return JsonResponse({
        'id': usuario.id,
        'username': usuario.username,
        'first_name': usuario.first_name,
        'last_name': usuario.last_name,
        'telefono': usuario.telefono or '',
        'email': usuario.email,
        'rol': usuario.get_rol_display(),
    })

@login_required
def buscar_clientes(request):
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'clientes': []})

    clientes = Usuario.objects.filter(
        rol='cliente'
    ).filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(telefono__icontains=query)
    )[:10]

    clientes_data = [
        {
            'id': c.id,
            'username': c.username,
            'nombre_completo': f"{c.first_name} {c.last_name}".strip() or c.username,
            'telefono': c.telefono or 'Sin telefono'
        }
        for c in clientes
    ]

    return JsonResponse({'clientes': clientes_data})

@solo_trabajador
@require_POST
def api_registrar_cliente_rapido(request):
    """
    Crea un cliente desde la pantalla de Nuevo Servicio sin recargar.
    Genera usuario y contraseña automática basada en el teléfono.
    """
    try:
        data = json.loads(request.body)

        nombre = data.get('nombre', '').strip()
        apellido = data.get('apellido', '').strip()
        telefono = data.get('telefono', '').strip()
        email = data.get('email', '').strip()

        # 1. Validaciones básicas
        if not nombre or not telefono:
            return JsonResponse({'success': False, 'message': 'Nombre y Teléfono son obligatorios.'})

        if Usuario.objects.filter(telefono=telefono).exists():
            return JsonResponse({'success': False, 'message': 'Ya existe un cliente con este teléfono.'})

        if email and Usuario.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Ese correo ya está registrado.'})

        # 2. Generación automática de Username (Usamos el teléfono para que sea único)
        username = telefono

        # 3. Crear el usuario
        nuevo_cliente = Usuario.objects.create(
            username=username,
            first_name=nombre,
            last_name=apellido,
            email=email,
            telefono=telefono,
            rol='cliente',
            # Contraseña por defecto es su teléfono
            password=make_password(telefono)
        )

        return JsonResponse({
            'success': True,
            'message': 'Cliente registrado correctamente.',
            'cliente': {
                'id': nuevo_cliente.id,
                'nombre_completo': f"{nuevo_cliente.first_name} {nuevo_cliente.last_name} ({nuevo_cliente.telefono})"
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@solo_cliente
def perfil(request):
    usuario = request.user

    if request.method == 'POST':
        # 1. Recibir los datos del formulario (Nombres del HTML)
        nuevo_nombre = request.POST.get('first_name', '').strip()
        nuevo_apellido = request.POST.get('last_name', '').strip()
        nuevo_email = request.POST.get('email', '').strip()
        nueva_direccion = request.POST.get('direccion', '').strip()

        errores = False

        # 2. Actualizar Nombre y Apellido (Si escribieron algo)
        if nuevo_nombre:
            usuario.first_name = nuevo_nombre
        if nuevo_apellido:
            usuario.last_name = nuevo_apellido

        # 3. Actualizar Dirección (El dato clave que faltaba)
        usuario.direccion = nueva_direccion

        # 4. Validar y Actualizar Email (Con cuidado de duplicados)
        if nuevo_email and nuevo_email != usuario.email:
            # Revisar si alguien más ya usa ese correo
            if Usuario.objects.filter(email=nuevo_email).exclude(id=usuario.id).exists():
                messages.error(
                    request, '❌ Ese correo electrónico ya está registrado por otra persona.')
                errores = True
            else:
                usuario.email = nuevo_email
                # OJO: NO cambiamos usuario.username, ese sigue siendo el teléfono.

        # 5. Guardar cambios si todo está bien
        if not errores:
            usuario.save()
            messages.success(
                request, '✅ ¡Tu información ha sido actualizada correctamente!')
            return redirect('usuarios:perfil')

        # Si hubo errores, el código sigue y recarga la página mostrando las alertas

    # --- SECCIÓN GET (Mostrar datos) ---
    ultimo_pedido = Pedido.objects.filter(
        cliente=usuario
    ).exclude(
        estado='cancelado'
    ).order_by('-fecha_recepcion').first()

    context = {
        'ultimo_pedido': ultimo_pedido,
        'fecha_registro': usuario.date_joined
    }
    return render(request, 'cliente/perfil.html', context)