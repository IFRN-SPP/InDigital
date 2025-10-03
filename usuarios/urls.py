from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.custom_login, name='login'),
    path('perfil/', views.perfil, name='perfil'),
    path('editar/perfil/', views.editar_perfil, name='editar_perfil'),
    path('listar/usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/deletar/', views.deletar_usuario, name='deletar_usuario'),
    path('usuarios/<int:usuario_id>/tornar_monitor/', views.tornar_monitor, name='tornar_monitor'),
    path('usuarios/<int:usuario_id>/remover_monitor/', views.remover_monitor, name='remover_monitor'),
    path('listar/monitores/', views.listar_monitores, name='listar_monitores'),
    
    # URLs para recuperação de senha (esqueci a senha)
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='account/password_reset.html',
             email_template_name='account/password_reset_email.html',
             subject_template_name='account/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='account/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='account/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='account/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # URLs para alteração de senha (usuário logado)
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='account/password_change_form.html'
         ), 
         name='password_change'),
    
    path('password-change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='account/password_change_done.html'
         ), 
         name='password_change_done'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)