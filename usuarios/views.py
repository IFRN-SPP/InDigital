from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from .forms import CadastroForm, EditarPerfilForm
from django.contrib import messages
from .models import User

def cadastro(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST, request.FILES)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.perfil = 'aluno'
            usuario.save()
            messages.success(request, 'Usuário cadastrado com sucesso! Faça login para acessar o sistema.')
            return redirect('login')
        else:
            messages.error(request, 'Erro ao cadastrar usuário. Por favor, corrija os erros!')
    else:
        form = CadastroForm()
    return render(request, 'cadastro.html', {'form': form})

@login_required
def perfil(request):
    usuario = request.user
    return render(request, "perfil.html", {'usuario': usuario})

@login_required
def editar_perfil(request):
    usuario = request.user
    if request.method == "POST":
        form = EditarPerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('perfil')
        else:
            messages.error(request, "Erro ao atualizar o perfil. Por favor, corrija os erros!")
    else:
        form = EditarPerfilForm(instance=usuario)

    return render(request, "editar_perfil.html", {'form': form})

@login_required
@permission_required('usuarios.listar_usuarios', raise_exception=True)
def listar_usuarios(request):
    usuarios = User.objects.all()
    return render(request, "listar_usuarios.html", {'usuarios': usuarios})

@login_required
@permission_required('usuarios.editar_usuario', raise_exception=True)
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    form = EditarPerfilForm(request.POST or None, instance=usuario)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuário atualizado com sucesso!')
        return redirect('listar_usuarios')

    return render(request, 'editar_usuario.html', {'form': form})

@login_required
@permission_required('usuarios.deletar_usuario', raise_exception=True)
def deletar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuário excluído com sucesso!')
        return redirect('listar_usuarios')

    return render(request, 'deletar_usuario.html', {'usuario': usuario})

@login_required
@permission_required('usuarios.tornar_monitor', raise_exception=True)
def tornar_monitor(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    usuario.perfil = 'monitor'
    usuario.save()
    messages.success(request, 'Usuário promovido a monitor com sucesso!')
    return redirect('listar_usuarios')

@login_required
@permission_required('usuarios.remover_monitor', raise_exception=True)
def remover_monitor(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    usuario.perfil = 'aluno'
    usuario.save()
    messages.success(request, 'Usuário removido de monitor com sucesso!')
    return redirect('listar_usuarios')

@login_required
@permission_required('usuarios.listar_monitores', raise_exception=True)
def listar_monitores(request):
    monitores = User.objects.filter(perfil='monitor')
    return render(request, "listar_monitores.html", {'monitores': monitores})