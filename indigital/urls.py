from django.urls import path 
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('listar/disponibilidades/', views.listar_disponibilidades, name='listar_disponibilidades'),
    path('criar/disponibilidade/', views.criar_disponibilidade, name='criar_disponibilidade'),
    path('disponibilidade/<int:reserva_id>/editar', views.editar_disponibilidade, name='editar_disponibilidade'),
    path('disponibilidade/<int:reserva_id>/excluir', views.excluir_disponibilidade, name="excluir_disponibilidade"),
    path('listar/laboratorios/', views.listar_laboratorios, name='listar_laboratorios'),
    path('criar/laboratorio/', views.criar_laboratorio, name='criar_laboratorio'),
    path('laboratorio/<int:laboratorio_id>/editar', views.editar_laboratorio, name='editar_laboratorio'),
    path('laboratorio/<int:laboratorio_id>/excluir', views.excluir_laboratorio, name="excluir_laboratorio"),
    path('horarios/', views.horarios, name='horarios'),
    path('reservar/<int:disponibilidade_id>/', views.reservar_laboratorio, name='reservar_laboratorio'),
    path('reservas/', views.reservas, name='reservas'),
    path('cancelar_reserva/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('minhas/reservas/', views.minhas_reservas, name='minhas_reservas'),
    path('reservas/dia/', views.reservas_do_dia, name='reservas_do_dia'),
    path('fila/espera/', views.fila_espera, name='fila_espera'),
    path('fila/espera/promover/<int:fila_id>/', views.promover_fila, name='promover_fila'),
    path('fila/espera/remover/<int:fila_id>/', views.remover_fila, name='remover_fila'),
    path('entrar/fila/<int:disponibilidade_id>/', views.entrar_fila_espera, name='entrar_fila_espera'),
    path('sair/fila/<int:fila_id>/', views.sair_fila_espera, name='sair_fila_espera'),
    path('minha/fila/espera/', views.minha_fila_espera, name='minha_fila_espera'),
    path('usuarios/reserva/<int:disponibilidade_id>/', views.usuarios_da_reserva, name='usuarios_da_reserva'),
    path('disponibilidade/<int:disponibilidade_id>/registrar_frequencias/', views.registrar_frequencias, name='registrar_frequencias'),
]