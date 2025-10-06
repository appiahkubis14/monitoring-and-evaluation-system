import json
from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from portal.models import Farmer, Farm, District, Region, UserProfile

@login_required
def farmer_management(request):
    """Main farmer management page with tabs"""
    return render(request, 'portal/farmer-management/farmers/farmers.html')

@require_http_methods(["GET"])
@login_required
def farmer_list(request):
    """Server-side processing for farmers datatable"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    
    # Base queryset with related data - FIXED: Use region_foreignkey instead of region
    queryset = Farmer.objects.select_related(
        'user_profile__user', 
        'user_profile__district__region_foreignkey'
    ).all()
    
    # Apply search filter - FIXED: Use region_foreignkey
    if search_value:
        queryset = queryset.filter(
            Q(user_profile__user__first_name__icontains=search_value) |
            Q(user_profile__user__last_name__icontains=search_value) |
            Q(national_id__icontains=search_value) |
            Q(user_profile__district__district__icontains=search_value) |
            Q(user_profile__district__region_foreignkey__region__icontains=search_value)
        )
    
    # Total records count
    total_records = Farmer.objects.count()
    total_filtered = queryset.count()
    
    # Apply ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    
    # Map column index to model field - FIXED: Use correct field names
    column_mapping = {
        0: 'user_profile__user__first_name',
        1: 'user_profile__user__last_name',
        2: 'national_id',
        3: 'user_profile__district__district',  # Changed from 'name' to 'district'
        4: 'years_of_experience',  # Removed farm_size since it doesn't exist in Farmer model
        5: 'user_profile__user__date_joined'
    }
    
    order_column = column_mapping.get(order_column_index, 'user_profile__user__first_name')
    if order_direction == 'desc':
        order_column = f'-{order_column}'
    
    queryset = queryset.order_by(order_column)
    
    # Apply pagination
    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)
    
    # Prepare data for response - FIXED: Use correct field names and relationships
    data = []
    for farmer in page_obj:
        # Get district and region info safely
        district = farmer.user_profile.district
        region_name = 'N/A'
        district_name = 'N/A'
        
        if district:
            district_name = district.district  # Changed from district.name
            if district.region_foreignkey:
                region_name = district.region_foreignkey.region
        
        data.append({
            'id': farmer.id,
            'first_name': farmer.user_profile.user.first_name,
            'last_name': farmer.user_profile.user.last_name,
            'national_id': farmer.national_id,
            'district': district_name,
            'region': region_name,
            'years_of_experience': farmer.years_of_experience,
            'phone_number': farmer.user_profile.phone_number or 'N/A',
            'registration_date': farmer.user_profile.user.date_joined.strftime('%Y-%m-%d'),
            'farms_count': farmer.farms.count(),
            'status': 'Active' if farmer.user_profile.user.is_active else 'Inactive'
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
def get_farmer_detail(request, farmer_id):
    """Get detailed information about a specific farmer"""
    try:
        farmer = Farmer.objects.select_related(
            'user_profile__user',
            'user_profile__district__region_foreignkey'
        ).prefetch_related('farms').get(id=farmer_id)
        
        # Get district and region info safely
        district = farmer.user_profile.district
        region_name = 'N/A'
        district_name = 'N/A'
        
        if district:
            district_name = district.district
            if district.region_foreignkey:
                region_name = district.region_foreignkey.region
        
        # Get farms with their locations
        farms_data = []
        for farm in farmer.farms.all():
            farms_data.append({
                'id': farm.id,
                'name': farm.name,
                'farm_code': farm.farm_code,
                'area_hectares': farm.area_hectares,
                'status': farm.get_status_display(),
                'latitude': farm.location.y if farm.location else None,
                'longitude': farm.location.x if farm.location else None,
                'registration_date': farm.registration_date.strftime('%Y-%m-%d') if farm.registration_date else 'N/A'
            })
        
        data = {
            'success': True,
            'farmer': {
                'id': farmer.id,
                'first_name': farmer.user_profile.user.first_name,
                'last_name': farmer.user_profile.user.last_name,
                'national_id': farmer.national_id,
                'email': farmer.user_profile.user.email,
                'phone_number': farmer.user_profile.phone_number,
                'district': district_name,
                'region': region_name,
                'address': farmer.user_profile.address,
                'gender': farmer.user_profile.get_gender_display() if farmer.user_profile.gender else 'N/A',
                'date_of_birth': farmer.user_profile.date_of_birth.strftime('%Y-%m-%d') if farmer.user_profile.date_of_birth else 'N/A',
                'years_of_experience': farmer.years_of_experience,
                'primary_crop': farmer.primary_crop,
                'secondary_crops': farmer.secondary_crops or [],
                'cooperative_membership': farmer.cooperative_membership or 'None',
                'extension_services': 'Yes' if farmer.extension_services else 'No',
                'bank_account_number': farmer.user_profile.bank_account_number or 'Not provided',
                'bank_name': farmer.user_profile.bank_name or 'Not provided',
                'registration_date': farmer.user_profile.user.date_joined.strftime('%Y-%m-%d %H:%M'),
                'status': 'Active' if farmer.user_profile.user.is_active else 'Inactive'
            },
            'farms': farms_data,
            'farms_count': len(farms_data)
        }
        
        return JsonResponse(data)
        
    except Farmer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farmer not found'}, status=404)

@require_http_methods(["GET"])
@login_required
def farmer_get_farm_geojson(request, farmer_id):
    """Get GeoJSON data for all farms of a specific farmer"""
    try:
        farmer = Farmer.objects.get(id=farmer_id)
        farms = farmer.farms.all()
        
        features = []
        for farm in farms:
            if farm.location:
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [farm.location.x, farm.location.y]
                    },
                    'properties': {
                        'id': farm.id,
                        'name': farm.name,
                        'farm_code': farm.farm_code,
                        'area_hectares': farm.area_hectares,
                        'status': farm.status,
                        'status_display': farm.get_status_display(),
                        'registration_date': farm.registration_date.strftime('%Y-%m-%d') if farm.registration_date else 'N/A'
                    }
                }
                features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return JsonResponse(geojson)
        
    except Farmer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farmer not found'}, status=404)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def create_farmer(request):
    """Create a new farmer with user profile"""
    try:
        data = json.loads(request.body)
        print("Creating farmer with data:", data)
        
        # Required fields - REMOVED: farm_size since it doesn't exist in Farmer model
        required_fields = ['first_name', 'last_name', 'national_id', 'district_id']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)
        
        # Check if national ID already exists
        if Farmer.objects.filter(national_id=data['national_id']).exists():
            return JsonResponse({'success': False, 'error': 'National ID already exists'}, status=400)
        
        # Create user first
        username = f"farmer_{data['national_id']}"
        email = data.get('email', f"{username}@example.com")
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            username = f"{username}_{User.objects.count() + 1}"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password='default_password',  # Should be changed on first login
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        
        # Create user profile
        district = District.objects.get(id=data['district_id'])
        
        user_profile = UserProfile.objects.create(
            user=user,
            role='farmer',
            phone_number=data.get('phone_number', ''),
            district=district,
            address=data.get('address', ''),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            bank_account_number=data.get('bank_account_number', ''),
            bank_name=data.get('bank_name', '')
        )
        
        # Handle extension_services conversion
        extension_services = False
        if data.get('extension_services'):
            if isinstance(data['extension_services'], str):
                extension_services = data['extension_services'].lower() in ['true', 'on', 'yes', '1']
            else:
                extension_services = bool(data['extension_services'])
        
        # Create farmer - REMOVED: farm_size field
        farmer = Farmer.objects.create(
            user_profile=user_profile,
            national_id=data['national_id'],
            years_of_experience=data.get('years_of_experience', 0),
            primary_crop=data.get('primary_crop', 'Mango'),
            secondary_crops=data.get('secondary_crops', []),
            cooperative_membership=data.get('cooperative_membership', ''),
            extension_services=extension_services
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Farmer created successfully',
            'id': farmer.id
        })
        
    except District.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'District not found'}, status=404)
    except Exception as e:
        print("Error creating farmer:", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def create_farmers(request):
    """Create multiple farmers with user profiles in bulk"""
    try:
        data = json.loads(request.body)
        print("Received bulk farmer data:", data)
        
        # Check if data is a list
        if not isinstance(data, list):
            return JsonResponse({'success': False, 'error': 'Expected a list of farmers'}, status=400)
        
        if not data:
            return JsonResponse({'success': False, 'error': 'No farmer data provided'}, status=400)
        
        created_farmers = []
        errors = []
        
        for index, farmer_data in enumerate(data):
            try:
                # Required fields for each farmer - REMOVED: farm_size
                required_fields = ['first_name', 'last_name', 'national_id', 'district_id']
                missing_fields = [field for field in required_fields if not farmer_data.get(field)]
                
                if missing_fields:
                    errors.append({
                        'index': index,
                        'national_id': farmer_data.get('national_id', 'Unknown'),
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    })
                    continue
                
                # Check if national ID already exists
                if Farmer.objects.filter(national_id=farmer_data['national_id']).exists():
                    errors.append({
                        'index': index,
                        'national_id': farmer_data['national_id'],
                        'error': 'National ID already exists'
                    })
                    continue
                
                # Create user first
                username = f"farmer_{farmer_data['national_id']}"
                email = farmer_data.get('email', f"{username}@example.com")
                
                # Check if username already exists
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{User.objects.count() + 1}"
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='default_password',
                    first_name=farmer_data['first_name'],
                    last_name=farmer_data['last_name']
                )
                
                # Create user profile
                district = District.objects.get(id=farmer_data['district_id'])
                
                user_profile = UserProfile.objects.create(
                    user=user,
                    role='farmer',
                    phone_number=farmer_data.get('phone_number', ''),
                    district=district,
                    address=farmer_data.get('address', ''),
                    date_of_birth=farmer_data.get('date_of_birth'),
                    gender=farmer_data.get('gender'),
                    bank_account_number=farmer_data.get('bank_account_number', ''),
                    bank_name=farmer_data.get('bank_name', '')
                )
                
                # Handle extension_services conversion
                extension_services = False
                if farmer_data.get('extension_services'):
                    if isinstance(farmer_data['extension_services'], str):
                        extension_services = farmer_data['extension_services'].lower() in ['true', 'on', 'yes', '1']
                    else:
                        extension_services = bool(farmer_data['extension_services'])
                
                # Create farmer - REMOVED: farm_size
                farmer = Farmer.objects.create(
                    user_profile=user_profile,
                    national_id=farmer_data['national_id'],
                    years_of_experience=farmer_data.get('years_of_experience', 0),
                    primary_crop=farmer_data.get('primary_crop', 'Mango'),
                    secondary_crops=farmer_data.get('secondary_crops', []),
                    cooperative_membership=farmer_data.get('cooperative_membership', ''),
                    extension_services=extension_services
                )
                
                created_farmers.append({
                    'id': farmer.id,
                    'national_id': farmer.national_id,
                    'name': f"{farmer_data['first_name']} {farmer_data['last_name']}",
                    'username': username
                })
                
            except District.DoesNotExist:
                errors.append({
                    'index': index,
                    'national_id': farmer_data.get('national_id', 'Unknown'),
                    'error': 'District not found'
                })
                continue
            except Exception as e:
                errors.append({
                    'index': index,
                    'national_id': farmer_data.get('national_id', 'Unknown'),
                    'error': str(e)
                })
                continue
        
        # Prepare response
        response_data = {
            'success': True,
            'message': f'Successfully created {len(created_farmers)} farmers',
            'created_farmers': created_farmers,
            'total_processed': len(data)
        }
        
        # Add errors if any
        if errors:
            response_data['errors'] = errors
            response_data['message'] += f', {len(errors)} failed'
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print("Unexpected error in bulk create:", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def update_farmer(request, farmer_id):
    """Update an existing farmer"""
    try:
        data = json.loads(request.body)
        print("Updating farmer with data:", data)
        
        farmer = Farmer.objects.get(id=data['id'])
        
        # Update user data
        user = farmer.user_profile.user
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        user.save()
        
        # Update user profile
        profile = farmer.user_profile
        if 'phone_number' in data:
            profile.phone_number = data['phone_number']
        if 'district_id' in data:
            district = District.objects.get(id=data['district_id'])
            profile.district = district
        if 'address' in data:
            profile.address = data['address']
        if 'date_of_birth' in data:
            profile.date_of_birth = data['date_of_birth']
        if 'gender' in data:
            profile.gender = data['gender']
        if 'bank_account_number' in data:
            profile.bank_account_number = data['bank_account_number']
        if 'bank_name' in data:
            profile.bank_name = data['bank_name']
        profile.save()
        
        # Update farmer data - REMOVED: farm_size
        if 'years_of_experience' in data:
            farmer.years_of_experience = data['years_of_experience']
        if 'primary_crop' in data:
            farmer.primary_crop = data['primary_crop']
        if 'secondary_crops' in data:
            farmer.secondary_crops = data['secondary_crops']
        if 'cooperative_membership' in data:
            farmer.cooperative_membership = data['cooperative_membership']
        if 'extension_services' in data:
            # Handle extension_services conversion
            if isinstance(data['extension_services'], str):
                farmer.extension_services = data['extension_services'].lower() in ['true', 'on', 'yes', '1']
            else:
                farmer.extension_services = bool(data['extension_services'])
        farmer.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Farmer updated successfully'
        })
        
    except Farmer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farmer not found'}, status=404)
    except District.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'District not found'}, status=404)
    except Exception as e:
        print("Error updating farmer:", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def delete_farmer(request):
    """Delete a farmer (soft delete)"""
    try:
        data = json.loads(request.body)
        farmer_id = data.get('id')
        
        if not farmer_id:
            return JsonResponse({'success': False, 'error': 'Farmer ID is required'}, status=400)
        
        farmer = Farmer.objects.get(id=farmer_id)
        farmer.delete()  # This will set is_deleted=True due to TimeStampModel
        
        return JsonResponse({'success': True, 'message': 'Farmer deleted successfully'})
        
    except Farmer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farmer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_districts(request):
    """Get all districts for dropdowns - FIXED: Use correct field names"""
    districts = District.objects.select_related('region_foreignkey').all()
    
    data = []
    for district in districts:
        region_name = district.region_foreignkey.region if district.region_foreignkey else 'N/A'
        data.append({
            'id': district.id,
            'name': district.district,  # Changed from district.name
            'region': region_name,
            'code': district.district_code or ''  # Changed from district.code
        })
    
    return JsonResponse({'success': True, 'districts': data})

@require_http_methods(["GET"])
@login_required
def get_regions(request):
    """Get all regions for dropdowns"""
    regions = Region.objects.all()
    
    data = []
    for region in regions:
        data.append({
            'id': region.id,
            'name': region.region,
            'code': region.reg_code or ''
        })
    
    return JsonResponse({'success': True, 'regions': data})

@require_http_methods(["GET"])
@login_required
def farmer_export(request):
    """Export farmers data in various formats - FIXED: Use correct field names"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    format_type = request.GET.get('format', 'csv')
    farmers = Farmer.objects.select_related(
        'user_profile__user', 
        'user_profile__district__region_foreignkey'
    ).all()
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="farmers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'First Name', 'Last Name', 'National ID', 'Email', 'Phone', 
            'District', 'Region', 'Experience (years)',
            'Primary Crop', 'Registration Date', 'Status'
        ])
        
        for farmer in farmers:
            district = farmer.user_profile.district
            district_name = district.district if district else ''
            region_name = district.region_foreignkey.region if district and district.region_foreignkey else ''
            
            writer.writerow([
                farmer.user_profile.user.first_name,
                farmer.user_profile.user.last_name,
                farmer.national_id,
                farmer.user_profile.user.email,
                farmer.user_profile.phone_number or '',
                district_name,
                region_name,
                farmer.years_of_experience,
                farmer.primary_crop,
                farmer.user_profile.user.date_joined.strftime('%Y-%m-%d'),
                'Active' if farmer.user_profile.user.is_active else 'Inactive'
            ])
        
        return response
    
    elif format_type == 'json':
        data = []
        for farmer in farmers:
            district = farmer.user_profile.district
            district_name = district.district if district else ''
            region_name = district.region_foreignkey.region if district and district.region_foreignkey else ''
            
            data.append({
                'first_name': farmer.user_profile.user.first_name,
                'last_name': farmer.user_profile.user.last_name,
                'national_id': farmer.national_id,
                'email': farmer.user_profile.user.email,
                'phone': farmer.user_profile.phone_number,
                'district': district_name,
                'region': region_name,
                'experience_years': farmer.years_of_experience,
                'primary_crop': farmer.primary_crop,
                'registration_date': farmer.user_profile.user.date_joined.strftime('%Y-%m-%d'),
                'status': 'Active' if farmer.user_profile.user.is_active else 'Inactive'
            })
        
        return JsonResponse({'farmers': data})
    
    else:
        return JsonResponse({'success': False, 'error': 'Unsupported format'}, status=400)