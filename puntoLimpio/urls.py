"""
URL configuration for puntoLimpio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from usuarios import views
from django.conf import settings
from django.conf.urls.static import static

# from usuarios.views import hello #Asi se debe importar la funcion hello para probar
# from usuarios import views #Así funciona para importar todo el archivo views
urlpatterns = [
    path('admin/', admin.site.urls),
    # Lo que esta '' a lado del path es la url que se debe agregar para que te pueda redirigir a la función/vista que se muestra
    # en tu url del navegador, y lo que esta a la derecha ',' es la función que se va a ejecutar
    # path('', hello), #Asi se debe agregar la url para probar
    # path('', views.hello), #Así se usa para probar una función de esa vista

    # Sus vistas estan en usuarios/views.py, esto para que no se repita codigo y este mejor orgnizado
    path('', include('usuarios.urls')),
    # Sus urls estan en usuarios/urls.py
    path('', include('gestion.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
