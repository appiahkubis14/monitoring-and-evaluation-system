# loans/views.py
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from portal.models import Loan, LoanDisbursement, LoanRepayment, Farmer, Project, Staff

@login_required
def loan_management(request):
    """Main loan management page with tabs"""
    return render(request, 'portal/loans/loan-application.html')

@require_http_methods(["GET"])
@login_required
def loan_list(request):
    """Server-side processing for loans datatable"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    status_filter = request.GET.get('status')
    
    # Base queryset with related data
    queryset = Loan.objects.select_related(
        'farmer__user_profile__user', 
        'project',
        'farmer__user_profile__district__region_foreignkey'
    ).all()
    
    # Apply filters
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Apply search filter
    if search_value:
        queryset = queryset.filter(
            Q(loan_id__icontains=search_value) |
            Q(farmer__user_profile__user__first_name__icontains=search_value) |
            Q(farmer__user_profile__user__last_name__icontains=search_value) |
            Q(farmer__national_id__icontains=search_value) |
            Q(purpose__icontains=search_value) |
            Q(project__name__icontains=search_value) |
            Q(project__code__icontains=search_value)
        )
    
    # Total records count
    total_records = Loan.objects.count()
    total_filtered = queryset.count()
    
    # Apply ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    
    # Map column index to model field
    column_mapping = {
        0: 'loan_id',
        1: 'farmer__user_profile__user__first_name',
        2: 'farmer__national_id',
        3: 'project__name',
        4: 'amount',
        5: 'application_date',
        6: 'status',
        7: 'term_months'
    }
    
    order_column = column_mapping.get(order_column_index, 'application_date')
    if order_direction == 'desc':
        order_column = f'-{order_column}'
    
    queryset = queryset.order_by(order_column)
    
    # Apply pagination
    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)
    
    # Prepare data for response
    data = []
    for loan in page_obj:
        # Calculate disbursed amount
        disbursed_amount = loan.disbursements.aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate repaid amount
        repaid_amount = loan.repayments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate outstanding amount
        outstanding_amount = disbursed_amount - repaid_amount

        data.append({
            'id': loan.id,
            'loan_id': loan.loan_id,
            'farmer_name': f"{loan.farmer.user_profile.user.first_name} {loan.farmer.user_profile.user.last_name}",
            'farmer_national_id': loan.farmer.national_id,
            'project_name': loan.project.name if loan.project else 'N/A',
            'project_code': loan.project.code if loan.project else 'N/A',
            'amount': float(loan.amount),
            'purpose': loan.purpose,
            'application_date': loan.application_date.strftime('%Y-%m-%d'),
            'approval_date': loan.approval_date.strftime('%Y-%m-%d') if loan.approval_date else 'N/A',
            'interest_rate': loan.interest_rate,
            'term_months': loan.term_months,
            'status': loan.status,
            'status_display': loan.get_status_display(),
            'disbursed_amount': float(disbursed_amount),
            'repaid_amount': float(repaid_amount),
            'outstanding_amount': float(outstanding_amount),
            'collateral_details': loan.collateral_details or 'No collateral'
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
def get_loan_detail(request, loan_id):
    """Get detailed information about a specific loan"""
    try:
        loan = Loan.objects.select_related(
            'farmer__user_profile__user',
            'farmer__user_profile__district__region',
            'project'
        ).prefetch_related('disbursements', 'repayments').get(id=loan_id)
        
        # Get disbursements
        disbursements_data = []
        for disbursement in loan.disbursements.all():
            disbursements_data.append({
                'id': disbursement.id,
                'amount': float(disbursement.amount),
                'disbursement_date': disbursement.disbursement_date.strftime('%Y-%m-%d'),
                'stage': disbursement.stage,
                'transaction_reference': disbursement.transaction_reference or 'N/A',
                'disbursed_by': f"{disbursement.disbursed_by.user_profile.user.first_name} {disbursement.disbursed_by.user_profile.user.last_name}" if disbursement.disbursed_by else 'N/A',
                'notes': disbursement.notes or 'No notes',
                'created_at': disbursement.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Get repayments
        repayments_data = []
        for repayment in loan.repayments.all():
            repayments_data.append({
                'id': repayment.id,
                'amount': float(repayment.amount),
                'repayment_date': repayment.repayment_date.strftime('%Y-%m-%d'),
                'transaction_reference': repayment.transaction_reference or 'N/A',
                'received_by': f"{repayment.received_by.user_profile.user.first_name} {repayment.received_by.user_profile.user.last_name}" if repayment.received_by else 'N/A',
                'notes': repayment.notes or 'No notes',
                'created_at': repayment.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Calculate totals
        total_disbursed = loan.disbursements.aggregate(total=Sum('amount'))['total'] or 0
        total_repaid = loan.repayments.aggregate(total=Sum('amount'))['total'] or 0
        outstanding_amount = loan.amount - total_disbursed
        
        data = {
            'success': True,
            'loan': {
                'id': loan.id,
                'loan_id': loan.loan_id,
                'farmer_name': f"{loan.farmer.user_profile.user.first_name} {loan.farmer.user_profile.user.last_name}",
                'farmer_national_id': loan.farmer.national_id,
                'farmer_id': loan.farmer.id,
                'project_name': loan.project.name if loan.project else 'N/A',
                'project_code': loan.project.code if loan.project else 'N/A',
                'project_id': loan.project.id if loan.project else None,
                'amount': float(loan.amount),
                'purpose': loan.purpose,
                'application_date': loan.application_date.strftime('%Y-%m-%d'),
                'approval_date': loan.approval_date.strftime('%Y-%m-%d') if loan.approval_date else 'N/A',
                'interest_rate': loan.interest_rate,
                'term_months': loan.term_months,
                'status': loan.status,
                'status_display': loan.get_status_display(),
                'collateral_details': loan.collateral_details or 'No collateral',
                'created_at': loan.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': loan.updated_at.strftime('%Y-%m-%d %H:%M')
            },
            'financials': {
                'total_disbursed': float(total_disbursed),
                'total_repaid': float(total_repaid),
                'outstanding_amount': float(outstanding_amount),
                'repayment_rate': (float(total_repaid) / float(total_disbursed) * 100) if total_disbursed > 0 else 0
            },
            'disbursements': disbursements_data,
            'repayments': repayments_data,
            'disbursements_count': len(disbursements_data),
            'repayments_count': len(repayments_data)
        }
        
        return JsonResponse(data)
        
    except Loan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Loan not found'}, status=404)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def create_loan(request):
    """Create a new loan application"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['farmer_id', 'amount', 'purpose', 'interest_rate', 'term_months']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)
        
        # Check if farmer exists
        try:
            farmer = Farmer.objects.get(id=data['farmer_id'])
        except Farmer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Farmer not found'}, status=404)
        
        # Check if project exists if provided
        project = None
        if data.get('project_id'):
            try:
                project = Project.objects.get(id=data['project_id'])
            except Project.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
        
        # Create loan
        loan = Loan.objects.create(
            farmer=farmer,
            project=project,
            amount=float(data['amount']),
            purpose=data['purpose'],
            interest_rate=float(data['interest_rate']),
            term_months=int(data['term_months']),
            collateral_details=data.get('collateral_details', ''),
            status='applied'
        )
        
        # If application date is provided, use it
        if data.get('application_date'):
            loan.application_date = data['application_date']
            loan.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Loan application created successfully',
            'loan_id': loan.id,
            'loan_number': loan.loan_id
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def update_loan(request, loan_id):
    """Update an existing loan application"""
    try:
        data = json.loads(request.body)
        loan = Loan.objects.get(id=loan_id)
        
        # Only allow updates for applied loans
        if loan.status != 'applied':
            return JsonResponse({'success': False, 'error': 'Only applied loans can be updated'}, status=400)
        
        # Update loan data
        if 'amount' in data:
            loan.amount = float(data['amount'])
        if 'purpose' in data:
            loan.purpose = data['purpose']
        if 'interest_rate' in data:
            loan.interest_rate = float(data['interest_rate'])
        if 'term_months' in data:
            loan.term_months = int(data['term_months'])
        if 'collateral_details' in data:
            loan.collateral_details = data['collateral_details']
        if 'application_date' in data:
            loan.application_date = data['application_date']
        
        # Update project if provided
        if 'project_id' in data:
            if data['project_id']:
                try:
                    project = Project.objects.get(id=data['project_id'])
                    loan.project = project
                except Project.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
            else:
                loan.project = None
        
        loan.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Loan application updated successfully'
        })
        
    except Loan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Loan not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



@require_http_methods(["POST"])
@login_required
@transaction.atomic
def delete_loan(request):
    """Delete a loan application (only allowed for applied status)"""
    try:
        data = json.loads(request.body)
        loan_id = data.get('id')
        
        if not loan_id:
            return JsonResponse({'success': False, 'error': 'Loan ID is required'}, status=400)
        
        loan = Loan.objects.get(id=loan_id)
        
        # Only allow deletion for applied loans
        if loan.status != 'applied':
            return JsonResponse({'success': False, 'error': 'Only applied loans can be deleted'}, status=400)
        
        loan.delete()
        
        return JsonResponse({'success': True, 'message': 'Loan application deleted successfully'})
        
    except Loan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Loan not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



@require_http_methods(["POST"])
@login_required
@transaction.atomic
def approve_loan(request, loan_id):
    """Approve a loan application"""
    try:
        loan = Loan.objects.get(id=loan_id)
        
        # Only allow approval for applied loans
        if loan.status != 'applied':
            return JsonResponse({'success': False, 'error': 'Only applied loans can be approved'}, status=400)
        
        # Update loan status
        loan.status = 'approved'
        loan.approval_date = timezone.now().date()
        loan.save()

        
        
        return JsonResponse({
            'success': True,
            'message': 'Loan application approved successfully'
        })
        
    except Loan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Loan not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

@require_http_methods(["POST"])
@login_required

def disburse_loan(request, loan_id):
    """Disburse a loan"""
    try:
        loan = get_object_or_404(Loan, id=loan_id)
        
        # Check if loan can be disbursed
        if loan.status != 'approved':
            return JsonResponse({
                'success': False,
                'error': f'Loan cannot be disbursed. Current status: {loan.get_status_display()}'
            })
        
        # Parse request body for disbursement details
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}
        
        # Create disbursement record
        disbursement = LoanDisbursement(
            loan=loan,
            amount=loan.amount,
            disbursement_date=timezone.now().date(),
            stage=data.get('stage', 'Initial Disbursement'),
            transaction_reference=data.get('transaction_reference', ''),
            disbursed_by=request.user.staff if hasattr(request.user, 'staff') else None,
            notes=data.get('notes', '')
        )
        disbursement.save()
        
        # Update loan status
        loan.status = 'disbursed'
        loan.modified_by = request.user
        loan.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Loan disbursed successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    


    
@require_http_methods(["POST"])
@login_required
@transaction.atomic
def reject_loan(request, loan_id):
    """Reject a loan application"""
    try:
        data = json.loads(request.body)
        loan = Loan.objects.get(id=loan_id)
        
        # Only allow rejection for applied loans
        if loan.status != 'applied':
            return JsonResponse({'success': False, 'error': 'Only applied loans can be rejected'}, status=400)
        
        # Update loan status
        loan.status = 'rejected'
        loan.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Loan application rejected successfully'
        })
        
    except Loan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Loan not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_available_farmers_for_loan(request):
    """Get farmers who can apply for loans (active farmers)"""
    try:
        # Get active farmers (those with active user accounts)
        available_farmers = Farmer.objects.filter(
            user_profile__user__is_active=True
        ).select_related('user_profile__user', 'user_profile__district')
        
        data = []
        for farmer in available_farmers:
            data.append({
                'id': farmer.id,
                'name': f"{farmer.user_profile.user.first_name} {farmer.user_profile.user.last_name}",
                'national_id': farmer.national_id,
                'district': farmer.user_profile.district.name if farmer.user_profile.district else 'N/A',
                'farm_size': farmer.farm_size,
                'years_of_experience': farmer.years_of_experience,
                'active_loans_count': farmer.loans.filter(status__in=['applied', 'approved', 'disbursed', 'repaying']).count(),
                'completed_loans_count': farmer.loans.filter(status='completed').count()
            })
        
        return JsonResponse({'success': True, 'farmers': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_active_projects(request):
    """Get active projects for loan association"""
    try:
        active_projects = Project.objects.filter(
            status='active',
            end_date__gte=timezone.now().date()
        )
        
        data = []
        for project in active_projects:
            data.append({
                'id': project.id,
                'name': project.name,
                'code': project.code,
                'start_date': project.start_date.strftime('%Y-%m-%d'),
                'end_date': project.end_date.strftime('%Y-%m-%d'),
                'total_budget': float(project.total_budget),
                'farmers_count': project.participating_farmers.count()
            })
        
        return JsonResponse({'success': True, 'projects': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_loan_stats(request):
    """Get statistics about loans"""
    try:
        # Total loans count
        total_loans = Loan.objects.count()
        
        # Loans by status
        loans_by_status = Loan.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Active loans (approved, disbursed, repaying)
        active_loans = Loan.objects.filter(status__in=['approved', 'disbursed', 'repaying']).count()
        
        # Defaulted loans
        defaulted_loans = Loan.objects.filter(status='defaulted').count()
        
        # Total loan amount
        total_loan_amount = Loan.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # Total disbursed amount
        total_disbursed = LoanDisbursement.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # Total repaid amount
        total_repaid = LoanRepayment.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # Average loan amount
        avg_loan_amount = Loan.objects.aggregate(avg=Avg('amount'))['avg'] or 0
        
        # Recent loans (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_loans = Loan.objects.filter(created_at__gte=thirty_days_ago).count()
        
        data = {
            'success': True,
            'stats': {
                'total_loans': total_loans,
                'loans_by_status': list(loans_by_status),
                'active_loans': active_loans,
                'defaulted_loans': defaulted_loans,
                'total_loan_amount': float(total_loan_amount),
                'total_disbursed': float(total_disbursed),
                'total_repaid': float(total_repaid),
                'outstanding_amount': float(total_loan_amount - total_disbursed),
                'avg_loan_amount': float(avg_loan_amount),
                'recent_loans': recent_loans,
                'repayment_rate': (float(total_repaid) / float(total_disbursed) * 100) if total_disbursed > 0 else 0
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def loan_export(request):
    """Export loans data in various formats"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    format_type = request.GET.get('format', 'csv')
    status_filter = request.GET.get('status', '')
    
    # Base queryset
    loans = Loan.objects.select_related(
        'farmer__user_profile__user', 
        'project'
    ).prefetch_related('disbursements', 'repayments')
    
    # Apply status filter if provided
    if status_filter:
        loans = loans.filter(status=status_filter)
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="loans_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Loan ID', 'Farmer Name', 'National ID', 'Project', 'Amount', 
            'Purpose', 'Application Date', 'Approval Date', 'Interest Rate',
            'Term (Months)', 'Status', 'Disbursed Amount', 'Repaid Amount',
            'Outstanding Amount', 'Collateral Details'
        ])
        
        for loan in loans:
            disbursed_amount = loan.disbursements.aggregate(total=Sum('amount'))['total'] or 0
            repaid_amount = loan.repayments.aggregate(total=Sum('amount'))['total'] or 0
            
            writer.writerow([
                loan.loan_id,
                f"{loan.farmer.user_profile.user.first_name} {loan.farmer.user_profile.user.last_name}",
                loan.farmer.national_id,
                loan.project.name if loan.project else 'N/A',
                float(loan.amount),
                loan.purpose,
                loan.application_date.strftime('%Y-%m-%d'),
                loan.approval_date.strftime('%Y-%m-%d') if loan.approval_date else 'N/A',
                loan.interest_rate,
                loan.term_months,
                loan.get_status_display(),
                float(disbursed_amount),
                float(repaid_amount),
                float(loan.amount - disbursed_amount),
                loan.collateral_details or 'No collateral'
            ])
        
        return response
    
    elif format_type == 'json':
        data = []
        for loan in loans:
            disbursed_amount = loan.disbursements.aggregate(total=Sum('amount'))['total'] or 0
            repaid_amount = loan.repayments.aggregate(total=Sum('amount'))['total'] or 0
            
            data.append({
                'loan_id': loan.loan_id,
                'farmer_name': f"{loan.farmer.user_profile.user.first_name} {loan.farmer.user_profile.user.last_name}",
                'national_id': loan.farmer.national_id,
                'project': loan.project.name if loan.project else 'N/A',
                'amount': float(loan.amount),
                'purpose': loan.purpose,
                'application_date': loan.application_date.strftime('%Y-%m-%d'),
                'approval_date': loan.approval_date.strftime('%Y-%m-%d') if loan.approval_date else 'N/A',
                'interest_rate': loan.interest_rate,
                'term_months': loan.term_months,
                'status': loan.status,
                'status_display': loan.get_status_display(),
                'disbursed_amount': float(disbursed_amount),
                'repaid_amount': float(repaid_amount),
                'outstanding_amount': float(loan.amount - disbursed_amount),
                'collateral_details': loan.collateral_details or 'No collateral'
            })
        
        return JsonResponse({'loans': data})
    
    else:
        return JsonResponse({'success': False, 'error': 'Unsupported format'}, status=500)
    




################################################################################################################################

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json

from portal.models import LoanDisbursement, Loan, Farmer, Project, Staff

@require_http_methods(["GET"])
@login_required
def disbursement_list_page(request):
    """Loan disbursements page view"""
    return render(request, 'portal/loans/disbursement.html')

@require_http_methods(["GET"])
@login_required
def disbursement_list(request):
    """Get paginated loan disbursements for DataTables"""
    try:
        # Get request parameters for DataTables
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        loan_id_filter = request.GET.get('loan_id', '')
        
        # Base queryset
        disbursements = LoanDisbursement.objects.select_related(
            'loan', 
            'loan__farmer', 
            'loan__farmer__user_profile',
            'loan__project',
            'disbursed_by',
            'disbursed_by__user_profile'
        ).order_by('-disbursement_date')
        
        # Apply filters
        if loan_id_filter:
            disbursements = disbursements.filter(loan_id=loan_id_filter)
        
        if search_value:
            disbursements = disbursements.filter(
                Q(loan__loan_id__icontains=search_value) |
                Q(transaction_reference__icontains=search_value) |
                Q(loan__farmer__user_profile__user__first_name__icontains=search_value) |
                Q(loan__farmer__user_profile__user__last_name__icontains=search_value) |
                Q(loan__farmer__national_id__icontains=search_value) |
                Q(stage__icontains=search_value) |
                Q(disbursed_by__user_profile__user__first_name__icontains=search_value) |
                Q(disbursed_by__user_profile__user__last_name__icontains=search_value)
            )
        
        # Get total count
        total_records = disbursements.count()
        
        # Apply pagination
        disbursements = disbursements[start:start + length]
        
        # Prepare data for response
        data = []
        for disbursement in disbursements:
            farmer = disbursement.loan.farmer
            farmer_name = f"{farmer.user_profile.user.first_name} {farmer.user_profile.user.last_name}"
            disbursed_by_name = f"{disbursement.disbursed_by.user_profile.user.first_name} {disbursement.disbursed_by.user_profile.user.last_name}" if disbursement.disbursed_by else "Not specified"
            
            data.append({
                'id': disbursement.id,
                'loan_id': disbursement.loan.loan_id,
                'farmer_name': farmer_name,
                'farmer_national_id': farmer.national_id,
                'amount': float(disbursement.amount),
                'disbursement_date': disbursement.disbursement_date.strftime('%Y-%m-%d'),
                'stage': disbursement.stage,
                'transaction_reference': disbursement.transaction_reference or 'Not provided',
                'disbursed_by': disbursed_by_name,
                'project_name': disbursement.loan.project.name if disbursement.loan.project else 'N/A',
                'project_code': disbursement.loan.project.code if disbursement.loan.project else 'N/A',
                'created_at': disbursement.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': disbursement.updated_at.strftime('%Y-%m-%d %H:%M'),
                'notes': disbursement.notes or 'No notes provided'
            })
        
        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required
def disbursement_detail(request, disbursement_id):
    """Get disbursement details for modal"""
    try:
        disbursement = get_object_or_404(LoanDisbursement.objects.select_related(
            'loan', 
            'loan__farmer', 
            'loan__farmer__user_profile',
            'loan__project',
            'disbursed_by',
            'disbursed_by__user_profile'
        ), id=disbursement_id)
        
        farmer = disbursement.loan.farmer
        farmer_name = f"{farmer.user_profile.user.first_name} {farmer.user_profile.user.last_name}"
        disbursed_by_name = f"{disbursement.disbursed_by.user_profile.user.first_name} {disbursement.disbursed_by.user_profile.user.last_name}" if disbursement.disbursed_by else "Not specified"
        
        return JsonResponse({
            'success': True,
            'disbursement': {
                'id': disbursement.id,
                'loan_id': disbursement.loan.loan_id,
                'farmer_name': farmer_name,
                'farmer_national_id': farmer.national_id,
                'amount': float(disbursement.amount),
                'disbursement_date': disbursement.disbursement_date.strftime('%Y-%m-%d'),
                'stage': disbursement.stage,
                'transaction_reference': disbursement.transaction_reference or 'Not provided',
                'disbursed_by': disbursed_by_name,
                'project_name': disbursement.loan.project.name if disbursement.loan.project else 'N/A',
                'project_code': disbursement.loan.project.code if disbursement.loan.project else 'N/A',
                'created_at': disbursement.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': disbursement.updated_at.strftime('%Y-%m-%d %H:%M'),
                'notes': disbursement.notes or 'No notes provided'
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_loans_with_disbursements(request):
    """Get loans that have disbursements for filter dropdown"""
    try:
        # Get loans that have at least one disbursement
        loans = Loan.objects.filter(
            disbursements__isnull=False
        ).select_related(
            'farmer', 
            'farmer__user_profile'
        ).distinct()
        
        loan_data = []
        for loan in loans:
            farmer_name = f"{loan.farmer.user_profile.user.first_name} {loan.farmer.user_profile.user.last_name}"
            loan_data.append({
                'id': loan.id,
                'loan_id': loan.loan_id,
                'farmer_name': farmer_name
            })
        
        return JsonResponse({
            'success': True,
            'loans': loan_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    


#####################################################################################################################################

# loans/views.py (continued)
@login_required
def repayment_tracking(request):
    """Main repayment tracking page"""
    return render(request, 'portal/loans/repayment.html')

@require_http_methods(["GET"])
@login_required
def repayment_list(request):
    """Server-side processing for repayments datatable"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base queryset with related data
    queryset = LoanRepayment.objects.select_related(
        'loan__farmer__user_profile__user',
        'loan__project',
        'received_by__user_profile__user'
    ).all()
    
    # Apply filters
    if status_filter:
        queryset = queryset.filter(loan__status=status_filter)
    
    # Apply date filters
    if date_from:
        queryset = queryset.filter(repayment_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(repayment_date__lte=date_to)
    
    # Apply search filter
    if search_value:
        queryset = queryset.filter(
            Q(loan__loan_id__icontains=search_value) |
            Q(loan__farmer__user_profile__user__first_name__icontains=search_value) |
            Q(loan__farmer__user_profile__user__last_name__icontains=search_value) |
            Q(loan__farmer__national_id__icontains=search_value) |
            Q(transaction_reference__icontains=search_value) |
            Q(received_by__user_profile__user__first_name__icontains=search_value) |
            Q(received_by__user_profile__user__last_name__icontains=search_value)
        )
    
    # Total records count
    total_records = LoanRepayment.objects.count()
    total_filtered = queryset.count()
    
    # Apply ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    
    # Map column index to model field
    column_mapping = {
        0: 'repayment_date',
        1: 'loan__loan_id',
        2: 'loan__farmer__user_profile__user__first_name',
        3: 'amount',
        4: 'transaction_reference',
        5: 'received_by__user_profile__user__first_name'
    }
    
    order_column = column_mapping.get(order_column_index, 'repayment_date')
    if order_direction == 'desc':
        order_column = f'-{order_column}'
    
    queryset = queryset.order_by(order_column)
    
    # Apply pagination
    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)
    
    # Prepare data for response
    data = []
    for repayment in page_obj:
        data.append({
            'id': repayment.id,
            'repayment_date': repayment.repayment_date.strftime('%Y-%m-%d'),
            'loan_id': repayment.loan.loan_id,
            'farmer_name': f"{repayment.loan.farmer.user_profile.user.first_name} {repayment.loan.farmer.user_profile.user.last_name}",
            'farmer_national_id': repayment.loan.farmer.national_id,
            'project_name': repayment.loan.project.name if repayment.loan.project else 'N/A',
            'amount': float(repayment.amount),
            'transaction_reference': repayment.transaction_reference or 'N/A',
            'received_by': f"{repayment.received_by.user_profile.user.first_name} {repayment.received_by.user_profile.user.last_name}" if repayment.received_by else 'N/A',
            'notes': repayment.notes or 'No notes',
            'created_at': repayment.created_at.strftime('%Y-%m-%d %H:%M')
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
def get_repayment_detail(request, repayment_id):
    """Get detailed information about a specific repayment"""
    try:
        repayment = LoanRepayment.objects.select_related(
            'loan__farmer__user_profile__user',
            'loan__farmer__user_profile__district__region',
            'loan__project',
            'received_by__user_profile__user'
        ).get(id=repayment_id)
        
        # Get loan details
        loan = repayment.loan
        total_disbursed = loan.disbursements.aggregate(total=Sum('amount'))['total'] or 0
        total_repaid = loan.repayments.aggregate(total=Sum('amount'))['total'] or 0
        outstanding_amount = loan.amount - total_disbursed
        
        data = {
            'success': True,
            'repayment': {
                'id': repayment.id,
                'amount': float(repayment.amount),
                'repayment_date': repayment.repayment_date.strftime('%Y-%m-%d'),
                'transaction_reference': repayment.transaction_reference or 'N/A',
                'received_by': f"{repayment.received_by.user_profile.user.first_name} {repayment.received_by.user_profile.user.last_name}" if repayment.received_by else 'N/A',
                'received_by_id': repayment.received_by.id if repayment.received_by else None,
                'notes': repayment.notes or 'No notes',
                'created_at': repayment.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': repayment.updated_at.strftime('%Y-%m-%d %H:%M')
            },
            'loan': {
                'id': loan.id,
                'loan_id': loan.loan_id,
                'farmer_name': f"{loan.farmer.user_profile.user.first_name} {loan.farmer.user_profile.user.last_name}",
                'farmer_national_id': loan.farmer.national_id,
                'farmer_id': loan.farmer.id,
                'project_name': loan.project.name if loan.project else 'N/A',
                'project_code': loan.project.code if loan.project else 'N/A',
                'amount': float(loan.amount),
                'purpose': loan.purpose,
                'interest_rate': loan.interest_rate,
                'term_months': loan.term_months,
                'status': loan.status,
                'status_display': loan.get_status_display(),
                'application_date': loan.application_date.strftime('%Y-%m-%d'),
                'approval_date': loan.approval_date.strftime('%Y-%m-%d') if loan.approval_date else 'N/A'
            },
            'financials': {
                'total_disbursed': float(total_disbursed),
                'total_repaid': float(total_repaid),
                'outstanding_amount': float(outstanding_amount),
                'repayment_percentage': (float(total_repaid) / float(total_disbursed) * 100) if total_disbursed > 0 else 0
            }
        }
        
        return JsonResponse(data)
        
    except LoanRepayment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Repayment not found'}, status=404)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def create_repayment(request):
    """Create a new loan repayment"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['loan_id', 'amount', 'repayment_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)
        
        # Check if loan exists
        try:
            loan = Loan.objects.get(id=data['loan_id'])
        except Loan.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Loan not found'}, status=404)
        
        # Check if loan is in a state that allows repayments
        if loan.status not in ['disbursed', 'repaying']:
            return JsonResponse({'success': False, 'error': 'Repayments can only be made for disbursed or repaying loans'}, status=400)
        
        # Check if staff exists if provided
        received_by = None
        if data.get('received_by_id'):
            try:
                received_by = Staff.objects.get(id=data['received_by_id'])
            except Staff.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Staff member not found'}, status=404)
        
        # Create repayment
        repayment = LoanRepayment.objects.create(
            loan=loan,
            amount=float(data['amount']),
            repayment_date=data['repayment_date'],
            transaction_reference=data.get('transaction_reference', ''),
            received_by=received_by,
            notes=data.get('notes', '')
        )
        
        # Update loan status if this is the first repayment
        if loan.status == 'disbursed':
            loan.status = 'repaying'
            loan.save()
        
        # Check if loan is fully repaid
        total_disbursed = loan.disbursements.aggregate(total=Sum('amount'))['total'] or 0
        total_repaid = loan.repayments.aggregate(total=Sum('amount'))['total'] or 0
        
        if total_repaid >= total_disbursed:
            loan.status = 'completed'
            loan.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Repayment recorded successfully',
            'repayment_id': repayment.id
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def update_repayment(request, repayment_id):
    """Update an existing repayment"""
    try:
        data = json.loads(request.body)
        repayment = LoanRepayment.objects.get(id=repayment_id)
        
        # Update repayment data
        if 'amount' in data:
            repayment.amount = float(data['amount'])
        if 'repayment_date' in data:
            repayment.repayment_date = data['repayment_date']
        if 'transaction_reference' in data:
            repayment.transaction_reference = data['transaction_reference']
        if 'notes' in data:
            repayment.notes = data['notes']
        
        # Update received_by if provided
        if 'received_by_id' in data:
            if data['received_by_id']:
                try:
                    received_by = Staff.objects.get(id=data['received_by_id'])
                    repayment.received_by = received_by
                except Staff.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Staff member not found'}, status=404)
            else:
                repayment.received_by = None
        
        repayment.save()
        
        # Recalculate loan status
        loan = repayment.loan
        total_disbursed = loan.disbursements.aggregate(total=Sum('amount'))['total'] or 0
        total_repaid = loan.repayments.aggregate(total=Sum('amount'))['total'] or 0
        
        if total_repaid >= total_disbursed:
            loan.status = 'completed'
        elif total_repaid > 0:
            loan.status = 'repaying'
        else:
            loan.status = 'disbursed'
        
        loan.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Repayment updated successfully'
        })
        
    except LoanRepayment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Repayment not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def delete_repayment(request):
    """Delete a repayment"""
    try:
        data = json.loads(request.body)
        repayment_id = data.get('id')
        
        if not repayment_id:
            return JsonResponse({'success': False, 'error': 'Repayment ID is required'}, status=400)
        
        repayment = LoanRepayment.objects.get(id=repayment_id)
        loan = repayment.loan
        
        # Store repayment amount before deletion
        repayment_amount = repayment.amount
        
        # Delete the repayment
        repayment.delete()
        
        # Recalculate loan status
        total_disbursed = loan.disbursements.aggregate(total=Sum('amount'))['total'] or 0
        total_repaid = loan.repayments.aggregate(total=Sum('amount'))['total'] or 0
        
        if total_repaid >= total_disbursed:
            loan.status = 'completed'
        elif total_repaid > 0:
            loan.status = 'repaying'
        else:
            loan.status = 'disbursed'
        
        loan.save()
        
        return JsonResponse({'success': True, 'message': 'Repayment deleted successfully'})
        
    except LoanRepayment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Repayment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_repayable_loans(request):
    """Get loans that are eligible for repayment (disbursed or repaying)"""
    try:
        repayable_loans = Loan.objects.filter(
            status__in=['disbursed', 'repaying']
        ).select_related(
            'farmer__user_profile__user',
            'project'
        ).prefetch_related('disbursements', 'repayments')
        
        data = []
        for loan in repayable_loans:
            total_disbursed = loan.disbursements.aggregate(total=Sum('amount'))['total'] or 0
            total_repaid = loan.repayments.aggregate(total=Sum('amount'))['total'] or 0
            outstanding_amount = total_disbursed - total_repaid
            
            data.append({
                'id': loan.id,
                'loan_id': loan.loan_id,
                'farmer_name': f"{loan.farmer.user_profile.user.first_name} {loan.farmer.user_profile.user.last_name}",
                'farmer_national_id': loan.farmer.national_id,
                'project_name': loan.project.name if loan.project else 'N/A',
                'loan_amount': float(loan.amount),
                'total_disbursed': float(total_disbursed),
                'total_repaid': float(total_repaid),
                'outstanding_amount': float(outstanding_amount),
                'repayment_percentage': (float(total_repaid) / float(total_disbursed) * 100) if total_disbursed > 0 else 0,
                'status': loan.status,
                'status_display': loan.get_status_display()
            })
        
        return JsonResponse({'success': True, 'loans': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_repayment_stats(request):
    """Get statistics about repayments"""
    try:
        # Total repayments count
        total_repayments = LoanRepayment.objects.count()
        
        # Total repayment amount
        total_repayment_amount = LoanRepayment.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # Repayments by month (last 6 months)
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        repayments_by_month = LoanRepayment.objects.filter(
            repayment_date__gte=six_months_ago
        ).extra(
            select={'month': "DATE_FORMAT(repayment_date, '%%Y-%%m')"}
        ).values('month').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('month')
        
        # Average repayment amount
        avg_repayment_amount = LoanRepayment.objects.aggregate(avg=Avg('amount'))['avg'] or 0
        
        # Recent repayments (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_repayments = LoanRepayment.objects.filter(created_at__gte=thirty_days_ago).count()
        recent_repayment_amount = LoanRepayment.objects.filter(
            created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Loans by repayment status
        loans_by_repayment_status = Loan.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        data = {
            'success': True,
            'stats': {
                'total_repayments': total_repayments,
                'total_repayment_amount': float(total_repayment_amount),
                'repayments_by_month': list(repayments_by_month),
                'avg_repayment_amount': float(avg_repayment_amount),
                'recent_repayments': recent_repayments,
                'recent_repayment_amount': float(recent_repayment_amount),
                'loans_by_repayment_status': list(loans_by_repayment_status)
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def repayment_export(request):
    """Export repayments data in various formats"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    format_type = request.GET.get('format', 'csv')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base queryset
    repayments = LoanRepayment.objects.select_related(
        'loan__farmer__user_profile__user',
        'loan__project',
        'received_by__user_profile__user'
    )
    
    # Apply date filters
    if date_from:
        repayments = repayments.filter(repayment_date__gte=date_from)
    if date_to:
        repayments = repayments.filter(repayment_date__lte=date_to)
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="repayments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Repayment Date', 'Loan ID', 'Farmer Name', 'National ID', 'Project', 
            'Amount', 'Transaction Reference', 'Received By', 'Notes', 'Created At'
        ])
        
        for repayment in repayments:
            writer.writerow([
                repayment.repayment_date.strftime('%Y-%m-%d'),
                repayment.loan.loan_id,
                f"{repayment.loan.farmer.user_profile.user.first_name} {repayment.loan.farmer.user_profile.user.last_name}",
                repayment.loan.farmer.national_id,
                repayment.loan.project.name if repayment.loan.project else 'N/A',
                float(repayment.amount),
                repayment.transaction_reference or 'N/A',
                f"{repayment.received_by.user_profile.user.first_name} {repayment.received_by.user_profile.user.last_name}" if repayment.received_by else 'N/A',
                repayment.notes or 'No notes',
                repayment.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    
    elif format_type == 'json':
        data = []
        for repayment in repayments:
            data.append({
                'repayment_date': repayment.repayment_date.strftime('%Y-%m-%d'),
                'loan_id': repayment.loan.loan_id,
                'farmer_name': f"{repayment.loan.farmer.user_profile.user.first_name} {repayment.loan.farmer.user_profile.user.last_name}",
                'national_id': repayment.loan.farmer.national_id,
                'project': repayment.loan.project.name if repayment.loan.project else 'N/A',
                'amount': float(repayment.amount),
                'transaction_reference': repayment.transaction_reference or 'N/A',
                'received_by': f"{repayment.received_by.user_profile.user.first_name} {repayment.received_by.user_profile.user.last_name}" if repayment.received_by else 'N/A',
                'notes': repayment.notes or 'No notes',
                'created_at': repayment.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return JsonResponse({'repayments': data})
    
    else:
        return JsonResponse({'success': False, 'error': 'Unsupported format'}, status=500)
    



@require_http_methods(["GET"])
@login_required
def get_staff_members(request):
    """Get all staff members for dropdowns"""
    staff_members = Staff.objects.select_related('user_profile__user').filter(is_active=True)
    
    data = []
    for staff in staff_members:
        data.append({
            'id': staff.id,
            'name': f"{staff.user_profile.user.first_name} {staff.user_profile.user.last_name}",
            'designation': staff.designation,
            'staff_id': staff.staff_id
        })
    
    return JsonResponse({'success': True, 'staff': data})