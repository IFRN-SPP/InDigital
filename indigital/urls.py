from django.urls import path 
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('reserva', views.reserva, name='reserva'),
    path('login', views.login, name='login'),
    path('esqueceuasenha', views.esqueceuasenha, name='esqueceuasenha'),
    path('cadastro', views.cadastro, name='cadastro'),
    path('perfil', views.perfil, name='perfil'),
    path('confirmacaodasenha', views.confirmacaodasenha, name='confirmacaodasenha'),
    path('minhasreservas', views.minhasreservas, name='minhasreservas'),
]