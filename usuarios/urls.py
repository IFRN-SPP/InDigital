from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/', views.perfil, name='perfil'),
    path('editar/perfil/', views.editar_perfil, name='editar_perfil'),
    path('listar/usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/deletar/', views.deletar_usuario, name='deletar_usuario'),
    path('usuarios/<int:usuario_id>/tornar_monitor/', views.tornar_monitor, name='tornar_monitor'),
    path('usuarios/<int:usuario_id>/remover_monitor/', views.remover_monitor, name='remover_monitor'),
    path('listar/monitores/', views.listar_monitores, name='listar_monitores'),
    path('adicionar/monitor/', views.adicionar_monitor, name='adicionar_monitor'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)