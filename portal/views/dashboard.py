# monitoring/views.py
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg, Q
from portal.models import Farmer, Harvest, Project, Loan, Farm, Region, ComplianceCheck, AuditLog, Staff, Tree, societyTble, UserProfile

def monitoring_dashboard(request):
    # Basic statistics
    total_farmers = Farmer.objects.count()
    active_projects = Project.objects.filter(status='active').count()
    
    # Loan statistics
    total_loan_disbursed = Loan.objects.filter(status__in=['disbursed', 'repaying', 'completed']).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Farm statistics
    total_hectares = Farm.objects.aggregate(total=Sum('area_hectares'))['total'] or 0
    
    # Tree survival rate - using actual Tree and TreeMonitoring models
    total_trees = Tree.objects.count()
    healthy_trees = Tree.objects.filter(status='healthy').count()
    tree_survival_rate = (healthy_trees / total_trees * 100) if total_trees > 0 else 0
    
    # Projects with progress calculation
    projects = Project.objects.all().annotate(
        farmer_count=Count('participating_farmers'),
        budget_utilized=Sum('loans__amount')
    )
    
    for project in projects:
        # Simplified progress calculation based on time elapsed
        total_days = (project.end_date - project.start_date).days
        elapsed_days = (timezone.now().date() - project.start_date).days
        project.progress = min(100, max(0, (elapsed_days / total_days * 100))) if total_days > 0 else 0
    
    # Compliance checks
    compliance_checks = ComplianceCheck.objects.filter(status='pending').order_by('due_date')
    
    # Recent activities
    recent_activities = AuditLog.objects.all().order_by('-timestamp')[:10]
    
    # Chart data
    regional_data = get_regional_data()
    loan_data = get_loan_performance_data()
    yield_data = get_yield_analysis_data()
    
    context = {
        'total_farmers': total_farmers,
        'active_projects': active_projects,
        'total_loan_disbursed': total_loan_disbursed,
        'total_hectares': total_hectares,
        'tree_survival_rate': tree_survival_rate,
        'projects': projects,
        'compliance_checks': compliance_checks,
        'recent_activities': recent_activities,
        'regional_data': regional_data,
        'loan_data': loan_data,
        'yield_data': yield_data,
        'regions': Region.objects.all(),
        'staff_members': Staff.objects.filter(is_active=True),
        'farms': Farm.objects.all()[:50],  # Limit for performance
    }

    print(context['yield_data'])
    
    return render(request, 'portal/dashboard/dashboard.html', context)

def get_regional_data():
    # Alternative approach if the direct relationship doesn't work
    regions = Region.objects.all()
    regional_data = []
    
    for region in regions:
        # Get farmers through districts and societies
        farmers = Farmer.objects.filter(
            user_profile__district__region=region
        )
        
        regional_data.append({
            'region': region.name,
            'farmers': farmers.count(),
            'farms': Farm.objects.filter(farmer__in=farmers).count(),
            'hectares': Farm.objects.filter(farmer__in=farmers).aggregate(
                total=Sum('area_hectares')
            )['total'] or 0
        })
    
    return regional_data

def get_loan_performance_data():
    # Last 6 months loan performance with actual data
    six_months_ago = timezone.now() - timedelta(days=180)
    
    # Get actual loan data for the last 6 months
    loans = Loan.objects.filter(application_date__gte=six_months_ago)
    
    # Group by month
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = timezone.now() - timedelta(days=30*(i+1))
        month_end = timezone.now() - timedelta(days=30*i)
        
        month_loans = loans.filter(application_date__range=[month_start, month_end])
        
        disbursed = month_loans.filter(status__in=['disbursed', 'repaying', 'completed']).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        repaid = sum(
            repayment.amount for loan in month_loans.filter(status__in=['repaying', 'completed'])
            for repayment in loan.repayments.all()
        )
        
        defaulted = month_loans.filter(status='defaulted').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'disbursed': float(disbursed),
            'repaid': float(repaid),
            'defaulted': float(defaulted)
        })
    
    return monthly_data

def get_yield_analysis_data():
    # Actual yield analysis by variety from Harvest data
    from portal.models import Harvest, MangoVariety
    
    varieties = MangoVariety.objects.all()
    yield_data = []
    
    for variety in varieties:
        # Get harvests for this variety
        harvests = Harvest.objects.filter(variety=variety)
        total_quantity = harvests.aggregate(total=Sum('quantity'))['total'] or 0
        total_farms = harvests.values('farm').distinct().count()
        
        # Calculate average yield per hectare
        avg_yield = 0
        if total_farms > 0:
            # Get farm areas for these harvests
            farm_areas = Farm.objects.filter(
                id__in=harvests.values_list('farm_id', flat=True)
            ).aggregate(total_area=Sum('area_hectares'))['total_area'] or 0
            
            if farm_areas > 0:
                avg_yield = (total_quantity / 1000) / farm_areas  # Convert kg to tons
        
        yield_data.append({
            'variety': variety.name,
            'yield': round(avg_yield, 2) if avg_yield > 0 else 0
        })

        print(variety.name, yield_data)
    
    return yield_data

def performance_analysis_api(request):
    # API endpoint for the detailed performance chart with actual data
    time_range = int(request.GET.get('time_range', 180))
    regions = request.GET.getlist('regions')
    projects = request.GET.getlist('projects')
    
    # Calculate date range
    start_date = timezone.now() - timedelta(days=time_range)
    
    # Generate actual data based on time range
    months = []
    farmers_data = []
    loans_data = []
    hectares_data = []
    yield_data = []
    
    # Generate monthly data points
    for i in range(6, 0, -1):
        month_start = timezone.now() - timedelta(days=30*i)
        month_end = timezone.now() - timedelta(days=30*(i-1))
        months.append(month_start.strftime('%b %Y'))
        
        # Farmers registered in this month
        farmers_count = UserProfile.objects.filter(
            role='farmer',
            created_at__range=[month_start, month_end]
        ).count()
        farmers_data.append(farmers_count)
        
        # Loans disbursed in this month
        loans_amount = Loan.objects.filter(
            disbursement_date__range=[month_start, month_end],
            status__in=['disbursed', 'repaying', 'completed']
        ).aggregate(total=Sum('amount'))['total'] or 0
        loans_data.append(float(loans_amount))
        
        # Hectares cultivated (new farms registered)
        new_hectares = Farm.objects.filter(
            registration_date__range=[month_start, month_end]
        ).aggregate(total=Sum('area_hectares'))['total'] or 0
        hectares_data.append(float(new_hectares))
        
        # Average yield for this month
        monthly_yield = Harvest.objects.filter(
            harvest_date__range=[month_start, month_end]
        ).aggregate(avg_yield=Avg('quantity'))['avg_yield'] or 0
        # Convert kg to tons per hectare (simplified)
        yield_value = (monthly_yield / 1000) if monthly_yield else 0
        yield_data.append(round(yield_value, 2))
    
    data = {
        'months': months,
        'series': [
            {
                'name': 'Farmers Registered',
                'type': 'farmers',
                'data': farmers_data,
                'color': '#4e73df'
            },
            {
                'name': 'Loans Disbursed (GHS)',
                'type': 'loans',
                'data': loans_data,
                'color': '#1cc88a'
            },
            {
                'name': 'Hectares Cultivated',
                'type': 'hectares',
                'data': hectares_data,
                'color': '#36b9cc'
            },
            {
                'name': 'Yield (tons/ha)',
                'type': 'yield',
                'data': yield_data,
                'color': '#f6c23e'
            }
        ]
    }
    
    return JsonResponse(data)

# Additional utility functions for monitoring
def get_project_progress_stats():
    """Get detailed project progress statistics"""
    projects = Project.objects.annotate(
        total_milestones=Count('milestones'),
        completed_milestones=Count('milestones', filter=Q(milestones__status='completed')),
        pending_milestones=Count('milestones', filter=Q(milestones__status='pending')),
        delayed_milestones=Count('milestones', filter=Q(milestones__status='delayed'))
    )
    
    return projects

def get_compliance_stats():
    """Get compliance statistics"""
    total_checks = ComplianceCheck.objects.count()
    passed_checks = ComplianceCheck.objects.filter(status='passed').count()
    failed_checks = ComplianceCheck.objects.filter(status='failed').count()
    pending_checks = ComplianceCheck.objects.filter(status='pending').count()
    
    return {
        'total': total_checks,
        'passed': passed_checks,
        'failed': failed_checks,
        'pending': pending_checks,
        'compliance_rate': (passed_checks / total_checks * 100) if total_checks > 0 else 0
    }

def get_farm_health_stats():
    """Get farm health statistics"""
    total_farms = Farm.objects.count()
    active_farms = Farm.objects.filter(status='active').count()
    critical_farms = Farm.objects.filter(status='critical').count()
    delayed_farms = Farm.objects.filter(status='delayed').count()
    
    # Tree health statistics
    total_trees = Tree.objects.count()
    healthy_trees = Tree.objects.filter(status='healthy').count()
    stressed_trees = Tree.objects.filter(status='stressed').count()
    diseased_trees = Tree.objects.filter(status='diseased').count()
    dead_trees = Tree.objects.filter(status='dead').count()
    
    return {
        'farms_total': total_farms,
        'farms_active': active_farms,
        'farms_critical': critical_farms,
        'farms_delayed': delayed_farms,
        'trees_total': total_trees,
        'trees_healthy': healthy_trees,
        'trees_stressed': stressed_trees,
        'trees_diseased': diseased_trees,
        'trees_dead': dead_trees,
        'tree_health_rate': (healthy_trees / total_trees * 100) if total_trees > 0 else 0
    }