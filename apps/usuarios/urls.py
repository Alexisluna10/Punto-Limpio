from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'usuarios'

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.signout, name='logout'),
    path('tasks/', views.tasks, name='tasks'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),

    path('recuperar-contrasena/',
         auth_views.PasswordResetView.as_view(
             template_name='usuarios/password_reset.html',
             html_email_template_name='usuarios/password_reset_email.html'
         ),
         name='password_reset'),

    path('recuperar-contrasena/envio/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='usuarios/password_reset_done.html'),
         name='password_reset_done'),

    path('recuperar-contrasena/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='usuarios/password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('recuperar-contrasena/completado/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='usuarios/password_reset_complete.html'),
         name='password_reset_complete'),


    # --- Auth Pública ---
    path('', views.home, name='home'),
    path('registrar/', views.signup, name='signup'),
    path('iniciar-sesion/', views.signin, name='signin'), # Tu vista personalizada
    path('cerrar-sesion/', views.signout, name='logout'),
    path('perfil/', views.perfil, name='perfil'),

    # --- Gestión de Usuarios (Admin) ---
    path('panel-admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('panel-admin/usuarios/nuevo/', views.admin_nuevo_usuario, name='admin_nuevo_usuario'),
    path('panel-admin/usuarios/eliminar/<int:usuario_id>/', views.admin_eliminar_usuario, name='admin_eliminar_usuario'),
    path('panel-admin/usuarios/editar/<int:usuario_id>/', views.admin_editar_usuario, name='admin_editar_usuario'),

    # --- APIs ---
    path('api/buscar-clientes/', views.buscar_clientes, name='buscar_clientes'),
    path('api/registrar-cliente-rapido/', views.api_registrar_cliente_rapido, name='api_registrar_cliente_rapido'),
    
    # --- Recuperar Contraseña (Django Default) ---
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="usuarios/password_reset.html"), name='password_reset'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="usuarios/password_reset_sent.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="usuarios/password_reset_form.html"), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="usuarios/password_reset_done.html"), name='password_reset_complete'),
]
