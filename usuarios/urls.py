from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.signout, name='logout'),
    path('tasks/', views.tasks, name='tasks'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('recuperar-contrasena/',
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html',
             html_email_template_name='password_reset_email.html'
         ),
         name='password_reset'),

    path('recuperar-contrasena/envio/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'),
         name='password_reset_done'),

    path('recuperar-contrasena/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('recuperar-contrasena/completado/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'),
         name='password_reset_complete'),
]
