from django.urls import path 
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('listar/reservas/', views.listar_reservas, name='listar_reservas'),
    path('criar/reserva/', views.criar_reserva, name='criar_reserva'),
    path('reserva/<int:reserva_id>/editar', views.editar_reserva, name='editar_reserva'),
    path('reserva/<int:reserva_id>/excluir', views.excluir_reserva, name="excluir_reserva"),


    path('reserva/', views.reserva, name='reserva'),
    path('esqueceuasenha', views.esqueceuasenha, name='esqueceuasenha'),
    path('perfil', views.perfil, name='perfil'),
    path('confirmacaodasenha', views.confirmacaodasenha, name='confirmacaodasenha'),
    path('minhasreservas', views.minhasreservas, name='minhasreservas'),
    path('editar_perfil', views.editar_perfil, name='editar_perfil'),
    path('contaexcluida', views.contaexcluida, name='contaexcluida'),
    path('editar_reserva', views.editar_reserva, name='editar_reserva'),
    path('cancelar_reserva', views.cancelar_reserva, name='cancelar_reserva'),
    path('listar_reservas', views.listar_reservas, name='listar_reservas'),
    path('criar_reserva', views.criar_reserva, name='criar_reserva'),
]