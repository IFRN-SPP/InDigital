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
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_POST


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
    
def aluno_required(view_func):
    """
    Decorator para verificar se o usuário é aluno, monitor ou administrador.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if (
            request.user.perfil in ['aluno', 'monitor', 'administrador']
            or request.user.is_superuser
        ):
            return view_func(request, *args, **kwargs)    
        messages.error(request, "Acesso negado. Apenas usuários autenticados com vínculo institucional podem acessar esta página.")
        return render(request, '403.html', status=403)
    
    return _wrapped_view

def monitor_required(view_func):
    """
    Decorator para verificar se o usuário é um monitor.
    Usuários com perfil 'outro' não têm permissão para acessar páginas de monitor.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if request.user.perfil == 'outro':
            messages.error(request, "Acesso restrito a usuários autenticados via SUAP.")
            return render(request, '403.html', status=403)
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
            return redirect('account_login')
        if request.user.perfil == 'outro':
            messages.error(request, "Acesso restrito a usuários autenticados via SUAP.")
            return render(request, '403.html', status=403)
        # Verificar se o usuário é administrador/superuser
        if request.user.is_superuser or request.user.perfil == 'administrador':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Acesso negado. Apenas administradores têm permissão para acessar esta página.")
            return render(request, '403.html', status=403)
    
    return _wrapped_view


def filter_by_status(queryset, status):
    if status and status != 'todos':
        if status == 'N':
            return queryset.filter(Q(status_frequencia='N') | Q(status_frequencia=''))
        return queryset.filter(status_frequencia=status)
    return queryset

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
    user = request.user
    # Estatísticas
    minhas_reservas = Reserva.objects.filter(usuario=user)

    total_reservas = minhas_reservas.count()
    reservas_presentes = minhas_reservas.filter(status_frequencia='P').count()
    reservas_faltas = minhas_reservas.filter(status_frequencia='F').count()
    reservas_pendentes = minhas_reservas.filter(
        disponibilidade__data__gte=date.today()
    ).filter(Q(status_frequencia='') | Q(status_frequencia='N')).count()
    
    context = {
        'total_reservas': total_reservas,
        'reservas_presentes': reservas_presentes,
        'reservas_faltas': reservas_faltas,
        'reservas_pendentes': reservas_pendentes,
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

    minhas_reservas = Reserva.objects.filter(usuario=user)

    total_reservas = minhas_reservas.count()
    reservas_presentes = minhas_reservas.filter(status_frequencia='P').count()
    reservas_faltas = minhas_reservas.filter(status_frequencia='F').count()
    reservas_pendentes = minhas_reservas.filter(
        disponibilidade__data__gte=date.today()
    ).filter(Q(status_frequencia='') | Q(status_frequencia='N')).count()

    context = {
        'total_reservas': total_reservas,
        'reservas_presentes': reservas_presentes,
        'reservas_faltas': reservas_faltas,
        'reservas_pendentes': reservas_pendentes,
    }
    return render(request, "index.html", context)

# crud de disponibilidade
@login_required
@admin_required
def editar_disponibilidade(request, reserva_id):
    reserva = get_object_or_404(Disponibilidade, id=reserva_id)
    context = {
        "reserva": reserva,
        "form": DisponibilidadeForm(instance=reserva),
        "laboratorios": Laboratorio.objects.all()
    }

    if request.method == 'POST':
        form = DisponibilidadeForm(request.POST, instance=reserva)
        if form.is_valid():
            disponibilidade = form.save(commit=False)

            # VALIDAÇÃO: Número de vagas não pode ser maior que a capacidade do laboratório
            if disponibilidade.vagas > disponibilidade.laboratorio.capacidade:
                error_msg = f"O número de vagas não pode ser maior que a capacidade máxima do laboratório: {disponibilidade.laboratorio.capacidade} vagas."
                form.add_error('vagas', error_msg)
                context["form"] = form

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False, 
                        'errors': {'vagas': error_msg}
                    }, status=400)

                messages.error(request, error_msg)
                return render(request, "editar_disponibilidade.html", context)

            if disponibilidade.horario_inicio >= disponibilidade.horario_fim:
                form.add_error(None, "O horário de início deve ser menor que o horário de fim.")
                context["form"] = form

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    form_html = render_to_string('modal_form.html', {'form': form}, request=request)
                    return JsonResponse({'success': False, 'form_html': form_html})

                messages.error(request, "O horário de início deve ser menor que o horário de fim.")
                return render(request, "editar_disponibilidade.html", context)

            conflito = Disponibilidade.objects.filter(
                laboratorio=disponibilidade.laboratorio,
                data=disponibilidade.data,
                horario_inicio__lt=disponibilidade.horario_fim,
                horario_fim__gt=disponibilidade.horario_inicio
            ).exclude(id=disponibilidade.id).exists()

            if conflito:
                form.add_error(None, "Já existe uma disponibilidade nesse horário para este laboratório.")
                context["form"] = form

                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    form_html = render_to_string('modal_form.html', {'form': form}, request=request)
                    return JsonResponse({'success': False, 'form_html': form_html})

                messages.error(request, "Já existe uma disponibilidade nesse horário para este laboratório.")
                return render(request, "editar_disponibilidade.html", context)

            
            disponibilidade.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': 'Disponibilidade atualizada com sucesso!'
                })
                
            messages.success(request, "Disponibilidade editada com sucesso!")
            return redirect('listar_disponibilidades')
        else:
            context["form"] = form
            
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {field: error[0] for field, error in form.errors.items()}
                return JsonResponse({
                    'success': False, 
                    'errors': errors
                }, status=400)
                
            messages.error(request, "Erro ao editar disponibilidade!")

    return render(request, "editar_disponibilidade.html", context)

@login_required
@admin_required
def listar_disponibilidades(request):
    form = DisponibilidadeForm()
    
    disponibilidades = Disponibilidade.objects.all().select_related('laboratorio', 'monitor').order_by('-data', 'horario_inicio')
    
    # Filtros
    laboratorio_id = request.GET.get('laboratorio_id')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    monitor_id = request.GET.get('monitor_id')
    
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
    
    # Paginação
    paginator = Paginator(disponibilidades, 5)
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
        'form': form,
        'today': date.today(),
    }
    
    return render(request, "listar_disponibilidades.html", context)

@login_required
@admin_required
def excluir_disponibilidade(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)
    reservas_existentes = Reserva.objects.filter(disponibilidade=disponibilidade).exists()

    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if reservas_existentes:
            return JsonResponse({
                'success': False,
                'message': 'Não é possível excluir esta disponibilidade porque existem reservas associadas.'
            })

        
        if request.method == 'POST':
            disponibilidade.delete()
            return JsonResponse({
                'success': True,
                'message': 'Disponibilidade excluída com sucesso!'
            })

        
        return JsonResponse({'success': False, 'message': 'Método inválido.'}, status=400)

    
    if reservas_existentes:
        messages.error(request, "Não é possível excluir esta disponibilidade porque existem reservas associadas.")
        return redirect('listar_disponibilidades')

    if request.method == 'POST':
        disponibilidade.delete()
        messages.success(request, "Disponibilidade excluída com sucesso!")
        return redirect('listar_disponibilidades')

    
    return render(request, "excluir_disponibilidade.html", {'reserva': disponibilidade})

@login_required
@admin_required
def criar_disponibilidade(request):
    if request.method == 'POST':
        form = DisponibilidadeForm(request.POST)
        if form.is_valid():
            disponibilidade = form.save(commit=False)

            if disponibilidade.vagas <= 0:
                form.add_error('vagas', "O número de vagas deve ser maior que zero.")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    form_html = render_to_string('modal_form.html', {'form': form}, request=request)
                    return JsonResponse({'success': False, 'form_html': form_html})

                messages.error(request, "O número de vagas deve ser maior que zero.")
                return redirect('listar_disponibilidades')

            if disponibilidade.horario_inicio >= disponibilidade.horario_fim:
                form.add_error(None, "O horário de início deve ser menor que o horário de fim.")

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    form_html = render_to_string('modal_form.html', {'form': form}, request=request)
                    return JsonResponse({'success': False, 'form_html': form_html})

                messages.error(request, "O horário de início deve ser menor que o horário de fim.")
                return redirect('listar_disponibilidades')

            conflito = Disponibilidade.objects.filter(
                laboratorio=disponibilidade.laboratorio,
                data=disponibilidade.data,
                horario_inicio__lt=disponibilidade.horario_fim,
                horario_fim__gt=disponibilidade.horario_inicio
            ).exists()

            if conflito:
                messages.error(request, "Já existe uma disponibilidade nesse horário para este laboratório.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    form_html = render_to_string('modal_form.html', {'form': form}, request=request)
                    return JsonResponse({'success': False, 'form_html': form_html})
                return redirect('listar_disponibilidades')

            disponibilidade.save()
            
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
    laboratorios_list = Laboratorio.objects.all().order_by('num_laboratorio')

    # Filtros
    laboratorio_id = request.GET.get('laboratorio_id')
    capacidade_min = request.GET.get('capacidade_min')
    capacidade_max = request.GET.get('capacidade_max')
   
    if laboratorio_id and laboratorio_id != 'todos':
        laboratorios_list = laboratorios_list.filter(id=laboratorio_id)    
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
    paginator = Paginator(laboratorios_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'form': form, 
        'laboratorios': Laboratorio.objects.all(),
        'laboratorio_id': laboratorio_id,
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
@aluno_required
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
    # Remover disponibilidades cujo horário de início já passou (tempo local)
    # Convertendo queryset em lista filtrada para usar o método is_passada()
    from django.utils import timezone
    agora = timezone.localtime(timezone.now())
    disponibilidades = [d for d in disponibilidades if not d.is_passada()]
    # marcar flag para templates
    for d in disponibilidades:
        d.expirada = d.is_passada()
    # Paginação 
    paginator = Paginator(disponibilidades, 5) 
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
        'now_time': agora.strftime('%H:%M'),
    }
    return render(request, "horarios.html", context)

@login_required
def reservar_laboratorio(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)
    # Impedir reservas para disponibilidades que já iniciaram
    if disponibilidade.is_passada():
        messages.error(request, "Não é possível reservar: este horário já passou.")
        return redirect('horarios')
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
        return redirect('historico_reservas')
    disponibilidade = reserva.disponibilidade
    # Só devolver vaga se a reserva estava aprovada
    if reserva.status_aprovacao == 'A':
        disponibilidade.vagas += 1
        disponibilidade.save()
    reserva.delete()
    messages.success(request, "Sua reserva foi cancelada com sucesso!")
    return redirect('historico_reservas')

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
    laboratorio_id = request.GET.get('laboratorio_id')
    status_frequencia = request.GET.get('status_frequencia')
    usuario_id = request.GET.get('usuario_id')
    monitor_id = request.GET.get('monitor_id')
    # Aplicar filtros
    if laboratorio_id and laboratorio_id != 'todos':
        reservas = reservas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    reservas = filter_by_status(reservas, status_frequencia)
    if usuario_id and usuario_id != 'todos':
        reservas = reservas.filter(usuario_id=usuario_id)
    if monitor_id and monitor_id != 'todos' and (request.user.is_superuser or request.user.perfil == 'administrador'):
        reservas = reservas.filter(disponibilidade__monitor_id=monitor_id)
    # Paginação
    paginator = Paginator(reservas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Dados para os filtros
    if request.user.is_superuser or request.user.perfil == 'administrador':
        laboratorios = Laboratorio.objects.all().order_by('num_laboratorio')
        monitores = User.objects.filter(perfil='monitor').order_by('username')
        usuarios = User.objects.filter(reserva__disponibilidade__data=date.today()).distinct().order_by('username')
    else:
        laboratorios = Laboratorio.objects.filter(
            disponibilidade__monitor=request.user
        ).distinct().order_by('num_laboratorio')
        usuarios = User.objects.filter(reserva__disponibilidade__monitor=request.user, reserva__disponibilidade__data=date.today()).distinct().order_by('username')
    
    context = {
        'page_obj': page_obj,
        'laboratorios': laboratorios,
        'monitores': monitores,
        'usuarios': usuarios,
        'laboratorio_id': laboratorio_id,
        'monitor_id': monitor_id,
        'status_frequencia': status_frequencia,
        'usuario_id': usuario_id,
        'today': date.today(),
    }
    return render(request, 'reservas_do_dia.html', context)

# fila de espera
@login_required
@admin_required
def fila_espera(request):
    filas = FilaEspera.objects.select_related('usuario', 'disponibilidade__laboratorio', 'disponibilidade__monitor').all().order_by('disponibilidade__data', 'disponibilidade__horario_inicio', 'data_solicitacao')
    # Filtros
    laboratorio_id = request.GET.get('laboratorio_id')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    usuario_id = request.GET.get('usuario_id')
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
    if usuario_id and usuario_id != 'todos':
        filas = filas.filter(usuario_id=usuario_id)
    # Paginação
    paginator = Paginator(filas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'laboratorio_id': laboratorio_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'usuario_id': usuario_id,
        'laboratorios': Laboratorio.objects.all(),
        'usuarios': User.objects.filter(),
    }
    return render(request, 'fila_espera.html', context)

@login_required
@admin_required
def promover_fila(request, fila_id):
    fila = get_object_or_404(FilaEspera, id=fila_id)
    disponibilidade = fila.disponibilidade
    agora = timezone.localtime(timezone.now())

    # Rejeitar métodos diferentes de POST para segurança
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if request.method != 'POST':
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Método inválido.'}, status=405)
        return redirect('fila_espera')

    # Não permitir promover reservas cujo horário já passou (início já ocorreu ou término já passou)
    if disponibilidade.is_passada() or disponibilidade.end_datetime() <= agora:
        msg = "Não é possível promover esta reserva: o horário já passou."
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg}, status=400)
        messages.error(request, msg)
        return redirect('fila_espera')

    if disponibilidade.vagas <= 0:
        msg = "Não há vagas disponíveis para promover o usuário da fila de espera."
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg}, status=400)
        messages.error(request, msg)
        return redirect('fila_espera')

    # Usar transação para evitar condições de corrida
    try:
        with transaction.atomic():
            reserva = Reserva(usuario=fila.usuario, disponibilidade=disponibilidade, status_aprovacao='A')
            reserva.clean()
            reserva.save()
            disponibilidade.vagas -= 1
            disponibilidade.save()
            fila.delete()
    except ValidationError as e:
        if hasattr(e, 'message'):
            error_msg = e.message
        elif hasattr(e, 'messages') and e.messages:
            error_msg = e.messages[0]
        else:
            error_msg = str(e)
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, f"Não foi possível promover {fila.usuario.username}: {error_msg}")
        return redirect('fila_espera')
    except Exception as e:
        if is_ajax:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        messages.error(request, f"Erro ao promover usuário: {str(e)}")
        return redirect('fila_espera')

    success_msg = f"Usuário {fila.usuario.username} promovido da fila de espera para reserva."
    if is_ajax:
        return JsonResponse({'success': True, 'message': success_msg})
    messages.success(request, success_msg)
    return redirect('fila_espera')

@login_required
@admin_required
def remover_fila(request, fila_id):
    fila = get_object_or_404(FilaEspera, id=fila_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if request.method != 'POST':
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Método inválido.'}, status=405)
        return redirect('fila_espera')

    usuario_nome = fila.usuario.username
    fila.delete()
    success_msg = f"Usuário {usuario_nome} removido da fila de espera."
    if is_ajax:
        return JsonResponse({'success': True, 'message': success_msg})
    messages.success(request, success_msg)
    return redirect('fila_espera')

@login_required
def entrar_fila_espera(request, disponibilidade_id):
    disponibilidade = get_object_or_404(Disponibilidade, id=disponibilidade_id)
    # Impedir entrar na fila para disponibilidades que já iniciaram
    if disponibilidade.is_passada():
        messages.error(request, "Não é possível entrar na fila: este horário já passou.")
        return redirect('horarios')
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
    # Não permitir sair da fila se o horário já passou
    agora = timezone.localtime(timezone.now())
    try:
        if fila.disponibilidade.end_datetime() <= agora:
            messages.error(request, "Não é possível sair da fila: o horário já passou.")
            return redirect('minha_fila_espera')
    except Exception:
        # Se houver qualquer problema ao calcular end_datetime, prevenir a ação por segurança
        messages.error(request, "Não é possível sair da fila neste momento.")
        return redirect('minha_fila_espera')

    fila.delete()
    messages.success(request, "Você saiu da fila de espera.")
    return redirect('minha_fila_espera')

@login_required
@aluno_required
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
    agora = timezone.localtime(timezone.now())
    
    for fila in minhas_filas:
        fila_geral = FilaEspera.objects.filter(disponibilidade=fila.disponibilidade).order_by('data_solicitacao')
        usuarios_em_ordem = list(fila_geral.values_list('usuario_id', flat=True))
        posicao = usuarios_em_ordem.index(request.user.id) + 1
        
        # Determinar o status da fila
        if fila.disponibilidade.data < today:
            status_fila = 'processado'
        else:
            status_fila = 'ativo'
        
        # Determinar se o usuário ainda pode sair da fila (horário não passou e status ativo)
        try:
            can_sair = (fila.disponibilidade.end_datetime() > agora) and (status_fila == 'ativo')
        except Exception:
            can_sair = False

        item = {
            'id': fila.id,
            'disponibilidade': fila.disponibilidade,
            'data_solicitacao': fila.data_solicitacao,
            'posicao': posicao,
            'status': status_fila,
            'can_sair': can_sair,
        }
        
        # Aplicar filtro de status se especificado
        if not status or status == 'todos' or status == status_fila:
            dados_filas.append(item)
    
    # Paginação
    paginator = Paginator(dados_filas, 5)
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


@login_required
@aluno_required
def sair_fila_espera(request, fila_id):
    if request.method == 'POST':
        try:
            fila = FilaEspera.objects.get(id=fila_id, usuario=request.user)
            
            today = date.today()
            agora = timezone.localtime(timezone.now())
            
            try:
                can_sair = (fila.disponibilidade.end_datetime() > agora) and (fila.disponibilidade.data >= today)
            except Exception:
                can_sair = False
            
            if can_sair:
                laboratorio_num = fila.disponibilidade.laboratorio.num_laboratorio
                data_fila = fila.disponibilidade.data
                fila.delete()
                messages.success(request, f'Você saiu da fila de espera do laboratório {laboratorio_num} para o dia {data_fila.strftime("%d/%m/%Y")}.')
            else:
                messages.error(request, 'Não é possível sair desta fila. O horário já passou ou a reserva já foi processada.')
                
        except FilaEspera.DoesNotExist:
            messages.error(request, 'Erro: Solicitação não encontrada ou você não tem permissão para esta ação.')
        
        return redirect('minha_fila_espera')
    
    
    return redirect('minha_fila_espera')

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
    reservas = filter_by_status(reservas, status_frequencia)
    # Aplicar filtro na fila de espera
    if usuario_nome:
        fila_espera = fila_espera.filter(usuario__suap_nome_completo__icontains=usuario_nome)
    # Paginação para reservas e fila de espera
    reservas_paginator = Paginator(reservas, 5)
    reservas_page_number = request.GET.get('reservas_page')
    reservas_page_obj = reservas_paginator.get_page(reservas_page_number)
    fila_paginator = Paginator(fila_espera, 5)
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
    laboratorio_id = request.GET.get('laboratorio_id')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
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
    # Paginação
    paginator = Paginator(disponibilidades, 5)
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
    reservas = filter_by_status(reservas, status_frequencia)
    # Paginação
    paginator = Paginator(reservas, 5)
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
@aluno_required
def historico_reservas(request):
    # Buscar todas as reservas do usuário logado
    reservas = Reserva.objects.filter(usuario=request.user).select_related(
        'disponibilidade__laboratorio'
    ).order_by('-disponibilidade__data', '-disponibilidade__horario_inicio')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status_frequencia = request.GET.get('status_frequencia')
    laboratorio_id = request.GET.get('laboratorio_id')
    active_tab = request.GET.get('tab', 'todas')  
    
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
    
    reservas = filter_by_status(reservas, status_frequencia)
    
    if laboratorio_id and laboratorio_id != 'todos':
        reservas = reservas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    
    # Separar reservas por categoria considerando horário de término
    from django.utils import timezone
    agora = timezone.localtime(timezone.now())
    
    
    reservas_list = list(reservas)
    
    
    for r in reservas_list:
        try:
            r.expirada = (r.disponibilidade.end_datetime() <= agora)
        except Exception:
            r.expirada = False
    
    reservas_futuras = [r for r in reservas_list if r.disponibilidade.end_datetime() > agora]
    reservas_passadas = [r for r in reservas_list if r.disponibilidade.end_datetime() <= agora]
    reservas_hoje = [r for r in reservas_list if r.disponibilidade.data == agora.date() and r.disponibilidade.end_datetime() > agora]
    
    # Paginação para todas as reservas
    paginator = Paginator(reservas_list, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Paginação para reservas futuras
    paginator_futuras = Paginator(reservas_futuras, 4)
    page_number_futuras = request.GET.get('page_futuras')
    page_obj_futuras = paginator_futuras.get_page(page_number_futuras)
    
    # Paginação para reservas de hoje
    paginator_hoje = Paginator(reservas_hoje, 4)
    page_number_hoje = request.GET.get('page_hoje')
    page_obj_hoje = paginator_hoje.get_page(page_number_hoje)
    
    # Paginação para reservas passadas
    paginator_passadas = Paginator(reservas_passadas, 4)
    page_number_passadas = request.GET.get('page_passadas')
    page_obj_passadas = paginator_passadas.get_page(page_number_passadas)
    
    # Laboratórios para o filtro
    laboratorios = Laboratorio.objects.all()
    hoje = agora.date()
    
    context = {
        'page_obj': page_obj,
        'page_obj_futuras': page_obj_futuras,
        'page_obj_hoje': page_obj_hoje,
        'page_obj_passadas': page_obj_passadas,
        'reservas_futuras': reservas_futuras,
        'reservas_passadas': reservas_passadas,
        'reservas_hoje': reservas_hoje,
        'laboratorios': laboratorios,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_frequencia': status_frequencia,
        'laboratorio_id': laboratorio_id,
        'today': hoje,
        'active_tab': active_tab,  
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
    laboratorio_id = request.GET.get('laboratorio_id')
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
    reservas = filter_by_status(reservas, status_frequencia)
    if laboratorio_id and laboratorio_id != 'todos':
        reservas = reservas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    # Paginação
    paginator = Paginator(reservas, 5)
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
    if data_inicio:
        try:
            data_inicio_parsed = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__gte=data_inicio_parsed)
        except ValueError:
            messages.error(request, "Data de início inválida.")
    if data_fim:
        try:
            data_fim_parsed = datetime.strptime(data_fim, '%Y-%m-%d').date()
            reservas = reservas.filter(disponibilidade__data__lte=data_fim_parsed)
        except ValueError:
            messages.error(request, "Data de fim inválida.")
    if laboratorio_id and laboratorio_id != 'todos':
        reservas = reservas.filter(disponibilidade__laboratorio_id=laboratorio_id)
    if usuario_id and usuario_id != 'todos':
        reservas = reservas.filter(usuario_id=usuario_id)
    # Paginação
    paginator = Paginator(reservas, 5)
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
    agora = timezone.localtime(timezone.now())
    
    # Não permitir aprovar reservas cujo horário já passou
    if disponibilidade.is_passada() or disponibilidade.end_datetime() <= agora:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': "Não é possível aprovar esta reserva: o horário já passou."})
        messages.error(request, "Não é possível aprovar esta reserva: o horário já passou.")
        return redirect('reservas_pendentes')
    
    if disponibilidade.vagas > 0:
        reserva.status_aprovacao = 'A'
        reserva.save()
        disponibilidade.vagas -= 1
        disponibilidade.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f"Reserva aprovada com sucesso!"})
        messages.success(request, f"Reserva de {reserva.usuario.username} foi aprovada com sucesso!")
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': "Não há mais vagas disponíveis para este horário."})
        messages.error(request, "Não há mais vagas disponíveis para este horário.")
    
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('reservas_pendentes')

@login_required
@admin_required
@require_POST
def aprovar_multiplas_reservas(request):
    try:
        reservas_ids = request.POST.getlist('reservas_selecionadas[]')
        reservas_aprovadas = 0
        errors = []
        
        for reserva_id in reservas_ids:
            try:
                reserva = Reserva.objects.get(id=reserva_id, status_aprovacao='P')
                disponibilidade = reserva.disponibilidade
                agora = timezone.localtime(timezone.now())
                
                # Verificar se pode aprovar
                if disponibilidade.is_passada() or disponibilidade.end_datetime() <= agora:
                    errors.append(f"Reserva {reserva_id}: horário já passou")
                    continue
                
                if disponibilidade.vagas > 0:
                    reserva.status_aprovacao = 'A'
                    reserva.save()
                    disponibilidade.vagas -= 1
                    disponibilidade.save()
                    reservas_aprovadas += 1
                else:
                    errors.append(f"Reserva {reserva_id}: não há vagas disponíveis")
                    
            except Reserva.DoesNotExist:
                errors.append(f"Reserva {reserva_id}: não encontrada ou já aprovada")
        
        return JsonResponse({
            'success': True,
            'message': f'{reservas_aprovadas} reserva(s) aprovada(s) com sucesso!',
            'aprovadas': reservas_aprovadas,
            'errors': errors
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
        reservas_aprovadas = 0
        
        for reserva_id in reservas_ids:
            try:
                reserva = Reserva.objects.get(id=reserva_id, status_aprovacao='P')
                disponibilidade = reserva.disponibilidade
                agora = timezone.localtime(timezone.now())
                
                # Verificar se pode aprovar
                if not (disponibilidade.is_passada() or disponibilidade.end_datetime() <= agora):
                    if disponibilidade.vagas > 0:
                        reserva.status_aprovacao = 'A'
                        reserva.save()
                        disponibilidade.vagas -= 1
                        disponibilidade.save()
                        reservas_aprovadas += 1
                        
            except Reserva.DoesNotExist:
                continue
        
        if reservas_aprovadas > 0:
            messages.success(request, f'{reservas_aprovadas} reserva(s) aprovada(s) com sucesso!')
        else:
            messages.error(request, 'Nenhuma reserva pôde ser aprovada.')
    
    return redirect('reservas_pendentes')