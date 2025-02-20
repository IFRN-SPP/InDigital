from django.shortcuts import render, redirect, get_object_or_404
from .models import Laboratorio, Reserva, Disponibilidade
from .forms import DisponibilidadeForm, LaboratorioForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

def index(request):
    return render(request, "index.html")

# crud de disponibilidade

@login_required
@permission_required('indigital.criar_disponibilidade', raise_exception=True)
def criar_disponibilidade(request):
    laboratorios = Laboratorio.objects.all()
    if request.method == "POST":
        form = DisponibilidadeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Disponibilidade cadastrada com sucesso!')
            return redirect('horarios')
        else:
            messages.error(request, 'Erro ao cadastrar nova disponibilidade!')
    else:
        form = DisponibilidadeForm()
    
    return render(request, "criar_disponibilidade.html", {'form' : form, "laboratorios": laboratorios})

@login_required
@permission_required('indigital.editar_reserva', raise_exception=True)
def editar_disponibilidade(request, reserva_id):
    reserva = get_object_or_404(Disponibilidade, id=reserva_id)

    context = {
        "reserva" : reserva,
        "form" : DisponibilidadeForm(instance=reserva),
        "laboratorios": Laboratorio.objects.all()
    }

    if request.method == 'POST':
        form = DisponibilidadeForm(request.POST, instance=reserva)
        if form.is_valid():
            form.save()
            return redirect('listar_disponibilidades')
        else:
            context["form"] = form
    
    return render(request, "editar_disponibilidade.html", context)

@login_required
def listar_disponibilidades(request):
    reserva = Disponibilidade.objects.all()
    return render(request, "listar_disponibilidades.html", {'reservas' : reserva})

@login_required
@permission_required('indigital.excluir_disponibilidade', raise_exception=True)
def excluir_disponibilidade(request, reserva_id):
    context = {
        "reserva": get_object_or_404(Disponibilidade, id=reserva_id)
    }

    if request.method == "POST":
        context["reserva"].delete()
        return redirect('listar_disponibilidade')
    else:
        return render(request, "excluir_disponibilidade.html", context)

# crud laboratorio

@login_required
@permission_required('indigital.criar_laboratorio', raise_exception=True)
def criar_laboratorio(request):
    if request.method == "POST":
        form = LaboratorioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Laboratório cadastrado com sucesso!')
            return redirect('listar_laboratorios')
        else:
            messages.error(request, 'Erro ao cadastrar laboratório!')
    else:
        form = LaboratorioForm()
    
    return render(request, "criar_laboratorio.html", {'form' : form})

@login_required
@permission_required('indigital.editar_laboratorio', raise_exception=True)
def editar_laboratorio(request, laboratorio_id):
    laboratorio = get_object_or_404(Laboratorio, id=laboratorio_id)
    context = {
        "reserva" : laboratorio,
        "form" : LaboratorioForm(instance=laboratorio),
        "laboratorios": Laboratorio.objects.all()
    }

    if request.method == 'POST':
        form = LaboratorioForm(request.POST, instance=laboratorio)
        if form.is_valid():
            form.save()
            return redirect('listar_laboratorios')
        else:
            context["form"] = form
    return render(request, "editar_laboratorio.html", context)

@login_required
def listar_laboratorios(request):
    laboratorios = Laboratorio.objects.all()
    return render(request, "listar_laboratorios.html", {'laboratorios': laboratorios})

@login_required
@permission_required('indigital.excluir_laboratorio', raise_exception=True)
def excluir_laboratorio(request, laboratorio_id):
    laboratorio = get_object_or_404(Laboratorio, id=laboratorio_id)
    if request.method == "POST":
        laboratorio.delete()
        return redirect('listar_laboratorios')
    else:
        return render(request, "excluir_laboratorio.html", {'laboratorio': laboratorio})
    
# horarios e reservas
@login_required
def horarios(request):
    reservas = Disponibilidade.objects.all()
    return render(request, "horarios.html", {'reservas': reservas})

@login_required
def reservar_laboratorio(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)

    if disponibilidade.laboratorio.vagas <= 0:
        messages.error(request, "Não há vagas disponíveis para este horário.")
        return redirect('horarios')

    if Reserva.objects.filter(usuario=request.user, disponibilidade=disponibilidade).exists():
        messages.error(request, "Você já possui uma reserva para este horário.")
        return redirect('horarios')

    reserva = Reserva.objects.create(usuario=request.user, disponibilidade=disponibilidade)

    disponibilidade.laboratorio.vagas -= 1
    disponibilidade.laboratorio.save()

    messages.success(request, "Reserva realizada com sucesso!")
    return redirect("reservas")

@login_required
def reservas(request):
    if request.user.is_superuser:
        return render(request, "admin_reservas.html")
    
    reservas = Reserva.objects.filter(usuario=request.user)
    return render(request, "user_reservas.html", {"reservas": reservas})

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    reserva.disponibilidade.laboratorio.vagas += 1
    reserva.disponibilidade.laboratorio.save()

    reserva.delete()

    messages.success(request, "Reserva cancelada com sucesso.")
    return redirect("reservas")

@login_required
def admin_minhas_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user)
    return render(request, 'admin_minhas_reservas.html', {'reservas': reservas})

def esqueceuasenha(request):
    return render(request, "esqueceuasenha.html")

def contaexcluida(request):
    return render(request, "contaexcluida.html")

def confirmacaodasenha(request):
    return render(request, "confirmacaodasenha.html")