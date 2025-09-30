from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.gis.geos import Polygon

from portal.models import Farm, UserProfile
from utils.sidebar import UserRole

@login_required
def interactive_map(request):
    """Main interactive map view"""
    context = {
        'page_title': 'Interactive Farm Map',
    }
    return render(request, 'portal/map/map.html')

@login_required
def get_farm_data(request):
    """Get farm data for the map"""
    try:
        # Get all farms with related data
        farms = Farm.objects.filter(is_deleted=False).select_related(
            'farmer', 
            'farmer__user_profile', 
            'farmer__user_profile__user'
        )
        
        farm_data = []
        for farm in farms:
            farmer = farm.farmer
            user_profile = farmer.user_profile
            
            farm_info = {
                'id': farm.id,
                'farm_code': farm.farm_code,
                'name': farm.name or f"Farm {farm.farm_code}",
                'status': farm.status,
                'area_hectares': farm.area_hectares,
                'soil_type': farm.soil_type,
                'irrigation_type': farm.irrigation_type,
                'irrigation_coverage': farm.irrigation_coverage,
                'boundary_coord': farm.boundary_coord,  # This should be the ArrayField data
                'validation_status': farm.validation_status,
                'registration_date': farm.registration_date.strftime('%Y-%m-%d') if farm.registration_date else '',
                'last_visit_date': farm.last_visit_date.strftime('%Y-%m-%d') if farm.last_visit_date else '',
                
                # Farmer information
                'farmer_name': user_profile.user.get_full_name(),
                'farmer_national_id': farmer.national_id,
                'primary_crop': farmer.primary_crop,
                'years_of_experience': farmer.years_of_experience,
                'cooperative_membership': farmer.cooperative_membership,
                
                # Location data
                'has_boundary': bool(farm.boundary),
                'has_location': bool(farm.location),
            }
            
            # Add boundary coordinates if available - FIXED VERSION
            if farm.boundary:
                try:
                    # Get coordinates from the Polygon field
                    coords = list(farm.boundary.coords[0])  # This gives us the exterior ring
                    
                    # Convert to the format Leaflet expects: [[lng, lat], [lng, lat], ...]
                    leaflet_coords = []
                    for coord in coords:
                        if len(coord) >= 2:
                            leaflet_coords.append([float(coord[0]), float(coord[1])])
                    
                    farm_info['boundary'] = {
                        'type': 'Polygon',
                        'coordinates': [leaflet_coords]  # Note: coordinates is an array of arrays
                    }
                    print(f"Farm {farm.id} boundary coordinates: {leaflet_coords[:3]}...")  # Debug first 3 points
                    
                except Exception as e:
                    print(f"Error converting boundary for farm {farm.id}: {e}")
                    farm_info['boundary'] = None
            
            # Add point location if available
            if farm.location:
                try:
                    farm_info['location'] = {
                        'type': 'Point',
                        'coordinates': [float(farm.location.x), float(farm.location.y)]
                    }
                except Exception as e:
                    print(f"Error converting location for farm {farm.id}: {e}")
                    farm_info['location'] = None
            
            farm_data.append(farm_info)
        
        return JsonResponse({
            'success': True,
            'farms': farm_data,
            'total_count': len(farm_data)
        })
        
    except Exception as e:
        import traceback
        print(f"Error in get_farm_data: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@csrf_exempt
def update_farm_boundary(request, farm_id):
    """Update farm boundary coordinates"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        farm = Farm.objects.get(id=farm_id)
        data = json.loads(request.body)
        print("Received boundary data:", data)
        
        # # Check if user has permission to edit this farm
        # user_role = request.user.userprofile.role
        # if user_role not in [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]:
        #     return JsonResponse({'success': False, 'error': 'Insufficient permissions'})
        
        # Update boundary coordinates
        boundary_coords = data.get('boundary_coordinates')
        if boundary_coords and len(boundary_coords) >= 3:
            print(f"Processing {len(boundary_coords)} coordinates")
            
            # Ensure the polygon is closed (first and last points are the same)
            if boundary_coords[0] != boundary_coords[-1]:
                boundary_coords.append(boundary_coords[0])
                
            # Create Polygon - coordinates should be in [lng, lat] format
            polygon = Polygon(boundary_coords)
            farm.boundary = polygon
            farm.boundary_coord = boundary_coords  # Store raw coordinates in ArrayField
            farm.save()
            
            print(f"Successfully updated boundary for farm {farm_id}")
            
            return JsonResponse({
                'success': True, 
                'message': 'Boundary updated successfully',
                'farm_id': farm.id
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid boundary coordinates provided - need at least 3 points'
            })
            
    except Farm.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farm not found'})
    except Exception as e:
        import traceback
        print(f"Error updating boundary: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})