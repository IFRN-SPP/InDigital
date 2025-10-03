from django.shortcuts import render, redirect, get_object_or_404
from functools import wraps
from datetime import date, datetime
from django.core.exceptions import ValidationError

from usuarios.models import User
from .models import Laboratorio, Reserva, Disponibilidade, FilaEspera
from .forms import DisponibilidadeForm, LaboratorioForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
import traceback
from django.http import HttpResponse

@login_required
def dashboard_redirect(request):
    """
    Redireciona o usuário para o dashboard apropriado baseado no seu perfil
    """
    user = request.user
    if user.is_superuser or user.perfil == 'administrador':
        return redirect('admin_dashboard')
    elif user.perfil == 'monitor':
        return redirect('monitor_dashboard')
    else:
        return redirect('index')

def monitor_required(view_func):
    """
    Decorator para verificar se o usuário é um monitor.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        # Verificar se o usuário é monitor ou administrador/superuser
        if request.user.perfil == 'monitor' or request.user.is_superuser or request.user.perfil == 'administrador':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Acesso negado. Apenas monitores têm permissão para acessar esta página.")
            return render(request, '403.html', status=403)
    
    return _wrapped_view

def admin_required(view_func):
    """
    Decorator para verificar se o usuário é um administrador.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        # Verificar se o usuário é administrador/superuser
        if request.user.is_superuser or request.user.perfil == 'administrador':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Acesso negado. Apenas administradores têm permissão para acessar esta página.")
            return render(request, '403.html', status=403)
    
    return _wrapped_view

@login_required
@admin_required
def admin_dashboard(request):
    # Estatísticas
    total_usuarios = User.objects.count()
    total_reservas = Reserva.objects.count()
    reservas_aprovadas = Reserva.objects.filter(status_aprovacao='A').count()
    solicitacoes_pendentes = Reserva.objects.filter(status_aprovacao='P').count()
    fila_espera = FilaEspera.objects.count()
    # Reservas do dia (apenas aprovadas)
    reservas_hoje = Reserva.objects.filter(
        disponibilidade__data=date.today(),
        status_aprovacao='A'
    ).select_related(
        'usuario', 'disponibilidade__laboratorio', 'disponibilidade__monitor'
    ).order_by('disponibilidade__horario_inicio')
    # Paginação
    paginator = Paginator(reservas_hoje, 5)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'total_usuarios': total_usuarios,
        'total_reservas': total_reservas,
        'reservas_aprovadas': reservas_aprovadas,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'fila_espera': fila_espera,
        'reservas_hoje': page_obj,
        'page_obj': page_obj,
        'today': date.today(),
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
@monitor_required
def monitor_dashboard(request):
    # Buscar reservas aprovadas do dia de hoje diretamente
    reservas_hoje = Reserva.objects.filter(
        disponibilidade__data=date.today(),
        status_aprovacao='A'
    ).select_related(
        'usuario', 'disponibilidade__laboratorio', 'disponibilidade__monitor'
    ).order_by('disponibilidade__horario_inicio')
    # Paginação
    paginator = Paginator(reservas_hoje, 5)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Reservas aprovadas que o monitor é responsável (para estatísticas)
    reservas_monitor = Reserva.objects.filter(
        disponibilidade__monitor=request.user,
        status_aprovacao='A'
    )
    # Estatísticas
    total_reservas = reservas_monitor.count()
    presentes = reservas_monitor.filter(status_frequencia='P').count()
    faltas = reservas_monitor.filter(status_frequencia='F').count()
    pendentes = reservas_monitor.filter(disponibilidade__data__gte=date.today()).count()
    
    context = {
        'total_reservas': total_reservas,
        'presentes': presentes,
        'faltas': faltas,
        'pendentes': pendentes,
        'reservas_hoje': page_obj,
        'page_obj': page_obj,
        'today': date.today(),
    }
    return render(request, 'monitor_dashboard.html', context)

@login_required
def index(request):
    # Redirecionar superusuários e administradores para seus dashboards específicos
    user = request.user
    if user.is_superuser or user.perfil == 'administrador':
        return redirect('admin_dashboard')
    elif user.perfil == 'monitor':
        return redirect('monitor_dashboard')

    total_reservas = Reserva.objects.count()
    presentes = Reserva.objects.filter(status_frequencia='P').count()
    faltas = Reserva.objects.filter(status_frequencia='F').count()
    pendentes = Reserva.objects.filter(disponibilidade__data__gte=date.today()).count()
    
    context = {
        'total_reservas': total_reservas,
        'presentes': presentes,
        'faltas': faltas,
        'pendentes': pendentes,
    }
    return render(request, "index.html", context)

# crud de disponibilidade
@login_required
@admin_required
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
@admin_required
def listar_disponibilidades(request):
    form = DisponibilidadeForm()
    
    disponibilidades = Disponibilidade.objects.all().select_related('laboratorio', 'monitor').order_by('-data', 'horario_inicio')
    
    # Filtros
    laboratorio_id = request.GET.get('laboratorio')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    monitor_id = request.GET.get('monitor')
    vagas_min = request.GET.get('vagas_min')
    
    # Aplicar filtros
    if laboratorio_id and laboratorio_id != 'todos':
        disponibilidades = disponibilidades.filter(laboratorio_id=laboratorio_id)
    
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            disponibilidades = disponibilidades.filter(data__gte=data_inicio_obj)
        except ValueError:
            messages.error(request, "Data de início inválida.")
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            disponibilidades = disponibilidades.filter(data__lte=data_fim_obj)
        except ValueError:
            messages.error(request, "Data de fim inválida.")
    
    if monitor_id and monitor_id != 'todos':
        disponibilidades = disponibilidades.filter(monitor_id=monitor_id)
    
    if vagas_min:
        try:
            disponibilidades = disponibilidades.filter(vagas__gte=int(vagas_min))
        except ValueError:
            messages.error(request, "Número mínimo de vagas deve ser um número.")
    
    # Paginação
    paginator = Paginator(disponibilidades, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtros para o template
    laboratorios = Laboratorio.objects.all().order_by('num_laboratorio')
    monitores = User.objects.filter(perfil='monitor').order_by('username')
    
    context = {
        'page_obj': page_obj,
        'laboratorios': laboratorios,
        'monitores': monitores,
        'laboratorio_id': laboratorio_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'monitor_id': monitor_id,
        'vagas_min': vagas_min,
        'form': form, 
    }
    
    return render(request, "listar_disponibilidades.html", context)

@login_required
@admin_required
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

@login_required
@admin_required
def criar_disponibilidade(request):
    if request.method == 'POST':
        form = DisponibilidadeForm(request.POST)
        if form.is_valid():
            disponibilidade = form.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            messages.success(request, "Disponibilidade criada com sucesso!")
            return redirect('listar_disponibilidades')
        else:

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                form_html = render_to_string('modal_form.html', {'form': form}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html})
            
            messages.error(request, "Erro ao criar disponibilidade!")
            return redirect('listar_disponibilidades')
    else:
        form = DisponibilidadeForm()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form_html = render_to_string('modal_form.html', {'form': form}, request=request)
            return HttpResponse(form_html)
        
        return redirect('listar_disponibilidades')
    

@login_required
@admin_required
def editar_laboratorio(request, laboratorio_id):
    laboratorio = get_object_or_404(Laboratorio, id=laboratorio_id)
    
    if request.method == 'POST':
        try:
            print("=== DEBUG POST ===")
            print(f"Dados POST: {dict(request.POST)}")
            
            form = LaboratorioForm(request.POST, instance=laboratorio)
            print(f"Formulário válido: {form.is_valid()}")
            
            if form.is_valid():
                print("Salvando laboratório...")
                laboratorio = form.save()
                print("Laboratório salvo!")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                
                messages.success(request, f'Laboratório {laboratorio.num_laboratorio} atualizado com sucesso!')
                return redirect('listar_laboratorios')
            else:
                print(f"Erros do formulário: {form.errors}")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    num_lab_errors = form.errors.get('num_laboratorio', [])
                    capacidade_errors = form.errors.get('capacidade', [])
                    
                    form_html = f"""
                    <form id="formEditarLaboratorio" method="POST" action="/editar-laboratorio/{laboratorio.id}/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get('CSRF_COOKIE', '')}">
                        <div class="form-field">
                            <label for="id_num_laboratorio" class="form-label">
                                <i class="fas fa-hashtag mr-1"></i>Número do Laboratório *
                            </label>
                            <input type="text" name="num_laboratorio" id="id_num_laboratorio" class="form-control {'is-invalid' if num_lab_errors else ''}" 
                                   value="{request.POST.get('num_laboratorio', laboratorio.num_laboratorio)}" placeholder="Ex: L001, LAB-01" required maxlength="10">
                            {"".join(f'<div class="error-message">{error}</div>' for error in num_lab_errors)}
                        </div>
                        <div class="form-field">
                            <label for="id_capacidade" class="form-label">
                                <i class="fas fa-users mr-1"></i>Capacidade *
                            </label>
                            <input type="number" name="capacidade" id="id_capacidade" class="form-control {'is-invalid' if capacidade_errors else ''}" 
                                   value="{request.POST.get('capacidade', laboratorio.capacidade)}" min="1" max="1000" required>
                            {"".join(f'<div class="error-message">{error}</div>' for error in capacidade_errors)}
                            <small class="text-muted">Número máximo de pessoas que o laboratório suporta</small>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times mr-2"></i>Cancelar
                            </button>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save mr-2"></i>Atualizar Laboratório
                            </button>
                        </div>
                    </form>
                    """
                    return JsonResponse({'success': False, 'form_html': form_html})
                
                messages.error(request, 'Erro ao editar laboratório!')
        
        except Exception as e:
            print(f" ERRO NO POST: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
            messages.error(request, f'Erro: {str(e)}')
            return redirect('listar_laboratorios')
    
    else: 
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form_html = f"""
            <form id="formEditarLaboratorio" method="POST" action="/editar-laboratorio/{laboratorio.id}/">
                <input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get('CSRF_COOKIE', '')}">
                <div class="form-field">
                    <label for="id_num_laboratorio" class="form-label">
                        <i class="fas fa-hashtag mr-1"></i>Número do Laboratório *
                    </label>
                    <input type="text" name="num_laboratorio" id="id_num_laboratorio" class="form-control" 
                           value="{laboratorio.num_laboratorio}" placeholder="Ex: L001, LAB-01" required maxlength="10">
                </div>
                <div class="form-field">
                    <label for="id_capacidade" class="form-label">
                        <i class="fas fa-users mr-1"></i>Capacidade *
                    </label>
                    <input type="number" name="capacidade" id="id_capacidade" class="form-control" 
                           value="{laboratorio.capacidade}" min="1" max="1000" required>
                    <small class="text-muted">Número máximo de pessoas que o laboratório suporta</small>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        <i class="fas fa-times mr-2"></i>Cancelar
                    </button>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save mr-2"></i>Atualizar Laboratório
                    </button>
                </div>
            </form>
            """
            return HttpResponse(form_html)
        
        form = LaboratorioForm(instance=laboratorio)
        context = {
            'form': form,
            'laboratorio': laboratorio
        }
        return render(request, 'listar_laboratorios.html', context)

@login_required
@admin_required
def listar_laboratorios(request):
    form = LaboratorioForm()

    # Filtra os laboratórios
    laboratorios_list = Laboratorio.objects.all().order_by('num_laboratorio')
    num_laboratorio = request.GET.get('num_laboratorio')
    capacidade_min = request.GET.get('capacidade_min')
    capacidade_max = request.GET.get('capacidade_max')
    
    if num_laboratorio:
        laboratorios_list = laboratorios_list.filter(num_laboratorio__icontains=num_laboratorio)
    
    if capacidade_min:
        try:
            laboratorios_list = laboratorios_list.filter(capacidade__gte=int(capacidade_min))
        except ValueError:
            messages.error(request, "Capacidade mínima deve ser um número.")
    
    if capacidade_max:
        try:
            laboratorios_list = laboratorios_list.filter(capacidade__lte=int(capacidade_max))
        except ValueError:
            messages.error(request, "Capacidade máxima deve ser um número.")
    
    # Paginação
    paginator = Paginator(laboratorios_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form, 
        'num_laboratorio': num_laboratorio,
        'capacidade_min': capacidade_min,
        'capacidade_max': capacidade_max,
    }
    
    return render(request, 'listar_laboratorios.html', context)


@login_required
@admin_required
def criar_laboratorio(request):
    if request.method == 'POST':
        form = LaboratorioForm(request.POST)
        if form.is_valid():
            laboratorio = form.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            messages.success(request, f'Laboratório {laboratorio.num_laboratorio} criado com sucesso!')
            return redirect('listar_laboratorios')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                form_html = render_to_string('partials/laboratorio_form.html', {'form': form}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html})
            
            messages.error(request, 'Erro ao criar laboratório!')
            return redirect('listar_laboratorios')
    
    else:
        form = LaboratorioForm()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form_html = render_to_string('partials/laboratorio_form.html', {'form': form}, request=request)
            return HttpResponse(form_html)
        
        return redirect('listar_laboratorios')

@login_required
@admin_required
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
    disponibilidades = Disponibilidade.objects.all().select_related('laboratorio', 'monitor').order_by('data', 'horario_inicio')
    # Filtros
    laboratorio_id = request.GET.get('laboratorio_id')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    monitor_id = request.GET.get('monitor')
    vagas_minimas = request.GET.get('vagas_minimas')
    apenas_com_vagas = request.GET.get('apenas_com_vagas')
    # Aplicar filtros
    if laboratorio_id and laboratorio_id != 'todos':
        disponibilidades = disponibilidades.filter(laboratorio_id=laboratorio_id)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            disponibilidades = disponibilidades.filter(data__gte=data_inicio_obj)
        except ValueError:
            messages.error(request, "Data de início inválida.")
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            disponibilidades = disponibilidades.filter(data__lte=data_fim_obj)
        except ValueError:
            messages.error(request, "Data de fim inválida.")
    if vagas_minimas:
        try:
            disponibilidades = disponibilidades.filter(vagas__gte=int(vagas_minimas))
        except ValueError:
            messages.error(request, "Número mínimo de vagas deve ser um número.")
    if monitor_id and monitor_id != 'todos':
        disponibilidades = disponibilidades.filter(monitor_id=monitor_id)
    if apenas_com_vagas == 'sim':
        disponibilidades = disponibilidades.filter(vagas__gt=0)
    # Paginação 
    paginator = Paginator(disponibilidades, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Buscar reservas e filas do usuário para verificar status
    reservas_em_fila = FilaEspera.objects.filter(usuario=request.user).values_list('disponibilidade_id', flat=True)
    # Buscar reservas do usuário (pendentes e aprovadas)
    minhas_reservas = Reserva.objects.filter(
        usuario=request.user,
        status_aprovacao__in=['P', 'A']
    ).values_list('disponibilidade_id', flat=True)
    # Buscar reservas pendentes específicas para mostrar status
    reservas_pendentes = Reserva.objects.filter(
        usuario=request.user,
        status_aprovacao='P'
    ).values_list('disponibilidade_id', flat=True)
    # Buscar reservas rejeitadas para mostrar feedback
    reservas_rejeitadas = Reserva.objects.filter(
        usuario=request.user,
        status_aprovacao='R'
    ).values_list('disponibilidade_id', flat=True)
    # Dados para os filtros
    laboratorios = Laboratorio.objects.all().order_by('num_laboratorio')
    monitores = User.objects.filter(perfil='monitor').order_by('username')
    
    context = {
        'page_obj': page_obj,
        'reservas_em_fila': reservas_em_fila,
        'minhas_reservas': minhas_reservas,
        'reservas_pendentes': reservas_pendentes,
        'reservas_rejeitadas': reservas_rejeitadas,
        'laboratorios': laboratorios,
        'monitores': monitores,
        'laboratorio_id': laboratorio_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'vagas_minimas': vagas_minimas,
        'monitor_id': monitor_id,
        'apenas_com_vagas': apenas_com_vagas,
        'today': date.today(),
    }
    return render(request, "horarios.html", context)

@login_required
def reservar_laboratorio(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)
    # Verificar se o usuário já tem uma reserva para essa disponibilidade
    reserva_existente = Reserva.objects.filter(
        usuario=request.user, 
        disponibilidade=disponibilidade,
        status_aprovacao__in=['P', 'A']  # Pendente ou Aprovada
    ).first()
    if reserva_existente:
        status_texto = "pendente" if reserva_existente.status_aprovacao == 'P' else "aprovada"
        messages.error(request, f"Você já possui uma reserva {status_texto} para este horário.")
        return redirect('horarios')
    if disponibilidade.vagas > 0:
        try:
            reserva = Reserva(usuario=request.user, disponibilidade=disponibilidade, status_aprovacao='P')
            reserva.clean()
            reserva.save()
            messages.success(request, "Solicitação de reserva enviada! Aguarde a aprovação do administrador.")
        except ValidationError as e:
            if hasattr(e, 'message'):
                error_msg = e.message
            elif hasattr(e, 'messages') and e.messages:
                error_msg = e.messages[0]
            else:
                error_msg = str(e)
            messages.error(request, error_msg)
            return redirect('horarios')
    else:
        fila_espera = FilaEspera.objects.filter(usuario=request.user, disponibilidade=disponibilidade).exists()
        if fila_espera:
            messages.error(request, "Você já está na fila de espera para este horário.")
        else:
            FilaEspera.objects.create(usuario=request.user, disponibilidade=disponibilidade)
            messages.info(request, "Sem vagas disponíveis, você foi adicionado à fila de espera para este horário.")
    return redirect('horarios')

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    if reserva.status_aprovacao == 'R':
        messages.error(request, "Não é possível cancelar uma reserva rejeitada.")
        return redirect("minhas_reservas")
    disponibilidade = reserva.disponibilidade
    # Só devolver vaga se a reserva estava aprovada
    if reserva.status_aprovacao == 'A':
        disponibilidade.vagas += 1
        disponibilidade.save()
    reserva.delete()
    messages.success(request, "Sua reserva foi cancelada com sucesso!")
    return redirect("minhas_reservas")

@login_required
def minhas_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user).select_related(
        'disponibilidade__laboratorio', 'disponibilidade__monitor'
    ).order_by('-disponibilidade__data', '-disponibilidade__horario_inicio')
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    laboratorio_id = request.GET.get('laboratorio_id')
    status = request.GET.get('status')
    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio_parsed = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__gte=data_inicio_parsed)
        except ValueError:
            pass
    if data_fim:
        try:
            data_fim_parsed = datetime.strptime(data_fim, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__lte=data_fim_parsed)
        except ValueError:
            pass
    if laboratorio_id and laboratorio_id != 'todos':
        reservas = reservas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    if status and status != 'todos':
        today = date.today()
        if status == 'futuras':
            reservas = reservas.filter(disponibilidade__data__gt=today)
        elif status == 'hoje':
            reservas = reservas.filter(disponibilidade__data=today)
        elif status == 'passadas':
            reservas = reservas.filter(disponibilidade__data__lt=today)
    # Paginação
    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Buscar laboratórios para o filtro
    laboratorios = Laboratorio.objects.all().order_by('num_laboratorio')
    
    context = {
        'page_obj': page_obj,
        'laboratorios': laboratorios,
        'today': date.today(),
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'laboratorio_id': laboratorio_id,
        'status': status,
    }
    return render(request, 'minhas_reservas.html', context)

@login_required
@monitor_required
def reservas_do_dia(request):
    # Se for administrador ou superuser, mostra todas as reservas aprovadas
    if request.user.is_superuser or request.user.perfil == 'administrador':
        reservas = Reserva.objects.filter(
            disponibilidade__data=date.today(),
            status_aprovacao='A'
        ).select_related(
            'usuario', 'disponibilidade__laboratorio', 'disponibilidade__monitor'
        )
    # Se for monitor, mostra apenas as reservas aprovadas dos laboratórios que ele monitora
    elif request.user.perfil == 'monitor':
        reservas = Reserva.objects.filter(
            disponibilidade__data=date.today(),
            disponibilidade__monitor=request.user,
            status_aprovacao='A'
        ).select_related('usuario', 'disponibilidade__laboratorio', 'disponibilidade__monitor')
    else:
        reservas = Reserva.objects.none()
    # Filtros
    laboratorio_id = request.GET.get('laboratorio')
    usuario_nome = request.GET.get('usuario_nome')
    monitor_id = request.GET.get('monitor')
    status_frequencia = request.GET.get('status_frequencia')
    # Aplicar filtros
    if laboratorio_id and laboratorio_id != 'todos':
        reservas = reservas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    if usuario_nome:
        reservas = reservas.filter(usuario__suap_nome_completo__icontains=usuario_nome)
    if monitor_id and monitor_id != 'todos' and (request.user.is_superuser or request.user.perfil == 'administrador'):
        reservas = reservas.filter(disponibilidade__monitor_id=monitor_id)
    if status_frequencia and status_frequencia != 'todos':
        reservas = reservas.filter(status_frequencia=status_frequencia)
    # Paginação
    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Dados para os filtros
    if request.user.is_superuser or request.user.perfil == 'administrador':
        laboratorios = Laboratorio.objects.all().order_by('num_laboratorio')
        monitores = User.objects.filter(perfil='monitor').order_by('username')
    else:
        laboratorios = Laboratorio.objects.filter(
            disponibilidade__monitor=request.user
        ).distinct().order_by('num_laboratorio')
        monitores = None
    
    context = {
        'page_obj': page_obj,
        'laboratorios': laboratorios,
        'monitores': monitores,
        'laboratorio_id': laboratorio_id,
        'usuario_nome': usuario_nome,
        'monitor_id': monitor_id,
        'status_frequencia': status_frequencia,
        'today': date.today(),
    }
    return render(request, 'reservas_do_dia.html', context)

# fila de espera
@login_required
@admin_required
def fila_espera(request):
    filas = FilaEspera.objects.select_related('usuario', 'disponibilidade__laboratorio', 'disponibilidade__monitor').all().order_by('disponibilidade__data', 'disponibilidade__horario_inicio', 'data_solicitacao')
    # Filtros
    laboratorio_id = request.GET.get('laboratorio')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    usuario_nome = request.GET.get('usuario_nome')
    monitor_id = request.GET.get('monitor')
    # Aplicar filtros
    if laboratorio_id and laboratorio_id != 'todos':
        filas = filas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            filas = filas.filter(disponibilidade__data__gte=data_inicio_obj)
        except ValueError:
            messages.error(request, "Data de início inválida.")
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            filas = filas.filter(disponibilidade__data__lte=data_fim_obj)
        except ValueError:
            messages.error(request, "Data de fim inválida.")
    if usuario_nome:
        filas = filas.filter(usuario__suap_nome_completo__icontains=usuario_nome)
    if monitor_id and monitor_id != 'todos':
        filas = filas.filter(disponibilidade__monitor_id=monitor_id)
    # Paginação
    paginator = Paginator(filas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Dados para os filtros
    laboratorios = Laboratorio.objects.all().order_by('num_laboratorio')
    monitores = User.objects.filter(perfil='monitor').order_by('username')
    
    context = {
        'page_obj': page_obj,
        'laboratorios': laboratorios,
        'monitores': monitores,
        'laboratorio_id': laboratorio_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'usuario_nome': usuario_nome,
        'monitor_id': monitor_id,
    }
    return render(request, 'fila_espera.html', context)

@login_required
@admin_required
def promover_fila(request, fila_id):
    fila = get_object_or_404(FilaEspera, id=fila_id)
    disponibilidade = fila.disponibilidade
    if disponibilidade.vagas > 0:
        try:
            reserva = Reserva(usuario=fila.usuario, disponibilidade=disponibilidade)
            reserva.clean()
            reserva.save()
            disponibilidade.vagas -= 1
            disponibilidade.save()
            fila.delete()
            messages.success(request, f"Usuário {fila.usuario.username} promovido da fila de espera para reserva.")
        except ValidationError as e:
            if hasattr(e, 'message'):
                error_msg = e.message
            elif hasattr(e, 'messages') and e.messages:
                error_msg = e.messages[0]
            else:
                error_msg = str(e)
            messages.error(request, f"Não foi possível promover {fila.usuario.username}: {error_msg}")
    else:
        messages.error(request, "Não há vagas disponíveis para promover o usuário da fila de espera.")
    return redirect('fila_espera')

@login_required
@admin_required
def remover_fila(request, fila_id):
    fila = get_object_or_404(FilaEspera, id=fila_id)
    fila.delete()
    messages.success(request, f"Usuário {fila.usuario.username} removido da fila de espera.")
    return redirect('fila_espera')

@login_required
def entrar_fila_espera(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)
    # Verificar se já tem uma reserva ativa (pendente ou aprovada) para essa disponibilidade
    reserva_ativa = Reserva.objects.filter(
        usuario=request.user, 
        disponibilidade=disponibilidade,
        status_aprovacao__in=['P', 'A']
    ).first()
    if reserva_ativa:
        status_texto = "pendente" if reserva_ativa.status_aprovacao == 'P' else "aprovada"
        messages.error(request, f"Você já possui uma reserva {status_texto} para este horário.")
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
    minhas_filas = FilaEspera.objects.filter(usuario=request.user).select_related('disponibilidade__laboratorio', 'disponibilidade__monitor').order_by('disponibilidade__data', 'disponibilidade__horario_inicio')
    # Filtros
    laboratorio_id = request.GET.get('laboratorio_id')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status = request.GET.get('status')
    # Aplicar filtros
    if laboratorio_id and laboratorio_id != 'todos':
        minhas_filas = minhas_filas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            minhas_filas = minhas_filas.filter(disponibilidade__data__gte=data_inicio_obj)
        except ValueError:
            messages.error(request, "Data de início inválida.")
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            minhas_filas = minhas_filas.filter(disponibilidade__data__lte=data_fim_obj)
        except ValueError:
            messages.error(request, "Data de fim inválida.")
    dados_filas = []
    today = date.today()
    for fila in minhas_filas:
        fila_geral = FilaEspera.objects.filter(disponibilidade=fila.disponibilidade).order_by('data_solicitacao')
        usuarios_em_ordem = list(fila_geral.values_list('usuario_id', flat=True))
        posicao = usuarios_em_ordem.index(request.user.id) + 1
        # Determinar o status da fila
        if fila.disponibilidade.data < today:
            status_fila = 'processado'
        else:
            status_fila = 'ativo'
        item = {
            'id': fila.id,
            'disponibilidade': fila.disponibilidade,
            'data_solicitacao': fila.data_solicitacao,
            'posicao': posicao,
            'status': status_fila,
        }
        # Aplicar filtro de status se especificado
        if not status or status == 'todos' or status == status_fila:
            dados_filas.append(item)
    # Paginação
    paginator = Paginator(dados_filas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Dados para os filtros
    laboratorios = Laboratorio.objects.all().order_by('num_laboratorio')
    
    context = {
        'page_obj': page_obj,
        'laboratorios': laboratorios,
        'laboratorio_id': laboratorio_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status': status,
        'today': today,
    }
    return render(request, 'minha_fila_espera.html', context)

# detalhes da reserva e usuarios
@login_required
@monitor_required
def usuarios_da_reserva(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)
    # Verificar se o usuário tem permissão para ver esta disponibilidade
    if not (request.user.is_superuser or 
            request.user.perfil == 'administrador' or 
            (request.user.perfil == 'monitor' and disponibilidade.monitor == request.user)):
        messages.error(request, "Acesso negado. Você não tem permissão para ver esta disponibilidade.")
        return render(request, '403.html', status=403)
    # Buscar reservas e fila de espera para esta disponibilidade
    reservas = Reserva.objects.filter(disponibilidade=disponibilidade).select_related('usuario').order_by('usuario__username')
    fila_espera = FilaEspera.objects.filter(disponibilidade=disponibilidade).select_related('usuario').order_by('data_solicitacao')
    # Filtros
    usuario_nome = request.GET.get('usuario_nome')
    status_frequencia = request.GET.get('status_frequencia')
    # Aplicar filtros nas reservas se fornecidos
    if usuario_nome:
        reservas = reservas.filter(usuario__suap_nome_completo__icontains=usuario_nome)
    if status_frequencia and status_frequencia != 'todos':
        reservas = reservas.filter(status_frequencia=status_frequencia)
    # Aplicar filtro na fila de espera
    if usuario_nome:
        fila_espera = fila_espera.filter(usuario__suap_nome_completo__icontains=usuario_nome)
    # Paginação para reservas e fila de espera
    reservas_paginator = Paginator(reservas, 10)
    reservas_page_number = request.GET.get('reservas_page')
    reservas_page_obj = reservas_paginator.get_page(reservas_page_number)
    fila_paginator = Paginator(fila_espera, 10)
    fila_page_number = request.GET.get('fila_page')
    fila_page_obj = fila_paginator.get_page(fila_page_number)

    context = {
        'disponibilidade': disponibilidade, 
        'reservas_page_obj': reservas_page_obj,
        'fila_page_obj': fila_page_obj,
        'reservas_count': reservas.count(),
        'fila_count': fila_espera.count(),
        'usuario_nome': usuario_nome,
        'status_frequencia': status_frequencia,
    }
    return render(request, 'usuarios_da_reserva.html', context)

@login_required
@monitor_required
def listar_disponibilidades_monitor(request):
    disponibilidades = Disponibilidade.objects.filter(monitor=request.user).select_related('laboratorio').order_by('-data', 'horario_inicio')
    # Filtros
    laboratorio_id = request.GET.get('laboratorio')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    vagas_min = request.GET.get('vagas_min')
    # Aplicar filtros
    if laboratorio_id and laboratorio_id != 'todos':
        disponibilidades = disponibilidades.filter(laboratorio_id=laboratorio_id)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            disponibilidades = disponibilidades.filter(data__gte=data_inicio_obj)
        except ValueError:
            messages.error(request, "Data de início inválida.")
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            disponibilidades = disponibilidades.filter(data__lte=data_fim_obj)
        except ValueError:
            messages.error(request, "Data de fim inválida.")
    if vagas_min:
        try:
            disponibilidades = disponibilidades.filter(vagas__gte=int(vagas_min))
        except ValueError:
            messages.error(request, "Número mínimo de vagas deve ser um número.")
    # Paginação
    paginator = Paginator(disponibilidades, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Dados para os filtros (apenas laboratórios que o monitor tem disponibilidades)
    laboratorios = Laboratorio.objects.filter(
        disponibilidade__monitor=request.user
    ).distinct().order_by('num_laboratorio')
    
    context = {
        'page_obj': page_obj,
        'laboratorios': laboratorios,
        'laboratorio_id': laboratorio_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'vagas_min': vagas_min,
    }
    return render(request, 'listar_disponibilidades_monitor.html', context)

# registrar frequencias
@login_required
@monitor_required
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
    # Paginação
    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "registrar_frequencias.html", {"disponibilidade": disponibilidade, "page_obj": page_obj})

# detalhes do usuario e suas reservas
@login_required
@admin_required
def reservas_por_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    reservas = Reserva.objects.filter(usuario=usuario).select_related('disponibilidade__laboratorio').order_by('-disponibilidade__data', '-disponibilidade__horario_inicio')
    # Filtros
    laboratorio_id = request.GET.get('laboratorio')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status_frequencia = request.GET.get('status_frequencia')
    # Aplicar filtros
    if laboratorio_id and laboratorio_id != 'todos':
        reservas = reservas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__gte=data_inicio_obj)
        except ValueError:
            messages.error(request, "Data de início inválida.")
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__lte=data_fim_obj)
        except ValueError:
            messages.error(request, "Data de fim inválida.")
    if status_frequencia and status_frequencia != 'todos':
        reservas = reservas.filter(status_frequencia=status_frequencia)
    # Paginação
    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Dados para os filtros
    laboratorios = Laboratorio.objects.all().order_by('num_laboratorio')

    context = {
        'usuario': usuario, 
        'page_obj': page_obj,
        'laboratorios': laboratorios,
        'laboratorio_id': laboratorio_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_frequencia': status_frequencia,
        'today': date.today(),
    }
    return render(request, "reservas_por_usuario.html", context)

# histórico de reservas
@login_required
def historico_reservas(request):
    # Buscar todas as reservas do usuário logado
    reservas = Reserva.objects.filter(usuario=request.user).select_related(
        'disponibilidade__laboratorio'
    ).order_by('-disponibilidade__data', '-disponibilidade__horario_inicio')
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status_frequencia = request.GET.get('status_frequencia')
    laboratorio_id = request.GET.get('laboratorio')
    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__gte=data_inicio_obj)
        except ValueError:
            messages.error(request, "Data de início inválida.")
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__lte=data_fim_obj)
        except ValueError:
            messages.error(request, "Data de fim inválida.")
    if status_frequencia and status_frequencia != 'todos':
        reservas = reservas.filter(status_frequencia=status_frequencia)
    if laboratorio_id and laboratorio_id != 'todos':
        reservas = reservas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    # Separar reservas por categoria
    hoje = date.today()
    reservas_futuras = reservas.filter(disponibilidade__data__gt=hoje)
    reservas_passadas = reservas.filter(disponibilidade__data__lt=hoje)
    reservas_hoje = reservas.filter(disponibilidade__data=hoje)
    # Paginação
    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Laboratórios para o filtro
    laboratorios = Laboratorio.objects.all()
    
    context = {
        'page_obj': page_obj,
        'reservas_futuras': reservas_futuras,
        'reservas_passadas': reservas_passadas,
        'reservas_hoje': reservas_hoje,
        'laboratorios': laboratorios,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_frequencia': status_frequencia,
        'laboratorio_id': laboratorio_id,
        'today': hoje,
    }
    return render(request, 'historico_reservas.html', context)

@login_required
@admin_required
def historico_geral_reservas(request):
    # Buscar todas as reservas
    reservas = Reserva.objects.all().select_related(
        'usuario', 'disponibilidade__laboratorio'
    ).order_by('-disponibilidade__data', '-disponibilidade__horario_inicio')
    # Filtros
    usuario_id = request.GET.get('usuario')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status_frequencia = request.GET.get('status_frequencia')
    laboratorio_id = request.GET.get('laboratorio')
    # Aplicar filtros
    if usuario_id and usuario_id != 'todos':
        reservas = reservas.filter(usuario_id=usuario_id)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__gte=data_inicio_obj)
        except ValueError:
            messages.error(request, "Data de início inválida.")
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__lte=data_fim_obj)
        except ValueError:
            messages.error(request, "Data de fim inválida.")
    if status_frequencia and status_frequencia != 'todos':
        reservas = reservas.filter(status_frequencia=status_frequencia)
    if laboratorio_id and laboratorio_id != 'todos':
        reservas = reservas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    # Paginação
    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Dados para os filtros
    usuarios = User.objects.all().order_by('username')
    laboratorios = Laboratorio.objects.all()
    
    context = {
        'page_obj': page_obj,
        'usuarios': usuarios,
        'laboratorios': laboratorios,
        'usuario_id': usuario_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_frequencia': status_frequencia,
        'laboratorio_id': laboratorio_id,
    }
    return render(request, 'historico_geral_reservas.html', context)

# reservas pendentes
@login_required
@admin_required
def reservas_pendentes(request):
    reservas = Reserva.objects.filter(status_aprovacao='P').select_related(
        'usuario', 'disponibilidade__laboratorio', 'disponibilidade__monitor'
    ).order_by('data_solicitacao')
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    laboratorio_id = request.GET.get('laboratorio_id')
    usuario_id = request.GET.get('usuario_id')
    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio_parsed = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__gte=data_inicio_parsed)
        except ValueError:
            pass
    if data_fim:
        try:
            data_fim_parsed = datetime.strptime(data_fim, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__lte=data_fim_parsed)
        except ValueError:
            pass
    if laboratorio_id:
        reservas = reservas.filter(disponibilidade__laboratorio__id=laboratorio_id)
    if usuario_id:
        reservas = reservas.filter(usuario__id=usuario_id)
    # Paginação
    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Filtros
    usuarios = User.objects.all().order_by('username')
    laboratorios = Laboratorio.objects.all()
    
    context = {
        'page_obj': page_obj,
        'usuarios': usuarios,
        'laboratorios': laboratorios,
        'usuario_id': usuario_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'laboratorio_id': laboratorio_id,
    }
    return render(request, 'reservas_pendentes.html', context)

@login_required
@admin_required
def aprovar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, status_aprovacao='P')
    disponibilidade = reserva.disponibilidade
    
    if disponibilidade.vagas > 0:
        reserva.status_aprovacao = 'A'
        reserva.save()
        
        disponibilidade.vagas -= 1
        disponibilidade.save()
    
        messages.success(request, f"Reserva de {reserva.usuario.username} foi aprovada com sucesso!")
    else:
        messages.error(request, "Não há mais vagas disponíveis para este horário.")
    return redirect('reservas_pendentes')

@login_required
@admin_required
def rejeitar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, status_aprovacao='P')
    reserva.status_aprovacao = 'R'
    reserva.save()
    messages.success(request, f"Reserva de {reserva.usuario.username} foi rejeitada.")
    return redirect('reservas_pendentes')

@login_required
@admin_required
def aprovar_multiplas_reservas(request):
    if request.method == 'POST':
        reservas_ids = request.POST.getlist('reservas_selecionadas')
        if not reservas_ids:
            messages.error(request, "Nenhuma reserva foi selecionada.")
            return redirect('reservas_pendentes')
        aprovadas = 0
        sem_vagas = 0
        for reserva_id in reservas_ids:
            try:
                reserva = Reserva.objects.get(id=reserva_id, status_aprovacao='P')
                disponibilidade = reserva.disponibilidade
                if disponibilidade.vagas > 0:
                    reserva.status_aprovacao = 'A'
                    reserva.save()
                    
                    disponibilidade.vagas -= 1
                    disponibilidade.save()
                    
                    aprovadas += 1
                else:
                    sem_vagas += 1
            except Reserva.DoesNotExist:
                continue
        if aprovadas > 0:
            messages.success(request, f"{aprovadas} reserva(s) aprovada(s) com sucesso!")
        if sem_vagas > 0:
            messages.warning(request, f"{sem_vagas} reserva(s) não puderam ser aprovadas por falta de vagas.")
    return redirect('reservas_pendentes')