from django.shortcuts import render, redirect, get_object_or_404
from .models import Laboratorio, Reserva
from .forms import ReservaForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

def index(request):
    return render(request, "index.html")

@login_required
@permission_required('indigital.criar_reserva', raise_exception=True)
def criar_reserva(request):
    laboratorios = Laboratorio.objects.all()
    if request.method == "POST":
        form = ReservaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reserva cadastrada com sucesso!')
            return redirect('reserva')
        else:
            messages.error(request, 'Erro ao cadastrar reserva!')
    else:
        form = ReservaForm()
    
    return render(request, "criar_reserva.html", {'form' : form, "laboratorios": laboratorios})

@login_required
@permission_required('indigital.editar_reserva', raise_exception=True)
def editar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)

    context = {
        "reserva" : reserva,
        "form" : ReservaForm(instance=reserva),
        "laboratorios": Laboratorio.objects.all()
    }

    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            form.save()
            return redirect('listar_reservas')
        else:
            context["form"] = form
    
    return render(request, "editar_reserva.html", context)

@login_required
def listar_reservas(request):
    reserva = Reserva.objects.all()
    return render(request, "listar_reservas.html", {'reservas' : reserva})

@login_required
@permission_required('indigital.excluir_reserva', raise_exception=True)
def excluir_reserva(request, reserva_id):
    context = {
        "reserva": get_object_or_404(Reserva, id=reserva_id)
    }

    if request.method == "POST":
        context["reserva"].delete()
        return redirect('listar_reservas')
    else:
        return render(request, "excluir_reserva.html", context)

@login_required
def reserva(request):
    reservas = Reserva.objects.all()
    return render(request, "reserva.html", {'reservas': reservas})

@login_required
def reservar_laboratorio(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)

    if reserva.usuario is not None:
        messages.error(request, "Essa reserva já foi realizada por outro usuário.")
        return redirect('reserva')

    reserva.usuario = request.user
    reserva.save()
    
    messages.success(request, "Reserva realizada com sucesso!")
    return redirect('minhas_reservas')

def minhas_reservas(request):
    if request.user.is_staff:  # Se for admin, renderiza o template de admin_reservas
        return render(request, "admin_reservas.html")
    
    # Se for usuário comum, busca suas reservas no banco de dados
    reservas = request.user.reserva_set.all()  
    return render(request, "user_reservas.html", {"reservas": reservas})

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)

    if reserva.usuario == request.user:
        reserva.usuario = None  # Remove a reserva do usuário
        reserva.save()
        messages.success(request, "Reserva cancelada com sucesso!")
    else:
        messages.error(request, "Você não tem permissão para cancelar esta reserva.")

    return redirect('minhas_reservas')


def esqueceuasenha(request):
    return render(request, "esqueceuasenha.html")

def perfil(request):
    return render(request, "perfil.html")

def contaexcluida(request):
    return render(request, "contaexcluida.html")

def confirmacaodasenha(request):
    return render(request, "confirmacaodasenha.html")

def editar_perfil(request):
    return render(request, "editar_perfil.html")