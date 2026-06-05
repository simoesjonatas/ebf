from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('auth/', include('accounts.urls')),
    path('responsaveis/', include('responsaveis.urls')),
    path('criancas/', include('criancas.urls')),
    path('presencas/', include('presencas.urls')),
    path('etiquetas/', include('etiquetas.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('turmas/', include('turmas.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
