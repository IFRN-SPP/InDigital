from django.urls import path 
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('listar/reservas/', views.listar_reservas, name='listar_reservas'),
    path('criar/reserva/', views.criar_reserva, name='criar_reserva'),
    path('reserva/<int:reserva_id>/editar', views.editar_reserva, name='editar_reserva'),
    path('reserva/<int:reserva_id>/excluir', views.excluir_reserva, name="excluir_reserva"),


    path('reserva/', views.reserva, name='reserva'),
    path('reservar/<int:reserva_id>/', views.reservar_laboratorio, name='reservar_laboratorio'),
    path('minhas/reservas/', views.minhas_reservas, name='minhas_reservas'),
    path('cancelar_reserva/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),

    path('esqueceuasenha', views.esqueceuasenha, name='esqueceuasenha'),
    path('perfil', views.perfil, name='perfil'),
    path('confirmacaodasenha', views.confirmacaodasenha, name='confirmacaodasenha'),
    path('editar_perfil', views.editar_perfil, name='editar_perfil'),
    path('contaexcluida', views.contaexcluida, name='contaexcluida'),
    path('editar_reserva', views.editar_reserva, name='editar_reserva'),
    path('cancelar_reserva', views.cancelar_reserva, name='cancelar_reserva'),
]