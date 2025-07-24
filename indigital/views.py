from django.shortcuts import render, redirect, get_object_or_404

from usuarios.models import User
from .models import Laboratorio, Reserva, Disponibilidade, FilaEspera
from .forms import DisponibilidadeForm, LaboratorioForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render

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
            return redirect('listar_disponibilidades')
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
            messages.success(request, "Disponibilidade editada com sucesso!")
            return redirect('listar_disponibilidades')
        else:
            context["form"] = form
            messages.error(request, "Erro ao editar disponibilidade!")
    
    return render(request, "editar_disponibilidade.html", context)

@login_required
@permission_required('indigital.listar_disponibilidades', raise_exception=True)
def listar_disponibilidades(request):
    reserva = Disponibilidade.objects.all()
    return render(request, "listar_disponibilidades.html", {'reservas' : reserva})

@login_required
@permission_required('indigital.excluir_disponibilidade', raise_exception=True)
def excluir_disponibilidade(request, reserva_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=reserva_id)

    reservas_existentes = Reserva.objects.filter(disponibilidade=disponibilidade).exists()

    if reservas_existentes:
        messages.error(request, "Não é possível excluir esta disponibilidade porque existem reservas associadas.")
        return redirect('listar_disponibilidades')

    if request.method == "POST":
        disponibilidade.delete()
        messages.success(request, "Disponibilidade excluída com sucesso!")
        return redirect('listar_disponibilidades')
    else:
        return render(request, "excluir_disponibilidade.html", {'reserva': disponibilidade})

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
            messages.success(request, "Laboratório editado com sucesso!")
            return redirect('listar_laboratorios')
        else:
            context["form"] = form
            messages.error(request, "Erro ao editar laboratório!")

    return render(request, "editar_laboratorio.html", context)

@login_required
@permission_required('indigital.listar_laboratorios', raise_exception=True)
def listar_laboratorios(request):
    laboratorios_list = Laboratorio.objects.all()
    paginator = Paginator(laboratorios_list, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'listar_laboratorios.html', {'page_obj': page_obj})

@login_required
@permission_required('indigital.excluir_laboratorio', raise_exception=True)
def excluir_laboratorio(request, laboratorio_id):
    laboratorio = get_object_or_404(Laboratorio, id=laboratorio_id)
    if request.method == "POST":
        laboratorio.delete()
        messages.success(request, "Laboratório excluído com sucesso!")
        return redirect('listar_laboratorios')
    else:
        return render(request, "excluir_laboratorio.html", {'laboratorio': laboratorio})
    
# horarios e reservas
@login_required
def horarios(request):
    reservas = Disponibilidade.objects.all()

    reservas_em_fila = FilaEspera.objects.filter(usuario=request.user).values_list('disponibilidade_id', flat=True)

    return render(request, "horarios.html", {'reservas': reservas, 'reservas_em_fila': reservas_em_fila})

@login_required
def reservar_laboratorio(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)

    conflito = Reserva.objects.filter(
        usuario=request.user,
        disponibilidade__data=disponibilidade.data,
        disponibilidade__horario_inicio=disponibilidade.horario_inicio,
    ).exists()

    if conflito:
        messages.error(request, "Você já possui uma reserva para este dia e horário.")
        return redirect('horarios')
    
    if disponibilidade.vagas > 0:
        reserva = Reserva.objects.create(usuario=request.user, disponibilidade=disponibilidade)
        disponibilidade.vagas -= 1
        disponibilidade.save()
        messages.success(request, "Reserva realizada com sucesso!")
    else:
        fila_espera = FilaEspera.objects.filter(usuario=request.user, disponibilidade=disponibilidade).exists()
        if fila_espera:
            messages.error(request, "Você já está na fila de espera para este horário.")
        else:
            FilaEspera.objects.create(usuario=request.user, disponibilidade=disponibilidade)
            messages.info(request, "Sem vagas disponíveis, você foi adicionado à fila de espera para este horário.")
    return redirect('horarios')

@login_required
@permission_required('indigital.reservas', raise_exception=True)
def reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user)
    return render(request, "gerenciar_reservas.html", {"reservas": reservas})

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    disponibilidade = reserva.disponibilidade

    disponibilidade.vagas += 1
    disponibilidade.save()

    reserva.delete()

    messages.success(request, "Sua reserva foi cancelada com sucesso!")
    return redirect("minhas_reservas")

@login_required
def minhas_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user)
    return render(request, 'minhas_reservas.html', {'reservas': reservas})

@login_required
def reservas_do_dia(request):
    from datetime import date
    reservas = Reserva.objects.filter(disponibilidade__data=date.today())
    return render(request, 'reservas_do_dia.html', {'reservas': reservas})

@login_required
def fila_espera(request):
    filas = FilaEspera.objects.select_related('usuario', 'disponibilidade').all()
    return render(request, 'fila_espera.html', {'filas': filas})

@login_required
def promover_fila(request, fila_id):
    fila = get_object_or_404(FilaEspera, id=fila_id)
    disponibilidade = fila.disponibilidade

    if disponibilidade.vagas > 0:
        reserva = Reserva.objects.create(usuario=fila.usuario, disponibilidade=disponibilidade)
        disponibilidade.vagas -= 1
        disponibilidade.save()
        fila.delete()
        messages.success(request, f"Usuário {fila.usuario.username} promovido da fila de espera para reserva.")
    else:
        messages.error(request, "Não há vagas disponíveis para promover o usuário da fila de espera.")

    return redirect('fila_espera')

@login_required
def remover_fila(request, fila_id):
    fila = get_object_or_404(FilaEspera, id=fila_id)
    fila.delete()
    messages.success(request, f"Usuário {fila.usuario.username} removido da fila de espera.")
    return redirect('fila_espera')

@login_required
def entrar_fila_espera(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)
    
    if Reserva.objects.filter(usuario=request.user, disponibilidade=disponibilidade).exists():
        messages.error(request, "Você já tem uma reserva para esse horário.")
        return redirect('horarios')

    if FilaEspera.objects.filter(usuario=request.user, disponibilidade=disponibilidade).exists():
        messages.info(request, "Você já está na fila de espera para esse horário.")
        return redirect('horarios')

    FilaEspera.objects.create(usuario=request.user, disponibilidade=disponibilidade)
    messages.success(request, "Você foi adicionado à fila de espera.")

    return redirect('horarios')

@login_required
def sair_fila_espera(request, fila_id):
    fila = get_object_or_404(FilaEspera, id=fila_id, usuario=request.user)
    fila.delete()
    messages.success(request, "Você saiu da fila de espera.")
    return redirect('minha_fila_espera')

@login_required
def minha_fila_espera(request):
    minhas_filas = FilaEspera.objects.filter(usuario=request.user).select_related('disponibilidade__laboratorio')
    
    dados_filas = []
    for fila in minhas_filas:
        fila_geral = FilaEspera.objects.filter(disponibilidade=fila.disponibilidade).order_by('data_solicitacao')
        usuarios_em_ordem = list(fila_geral.values_list('usuario_id', flat=True))
        posicao = usuarios_em_ordem.index(request.user.id) + 1

        dados_filas.append({
            'id': fila.id,
            'disponibilidade': fila.disponibilidade,
            'data_solicitacao': fila.data_solicitacao,
            'posicao': posicao,
            'status': "Você é o próximo" if posicao == 1 else f"Posição {posicao}",
        })

    return render(request, 'minha_fila_espera.html', {'filas': dados_filas})

@login_required
@permission_required('indigital.reservas', raise_exception=True)
def usuarios_da_reserva(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)
    reservas = Reserva.objects.filter(disponibilidade=disponibilidade).select_related('usuario')
    fila_espera = FilaEspera.objects.filter(disponibilidade=disponibilidade).select_related('usuario')

    return render(request, 'usuarios_da_reserva.html', {'disponibilidade': disponibilidade, 'reservas': reservas, 'fila_espera': fila_espera})

@login_required
def listar_disponibilidades_monitor(request):
    disponibilidades = Disponibilidade.objects.filter(monitor=request.user)
    return render(request, 'listar_disponibilidades_monitor.html', {'disponibilidades': disponibilidades})

@login_required
def registrar_frequencias(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)
    reservas = Reserva.objects.filter(disponibilidade=disponibilidade).select_related('usuario')

    if disponibilidade.monitor != request.user:
        messages.error(request, "Você não tem permissão para registrar frequências para esta disponibilidade.")
        return redirect('listar_disponibilidades_monitor')

    if request.method == "POST":
        reserva_id = request.POST.get("reserva_id")
        status = request.POST.get("status")

        reserva = get_object_or_404(Reserva, id=reserva_id, disponibilidade=disponibilidade)

        if status in ['P', 'F', 'N']:
            reserva.status_frequencia = status
            reserva.save()
            messages.success(request, f"Frequência de {reserva.usuario.username} registrada como {'Presente' if status == 'P' else 'Faltou' if status == 'F' else 'Não registrado'}.")
        return redirect('registrar_frequencias', disponibilidade_id=disponibilidade.id)

    return render(request, "registrar_frequencias.html", {"disponibilidade": disponibilidade, "reservas": reservas})

@login_required
def reservas_por_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    reservas = Reserva.objects.filter(usuario=usuario).select_related('disponibilidade__laboratorio')
    return render(request, "reservas_por_usuario.html", {'usuario': usuario, 'reservas': reservas})
