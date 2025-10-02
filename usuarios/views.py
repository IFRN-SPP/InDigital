from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from indigital.models import Reserva
from .forms import CadastroForm, EditarPerfilForm
from django.contrib import messages
from .models import User
from functools import wraps
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm

@login_required
def dashboard_redirect(request):
    """Redireciona o usuário para a página apropriada após login"""
    if request.user.perfil == 'administrador' or request.user.is_superuser:
        return redirect('admin_dashboard')  
    else:
        return redirect('index')  

def admin_required(view_func):
    """Decorator para verificar se o usuário é um administrador."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser or request.user.perfil == 'administrador':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Acesso negado. Apenas administradores têm permissão para acessar esta página.")
            return render(request, '403.html', status=403)
    return _wrapped_view

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


def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo(a) de volta, {user.first_name}!')
                return redirect('index')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'account/login.html', {'form': form})

@login_required
def perfil(request):
    usuario = request.user
    #Estatísticas
    total_reservas = Reserva.objects.count()
    reservas_aprovadas = Reserva.objects.filter(status_aprovacao='A').count()
    solicitacao_pendente = Reserva.objects.filter(status_aprovacao='P').count()
    context = {
        'usuario': usuario,
        'total_reservas': total_reservas,
        'reservas_aprovadas': reservas_aprovadas,
        'solicitacao_pendente': solicitacao_pendente,
    }
    return render(request, "perfil.html", context)

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
@admin_required
def listar_usuarios(request):
    usuarios = User.objects.all()
    # Filtros
    nome = request.GET.get('nome')
    matricula = request.GET.get('matricula')
    email = request.GET.get('email')
    perfil = request.GET.get('perfil')
    if nome:
        usuarios = usuarios.filter(suap_nome_completo__icontains=nome)
    if matricula:
        usuarios = usuarios.filter(suap_id__icontains=matricula)  
    if email:
        usuarios = usuarios.filter(email__icontains=email)
    if perfil and perfil != 'todos':
        usuarios = usuarios.filter(perfil=perfil)
    # Paginação
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'nome': nome,
        'matricula': matricula,
        'email': email,
        'perfil': perfil,
    }
    return render(request, "listar_usuarios.html", context)

@login_required
@admin_required
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    form = EditarPerfilForm(request.POST or None, instance=usuario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuário atualizado com sucesso!')
        return redirect('listar_usuarios')
    return render(request, 'editar_usuario.html', {'form': form})

@login_required
@admin_required
def deletar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuário excluído com sucesso!')
        return redirect('listar_usuarios')
    return render(request, 'deletar_usuario.html', {'usuario': usuario})

@login_required
@admin_required
def tornar_monitor(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    usuario.perfil = 'monitor'
    usuario.save()
    messages.success(request, 'Usuário promovido a monitor com sucesso!')
    return redirect('listar_usuarios')

@login_required
@admin_required
def remover_monitor(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    usuario.perfil = 'aluno'
    usuario.save()
    messages.success(request, 'Usuário removido de monitor com sucesso!')
    return redirect('listar_usuarios')

@login_required
@admin_required
def listar_monitores(request):
    monitores = User.objects.filter(perfil='monitor').order_by('username')
    # Filtros
    nome = request.GET.get('nome')
    matricula = request.GET.get('matricula')
    email = request.GET.get('email')
    if nome:
        monitores = monitores.filter(suap_nome_completo__icontains=nome)
    if matricula:
        monitores = monitores.filter(suap_id__icontains=matricula)
    if email:
        monitores = monitores.filter(email__icontains=email)
    # Paginação
    paginator = Paginator(monitores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'nome': nome,
        'matricula': matricula,
        'email': email,
    }
    return render(request, "listar_monitores.html", context)