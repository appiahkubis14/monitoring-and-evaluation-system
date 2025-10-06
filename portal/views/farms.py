import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers import serialize
from django.utils import timezone
from portal.models import Farm, Farmer, District, Region, FarmVisit, FarmCrop, MangoVariety

@login_required
def farm_management(request):
    """Main farm management page with tabs"""
    return render(request, 'portal/farmer-management/farms/farms.html')

@require_http_methods(["GET"])
@login_required
def farm_list(request):
    """Server-side processing for farms datatable"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    status_filter = request.GET.get('status')
    farmer_filter = request.GET.get('farmer_id')
    
    # Base queryset with related data
    queryset = Farm.objects.filter(validation_status=True).select_related(
        'farmer__user_profile__user', 
        'farmer__user_profile__district__region_foreignkey'
    ).all()
    
    # Apply filters
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    if farmer_filter:
        queryset = queryset.filter(farmer_id=farmer_filter)
    
    # Apply search filter
    if search_value:
        queryset = queryset.filter(
            Q(name__icontains=search_value) |
            Q(farm_code__icontains=search_value) |
            Q(farmer__user_profile__user__first_name__icontains=search_value) |
            Q(farmer__user_profile__user__last_name__icontains=search_value) |
            Q(farmer__national_id__icontains=search_value) |
            Q(soil_type__icontains=search_value) |
            Q(irrigation_type__icontains=search_value)
        )
    
    # Total records count
    total_records = Farm.objects.count()
    total_filtered = queryset.count()
    
    # Apply ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    
    # Map column index to model field
    column_mapping = {
        0: 'farm_code',
        1: 'name',
        2: 'farmer__user_profile__user__first_name',
        3: 'farmer__user_profile__user__last_name',
        4: 'area_hectares',
        5: 'status',
        6: 'registration_date',
        7: 'last_visit_date'
    }
    
    order_column = column_mapping.get(order_column_index, 'farm_code')
    if order_direction == 'desc':
        order_column = f'-{order_column}'
    
    queryset = queryset.order_by(order_column)
    
    # Apply pagination
    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)
    
    # Prepare data for response
    data = []
    for farm in page_obj:
        data.append({
            'id': farm.id,
            'farm_code': farm.farm_code,
            'name': farm.name,
            'farmer_name': f"{farm.farmer.user_profile.user.first_name} {farm.farmer.user_profile.user.last_name}",
            'farmer_id': farm.farmer.id,
            'national_id': farm.farmer.national_id,
            'area_hectares': farm.area_hectares,
            'status': farm.status,
            'status_display': farm.get_status_display(),
            'soil_type': farm.soil_type or 'Not specified',
            'irrigation_type': farm.irrigation_type or 'Not specified',
            'irrigation_coverage': f"{farm.irrigation_coverage}%",
            'registration_date': farm.registration_date.strftime('%Y-%m-%d'),
            'last_visit_date': farm.last_visit_date.strftime('%Y-%m-%d') if farm.last_visit_date else 'Never',
            'latitude': farm.location.y if farm.location else None,
            'longitude': farm.location.x if farm.location else None,
            'altitude': farm.altitude or 'N/A',
            'slope': farm.slope or 'N/A'
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
def get_farm_detail(request, farm_id):
    """Get detailed information about a specific farm"""
    try:
        farm = Farm.objects.select_related(
            'farmer__user_profile__user',
            'farmer__user_profile__district__region_foreignkey'
        ).prefetch_related('crops__variety', 'visits').get(id=farm_id)
        
        # Get farm crops
        crops_data = []
        for crop in farm.crops.all():
            crops_data.append({
                'variety': crop.variety.name,
                'planting_date': crop.planting_date.strftime('%Y-%m-%d'),
                'planting_density': crop.planting_density,
                'total_trees': crop.total_trees,
                'expected_yield': crop.expected_yield
            })
        
        # Get recent visits
        visits_data = []
        for visit in farm.visits.all().order_by('-visit_date')[:5]:
            visits_data.append({
                'visit_date': visit.visit_date.strftime('%Y-%m-%d'),
                'purpose': visit.purpose,
                'conducted_by': visit.conducted_by.user_profile.user.get_full_name() if visit.conducted_by else 'N/A'
            })
        
        data = {
            'success': True,
            'farm': {
                'id': farm.id,
                'farm_code': farm.farm_code,
                'name': farm.name,
                'farmer_name': f"{farm.farmer.user_profile.user.first_name} {farm.farmer.user_profile.user.last_name}",
                'farmer_id': farm.farmer.id,
                'national_id': farm.farmer.national_id,
                'area_hectares': farm.area_hectares,
                'status': farm.status,
                'status_display': farm.get_status_display(),
                'soil_type': farm.soil_type or 'Not specified',
                'irrigation_type': farm.irrigation_type or 'Not specified',
                'irrigation_coverage': farm.irrigation_coverage,
                'registration_date': farm.registration_date.strftime('%Y-%m-%d'),
                'last_visit_date': farm.last_visit_date.strftime('%Y-%m-%d') if farm.last_visit_date else 'Never',
                'latitude': farm.location.y if farm.location else None,
                'longitude': farm.location.x if farm.location else None,
                'altitude': farm.altitude,
                'slope': farm.slope,
                'boundary_available': bool(farm.boundary)
            },
            'crops': crops_data,
            'visits': visits_data,
            'crops_count': len(crops_data),
            'visits_count': farm.visits.count()
        }
        
        return JsonResponse(data)
        
    except Farm.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farm not found'}, status=404)

@require_http_methods(["GET"])
@login_required
def farrm_get_farm_geojson(request, farm_id):
    """Get GeoJSON data for a specific farm"""
    try:
        farm = Farm.objects.get(id=farm_id)
        
        features = []
        
        # Add farm location point
        if farm.location:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [farm.location.x, farm.location.y]
                },
                'properties': {
                    'type': 'location',
                    'id': farm.id,
                    'name': farm.name,
                    'farm_code': farm.farm_code,
                    'area_hectares': farm.area_hectares,
                    'status': farm.status,
                    'status_display': farm.get_status_display()
                }
            }
            features.append(feature)
        
        # Add farm boundary polygon if available
        if farm.boundary:
            # Convert polygon to GeoJSON format
            feature = {
                'type': 'Feature',
                'geometry': json.loads(farm.boundary.geojson),
                'properties': {
                    'type': 'boundary',
                    'id': farm.id,
                    'name': farm.name,
                    'farm_code': farm.farm_code,
                    'area_hectares': farm.area_hectares
                }
            }
            features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return JsonResponse(geojson)
        
    except Farm.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farm not found'}, status=404)

@require_http_methods(["GET"])
@login_required
def get_all_farms_geojson(request):
    """Get GeoJSON data for all farms"""
    farms = Farm.objects.all()
    
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
                    'farmer_name': f"{farm.farmer.user_profile.user.first_name} {farm.farmer.user_profile.user.last_name}",
                    'farmer_id': farm.farmer.id
                }
            }
            features.append(feature)
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    return JsonResponse(geojson)




@require_http_methods(["POST"])
@login_required
@transaction.atomic
def create_farm(request):
    """Create a new farm"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['farmer_id', 'name', 'area_hectares', 'latitude', 'longitude']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)
        
        # Check if farmer exists
        try:
            farmer = Farmer.objects.get(id=data['farmer_id'])
        except Farmer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Farmer not found'}, status=404)
        
        # Create point from coordinates
        from django.contrib.gis.geos import Point
        location = Point(float(data['longitude']), float(data['latitude']))
        
        # Create farm
        farm = Farm.objects.create(
            farmer=farmer,
            name=data['name'],
            location=location,
            area_hectares=float(data['area_hectares']),
            soil_type=data.get('soil_type'),
            irrigation_type=data.get('irrigation_type'),
            irrigation_coverage=float(data.get('irrigation_coverage', 0)),
            status=data.get('status', 'active'),
            altitude=data.get('altitude'),
            slope=data.get('slope')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Farm created successfully',
            'farm_id': farm.id,
            'farm_code': farm.farm_code
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


from django.views.decorators.csrf import csrf_exempt

@require_http_methods(["POST"])
@csrf_exempt
# @login_required
@transaction.atomic
def create_farms(request):
    """Create multiple farms in bulk"""
    try:
        data = json.loads(request.body)
        print("Received farm data:", data)
        
        # Check if data is a list
        if not isinstance(data, list):
            return JsonResponse({'success': False, 'error': 'Expected a list of farms'}, status=400)
        
        if not data:
            return JsonResponse({'success': False, 'error': 'No farm data provided'}, status=400)
        
        created_farms = []
        errors = []
        
        for index, farm_data in enumerate(data):
            try:
                # Required fields for each farm
                required_fields = ['farmer_id', 'name', 'area_hectares']
                missing_fields = [field for field in required_fields if not farm_data.get(field)]
                
                if missing_fields:
                    errors.append({
                        'index': index,
                        'name': farm_data.get('name', 'Unknown'),
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    })
                    continue
                
                # Check if farmer exists
                try:
                    farmer = Farmer.objects.get(id=farm_data['farmer_id'])
                except Farmer.DoesNotExist:
                    errors.append({
                        'index': index,
                        'name': farm_data.get('name', 'Unknown'),
                        'error': f"Farmer with ID {farm_data['farmer_id']} not found"
                    })
                    continue
                
                # Create location from coordinates
                from django.contrib.gis.geos import Point
                location = None
                
                # Handle different coordinate formats
                if farm_data.get('location') and farm_data['location'].get('coordinates'):
                    coords = farm_data['location']['coordinates']
                    if len(coords) >= 2:
                        # Handle [lng, lat] format
                        location = Point(float(coords[0]), float(coords[1]))
                elif farm_data.get('latitude') and farm_data.get('longitude'):
                    # Handle separate lat/long fields
                    location = Point(float(farm_data['longitude']), float(farm_data['latitude']))
                else:
                    errors.append({
                        'index': index,
                        'name': farm_data.get('name', 'Unknown'),
                        'error': 'Location coordinates required (either location object or latitude/longitude)'
                    })
                    continue
                
                # Create boundary if provided
                boundary = None
                if farm_data.get('boundary') and farm_data['boundary'].get('coordinates'):
                    from django.contrib.gis.geos import Polygon
                    try:
                        coords = farm_data['boundary']['coordinates'][0]  # Get first ring
                        # Convert to tuple of tuples for Polygon
                        polygon_coords = tuple((float(coord[0]), float(coord[1])) for coord in coords)
                        boundary = Polygon(polygon_coords)
                    except Exception as e:
                        errors.append({
                            'index': index,
                            'name': farm_data.get('name', 'Unknown'),
                            'error': f'Invalid boundary coordinates: {str(e)}'
                        })
                        continue
                
                # Handle dates
                registration_date = farm_data.get('registration_date')
                last_visit_date = farm_data.get('last_visit_date')
                
                if registration_date:
                    from django.utils.dateparse import parse_date
                    registration_date = parse_date(registration_date)
                
                if last_visit_date:
                    from django.utils.dateparse import parse_date
                    last_visit_date = parse_date(last_visit_date)
                
                # Create farm
                farm = Farm.objects.create(
                    farmer=farmer,
                    name=farm_data['name'],
                    location=location,
                    boundary=boundary,
                    area_hectares=float(farm_data['area_hectares']),
                    soil_type=farm_data.get('soil_type'),
                    irrigation_type=farm_data.get('irrigation_type'),
                    irrigation_coverage=float(farm_data.get('irrigation_coverage', 0)),
                    status=farm_data.get('status', 'active'),
                    registration_date=registration_date,
                    last_visit_date=last_visit_date,
                    boundary_coord=farm_data.get('boundary_coord'),
                    validation_status=farm_data.get('validation_status', False),
                    altitude=farm_data.get('altitude'),
                    slope=farm_data.get('slope')
                )
                
                created_farms.append({
                    'id': farm.id,
                    'farm_code': farm.farm_code,
                    'name': farm.name,
                    'farmer_id': farmer.id
                })
                
            except ValueError as e:
                errors.append({
                    'index': index,
                    'name': farm_data.get('name', 'Unknown'),
                    'error': f'Invalid numeric value: {str(e)}'
                })
                continue
            except Exception as e:
                errors.append({
                    'index': index,
                    'name': farm_data.get('name', 'Unknown'),
                    'error': str(e)
                })
                continue
        
        # Prepare response
        response_data = {
            'success': True,
            'message': f'Successfully created {len(created_farms)} farms',
            'created_farms': created_farms,
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
        print("Unexpected error:", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)






@require_http_methods(["POST"])
@login_required
@transaction.atomic
def update_farm(request, farm_id):
    """Update an existing farm"""
    try:
        data = json.loads(request.body)
        farm = Farm.objects.get(id=farm_id)
        
        # Update farm data
        if 'name' in data:
            farm.name = data['name']
        if 'area_hectares' in data:
            farm.area_hectares = float(data['area_hectares'])
        if 'soil_type' in data:
            farm.soil_type = data['soil_type']
        if 'irrigation_type' in data:
            farm.irrigation_type = data['irrigation_type']
        if 'irrigation_coverage' in data:
            farm.irrigation_coverage = float(data['irrigation_coverage'])
        if 'status' in data:
            farm.status = data['status']
        if 'altitude' in data:
            farm.altitude = data['altitude']
        if 'slope' in data:
            farm.slope = data['slope']
        
        # Update location if provided
        if 'latitude' in data and 'longitude' in data:
            from django.contrib.gis.geos import Point
            farm.location = Point(float(data['longitude']), float(data['latitude']))
        
        farm.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Farm updated successfully'
        })
        
    except Farm.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farm not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def delete_farm(request):
    """Delete a farm (soft delete)"""
    try:
        data = json.loads(request.body)
        farm_id = data.get('id')
        
        if not farm_id:
            return JsonResponse({'success': False, 'error': 'Farm ID is required'}, status=400)
        
        farm = Farm.objects.get(id=farm_id)
        farm.delete()  # This will set is_deleted=True due to TimeStampModel
        
        return JsonResponse({'success': True, 'message': 'Farm deleted successfully'})
        
    except Farm.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farm not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_farm_stats(request):
    """Get statistics about farms"""
    try:
        # Total farms count
        total_farms = Farm.objects.count()
        
        # Farms by status
        farms_by_status = Farm.objects.values('status').annotate(
            count=Count('id'),
            total_area=Sum('area_hectares')
        )
        
        # Farms by district
        farms_by_district = Farm.objects.filter(
            farmer__user_profile__district__isnull=False
        ).values(
            'farmer__user_profile__district__name'
        ).annotate(
            count=Count('id'),
            total_area=Sum('area_hectares')
        ).order_by('-count')
        
        # Average farm size
        avg_farm_size = Farm.objects.aggregate(avg_size=Avg('area_hectares'))
        
        # Recent registrations (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_registrations = Farm.objects.filter(
            registration_date__gte=thirty_days_ago
        ).count()
        
        data = {
            'success': True,
            'stats': {
                'total_farms': total_farms,
                'farms_by_status': list(farms_by_status),
                'farms_by_district': list(farms_by_district),
                'avg_farm_size': avg_farm_size['avg_size'] or 0,
                'recent_registrations': recent_registrations,
                'total_area': Farm.objects.aggregate(total=Sum('area_hectares'))['total'] or 0
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_mango_varieties(request):
    """Get all mango varieties for dropdowns"""
    varieties = MangoVariety.objects.all()
    
    data = []
    for variety in varieties:
        data.append({
            'id': variety.id,
            'name': variety.name,
            'scientific_name': variety.scientific_name or '',
            'maturity_period': variety.maturity_period,
            'yield_potential': variety.yield_potential
        })
    
    return JsonResponse({'success': True, 'varieties': data})

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def add_farm_crop(request, farm_id):
    """Add a crop to a farm"""
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['variety_id', 'planting_date', 'planting_density', 'total_trees']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)
        
        # Check if farm exists
        try:
            farm = Farm.objects.get(id=farm_id)
        except Farm.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Farm not found'}, status=404)
        
        # Check if variety exists
        try:
            variety = MangoVariety.objects.get(id=data['variety_id'])
        except MangoVariety.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Mango variety not found'}, status=404)
        
        # Create farm crop
        farm_crop = FarmCrop.objects.create(
            farm=farm,
            variety=variety,
            planting_date=data['planting_date'],
            planting_density=int(data['planting_density']),
            total_trees=int(data['total_trees']),
            expected_yield=float(data.get('expected_yield', 0))
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Crop added successfully',
            'crop_id': farm_crop.id
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid numeric value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def farm_export(request):
    """Export farms data in various formats"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    format_type = request.GET.get('format', 'csv')
    farms = Farm.objects.select_related(
        'farmer__user_profile__user', 
        'farmer__user_profile__district__region'
    ).all()
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="farms_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Farm Code', 'Name', 'Farmer', 'National ID', 'Area (ha)', 
            'Status', 'Soil Type', 'Irrigation Type', 'Irrigation Coverage (%)',
            'Registration Date', 'District', 'Region', 'Latitude', 'Longitude'
        ])
        
        for farm in farms:
            writer.writerow([
                farm.farm_code,
                farm.name,
                f"{farm.farmer.user_profile.user.first_name} {farm.farmer.user_profile.user.last_name}",
                farm.farmer.national_id,
                farm.area_hectares,
                farm.get_status_display(),
                farm.soil_type or '',
                farm.irrigation_type or '',
                farm.irrigation_coverage,
                farm.registration_date.strftime('%Y-%m-%d'),
                farm.farmer.user_profile.district.name if farm.farmer.user_profile.district else '',
                farm.farmer.user_profile.district.region.name if farm.farmer.user_profile.district and farm.farmer.user_profile.district.region else '',
                farm.location.y if farm.location else '',
                farm.location.x if farm.location else ''
            ])
        
        return response
    
    elif format_type == 'json':
        data = []
        for farm in farms:
            data.append({
                'farm_code': farm.farm_code,
                'name': farm.name,
                'farmer': f"{farm.farmer.user_profile.user.first_name} {farm.farmer.user_profile.user.last_name}",
                'national_id': farm.farmer.national_id,
                'area_hectares': farm.area_hectares,
                'status': farm.status,
                'status_display': farm.get_status_display(),
                'soil_type': farm.soil_type,
                'irrigation_type': farm.irrigation_type,
                'irrigation_coverage': farm.irrigation_coverage,
                'registration_date': farm.registration_date.strftime('%Y-%m-%d'),
                'district': farm.farmer.user_profile.district.name if farm.farmer.user_profile.district else '',
                'region': farm.farmer.user_profile.district.region.name if farm.farmer.user_profile.district and farm.farmer.user_profile.district.region else '',
                'latitude': farm.location.y if farm.location else None,
                'longitude': farm.location.x if farm.location else None
            })
        
        return JsonResponse({'farms': data})
    
    else:
        return JsonResponse({'success': False, 'error': 'Unsupported format'}, status=400)