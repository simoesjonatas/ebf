from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('termos-de-uso/', views.termos_uso, name='termos_uso'),
    path('access-denied/', views.access_denied, name='access_denied'),
]
