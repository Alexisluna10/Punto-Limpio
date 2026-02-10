from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.


def prueba(request):
    return HttpResponse("Prueba app gestión")


@login_required
def admin_dashboard(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/dashboard.html')


@login_required
def admin_servicios(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/servicios.html')

@login_required
def admin_finanzas(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/finanzas/finanzas.html')


@login_required
def admin_usuarios(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/usuarios.html')


@login_required
def admin_precios(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/precios.html')


@login_required
def admin_inventarios(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/inventarios.html')


@login_required
def admin_historialVentas(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/historial/historial-ventas.html')


@login_required
def admin_historialMovimientos(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/historial/historial-movimientos.html')


@login_required
def admin_incidencias(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/incidencias.html')


@login_required
def admin_configuracion(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/configuracion.html')

@login_required
def trabajador_dashboard(request):
    return render(request, 'trabajador/dashboard.html')


@login_required
def cliente_dashboard(request):
    return render(request, 'cliente/dashboard.html')


@login_required
def tasks(request):
    user = request.user

    if user.groups.filter(name='Administrador').exists():
        return redirect('admin_dashboard')

    elif user.groups.filter(name='Trabajador').exists():
        return redirect('trabajador_dashboard')

    else:
        return redirect('cliente_dashboard')
