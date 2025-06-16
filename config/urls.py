"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.views.generic import TemplateView

from django.conf.urls import handler404, handler500, handler403, handler400
from core import views as core_views
from sitecontent.views import CustomLoginView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', content_type='text/plain'
    )),
    path('', include('orders.urls')),
    path('', include('sitecontent.urls')),
    path('', include('gyoumu.urls')),
    path('accounts/login/', CustomLoginView.as_view(template_name='sitecontent/login.html'), name='login'),
    #path('accounts/login/', auth_views.LoginView.as_view(template_name='sitecontent/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]

# ハンドラを明示的に指定
handler400 = core_views.custom_bad_request
handler403 = core_views.custom_permission_denied
handler404 = core_views.custom_page_not_found
handler500 = core_views.custom_server_error

#if settings.DEBUG:
#    urlpatterns += [path('__reload__/', include('django_browser_reload.urls'))]