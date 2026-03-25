from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('tasks/', views.tasks, name='tasks'),
    path('panel-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('panel-admin/configuracion/', views.admin_configuracion, name='admin_configuracion'),
    path('prueba/', views.prueba, name='prueba'),
]