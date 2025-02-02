from django.urls import path 
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('reserva', views.reserva, name='reserva'),
    path('esqueceuasenha', views.esqueceuasenha, name='esqueceuasenha'),
    path('perfil', views.perfil, name='perfil'),
    path('confirmacaodasenha', views.confirmacaodasenha, name='confirmacaodasenha'),
    path('minhasreservas', views.minhasreservas, name='minhasreservas'),
    path('editarperfil', views.editarperfil, name='editarperfil'),
    path('contaexcluida', views.contaexcluida, name='contaexcluida'),
    path('salvaralteracoes', views.salvaralteracoes, name='salvaralteracoes'),
    path('editarreserva', views.editarreserva, name='editarreserva'),
    path('cancelarreserva', views.cancelarreserva, name='cancelarreserva'),
    path('reservaexcluida', views.reservaexcluida, name='reservaexcluida'),
]