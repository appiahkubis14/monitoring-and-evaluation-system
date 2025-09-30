from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
import json
from datetime import datetime
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from api import models
from portal.models import (
    Farm, FollowUpAction, Infrastructure, MonitoringVisit, UserProfile, 
    Staff, Farmer, Project
)

def render_monitoring_page(request):
    """Render the main monitoring page"""
    return render(request, 'portal/monitoring/monitoring.html')

@require_http_methods(["GET"])
def monitoring_visit_list(request):
    """List all monitoring visits with filtering and pagination"""
    print("Monitoring visit list requested")
    try:
        # Get query parameters
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 25)
        
        # Start with all visits
        visits = MonitoringVisit.objects.select_related('officer__user', 'farm__farmer__user_profile__user').all()
        print(visits)
        
        # Apply filters
        if status_filter:
            visits = visits.filter(follow_up_status=status_filter)
        
        if search_query:
            visits = visits.filter(
                Q(visit_id__icontains=search_query) |
                Q(farm__name__icontains=search_query) |
                Q(officer__user__first_name__icontains=search_query) |
                Q(officer__user__last_name__icontains=search_query) |
                Q(land_use_classification__icontains=search_query)
            )
        
        # Order by date (newest first)
        visits = visits.order_by('-date_of_visit')
        
        # Pagination
        paginator = Paginator(visits, per_page)
        page_obj = paginator.get_page(page)
        
        # Prepare data for JSON response
        visits_data = []
        for visit in page_obj:
            visits_data.append({
                'id': visit.id,
                'visit_id': visit.visit_id,
                'date_of_visit': visit.date_of_visit.strftime('%Y-%m-%d'),
                'officer_name': f"{visit.officer.user.first_name} {visit.officer.user.last_name}",
                'officer_id': visit.officer.id,
                'farm_name': visit.farm.name,
                'farm_id': visit.farm.id,
                'farm_code': visit.farm.farm_code,
                'farmer_name': f"{visit.farm.farmer.user_profile.user.first_name} {visit.farm.farmer.user_profile.user.last_name}" if visit.farm.farmer else 'N/A',
                'farm_boundary_polygon': visit.farm_boundary_polygon,
                'land_use_classification': visit.land_use_classification,
                'distance_to_road': float(visit.distance_to_road),
                'distance_to_market': float(visit.distance_to_market),
                'proximity_to_processing_facility': float(visit.proximity_to_processing_facility),
                'main_buyers': visit.main_buyers,
                'service_provider': visit.service_provider,
                'cooperatives_affiliated': visit.cooperatives_affiliated,
                'value_chain_linkages': visit.value_chain_linkages,
                'observations': visit.observations,
                'issues_identified': visit.issues_identified,
                'infrastructure_identified': visit.infrastructure_identified,
                'recommended_actions': visit.recommended_actions,
                'follow_up_status': visit.follow_up_status,
                'follow_up_status_display': visit.get_follow_up_status_display(),
                'created_at': visit.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': visit.updated_at.strftime('%Y-%m-%d %H:%M'),
            })

            print(visits_data)
        
        return JsonResponse({
            'success': True,
            'data': visits_data,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading monitoring visits: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def create_monitoring_visit(request):
    """Create a new monitoring visit"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['date_of_visit', 'officer_id', 'farm_id']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        # Generate visit ID
        visit_id = f"MV{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create monitoring visit
        visit = MonitoringVisit(
            visit_id=visit_id,
            date_of_visit=data.get('date_of_visit'),
            officer_id=data.get('officer_id'),
            farm_id=data.get('farm_id'),
            farm_boundary_polygon=data.get('farm_boundary_polygon', False),
            land_use_classification=data.get('land_use_classification', ''),
            distance_to_road=data.get('distance_to_road', 0),
            distance_to_market=data.get('distance_to_market', 0),
            proximity_to_processing_facility=data.get('proximity_to_processing_facility', 0),
            main_buyers=data.get('main_buyers', ''),
            service_provider=data.get('service_provider', ''),
            cooperatives_affiliated=data.get('cooperatives_affiliated', ''),
            value_chain_linkages=data.get('value_chain_linkages', ''),
            observations=data.get('observations', ''),
            issues_identified=data.get('issues_identified', ''),
            infrastructure_identified=data.get('infrastructure_identified', ''),
            recommended_actions=data.get('recommended_actions', ''),
            follow_up_status=data.get('follow_up_status', 'pending')
        )
        
        visit.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Monitoring visit created successfully',
            'visit_id': visit.visit_id,
            'id': visit.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error creating monitoring visit: {str(e)}'
        }, status=400)

@require_http_methods(["GET"])
def monitoring_visit_detail(request, visit_id):
    """Get detailed information about a specific monitoring visit"""
    try:
        visit = get_object_or_404(
            MonitoringVisit.objects.select_related(
                'officer__user', 
                'farm__farmer__user_profile__user'
            ), 
            id=visit_id
        )
        
        # Get follow-up actions
        follow_up_actions = FollowUpAction.objects.filter(monitoring_visit=visit).order_by('-deadline')
        follow_up_data = []
        for action in follow_up_actions:
            follow_up_data.append({
                'id': action.id,
                'action_description': action.action_description,
                'responsible_person': action.responsible_person,
                'deadline': action.deadline.strftime('%Y-%m-%d'),
                'status': action.status,
                'status_display': action.get_status_display(),
                'notes': action.notes,
                'created_at': action.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Get infrastructure details
        infrastructure_details = Infrastructure.objects.filter(monitoring_visit=visit)
        infrastructure_data = []
        for infra in infrastructure_details:
            infrastructure_data.append({
                'id': infra.id,
                'infrastructure_type': infra.infrastructure_type,
                'description': infra.description,
                'condition': infra.condition,
                'condition_display': infra.get_condition_display()
            })
        
        visit_data = {
            'id': visit.id,
            'visit_id': visit.visit_id,
            'date_of_visit': visit.date_of_visit.strftime('%Y-%m-%d'),
            'officer': {
                'id': visit.officer.id,
                'name': f"{visit.officer.user.first_name} {visit.officer.user.last_name}",
                'email': visit.officer.user.email,
                'phone': visit.officer.phone_number,
                'role': visit.officer.role
            },
            'farm': {
                'id': visit.farm.id,
                'name': visit.farm.name,
                'farm_code': visit.farm.farm_code,
                'location': visit.farm.location.wkt if visit.farm.location else 'N/A',
                'area_hectares': float(visit.farm.area_hectares) if visit.farm.area_hectares else 0,
                'farmer_name': f"{visit.farm.farmer.user_profile.user.first_name} {visit.farm.farmer.user_profile.user.last_name}" if visit.farm.farmer else 'N/A',
                'farmer_national_id': visit.farm.farmer.national_id if visit.farm.farmer else 'N/A'
            },
            'farm_boundary_polygon': visit.farm_boundary_polygon,
            'land_use_classification': visit.land_use_classification,
            'distance_to_road': float(visit.distance_to_road),
            'distance_to_market': float(visit.distance_to_market),
            'proximity_to_processing_facility': float(visit.proximity_to_processing_facility),
            'main_buyers': visit.main_buyers,
            'service_provider': visit.service_provider,
            'cooperatives_affiliated': visit.cooperatives_affiliated,
            'value_chain_linkages': visit.value_chain_linkages,
            'observations': visit.observations,
            'issues_identified': visit.issues_identified,
            'infrastructure_identified': visit.infrastructure_identified,
            'recommended_actions': visit.recommended_actions,
            'follow_up_status': visit.follow_up_status,
            'follow_up_status_display': visit.get_follow_up_status_display(),
            'created_at': visit.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': visit.updated_at.strftime('%Y-%m-%d %H:%M'),
            'follow_up_actions': follow_up_data,
            'infrastructure_details': infrastructure_data,
            'follow_up_actions_count': len(follow_up_data),
            'infrastructure_count': len(infrastructure_data)
        }
        
        return JsonResponse({
            'success': True,
            'visit': visit_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading monitoring visit details: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def update_monitoring_visit(request, visit_id):
    """Update an existing monitoring visit"""
    try:
        visit = get_object_or_404(MonitoringVisit, id=visit_id)
        data = json.loads(request.body)
        
        # Update fields
        update_fields = [
            'date_of_visit', 'farm_boundary_polygon', 'land_use_classification',
            'distance_to_road', 'distance_to_market', 'proximity_to_processing_facility',
            'main_buyers', 'service_provider', 'cooperatives_affiliated',
            'value_chain_linkages', 'observations', 'issues_identified',
            'infrastructure_identified', 'recommended_actions', 'follow_up_status'
        ]
        
        for field in update_fields:
            if field in data:
                setattr(visit, field, data[field])
        
        visit.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Monitoring visit updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error updating monitoring visit: {str(e)}'
        }, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def delete_monitoring_visit(request, visit_id):
    """Delete a monitoring visit"""
    try:
        visit = get_object_or_404(MonitoringVisit, id=visit_id)
        visit_id_str = visit.visit_id
        visit.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Monitoring visit {visit_id_str} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting monitoring visit: {str(e)}'
        }, status=400)

@require_http_methods(["GET"])
def get_available_farms(request):
    """Get list of available farms for dropdown"""
    try:
        farms = Farm.objects.select_related('farmer__user_profile__user').filter(is_deleted=False)
        farms_data = []
        
        for farm in farms:
            farms_data.append({
                'id': farm.id,
                'name': farm.name,
                'farm_code': farm.farm_code,
                'location': farm.location.wkt if farm.location else 'N/A',
                'area_hectares': float(farm.area_hectares) if farm.area_hectares else 0,
                'farmer_name': f"{farm.farmer.user_profile.user.first_name} {farm.farmer.user_profile.user.last_name}" if farm.farmer else 'N/A',
                'farmer_national_id': farm.farmer.national_id if farm.farmer else 'N/A'
            })
        
        return JsonResponse({
            'success': True,
            'farms': farms_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading farms: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_available_officers(request):
    """Get list of available officers for dropdown"""
    try:
        officers = UserProfile.objects.filter(
            user__is_active=True, 
            role__in=['field_officer', 'supervisor', 'manager', 'admin']
        ).select_related('user')
        
        officers_data = []
        
        for officer in officers:
            officers_data.append({
                'id': officer.id,
                'name': f"{officer.user.first_name} {officer.user.last_name}",
                'email': officer.user.email,
                'phone': officer.phone_number,
                'role': officer.role,
                'role_display': officer.get_role_display()
            })
        
        return JsonResponse({
            'success': True,
            'officers': officers_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading officers: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def create_follow_up_action(request, visit_id):
    """Create a follow-up action for a monitoring visit"""
    try:
        visit = get_object_or_404(MonitoringVisit, id=visit_id)
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['action_description', 'responsible_person', 'deadline']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        action = FollowUpAction(
            monitoring_visit=visit,
            action_description=data.get('action_description', ''),
            responsible_person=data.get('responsible_person', ''),
            deadline=data.get('deadline'),
            status=data.get('status', 'pending'),
            notes=data.get('notes', '')
        )
        
        action.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Follow-up action created successfully',
            'action_id': action.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error creating follow-up action: {str(e)}'
        }, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def update_follow_up_action(request, action_id):
    """Update a follow-up action"""
    try:
        action = get_object_or_404(FollowUpAction, id=action_id)
        data = json.loads(request.body)
        
        # Update fields
        update_fields = ['action_description', 'responsible_person', 'deadline', 'status', 'notes']
        for field in update_fields:
            if field in data:
                setattr(action, field, data[field])
        
        action.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Follow-up action updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error updating follow-up action: {str(e)}'
        }, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def delete_follow_up_action(request, action_id):
    """Delete a follow-up action"""
    try:
        action = get_object_or_404(FollowUpAction, id=action_id)
        action.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Follow-up action deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting follow-up action: {str(e)}'
        }, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def create_infrastructure(request, visit_id):
    """Create infrastructure detail for a monitoring visit"""
    try:
        visit = get_object_or_404(MonitoringVisit, id=visit_id)
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['infrastructure_type', 'description', 'condition']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        infrastructure = Infrastructure(
            monitoring_visit=visit,
            infrastructure_type=data.get('infrastructure_type', ''),
            description=data.get('description', ''),
            condition=data.get('condition', 'good')
        )
        
        infrastructure.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Infrastructure detail created successfully',
            'infrastructure_id': infrastructure.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error creating infrastructure detail: {str(e)}'
        }, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def update_infrastructure(request, infrastructure_id):
    """Update an infrastructure detail"""
    try:
        infrastructure = get_object_or_404(Infrastructure, id=infrastructure_id)
        data = json.loads(request.body)
        
        # Update fields
        update_fields = ['infrastructure_type', 'description', 'condition']
        for field in update_fields:
            if field in data:
                setattr(infrastructure, field, data[field])
        
        infrastructure.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Infrastructure detail updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error updating infrastructure detail: {str(e)}'
        }, status=400)

@require_http_methods(["POST"])
@csrf_exempt
def delete_infrastructure(request, infrastructure_id):
    """Delete an infrastructure detail"""
    try:
        infrastructure = get_object_or_404(Infrastructure, id=infrastructure_id)
        infrastructure.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Infrastructure detail deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting infrastructure detail: {str(e)}'
        }, status=400)

@require_http_methods(["GET"])
def export_monitoring_visits(request):
    """Export monitoring visits to CSV"""
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        
        # Query visits
        visits = MonitoringVisit.objects.select_related('officer__user', 'farm__farmer__user_profile__user').all()
        
        if status_filter:
            visits = visits.filter(follow_up_status=status_filter)
        
        if search_query:
            visits = visits.filter(
                Q(visit_id__icontains=search_query) |
                Q(farm__name__icontains=search_query) |
                Q(officer__user__first_name__icontains=search_query)
            )
        
        # Create HTTP response with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="monitoring_visits.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Visit ID', 'Date of Visit', 'Officer', 'Farm', 'Farmer',
            'Farm Boundary Polygon', 'Land Use Classification',
            'Distance to Road (km)', 'Distance to Market (km)', 
            'Proximity to Processing Facility (km)',
            'Main Buyers', 'Service Provider', 'Cooperatives Affiliated',
            'Value Chain Linkages', 'Observations', 'Issues Identified',
            'Infrastructure Identified', 'Recommended Actions', 'Follow-Up Status',
            'Created Date'
        ])
        
        for visit in visits:
            farmer_name = f"{visit.farm.farmer.user_profile.user.first_name} {visit.farm.farmer.user_profile.user.last_name}" if visit.farm.farmer else 'N/A'
            
            writer.writerow([
                visit.visit_id,
                visit.date_of_visit.strftime('%Y-%m-%d'),
                f"{visit.officer.user.first_name} {visit.officer.user.last_name}",
                visit.farm.name,
                farmer_name,
                'Yes' if visit.farm_boundary_polygon else 'No',
                visit.land_use_classification,
                float(visit.distance_to_road),
                float(visit.distance_to_market),
                float(visit.proximity_to_processing_facility),
                visit.main_buyers,
                visit.service_provider,
                visit.cooperatives_affiliated,
                visit.value_chain_linkages,
                visit.observations,
                visit.issues_identified,
                visit.infrastructure_identified,
                visit.recommended_actions,
                visit.get_follow_up_status_display(),
                visit.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error exporting data: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def monitoring_stats(request):
    """Get monitoring statistics"""
    try:
        total_visits = MonitoringVisit.objects.count()
        
        # Visits by status
        visits_by_status = MonitoringVisit.objects.values('follow_up_status').annotate(
            count=models.Count('id')
        )
        
        # Recent visits (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_visits = MonitoringVisit.objects.filter(
            date_of_visit__gte=thirty_days_ago
        ).count()
        
        # Visits by month (last 6 months)
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        visits_by_month = MonitoringVisit.objects.filter(
            date_of_visit__gte=six_months_ago
        ).extra(
            select={'month': "DATE_FORMAT(date_of_visit, '%%Y-%%m')"}
        ).values('month').annotate(
            count=models.Count('id')
        ).order_by('month')
        
        stats = {
            'total_visits': total_visits,
            'recent_visits': recent_visits,
            'visits_by_status': list(visits_by_status),
            'visits_by_month': list(visits_by_month)
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading statistics: {str(e)}'
        }, status=500)

# def monitoring_dashboard(request):
#     """Render the main monitoring dashboard"""
#     return render(request, 'portal/monitoring/monitoring_dashboard.html')