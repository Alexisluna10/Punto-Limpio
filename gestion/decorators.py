from django.shortcuts import redirect
from django.contrib import messages


def solo_cliente(view_func):
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # REGLA ESTRICTA: Solo pasa si el rol es EXACTAMENTE 'cliente'
        if request.user.rol == 'cliente':
            return view_func(request, *args, **kwargs)
        else:
            # Si no es cliente, lo expulsamos a su dashboard correspondiente
            if request.user.rol == 'operador':
                return redirect('trabajador_dashboard')
            elif request.user.rol == 'admin' or request.user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('login')
    return wrapper_func


def solo_trabajador(view_func):
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # REGLA ESTRICTA: Solo pasa si el rol es 'operador'
        # (Quitamos el permiso de superusuario aquí para que sea estricto)
        if request.user.rol == 'operador':
            return view_func(request, *args, **kwargs)
        else:
            messages.warning(
                request, "⛔ Acceso denegado: Área exclusiva de Operadores.")
            if request.user.rol == 'cliente':
                return redirect('cliente_dashboard')
            elif request.user.rol == 'admin' or request.user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('login')
    return wrapper_func


def solo_admin(view_func):
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # El Admin SÍ puede ser superusuario o tener rol 'admin'
        if request.user.rol == 'admin' or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(
                request, "⛔ Acceso denegado: Área exclusiva de Administradores.")
            if request.user.rol == 'operador':
                return redirect('trabajador_dashboard')
            elif request.user.rol == 'cliente':
                return redirect('cliente_dashboard')
            else:
                return redirect('login')
    return wrapper_func
