from django.shortcuts import redirect
from django.contrib import messages

def solo_cliente(view_func):
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('usuarios:signin')

        if request.user.rol == 'cliente':
            return view_func(request, *args, **kwargs)
        else:
            # Si no es cliente, lo mandamos a donde pertenece
            if request.user.rol == 'operador':
                return redirect('servicios:trabajador_dashboard')
            return redirect('core:admin_dashboard')
    return wrapper_func

def solo_trabajador(view_func):
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('usuarios:signin')

        if request.user.rol == 'operador':
            return view_func(request, *args, **kwargs)
        else:
            messages.warning(request, "⛔ Área exclusiva de Operadores.")
            if request.user.rol == 'admin' or request.user.is_superuser:
                return redirect('core:admin_dashboard')
            return redirect('servicios:cliente_dashboard')
    return wrapper_func

def solo_admin(view_func):
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('usuarios:signin')

        if request.user.rol == 'admin' or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "⛔ Área exclusiva de Administradores.")
            if request.user.rol == 'operador':
                return redirect('servicios:trabajador_dashboard')
            return redirect('servicios:cliente_dashboard')
    return wrapper_func