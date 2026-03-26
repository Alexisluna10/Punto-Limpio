from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings

app_name = 'usuarios'

urlpatterns = [
    # --- Auth Pública ---
    path('', views.home, name='home'),
    path('registrar/', views.signup, name='signup'),
    path('iniciar-sesion/', views.signin, name='signin'),
    path('cerrar-sesion/', views.signout, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('tasks/', views.tasks, name='tasks'),

    # --- Recuperar Contraseña (VERSIÓN CORRECTA Y PROTEGIDA) ---
    path('recuperar-contrasena/',
         auth_views.PasswordResetView.as_view(
             template_name='usuarios/password_reset.html',
             email_template_name='usuarios/password_reset_email.html',
             html_email_template_name='usuarios/password_reset_email.html',
             from_email=settings.DEFAULT_FROM_EMAIL,
             success_url=reverse_lazy('usuarios:password_reset_done')
         ),
         name='password_reset'),

    path('recuperar-contrasena/envio/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='usuarios/password_reset_done.html'),
         name='password_reset_done'),

    path('recuperar-contrasena/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='usuarios/password_reset_confirm.html',
             success_url=reverse_lazy('usuarios:password_reset_complete')
         ),
         name='password_reset_confirm'),

    path('recuperar-contrasena/completado/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='usuarios/password_reset_complete.html'),
         name='password_reset_complete'),

    # --- Gestión de Usuarios (Admin) ---
    path('panel-admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('panel-admin/usuarios/nuevo/',
         views.admin_nuevo_usuario, name='admin_nuevo_usuario'),
    path('panel-admin/usuarios/eliminar/<int:usuario_id>/',
         views.admin_eliminar_usuario, name='admin_eliminar_usuario'),
    path('panel-admin/usuarios/editar/<int:usuario_id>/',
         views.admin_editar_usuario, name='admin_editar_usuario'),

    # --- APIs ---
    path('api/buscar-clientes/', views.buscar_clientes, name='buscar_clientes'),
    path('api/registrar-cliente-rapido/', views.api_registrar_cliente_rapido,
         name='api_registrar_cliente_rapido'),
]
