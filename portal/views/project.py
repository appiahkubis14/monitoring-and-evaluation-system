import json
from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F, Func, Value, CharField
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.functions import Concat
from portal.models import Project, ProjectParticipation, Farmer, Staff, Farm, Loan, LoanDisbursement, LoanRepayment, Milestone, ComplianceCheck, ComplianceCategory

@login_required
def project_tracking(request):
    """Main project tracking page with tabs"""
    return render(request, 'portal/projects/project-tracking.html')

@require_http_methods(["GET"])
@login_required
def project_list(request):
    """Server-side processing for projects datatable"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    status_filter = request.GET.get('status')
    
    # Base queryset with optimized related data
    queryset = Project.objects.select_related(
        'manager__user_profile__user'
    ).prefetch_related(
        Prefetch(
            'farm_set',
            queryset=Farm.objects.select_related('farmer')
        )
    ).all()
    
    # Apply filters
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Apply search filter
    if search_value:
        queryset = queryset.filter(
            Q(name__icontains=search_value) |
            Q(code__icontains=search_value) |
            Q(description__icontains=search_value) |
            Q(manager__user_profile__user__first_name__icontains=search_value) |
            Q(manager__user_profile__user__last_name__icontains=search_value)
        )
    
    # Total records count
    total_records = Project.objects.count()
    total_filtered = queryset.count()
    
    # Apply ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    
    # Map column index to model field
    column_mapping = {
        0: 'code',
        1: 'name',
        2: 'start_date',
        3: 'end_date',
        4: 'status',
        5: 'total_budget',
        6: 'manager__user_profile__user__first_name'
    }
    
    order_column = column_mapping.get(order_column_index, 'code')
    if order_direction == 'desc':
        order_column = f'-{order_column}'
    
    queryset = queryset.order_by(order_column)
    
    # Apply pagination
    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)
    
    # Prepare data for response
    data = []
    for project in page_obj:
        # Get all farms for this project to calculate farmer count
        project_farms = project.farm_set.all()
        
        # Get unique farmers from the project farms
        farmer_ids = project_farms.values_list('farmer_id', flat=True).distinct()
        farmers_count = len(farmer_ids)
        
        # Calculate progress metrics
        today = timezone.now().date()
        total_days = (project.end_date - project.start_date).days
        elapsed_days = (today - project.start_date).days
        progress_percent = min(100, max(0, int((elapsed_days / total_days) * 100))) if total_days > 0 else 0
        
        # Safely get manager name with fallbacks
        manager_name = 'Not assigned'
        if project.manager and project.manager.user_profile:
            user = project.manager.user_profile.user
            first_name = getattr(user, 'first_name', '')
            last_name = getattr(user, 'last_name', '')
            manager_name = f"{first_name} {last_name}".strip()
            if not manager_name:
                manager_name = f"Staff {project.manager.staff_id}" if project.manager.staff_id else "Unnamed Staff"
        
        data.append({
            'id': project.id,
            'code': project.code,
            'name': project.name,
            'description': project.description or 'No description',
            'start_date': project.start_date.strftime('%Y-%m-%d'),
            'end_date': project.end_date.strftime('%Y-%m-%d'),
            'status': project.status,
            'status_display': project.get_status_display(),
            'total_budget': float(project.total_budget),
            'manager': manager_name,
            'farmers_count': farmers_count,
            'progress_percent': progress_percent,
            'days_remaining': max(0, (project.end_date - today).days),
            'is_overdue': today > project.end_date
        })

    response = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_filtered,
        'data': data
    }
    
    return JsonResponse(response)


from django.db.models import Prefetch, Sum, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone

@require_http_methods(["GET"])
@login_required
def get_project_detail(request, project_id):
    """Get detailed information about a specific project"""
    try:
        # Get project with optimized queries
        project = Project.objects.select_related(
            'manager__user_profile__user'
        ).prefetch_related(
            Prefetch(
                'farm_set',  # Reverse relation from Farm to Project
                queryset=Farm.objects.select_related(
                    'farmer__user_profile__user',
                    'farmer__user_profile__district'
                ).prefetch_related('farmer__farms')
            )
        ).get(id=project_id)
        
        # Get all farms for this project
        project_farms = project.farm_set.all()
        
        # Get unique farmers from the project farms
        farmer_ids = project_farms.values_list('farmer_id', flat=True).distinct()
        farmers = Farmer.objects.filter(id__in=farmer_ids).select_related(
            'user_profile__user', 
            'user_profile__district'
        ).prefetch_related('farms')
        
        # Create a mapping of farmer_id to their farms in this project
        farmer_farms_map = {}
        for farm in project_farms:
            if farm.farmer_id not in farmer_farms_map:
                farmer_farms_map[farm.farmer_id] = []
            farmer_farms_map[farm.farmer_id].append(farm)
        
        # Get loan information for this project
        loans = Loan.objects.filter(project=project).select_related('farmer__user_profile__user')
        total_loans = loans.count()
        total_loan_amount = loans.aggregate(total=Sum('amount'))['total'] or 0
        total_disbursed = LoanDisbursement.objects.filter(loan__project=project).aggregate(total=Sum('amount'))['total'] or 0
        total_repaid = LoanRepayment.objects.filter(loan__project=project).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate progress metrics
        today = timezone.now().date()
        total_days = (project.end_date - project.start_date).days
        elapsed_days = (today - project.start_date).days
        progress_percent = min(100, max(0, int((elapsed_days / total_days) * 100))) if total_days > 0 else 0
        
        # Build farmers data
        farmers_data = []
        for farmer in farmers:
            # Get this farmer's farms in this specific project
            farmer_project_farms = farmer_farms_map.get(farmer.id, [])
            
            # Get all farms for this farmer (across all projects)
            all_farmer_farms = farmer.farms.all()
            
            # Calculate project-specific farm stats
            project_farms_count = len(farmer_project_farms)
            project_total_area = sum(farm.area_hectares or 0 for farm in farmer_project_farms)
            
            # Get participation details if available
            try:
                participation = ProjectParticipation.objects.get(project=project, farmer=farmer)
                enrollment_date = participation.enrollment_date.strftime('%Y-%m-%d')
                status = participation.status
                status_display = participation.get_status_display()
            except ProjectParticipation.DoesNotExist:
                enrollment_date = 'N/A'
                status = 'unknown'
                status_display = 'Unknown'
            
            farmers_data.append({
                'id': farmer.id,
                'name': f"{farmer.user_profile.user.first_name} {farmer.user_profile.user.last_name}",
                'national_id': farmer.national_id,
                'district': farmer.user_profile.district.district if farmer.user_profile.district else 'N/A',
                'enrollment_date': enrollment_date,
                'status': status,
                'status_display': status_display,
                # Project-specific farm stats
                'project_farms_count': project_farms_count,
                'project_total_area': project_total_area,
                # Overall farmer stats (all farms)
                'total_farms_count': all_farmer_farms.count(),
                'total_area_all_farms': all_farmer_farms.aggregate(total=Sum('area_hectares'))['total'] or 0,
                # Farmer details
                'years_of_experience': farmer.years_of_experience,
                'primary_crop': farmer.primary_crop,
                'community': farmer.community or 'N/A',
                'cooperative_membership': farmer.cooperative_membership or 'N/A',
                # Project farm details
                'project_farms': [
                    {
                        'id': farm.id,
                        'name': farm.name or 'Unnamed Farm',
                        'farm_code': farm.farm_code,
                        'area_hectares': farm.area_hectares,
                        'status': farm.status,
                        'registration_date': farm.registration_date.strftime('%Y-%m-%d') if farm.registration_date else 'N/A'
                    }
                    for farm in farmer_project_farms
                ]
            })
        
        data = {
            'success': True,
            'project': {
                'id': project.id,
                'code': project.code,
                'name': project.name,
                'description': project.description,
                'start_date': project.start_date.strftime('%Y-%m-%d'),
                'end_date': project.end_date.strftime('%Y-%m-%d'),
                'status': project.status,
                'status_display': project.get_status_display(),
                'total_budget': float(project.total_budget),
                'manager': f"{project.manager.user_profile.user.first_name} {project.manager.user_profile.user.last_name}" if project.manager else 'Not assigned',
                'manager_id': project.manager.id if project.manager else None,
                'progress_percent': progress_percent,
                'days_remaining': max(0, (project.end_date - today).days),
                'is_overdue': today > project.end_date,
                # Project farm statistics
                'total_project_farms': project_farms.count(),
                'total_project_area': project_farms.aggregate(total=Sum('area_hectares'))['total'] or 0,
            },
            'financials': {
                'total_loans': total_loans,
                'total_loan_amount': float(total_loan_amount),
                'total_disbursed': float(total_disbursed),
                'total_repaid': float(total_repaid),
                'repayment_rate': (float(total_repaid) / float(total_disbursed) * 100) if total_disbursed > 0 else 0
            },
            'farmers': farmers_data,
            'farmers_count': len(farmers_data),
            'total_farms_in_project': project_farms.count(),
            'total_area_in_project': project_farms.aggregate(total=Sum('area_hectares'))['total'] or 0
        }

        print(data)
        
        return JsonResponse(data)
        
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    



@require_http_methods(["POST"])
@login_required
@transaction.atomic
def create_project(request):
    """Create a new project"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['name', 'code', 'start_date', 'end_date', 'total_budget']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)
        
        # Check if project code already exists
        if Project.objects.filter(code=data['code']).exists():
            return JsonResponse({'success': False, 'error': 'Project code already exists'}, status=400)
        
        # Get manager if provided
        manager = None
        if data.get('manager_id'):
            try:
                manager = Staff.objects.get(id=data['manager_id'])
            except Staff.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Manager not found'}, status=404)
        
        # Create project
        project = Project.objects.create(
            name=data['name'],
            code=data['code'],
            description=data.get('description'),
            start_date=data['start_date'],
            end_date=data['end_date'],
            status=data.get('status', 'planning'),
            total_budget=float(data['total_budget']),
            manager=manager
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Project created successfully',
            'project_id': project.id
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def update_project(request, project_id):
    """Update an existing project"""
    try:
        data = json.loads(request.body)
        project = Project.objects.get(id=project_id)
        
        # Update project data
        if 'name' in data:
            project.name = data['name']
        if 'code' in data and data['code'] != project.code:
            # Check if new code already exists
            if Project.objects.filter(code=data['code']).exclude(id=project_id).exists():
                return JsonResponse({'success': False, 'error': 'Project code already exists'}, status=400)
            project.code = data['code']
        if 'description' in data:
            project.description = data['description']
        if 'start_date' in data:
            project.start_date = data['start_date']
        if 'end_date' in data:
            project.end_date = data['end_date']
        if 'status' in data:
            project.status = data['status']
        if 'total_budget' in data:
            project.total_budget = float(data['total_budget'])
        
        # Update manager if provided
        if 'manager_id' in data:
            if data['manager_id']:
                try:
                    manager = Staff.objects.get(id=data['manager_id'])
                    project.manager = manager
                except Staff.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Manager not found'}, status=404)
            else:
                project.manager = None
        
        project.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Project updated successfully'
        })
        
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def delete_project(request):
    """Delete a project (soft delete)"""
    try:
        data = json.loads(request.body)
        project_id = data.get('id')
        
        if not project_id:
            return JsonResponse({'success': False, 'error': 'Project ID is required'}, status=400)
        
        project = Project.objects.get(id=project_id)
        project.delete()  # This will set is_deleted=True due to TimeStampModel
        
        return JsonResponse({'success': True, 'message': 'Project deleted successfully'})
        
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def add_farmer_to_project(request, project_id):
    """Add a farmer to a project"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        if not data.get('farmer_id'):
            return JsonResponse({'success': False, 'error': 'Farmer ID is required'}, status=400)
        
        # Check if project exists
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
        
        # Check if farmer exists
        try:
            farmer = Farmer.objects.get(id=data['farmer_id'])
        except Farmer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Farmer not found'}, status=404)
        
        # Check if farmer is already in project
        if ProjectParticipation.objects.filter(project=project, farmer=farmer).exists():
            return JsonResponse({'success': False, 'error': 'Farmer is already in this project'}, status=400)
        
        # Create project participation
        participation = ProjectParticipation.objects.create(
            project=project,
            farmer=farmer,
            status=data.get('status', 'active'),
            enrollment_date=data.get('enrollment_date', timezone.now().date())
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Farmer added to project successfully',
            'participation_id': participation.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def update_project_participation(request, participation_id):
    """Update a project participation record"""
    try:
        data = json.loads(request.body)
        
        # Get participation record
        participation = ProjectParticipation.objects.get(id=participation_id)
        
        # Update participation data
        if 'status' in data:
            participation.status = data['status']
        if 'exit_date' in data:
            participation.exit_date = data['exit_date']
        
        participation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Participation updated successfully'
        })
        
    except ProjectParticipation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Participation record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_project_timeline(request):
    """Get project timeline data for Gantt chart"""
    try:
        projects = Project.objects.all()
        
        timeline_data = []
        for project in projects:
            timeline_data.append({
                'id': project.id,
                'name': project.name,
                'code': project.code,
                'start': project.start_date.isoformat(),
                'end': project.end_date.isoformat(),
                'progress': min(100, max(0, int(((timezone.now().date() - project.start_date).days / 
                                       (project.end_date - project.start_date).days) * 100))) if (project.end_date - project.start_date).days > 0 else 0,
                'status': project.status,
                'status_display': project.get_status_display(),
                'manager': f"{project.manager.user_profile.user.first_name} {project.manager.user_profile.user.last_name}" if project.manager else 'Not assigned'
            })
        
        return JsonResponse({'success': True, 'timeline': timeline_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_project_stats(request):
    """Get statistics about projects"""
    try:
        # Total projects count
        total_projects = Project.objects.count()
        
        # Projects by status
        projects_by_status = Project.objects.values('status').annotate(
            count=Count('id'),
            total_budget=Sum('total_budget')
        )
        
        # Active projects
        active_projects = Project.objects.filter(status='active').count()
        
        # Overdue projects
        today = timezone.now().date()
        overdue_projects = Project.objects.filter(end_date__lt=today, status='active').count()
        
        # Total budget
        total_budget = Project.objects.aggregate(total=Sum('total_budget'))['total'] or 0
        
        # Average project duration
        avg_duration = Project.objects.annotate(
            duration=F('end_date') - F('start_date')
        ).aggregate(avg_duration=Avg('duration'))['avg_duration']
        
        # Recent projects (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_projects = Project.objects.filter(created_at__gte=thirty_days_ago).count()
        
        data = {
            'success': True,
            'stats': {
                'total_projects': total_projects,
                'projects_by_status': list(projects_by_status),
                'active_projects': active_projects,
                'overdue_projects': overdue_projects,
                'total_budget': float(total_budget),
                'avg_duration_days': avg_duration.days if avg_duration else 0,
                'recent_projects': recent_projects
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_available_farmers(request, project_id):
    """Get farmers not yet in a specific project"""
    try:
        # Get farmers already in project
        project_farmer_ids = ProjectParticipation.objects.filter(
            project_id=project_id
        ).values_list('farmer_id', flat=True)
        
        # Get available farmers
        available_farmers = Farmer.objects.exclude(
            id__in=project_farmer_ids
        ).select_related('user_profile__user', 'user_profile__district')
        
        data = []
        for farmer in available_farmers:
            data.append({
                'id': farmer.id,
                'name': f"{farmer.user_profile.user.first_name} {farmer.user_profile.user.last_name}",
                'national_id': farmer.national_id,
                'district': farmer.user_profile.district.name if farmer.user_profile.district else 'N/A',
                'farm_size': farmer.farm_size,
                'farms_count': farmer.farms.count()
            })
        
        return JsonResponse({'success': True, 'farmers': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_staff_members_project(request):
    """Get all staff members for dropdowns"""
    try:
        staff_members = Staff.objects.select_related('user_profile__user').filter(is_active=True)
        
        data = []
        for staff in staff_members:
            # Safely get user name with fallbacks
            first_name = getattr(staff.user_profile.user, 'first_name', '')
            last_name = getattr(staff.user_profile.user, 'last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            
            # Use staff ID if name is empty
            if not full_name:
                full_name = f"Staff {staff.staff_id}" if staff.staff_id else "Unnamed Staff"
            
            staff_data = {
                'id': staff.id,
                'name': full_name,
                'designation': staff.designation if staff.designation else 'Staff',
                'staff_id': staff.staff_id if staff.staff_id else f"ID-{staff.id}"
            }
            data.append(staff_data)

        print(f"Loaded {len(data)} staff members")
        
        return JsonResponse({'success': True, 'staff': data})
    
    except Exception as e:
        print(f"Error loading staff members: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f'Failed to load staff members: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def project_export(request):
    """Export projects data in various formats"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    format_type = request.GET.get('format', 'csv')
    projects = Project.objects.select_related('manager__user_profile__user').prefetch_related('participating_farmers')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="projects_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Code', 'Name', 'Description', 'Start Date', 'End Date', 
            'Status', 'Total Budget', 'Manager', 'Farmers Count',
            'Days Remaining', 'Progress (%)'
        ])
        
        for project in projects:
            today = timezone.now().date()
            total_days = (project.end_date - project.start_date).days
            elapsed_days = (today - project.start_date).days
            progress_percent = min(100, max(0, int((elapsed_days / total_days) * 100))) if total_days > 0 else 0
            
            writer.writerow([
                project.code,
                project.name,
                project.description or '',
                project.start_date.strftime('%Y-%m-%d'),
                project.end_date.strftime('%Y-%m-%d'),
                project.get_status_display(),
                float(project.total_budget),
                f"{project.manager.user_profile.user.first_name} {project.manager.user_profile.user.last_name}" if project.manager else '',
                project.participating_farmers.count(),
                max(0, (project.end_date - today).days),
                progress_percent
            ])
        
        return response
    
    elif format_type == 'json':
        data = []
        for project in projects:
            today = timezone.now().date()
            total_days = (project.end_date - project.start_date).days
            elapsed_days = (today - project.start_date).days
            progress_percent = min(100, max(0, int((elapsed_days / total_days) * 100))) if total_days > 0 else 0
            
            data.append({
                'code': project.code,
                'name': project.name,
                'description': project.description,
                'start_date': project.start_date.strftime('%Y-%m-%d'),
                'end_date': project.end_date.strftime('%Y-%m-%d'),
                'status': project.status,
                'status_display': project.get_status_display(),
                'total_budget': float(project.total_budget),
                'manager': f"{project.manager.user_profile.user.first_name} {project.manager.user_profile.user.last_name}" if project.manager else '',
                'farmers_count': project.participating_farmers.count(),
                'days_remaining': max(0, (project.end_date - today).days),
                'progress_percent': progress_percent
            })
        
        return JsonResponse({'projects': data})
    
    else:
        return JsonResponse({'success': False, 'error': 'Unsupported format'}, status=500)

# @require_http_methods(["GET"])
# @login_required
# def get_milestones(request, project_id):
#     """Get milestones for a specific project"""
#     try:
#         # Get actual milestones from database
#         milestones = Milestone.objects.filter(project_id=project_id).order_by('due_date')
        
#         milestone_data = []
#         for milestone in milestones:
#             milestone_data.append({
#                 'id': milestone.id,
#                 'name': milestone.name,
#                 'description': milestone.description,
#                 'due_date': milestone.due_date.strftime('%Y-%m-%d'),
#                 'status': milestone.status,
#                 'completion_date': milestone.completion_date.strftime('%Y-%m-%d') if milestone.completion_date else None,
#                 'weight': float(milestone.weight) if milestone.weight else 0,
#                 'dependencies': list(milestone.dependencies.values_list('id', flat=True)) if milestone.dependencies.exists() else []
#             })
        
#         return JsonResponse({'success': True, 'milestones': milestone_data})
        
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)

# @require_http_methods(["GET"])
# @login_required
# def get_compliance_data(request, project_id):
#     """Get compliance data for a specific project"""
#     try:
#         # Get compliance checks for this project
#         compliance_checks = ComplianceCheck.objects.filter(project_id=project_id).select_related('category')
        
#         # Group by category
#         compliance_data = {}
#         categories = ComplianceCategory.objects.all()
        
#         for category in categories:
#             category_checks = compliance_checks.filter(category=category)
#             total_checks = category_checks.count()
            
#             if total_checks > 0:
#                 passed_checks = category_checks.filter(status='passed').count()
#                 score = (passed_checks / total_checks) * 100
                
#                 # Determine status based on score
#                 if score >= 90:
#                     status = 'fully_compliant'
#                 elif score >= 80:
#                     status = 'compliant'
#                 elif score >= 70:
#                     status = 'needs_improvement'
#                 else:
#                     status = 'non_compliant'
                
#                 # Get issues (failed checks)
#                 issues = []
#                 for check in category_checks.filter(status='failed'):
#                     issues.append({
#                         'description': f"{check.description} - Due: {check.due_date.strftime('%Y-%m-%d')}",
#                         'severity': check.severity
#                     })
                
#                 compliance_data[category.name.lower()] = {
#                     'score': round(score, 1),
#                     'status': status,
#                     'issues': issues
#                 }
#             else:
#                 # No checks for this category
#                 compliance_data[category.name.lower()] = {
#                     'score': 0,
#                     'status': 'non_compliant',
#                     'issues': [{'description': 'No compliance checks configured for this category', 'severity': 'medium'}]
#                 }
        
#         return JsonResponse({'success': True, 'compliance': compliance_data})
        
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Update the get_milestones and get_compliance_data views

@require_http_methods(["GET"])
@login_required
def get_milestones(request, project_id):
    """Get milestones for a specific project"""
    try:
        # Get actual milestones from database
        milestones = Milestone.objects.filter(project_id=project_id).select_related(
            'assigned_to__user_profile__user'
        ).order_by('due_date')
        
        milestone_data = []
        for milestone in milestones:
            milestone_data.append({
                'id': milestone.id,
                'name': milestone.name,
                'description': milestone.description,
                'due_date': milestone.due_date.strftime('%Y-%m-%d'),
                'completion_date': milestone.completion_date.strftime('%Y-%m-%d') if milestone.completion_date else None,
                'status': milestone.status,
                'status_display': milestone.get_status_display(),
                'weight': float(milestone.weight),
                'assigned_to': f"{milestone.assigned_to.user_profile.user.first_name} {milestone.assigned_to.user_profile.user.last_name}" if milestone.assigned_to else 'Not assigned',
                'notes': milestone.notes,
                'dependencies': list(milestone.dependencies.values_list('id', flat=True))
            })
        
        return JsonResponse({'success': True, 'milestones': milestone_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_compliance_data(request, project_id):
    """Get compliance data for a specific project"""
    try:
        # Get compliance checks for this project
        compliance_checks = ComplianceCheck.objects.filter(
            project_id=project_id
        ).select_related('category', 'assigned_to__user_profile__user')
        
        # Group by category
        compliance_data = {}
        categories = ComplianceCategory.objects.filter(is_active=True)
        
        for category in categories:
            category_checks = compliance_checks.filter(category=category)
            total_checks = category_checks.count()
            
            if total_checks > 0:
                passed_checks = category_checks.filter(status='passed').count()
                score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
                
                # Determine status based on score
                if score >= 90:
                    status = 'fully_compliant'
                elif score >= 80:
                    status = 'compliant'
                elif score >= 70:
                    status = 'needs_improvement'
                else:
                    status = 'non_compliant'
                
                # Get issues (failed checks)
                issues = []
                for check in category_checks.filter(status='failed'):
                    issues.append({
                        'description': f"{check.name}: {check.description}",
                        'severity': check.severity,
                        'due_date': check.due_date.strftime('%Y-%m-%d'),
                        'assigned_to': f"{check.assigned_to.user_profile.user.first_name} {check.assigned_to.user_profile.user.last_name}" if check.assigned_to else 'Not assigned'
                    })
                
                compliance_data[category.name.lower().replace(' ', '_')] = {
                    'score': round(score, 1),
                    'status': status,
                    'total_checks': total_checks,
                    'passed_checks': passed_checks,
                    'failed_checks': category_checks.filter(status='failed').count(),
                    'pending_checks': category_checks.filter(status='pending').count(),
                    'issues': issues
                }
            else:
                # No checks for this category
                compliance_data[category.name.lower().replace(' ', '_')] = {
                    'score': 0,
                    'status': 'non_compliant',
                    'total_checks': 0,
                    'passed_checks': 0,
                    'failed_checks': 0,
                    'pending_checks': 0,
                    'issues': [{'description': 'No compliance checks configured for this category', 'severity': 'medium'}]
                }
        
        return JsonResponse({'success': True, 'compliance': compliance_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    







@require_http_methods(["POST"])
@login_required
@transaction.atomic
def create_milestone(request, project_id):
    """Create a new milestone for a project"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['name', 'due_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)
        
        # Check if project exists
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
        
        # Get assigned staff if provided
        assigned_to = None
        if data.get('assigned_to_id'):
            try:
                assigned_to = Staff.objects.get(id=data['assigned_to_id'])
            except Staff.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Staff member not found'}, status=404)
        
        # Create milestone
        milestone = Milestone.objects.create(
            project=project,
            name=data['name'],
            description=data.get('description'),
            due_date=data['due_date'],
            status=data.get('status', 'pending'),
            weight=float(data.get('weight', 0)),
            assigned_to=assigned_to,
            notes=data.get('notes')
        )
        
        # Add dependencies if provided
        if data.get('dependencies'):
            dependencies = Milestone.objects.filter(id__in=data['dependencies'], project=project)
            milestone.dependencies.set(dependencies)
        
        return JsonResponse({
            'success': True,
            'message': 'Milestone created successfully',
            'milestone_id': milestone.id
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def update_milestone(request, milestone_id):
    """Update an existing milestone"""
    try:
        data = json.loads(request.body)
        
        # Get milestone
        milestone = Milestone.objects.get(id=milestone_id)
        
        # Update milestone data
        if 'name' in data:
            milestone.name = data['name']
        if 'description' in data:
            milestone.description = data['description']
        if 'due_date' in data:
            milestone.due_date = data['due_date']
        if 'status' in data:
            milestone.status = data['status']
        if 'weight' in data:
            milestone.weight = float(data['weight'])
        if 'notes' in data:
            milestone.notes = data['notes']
        
        # Update assigned staff if provided
        if 'assigned_to_id' in data:
            if data['assigned_to_id']:
                try:
                    assigned_to = Staff.objects.get(id=data['assigned_to_id'])
                    milestone.assigned_to = assigned_to
                except Staff.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Staff member not found'}, status=404)
            else:
                milestone.assigned_to = None
        
        milestone.save()
        
        # Update dependencies if provided
        if 'dependencies' in data:
            dependencies = Milestone.objects.filter(id__in=data['dependencies'], project=milestone.project)
            milestone.dependencies.set(dependencies)
        
        return JsonResponse({
            'success': True,
            'message': 'Milestone updated successfully'
        })
        
    except Milestone.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Milestone not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def create_compliance_check(request, project_id):
    """Create a new compliance check for a project"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['name', 'category_id', 'due_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)
        
        # Check if project exists
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
        
        # Check if category exists
        try:
            category = ComplianceCategory.objects.get(id=data['category_id'])
        except ComplianceCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Compliance category not found'}, status=404)
        
        # Get assigned staff if provided
        assigned_to = None
        if data.get('assigned_to_id'):
            try:
                assigned_to = Staff.objects.get(id=data['assigned_to_id'])
            except Staff.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Staff member not found'}, status=404)
        
        # Create compliance check
        check = ComplianceCheck.objects.create(
            project=project,
            category=category,
            name=data['name'],
            description=data.get('description', ''),
            due_date=data['due_date'],
            status=data.get('status', 'pending'),
            severity=data.get('severity', 'medium'),
            assigned_to=assigned_to,
            notes=data.get('notes'),
            evidence_required=data.get('evidence_required', False),
            evidence_description=data.get('evidence_description'),
            auto_check=data.get('auto_check', False),
            check_frequency=data.get('check_frequency', 'once')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Compliance check created successfully',
            'check_id': check.id
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



@require_http_methods(["GET"])
@login_required
def get_compliance_categories(request):
    """Get all compliance categories for dropdowns"""
    categories = ComplianceCategory.objects.filter(is_active=True)
    
    data = []
    for category in categories:
        data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'weight': float(category.weight)
        })
    
    return JsonResponse({'success': True, 'categories': data})









############################################################################################################

@require_http_methods(["GET"])
@login_required
def milestones_page(request):
    """Milestones page view"""
    projects = Project.objects.all()
    staff_members = Staff.objects.select_related('user_profile__user').filter(is_active=True)
    
    context = {
        'projects': projects,
        'staff_members': staff_members
    }
    return render(request, 'portal/projects/milestones.html', context)

@require_http_methods(["GET"])
@login_required
def milestones_data(request):
    """Server-side processing for milestones datatable"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    project_id = request.GET.get('project_id')
    status_filter = request.GET.get('status')
    
    # Base queryset
    queryset = Milestone.objects.select_related(
        'project', 'assigned_to__user_profile__user'
    ).prefetch_related('dependencies')
    
    # Apply filters
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Total records count
    total_records = Milestone.objects.count()
    total_filtered = queryset.count()
    
    # Apply ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    
    # Map column index to model field
    column_mapping = {
        0: 'name',
        1: 'project__name',
        2: 'due_date',
        3: 'status',
        4: 'assigned_to__user_profile__user__first_name',
        5: 'weight'
    }
    
    order_column = column_mapping.get(order_column_index, 'due_date')
    if order_direction == 'desc':
        order_column = f'-{order_column}'
    
    queryset = queryset.order_by(order_column)
    
    # Apply pagination
    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)
    
    # Prepare data for response
    data = []
    for milestone in page_obj:
        data.append({
            'id': milestone.id,
            'name': milestone.name,
            'project_name': f"{milestone.project.code} - {milestone.project.name}",
            'project_id': milestone.project.id,
            'due_date': milestone.due_date.isoformat(),
            'completion_date': milestone.completion_date.isoformat() if milestone.completion_date else None,
            'status': milestone.status,
            'status_display': milestone.get_status_display(),
            'weight': float(milestone.weight),
            'assigned_to': f"{milestone.assigned_to.user_profile.user.first_name} {milestone.assigned_to.user_profile.user.last_name}" if milestone.assigned_to else 'Not assigned',
            'assigned_to_id': milestone.assigned_to.id if milestone.assigned_to else None,
            'description': milestone.description,
            'notes': milestone.notes,
            'created_at': milestone.created_at.isoformat(),
            'updated_at': milestone.updated_at.isoformat()
        })
    
    response = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_filtered,
        'data': data
    }
    
    return JsonResponse(response)

@require_http_methods(["GET"])
@login_required
def milestone_detail(request, milestone_id):
    """Get detailed information about a specific milestone"""
    try:
        milestone = Milestone.objects.select_related(
            'project', 'assigned_to__user_profile__user'
        ).prefetch_related('dependencies').get(id=milestone_id)
        
        data = {
            'success': True,
            'milestone': {
                'id': milestone.id,
                'name': milestone.name,
                'description': milestone.description,
                'due_date': milestone.due_date.isoformat(),
                'completion_date': milestone.completion_date.isoformat() if milestone.completion_date else None,
                'status': milestone.status,
                'status_display': milestone.get_status_display(),
                'weight': float(milestone.weight),
                'assigned_to': f"{milestone.assigned_to.user_profile.user.first_name} {milestone.assigned_to.user_profile.user.last_name}" if milestone.assigned_to else 'Not assigned',
                'assigned_to_id': milestone.assigned_to.id if milestone.assigned_to else None,
                'project_name': f"{milestone.project.code} - {milestone.project.name}",
                'project_id': milestone.project.id,
                'notes': milestone.notes,
                'created_at': milestone.created_at.isoformat(),
                'updated_at': milestone.updated_at.isoformat(),
                'dependencies': [
                    {
                        'id': dep.id,
                        'name': dep.name
                    } for dep in milestone.dependencies.all()
                ]
            }
        }
        
        return JsonResponse(data)
        
    except Milestone.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Milestone not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def milestones_summary(request):
    """Get milestones summary statistics"""
    try:
        project_id = request.GET.get('project_id')
        
        # Base queryset
        queryset = Milestone.objects.all()
        
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Calculate statistics
        total = queryset.count()
        completed = queryset.filter(status='completed').count()
        in_progress = queryset.filter(status='in_progress').count()
        delayed = queryset.filter(status='delayed').count()
        pending = queryset.filter(status='pending').count()
        
        # Calculate completion percentage
        completion_percent = (completed / total * 100) if total > 0 else 0
        
        data = {
            'success': True,
            'summary': {
                'total': total,
                'completed': completed,
                'in_progress': in_progress,
                'delayed': delayed,
                'pending': pending,
                'completion_percent': round(completion_percent, 1)
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def create_milestone(request):
    """Create a new milestone"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['name', 'project_id', 'due_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)
        
        # Check if project exists
        try:
            project = Project.objects.get(id=data['project_id'])
        except Project.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
        
        # Get assigned staff if provided
        assigned_to = None
        if data.get('assigned_to_id'):
            try:
                assigned_to = Staff.objects.get(id=data['assigned_to_id'])
            except Staff.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Staff member not found'}, status=404)
        
        # Create milestone
        milestone = Milestone.objects.create(
            project=project,
            name=data['name'],
            description=data.get('description'),
            due_date=data['due_date'],
            status=data.get('status', 'pending'),
            weight=float(data.get('weight', 0)),
            assigned_to=assigned_to,
            notes=data.get('notes')
        )
        
        # Add dependencies if provided
        if data.get('dependencies'):
            dependencies = Milestone.objects.filter(
                id__in=data['dependencies'], 
                project=project
            )
            milestone.dependencies.set(dependencies)
        
        return JsonResponse({
            'success': True,
            'message': 'Milestone created successfully',
            'milestone_id': milestone.id
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def update_milestone(request, milestone_id):
    """Update an existing milestone"""
    try:
        data = json.loads(request.body)
        
        # Get milestone
        milestone = Milestone.objects.get(id=milestone_id)
        
        # Update milestone data
        if 'name' in data:
            milestone.name = data['name']
        if 'description' in data:
            milestone.description = data['description']
        if 'due_date' in data:
            milestone.due_date = data['due_date']
        if 'status' in data:
            milestone.status = data['status']
        if 'weight' in data:
            milestone.weight = float(data['weight'])
        if 'notes' in data:
            milestone.notes = data['notes']
        
        # Update assigned staff if provided
        if 'assigned_to_id' in data:
            if data['assigned_to_id']:
                try:
                    assigned_to = Staff.objects.get(id=data['assigned_to_id'])
                    milestone.assigned_to = assigned_to
                except Staff.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Staff member not found'}, status=404)
            else:
                milestone.assigned_to = None
        
        milestone.save()
        
        # Update dependencies if provided
        if 'dependencies' in data:
            dependencies = Milestone.objects.filter(
                id__in=data['dependencies'], 
                project=milestone.project
            )
            milestone.dependencies.set(dependencies)
        
        return JsonResponse({
            'success': True,
            'message': 'Milestone updated successfully'
        })
        
    except Milestone.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Milestone not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def delete_milestone(request):
    """Delete a milestone"""
    try:
        data = json.loads(request.body)
        milestone_id = data.get('id')
        
        if not milestone_id:
            return JsonResponse({'success': False, 'error': 'Milestone ID is required'}, status=400)
        
        milestone = Milestone.objects.get(id=milestone_id)
        milestone.delete()
        
        return JsonResponse({'success': True, 'message': 'Milestone deleted successfully'})
        
    except Milestone.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Milestone not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

#####################################################################################################################

from datetime import datetime, date, timedelta
from django.db.models import Avg, Case, When, F, FloatField, Q
from django.db.models.functions import Coalesce

@require_http_methods(["GET"])
@login_required
def timeline_page(request):
    """Timeline page view"""
    projects = Project.objects.all()
    
    context = {
        'projects': projects
    }
    return render(request, 'portal/projects/timeline.html', context)

@require_http_methods(["GET"])
@login_required
def timeline_data(request):
    """Get timeline data for visualization"""
    try:
        project_id = request.GET.get('project_id')
        timeframe = request.GET.get('timeframe')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Base queryset
        if project_id:
            projects = Project.objects.filter(id=project_id)
        else:
            projects = Project.objects.all()
        
        # Apply date filters
        if timeframe or (start_date and end_date):
            today = timezone.now().date()
            
            if timeframe == 'month':
                start_date_filter = today.replace(day=1)
                end_date_filter = (start_date_filter + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            elif timeframe == 'quarter':
                quarter = (today.month - 1) // 3 + 1
                start_date_filter = date(today.year, 3 * quarter - 2, 1)
                end_date_filter = (start_date_filter + timedelta(days=92)).replace(day=1) - timedelta(days=1)
            elif timeframe == 'year':
                start_date_filter = date(today.year, 1, 1)
                end_date_filter = date(today.year, 12, 31)
            elif start_date and end_date:
                start_date_filter = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_filter = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                start_date_filter = None
                end_date_filter = None
            
            if start_date_filter and end_date_filter:
                projects = projects.filter(
                    Q(start_date__lte=end_date_filter, end_date__gte=start_date_filter) |
                    Q(milestones__due_date__range=[start_date_filter, end_date_filter])
                ).distinct()
        
        timeline_data = []
        for project in projects:
            # Calculate progress
            today = timezone.now().date()
            total_days = (project.end_date - project.start_date).days
            elapsed_days = (today - project.start_date).days
            progress_percent = min(100, max(0, int((elapsed_days / total_days) * 100))) if total_days > 0 else 0
            
            # Get milestones
            milestones = Milestone.objects.filter(project=project).values(
                'id', 'name', 'due_date', 'status', 'completion_date'
            )
            
            timeline_data.append({
                'id': project.id,
                'name': project.name,
                'code': project.code,
                'start': project.start_date.isoformat(),
                'end': project.end_date.isoformat(),
                'status': project.status,
                'status_display': project.get_status_display(),
                'progress': progress_percent,
                'days_remaining': max(0, (project.end_date - today).days),
                'manager': f"{project.manager.user_profile.user.first_name} {project.manager.user_profile.user.last_name}" if project.manager else 'Not assigned',
                'milestones': list(milestones)
            })
        
        return JsonResponse({'success': True, 'timeline': timeline_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def timeline_summary(request):
    """Get timeline summary statistics"""
    try:
        project_id = request.GET.get('project_id')
        
        # Base queryset
        if project_id:
            projects = Project.objects.filter(id=project_id)
            milestones = Milestone.objects.filter(project_id=project_id)
        else:
            projects = Project.objects.all()
            milestones = Milestone.objects.all()
        
        # Calculate statistics
        total_projects = projects.count()
        active_projects = projects.filter(status='active').count()
        
        today = timezone.now().date()
        upcoming_milestones = milestones.filter(
            due_date__gt=today,
            status__in=['pending', 'in_progress']
        ).count()
        
        delayed_milestones = milestones.filter(
            due_date__lt=today,
            status__in=['pending', 'in_progress']
        ).count()
        
        completed_milestones = milestones.filter(status='completed').count()
        
        # Calculate average progress - FIXED VERSION
        # Extract number of days from intervals using ExpressionWrapper
        from django.db.models import ExpressionWrapper, F, DurationField
        from django.db.models.functions import ExtractDay
        
        # Calculate progress for each project
        progress_cases = []
        for project in projects:
            if project.start_date <= today <= project.end_date:
                # Project is ongoing
                total_days = (project.end_date - project.start_date).days
                elapsed_days = (today - project.start_date).days
                progress = (elapsed_days / total_days) * 100 if total_days > 0 else 0
            elif project.end_date < today:
                # Project is completed
                progress = 100
            else:
                # Project hasn't started yet
                progress = 0
            progress_cases.append(progress)
        
        # Calculate average progress
        avg_progress = sum(progress_cases) / len(progress_cases) if progress_cases else 0
        
        data = {
            'success': True,
            'summary': {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'upcoming_milestones': upcoming_milestones,
                'delayed_milestones': delayed_milestones,
                'completed_milestones': completed_milestones,
                'avg_progress': round(avg_progress, 1)
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)