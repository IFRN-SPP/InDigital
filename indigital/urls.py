from django.urls import path 
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('listar/reservas/', views.listar_reservas, name='listar_reservas'),
    path('criar/reserva/', views.criar_reserva, name='criar_reserva'),
    path('reserva/<int:reserva_id>/editar', views.editar_reserva, name='editar_reserva'),
    path('reserva/<int:reserva_id>/excluir', views.excluir_reserva, name="excluir_reserva"),
    path('listar/laboratorios/', views.listar_laboratorios, name='listar_laboratorios'),
    path('criar/laboratorio/', views.criar_laboratorio, name='criar_laboratorio'),
    path('laboratorio/<int:laboratorio_id>/editar', views.editar_laboratorio, name='editar_laboratorio'),
    path('laboratorio/<int:laboratorio_id>/excluir', views.excluir_laboratorio, name="excluir_laboratorio"),
    path('horarios/', views.horarios, name='horarios'),
    path('reservar/<int:reserva_id>/', views.reservar_laboratorio, name='reservar_laboratorio'),
    path('reservas/', views.reservas, name='reservas'),
    path('cancelar_reserva/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('esqueceuasenha', views.esqueceuasenha, name='esqueceuasenha'),
    path('confirmacaodasenha', views.confirmacaodasenha, name='confirmacaodasenha'),
]