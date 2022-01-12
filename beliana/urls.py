"""beliana URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
#from django.contrib import admin
#from django.urls import include, path
#from zmluvy.views import OsobaAutorListView

#urlpatterns = [
    #path('zmluvy/', include('zmluvy.urls')),
    #path('admin/', admin.site.urls),
    #path('', OsobaAutorListView.as_view(), name='article-list'),
    #path('autori/', OsobaAutorListView.as_view())
#]

from django.contrib import admin
from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView

#required by file upload
from django.conf import settings # new
from django.urls import include # new
from django.conf.urls.static import static # new

from ipdb import set_trace as trace

#trace()
urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy('admin:index'))),
    path('admin/', admin.site.urls),
    path('export_action/', include("admin_export_action.urls", namespace="admin_export_action")),
    # Recent versions of Python however have special syntax to include an iterable in a list by using the asterisk (*)
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # needed because of file upload
]

