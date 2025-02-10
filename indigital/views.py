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

def reserva(request):
    return render(request, "reserva.html")

def esqueceuasenha(request):
    return render(request, "esqueceuasenha.html")

def perfil(request):
    return render(request, "perfil.html")

def contaexcluida(request):
    return render(request, "contaexcluida.html")

def confirmacaodasenha(request):
    return render(request, "confirmacaodasenha.html")

def minhasreservas(request):
    return render(request, "minhasreservas.html")

def editar_perfil(request):
    return render(request, "editar_perfil.html")

def cancelar_reserva(request):
    return render(request, "cancelarreserva.html")