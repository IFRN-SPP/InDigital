from django.shortcuts import render, redirect, get_list_or_404
from .models import Laboratorio, Reserva
from .forms import LaboratorioForm, ReservaForm

def index(request):
    return render(request, "index.html")

def reserva(request):
    return render(request, "reserva.html")

def login(request):
    return render(request, "login.html")

def esqueceuasenha(request):
    return render(request, "esqueceuasenha.html")

def cadastro(request):
    return render(request, "cadastro.html")

def perfil(request):
    return render(request, "perfil.html")

def confirmacaodasenha(request):
    return render(request, "confirmacaodasenha.html")

def minhasreservas(request):
    return render(request, "minhasreservas.html")

def criar_reserva(request):
    if request.method == "POST":
        form = LaboratorioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('reserva')
        else:
            form = LaboratorioForm()
    else:
        form = LaboratorioForm
    
    return render(request, "reserva.html", {'form' : form})

