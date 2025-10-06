# monitoring/views.py
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg, Q, FloatField
from django.db.models.functions import Cast
from portal.models import Farmer, Project, Loan, Farm, Region, District, UserProfile, Staff, MonitoringVisit, LoanRepayment, LoanDisbursement
import json

# monitoring/views.py
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg, Q, FloatField
from django.db.models.functions import Cast
from portal.models import Farmer, Project, Loan, Farm, Region, District, UserProfile, Staff, MonitoringVisit, LoanRepayment, LoanDisbursement
import json

def monitoring_dashboard(request):
    # Basic statistics - using only available models
    total_farmers = Farmer.objects.count()
    active_projects = Project.objects.filter(status='active').count()
    
    # Loan statistics - using Loan and related models
    total_loan_disbursed = LoanDisbursement.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_loan_repaid = LoanRepayment.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Farm statistics
    total_hectares = Farm.objects.aggregate(total=Sum('area_hectares'))['total'] or 0
    average_farm_size = Farm.objects.aggregate(avg=Avg('area_hectares'))['avg'] or 0
    
    # Regional performance data - FIXED
    regional_data = get_regional_data()
    
    # Yield projections vs actual (using estimated_yield from Farmer model as projection)
    yield_data = get_yield_analysis_data()
    
    # Loan performance data
    loan_data = get_loan_performance_data()
    
    # Projects with progress calculation
    projects = Project.objects.all().annotate(
        farmer_count=Count('participating_farmers')
    )
    
    for project in projects:
        # Simplified progress calculation based on time elapsed
        total_days = (project.end_date - project.start_date).days
        elapsed_days = (timezone.now().date() - project.start_date).days
        project.progress = min(100, max(0, (elapsed_days / total_days * 100))) if total_days > 0 else 0
    
    # Recent monitoring visits as activities
    recent_activities = MonitoringVisit.objects.all().order_by('-date_of_visit')[:10]
    
    context = {
        'total_farmers': total_farmers,
        'active_projects': active_projects,
        'total_loan_disbursed': total_loan_disbursed,
        'total_loan_repaid': total_loan_repaid,
        'total_hectares': total_hectares,
        'average_farm_size': average_farm_size,
        'projects': projects,
        'recent_activities': recent_activities,
        'regional_data': json.dumps(regional_data),  # Serialize for JavaScript
        'loan_data': json.dumps(loan_data),  # Serialize for JavaScript
        'yield_data': json.dumps(yield_data),  # Serialize for JavaScript
        'regions': Region.objects.all(),
        'staff_members': Staff.objects.filter(is_active=True),
        'farms': Farm.objects.all()[:50],  # Limit for performance
    }
    
    return render(request, 'portal/dashboard/dashboard.html', context)

def get_regional_data():
    """Get regional performance comparison data - FIXED VERSION"""
    regions = Region.objects.all()
    regional_data = []
    
    for region in regions:
        # FIXED: Use the ForeignKey relationship instead of char field
        districts = District.objects.filter(region_foreignkey=region)
        
        # Get farmers through districts - FIXED: Use the district ForeignKey in Farmer
        farmers = Farmer.objects.filter(district__in=districts)
        
        # Get farms for these farmers
        farms = Farm.objects.filter(farmer__in=farmers)
        
        # Get loans for these farmers
        loans = Loan.objects.filter(farmer__in=farmers, status__in=['disbursed', 'repaying', 'completed'])
        
        regional_data.append({
            'region': region.region,
            'farmers': farmers.count(),
            'farms': farms.count(),
            'hectares': float(farms.aggregate(total=Sum('area_hectares'))['total'] or 0),
            'loans_disbursed': float(loans.aggregate(total=Sum('amount'))['total'] or 0)
        })
    
    print("Regional Data:", regional_data)
    return regional_data

def get_loan_performance_data():
    """Get loan disbursed vs repaid data for the last 6 months - FIXED VERSION"""
    six_months_ago = timezone.now() - timedelta(days=180)
    
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = timezone.now() - timedelta(days=30*(i+1))
        month_end = timezone.now() - timedelta(days=30*i)
        
        # Get disbursements for this month
        disbursements = LoanDisbursement.objects.filter(
            disbursement_date__range=[month_start, month_end]
        )
        disbursed_amount = disbursements.aggregate(total=Sum('amount'))['total'] or 0
        
        # Get repayments for this month
        repayments = LoanRepayment.objects.filter(
            repayment_date__range=[month_start, month_end]
        )
        repaid_amount = repayments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Get defaulted loans (simplified - loans that are overdue)
        # FIXED: Check if Loan model has 'defaulted' status, otherwise use different logic
        try:
            defaulted_loans = Loan.objects.filter(
                status='defaulted',
                application_date__range=[month_start, month_end]
            )
            defaulted_amount = defaulted_loans.aggregate(total=Sum('amount'))['total'] or 0
        except:
            # If no 'defaulted' status, calculate based on overdue loans
            defaulted_amount = 0
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'disbursed': float(disbursed_amount),
            'repaid': float(repaid_amount),
            'defaulted': float(defaulted_amount)
        })
    
    print("Loan Data:", monthly_data)
    return monthly_data

def get_yield_analysis_data():
    """Get yield projections vs actual data using Farmer model data - FIXED VERSION"""
    
    yield_data = []
    
    # Get all farmers with their estimated_yield
    farmers = Farmer.objects.filter(estimated_yield__isnull=False).exclude(estimated_yield='')
    
    # If no farmers with estimated yield, get all farmers and use default values
    if not farmers.exists():
        total_farmers = Farmer.objects.count()
        if total_farmers > 0:
            yield_data.append({
                'crop': 'Mango',
                'projected_yield': 10.5,  # tons/ha
                'actual_yield': 8.4,     # tons/ha (80% of projected)
                'farmers_count': total_farmers
            })
        return yield_data
    
    # Group by primary crop and calculate averages manually
    crop_data = {}
    
    for farmer in farmers:
        crop = farmer.primary_crop or 'Mango'  # Default to Mango if None
        if crop not in crop_data:
            crop_data[crop] = {'yields': [], 'count': 0}
        
        # Try to convert estimated_yield to float, skip if invalid
        try:
            # Handle string like "10.5 tons", "15 kg", etc.
            yield_str = str(farmer.estimated_yield).lower()
            # Extract numbers from the string
            import re
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", yield_str)
            if numbers:
                yield_value = float(numbers[0])
                # If it's in kg, convert to tons (divide by 1000)
                if 'kg' in yield_str:
                    yield_value = yield_value / 1000
                crop_data[crop]['yields'].append(yield_value)
                crop_data[crop]['count'] += 1
        except (ValueError, TypeError) as e:
            print(f"Error converting yield for farmer {farmer.id}: {e}")
            continue
    
    # Calculate averages and create yield data
    for crop, data in crop_data.items():
        if data['yields']:
            avg_yield = sum(data['yields']) / len(data['yields'])
            # Assume actual yield is 80% of estimated for demonstration
            actual_yield = avg_yield * 0.8
            
            yield_data.append({
                'crop': crop,
                'projected_yield': round(avg_yield, 2),
                'actual_yield': round(actual_yield, 2),
                'farmers_count': data['count']
            })
    
    # If no valid yield data, provide default data
    if not yield_data:
        total_farmers = Farmer.objects.count()
        yield_data.append({
            'crop': 'Mango',
            'projected_yield': 10.5,  # tons/ha
            'actual_yield': 8.4,     # tons/ha (80% of projected)
            'farmers_count': total_farmers
        })
    
    print("Yield Data:", yield_data)
    return yield_data

# Alternative regional data function if the above still doesn't work
def get_regional_data_alternative():
    """Alternative approach to get regional data"""
    regional_data = []
    
    # Get all regions
    regions = Region.objects.all()
    
    for region in regions:
        # Method 1: Try through district ForeignKey
        districts = region.districts.all()  # Using the reverse relation
        
        if not districts.exists():
            # Method 2: Try through the char field matching
            districts = District.objects.filter(region=region.region)
        
        # Get farmers through these districts
        farmers = Farmer.objects.filter(district__in=districts)
        farms = Farm.objects.filter(farmer__in=farmers)
        
        # Get loans through farmers
        loans = Loan.objects.filter(farmer__in=farmers)
        
        regional_data.append({
            'region': region.region,
            'farmers': farmers.count(),
            'farms': farms.count(),
            'hectares': float(farms.aggregate(total=Sum('area_hectares'))['total'] or 0),
            'loans_disbursed': float(loans.aggregate(total=Sum('amount'))['total'] or 0)
        })
    
    return regional_data

# Debug function to check data relationships
def debug_regional_relationships():
    """Debug function to check why regional data might be returning 0"""
    print("=== DEBUG REGIONAL RELATIONSHIPS ===")
    
    # Check total counts
    total_regions = Region.objects.count()
    total_districts = District.objects.count()
    total_farmers = Farmer.objects.count()
    total_farms = Farm.objects.count()
    
    print(f"Total Regions: {total_regions}")
    print(f"Total Districts: {total_districts}")
    print(f"Total Farmers: {total_farmers}")
    print(f"Total Farms: {total_farms}")
    
    # Check a sample region
    sample_region = Region.objects.first()
    if sample_region:
        print(f"\nSample Region: {sample_region.region}")
        
        # Check districts in this region via ForeignKey
        districts_fk = District.objects.filter(region_foreignkey=sample_region)
        print(f"Districts via ForeignKey: {districts_fk.count()}")
        
        # Check districts in this region via char field
        districts_char = District.objects.filter(region=sample_region.region)
        print(f"Districts via char field: {districts_char.count()}")
        
        # Check farmers in these districts
        if districts_fk.exists():
            farmers = Farmer.objects.filter(district__in=districts_fk)
            print(f"Farmers in region: {farmers.count()}")
            
            if farmers.exists():
                farms = Farm.objects.filter(farmer__in=farmers)
                print(f"Farms in region: {farms.count()}")
                print(f"Total hectares: {farms.aggregate(total=Sum('area_hectares'))['total']}")
    
    print("=== END DEBUG ===")

# You can call this function in your view to debug
def monitoring_dashboard_with_debug(request):
    # Call debug function first
    debug_regional_relationships()
    
    # Then proceed with normal dashboard
    return monitoring_dashboard(request)
   


def performance_analysis_api(request):
    """API endpoint for detailed performance chart with actual data"""
    time_range = int(request.GET.get('time_range', 180))
    regions = request.GET.getlist('regions') or request.GET.get('regions', '').split(',')
    projects = request.GET.getlist('projects') or request.GET.get('projects', '').split(',')
    
    # Remove empty strings from filters
    regions = [r for r in regions if r]
    projects = [p for p in projects if p]
    
    # Generate actual data based on time range and filters
    months = []
    farmers_data = []
    loans_data = []
    hectares_data = []
    yield_data = []
    
    # Get the current date and calculate past months correctly
    current_date = timezone.now().date()
    
    # Generate monthly data points for the past 6 months
    for i in range(5, -1, -1):
        # Calculate month start and end correctly
        month_end = current_date.replace(day=1) - timedelta(days=1)  # Last day of previous month
        month_start = month_end.replace(day=1)  # First day of that month
        
        # Move backwards for each iteration
        for _ in range(i):
            month_end = month_start - timedelta(days=1)  # Last day of previous month
            month_start = month_end.replace(day=1)  # First day of that month
        
        months.append(month_start.strftime('%b %Y'))
        
        # Base querysets with filters
        user_profile_qs = UserProfile.objects.filter(role='farmer')
        farmer_qs = Farmer.objects.all()
        loan_disbursement_qs = LoanDisbursement.objects.all()
        farm_qs = Farm.objects.all()
        
        # Apply region filter if provided
        if regions:
            # Get districts in selected regions
            districts_in_regions = District.objects.filter(
                id__in=regions  # Use id since regions are passed as IDs
            ).values_list('id', flat=True)
            user_profile_qs = user_profile_qs.filter(district_id__in=districts_in_regions)
            farmer_qs = farmer_qs.filter(district_id__in=districts_in_regions)
            farm_qs = farm_qs.filter(farmer__district_id__in=districts_in_regions)
            
            # For loans, filter by farmers in selected regions
            farmers_in_regions = Farmer.objects.filter(
                district_id__in=districts_in_regions
            ).values_list('id', flat=True)
            loan_disbursement_qs = loan_disbursement_qs.filter(
                loan__farmer_id__in=farmers_in_regions
            )
        
        # Apply project filter if provided
        if projects:
            # For farms and farmers, filter by project participation
            farmer_qs = farmer_qs.filter(projectparticipation__project_id__in=projects)
            farm_qs = farm_qs.filter(project_id__in=projects)
            
            # For loans, filter by project
            loan_disbursement_qs = loan_disbursement_qs.filter(
                loan__project_id__in=projects
            )
        
        print(f"Month: {month_start.strftime('%b %Y')} - {month_start} to {month_end}")
        
        # Farmers registered in this month (using UserProfile creation date)
        farmers_count = user_profile_qs.filter(
            created_at__date__range=[month_start, month_end]
        ).count()
        farmers_data.append(farmers_count)
        print(f"Farmers found: {farmers_count}")
        
        # Loans disbursed in this month
        loans_amount = loan_disbursement_qs.filter(
            disbursement_date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        loans_data.append(float(loans_amount))
        print(f"Loans disbursed: {loans_amount}")
        
        # Hectares cultivated (new farms registered)
        new_hectares = farm_qs.filter(
            registration_date__range=[month_start, month_end]
        ).aggregate(total=Sum('area_hectares'))['total'] or 0
        hectares_data.append(float(new_hectares))
        print(f"Hectares: {new_hectares}")
        
        # Yield data - use farmers with estimated yield in this period
        monthly_farmers_with_yield = farmer_qs.filter(
            created_at__date__range=[month_start, month_end],
            estimated_yield__isnull=False
        ).exclude(estimated_yield='')
        
        # Calculate average yield for the month
        total_yield = 0
        count = 0
        for farmer in monthly_farmers_with_yield:
            try:
                # Parse estimated_yield string to extract numeric value
                import re
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", farmer.estimated_yield)
                if numbers:
                    yield_value = float(numbers[0])
                    # Convert kg to tons if needed
                    if 'kg' in farmer.estimated_yield.lower():
                        yield_value = yield_value / 1000
                    total_yield += yield_value
                    count += 1
            except (ValueError, TypeError):
                continue
        
        avg_yield = total_yield / count if count > 0 else 0
        yield_data.append(round(avg_yield, 2))
        print(f"Yield data: {avg_yield} from {count} farmers")
    
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
                'name': 'Avg Yield (tons/ha)',
                'type': 'yield',
                'data': yield_data,
                'color': '#f6c23e'
            }
        ]
    }

    print("Dashboard data:", data)
    
    return JsonResponse(data)

# Additional utility functions using only available models
def get_project_progress_stats():
    """Get detailed project progress statistics"""
    projects = Project.objects.annotate(
        total_farmers=Count('participating_farmers'),
        active_farmers=Count('participating_farmers', filter=Q(projectparticipation__status='active'))
    )
    
    return projects

def get_farm_health_stats():
    """Get farm health statistics using available farm status"""
    total_farms = Farm.objects.count()
    active_farms = Farm.objects.filter(status='active').count()
    critical_farms = Farm.objects.filter(status='critical').count()
    delayed_farms = Farm.objects.filter(status='delayed').count()
    completed_farms = Farm.objects.filter(status='completed').count()
    abandoned_farms = Farm.objects.filter(status='abandoned').count()
    
    return {
        'farms_total': total_farms,
        'farms_active': active_farms,
        'farms_critical': critical_farms,
        'farms_delayed': delayed_farms,
        'farms_completed': completed_farms,
        'farms_abandoned': abandoned_farms,
    }

def get_farmer_distribution_stats():
    """Get farmer distribution by district and region"""
    # Farmers by region
    farmers_by_region = []
    for region in Region.objects.all():
        districts = District.objects.filter(region=region.region)
        farmer_count = Farmer.objects.filter(district__in=districts).count()
        farmers_by_region.append({
            'region': region.region,
            'farmers': farmer_count
        })
    
    # Farmers by district
    farmers_by_district = Farmer.objects.values(
        'district__district', 'district__region'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:10]  # Top 10 districts
    
    return {
        'by_region': farmers_by_region,
        'by_district': list(farmers_by_district)
    }

def landing_page(request):
    """Simple landing page view"""
    return render(request, 'portal/dashboard/landing.html')