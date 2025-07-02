from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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