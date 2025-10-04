from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json
from portal.models import (
    TreeDensityData, CropHealthData, IrrigationSource, 
    SoilTypeArea, ClimateZone, RoadNetwork, Region, District
)

@csrf_exempt
@require_http_methods(["GET"])
def get_tree_density_data(request):
    """Get tree density data for map visualization"""
    try:
        region_id = request.GET.get('region_id')
        density_filter = request.GET.get('density')
        
        queryset = TreeDensityData.objects.all()
        
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if density_filter:
            queryset = queryset.filter(density=density_filter)
        
        data = []
        for item in queryset:
            data.append({
                'id': item.id,
                'lat': item.location.y if item.location else None,
                'lng': item.location.x if item.location else None,
                'density': item.density,
                'trees_per_hectare': item.trees_per_hectare,
                'region': item.region.name if item.region else None,
                'recorded_date': item.recorded_date.isoformat() if item.recorded_date else None
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_crop_health_data(request):
    """Get crop health (NDVI) data for map visualization"""
    try:
        region_id = request.GET.get('region_id')
        health_filter = request.GET.get('health')
        
        queryset = CropHealthData.objects.all()
        
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if health_filter:
            queryset = queryset.filter(health=health_filter)
        
        data = []
        for item in queryset:
            data.append({
                'id': item.id,
                'lat': item.location.y if item.location else None,
                'lng': item.location.x if item.location else None,
                'ndvi': float(item.ndvi) if item.ndvi else None,
                'health': item.health,
                'region': item.region.name if item.region else None,
                'recorded_date': item.recorded_date.isoformat() if item.recorded_date else None
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_irrigation_data(request):
    """Get irrigation sources data for map visualization"""
    try:
        region_id = request.GET.get('region_id')
        source_type = request.GET.get('source_type')
        
        queryset = IrrigationSource.objects.all()
        
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        data = []
        for item in queryset:
            data.append({
                'id': item.id,
                'lat': item.location.y if item.location else None,
                'lng': item.location.x if item.location else None,
                'type': item.source_type,
                'capacity': item.capacity,
                'region': item.region.name if item.region else None,
                'district': item.district.name if item.district else None,
                'operational_status': item.operational_status,
                'coverage_area': item.coverage_area
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_soil_data(request):
    """Get soil type data for map visualization"""
    try:
        region_id = request.GET.get('region_id')
        soil_type = request.GET.get('soil_type')
        
        queryset = SoilTypeArea.objects.all()
        
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if soil_type:
            queryset = queryset.filter(soil_type__icontains=soil_type)
        
        data = []
        for item in queryset:
            # Convert polygon to coordinate array
            coords = []
            if item.boundary:
                # Extract coordinates from polygon
                for coord in item.boundary.coords[0]:  # First ring of polygon
                    coords.append([coord[1], coord[0]])  # [lat, lng]
            
            data.append({
                'id': item.id,
                'coords': coords,
                'type': item.soil_type,
                'fertility': item.fertility,
                'region': item.region.name if item.region else None,
                'area_hectares': item.area_hectares,
                'ph_level': item.ph_level,
                'organic_matter': item.organic_matter
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_climate_data(request):
    """Get climate zone data for map visualization"""
    try:
        region_id = request.GET.get('region_id')
        zone_name = request.GET.get('zone_name')
        
        queryset = ClimateZone.objects.all()
        
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if zone_name:
            queryset = queryset.filter(zone_name__icontains=zone_name)
        
        data = []
        for item in queryset:
            # Convert polygon to coordinate array
            coords = []
            if item.boundary:
                for coord in item.boundary.coords[0]:  # First ring of polygon
                    coords.append([coord[1], coord[0]])  # [lat, lng]
            
            data.append({
                'id': item.id,
                'coords': coords,
                'zone': item.zone_name,
                'rainfall': item.rainfall,
                'region': item.region.name if item.region else None,
                'avg_temperature': item.avg_temperature,
                'avg_rainfall': item.avg_rainfall
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_road_data(request):
    """Get road network data for map visualization"""
    try:
        region_id = request.GET.get('region_id')
        road_type = request.GET.get('road_type')
        
        queryset = RoadNetwork.objects.all()
        
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if road_type:
            queryset = queryset.filter(road_type=road_type)
        
        data = []
        for item in queryset:
            # Convert linestring to coordinate array
            coords = []
            if item.path:
                for coord in item.path.coords:
                    coords.append([coord[1], coord[0]])  # [lat, lng]
            
            data.append({
                'id': item.id,
                'coords': coords,
                'type': item.road_type,
                'condition': item.condition,
                'name': item.name,
                'region': item.region.name if item.region else None,
                'district': item.district.name if item.district else None,
                'length_km': item.length_km
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_regions_list(request):
    """Get list of all regions for filtering"""
    try:
        regions = Region.objects.all()
        data = []
        for region in regions:
            data.append({
                'id': region.id,
                'name': region.name,
                'code': region.code
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_all_agricultural_data(request):
    """Get all agricultural data in one endpoint for initial map load"""
    try:
        region_id = request.GET.get('region_id')
        
        # Get all data types
        tree_data = list(TreeDensityData.objects.all()[:100])  # Limit for performance
        crop_data = list(CropHealthData.objects.all()[:100])
        irrigation_data = list(IrrigationSource.objects.all()[:50])
        soil_data = list(SoilTypeArea.objects.all()[:20])
        climate_data = list(ClimateZone.objects.all()[:10])
        road_data = list(RoadNetwork.objects.all()[:50])
        
        response_data = {
            'tree_density': [],
            'crop_health': [],
            'irrigation_sources': [],
            'soil_types': [],
            'climate_zones': [],
            'roads': []
        }
        
        # Process tree density data
        for item in tree_data:
            response_data['tree_density'].append({
                'id': item.id,
                'lat': item.location.y if item.location else None,
                'lng': item.location.x if item.location else None,
                'density': item.density,
                'trees_per_hectare': item.trees_per_hectare,
                'region': item.region.name if item.region else None
            })
        
        # Process crop health data
        for item in crop_data:
            response_data['crop_health'].append({
                'id': item.id,
                'lat': item.location.y if item.location else None,
                'lng': item.location.x if item.location else None,
                'ndvi': float(item.ndvi) if item.ndvi else None,
                'health': item.health,
                'region': item.region.name if item.region else None
            })
        
        # Process irrigation data
        for item in irrigation_data:
            response_data['irrigation_sources'].append({
                'id': item.id,
                'lat': item.location.y if item.location else None,
                'lng': item.location.x if item.location else None,
                'type': item.source_type,
                'capacity': item.capacity,
                'region': item.region.name if item.region else None
            })
        
        # Process soil data
        for item in soil_data:
            coords = []
            if item.boundary:
                for coord in item.boundary.coords[0]:
                    coords.append([coord[1], coord[0]])
            
            response_data['soil_types'].append({
                'id': item.id,
                'coords': coords,
                'type': item.soil_type,
                'fertility': item.fertility,
                'region': item.region.name if item.region else None
            })
        
        # Process climate data
        for item in climate_data:
            coords = []
            if item.boundary:
                for coord in item.boundary.coords[0]:
                    coords.append([coord[1], coord[0]])
            
            response_data['climate_zones'].append({
                'id': item.id,
                'coords': coords,
                'zone': item.zone_name,
                'rainfall': item.rainfall,
                'region': item.region.name if item.region else None
            })
        
        # Process road data
        for item in road_data:
            coords = []
            if item.path:
                for coord in item.path.coords:
                    coords.append([coord[1], coord[0]])
            
            response_data['roads'].append({
                'id': item.id,
                'coords': coords,
                'type': item.road_type,
                'condition': item.condition,
                'name': item.name,
                'region': item.region.name if item.region else None
            })
        
        return JsonResponse({
            'success': True,
            'data': response_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    


#########################################################################################################

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.contrib.gis.geos import Point, Polygon, LineString

@csrf_exempt
@require_http_methods(["POST"])
def create_tree_density_data(request):
    """Create tree density data from JSON"""
    try:
        data = json.loads(request.body)
        print("Received data:", data)
        created_count = 0
        
        # Handle both single object and array of objects
        if isinstance(data, list):
            items = data
        else:
            items = data.get('tree_density_data', [])
            if not items:  # Handle single object
                items = [data]
        
        for item in items:
            location_data = item.get('location', {})
            if location_data.get('type') == 'Point':
                coords = location_data['coordinates']
                point = Point(coords[0], coords[1], srid=4326)
                region = Region.objects.filter(id=item['region']).first()
                
                if region:
                    TreeDensityData.objects.create(
                        location=point,
                        density=item['density'],
                        trees_per_hectare=item['trees_per_hectare'],
                        region=region,
                        recorded_date=item.get('recorded_date', '2024-01-15')
                    )
                    created_count += 1
                else:
                    print(f"Region with id {item['region']} not found")
    
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {created_count} tree density records',
            'count': created_count
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_crop_health_data(request):
    """Create crop health data from JSON"""
    try:
        data = json.loads(request.body)
        created_count = 0
        
        # Handle both single object and array of objects
        if isinstance(data, list):
            items = data
        else:
            items = data.get('crop_health_data', [])
            if not items:  # Handle single object
                items = [data]
        
        for item in items:
            location_data = item.get('location', {})
            if location_data.get('type') == 'Point':
                coords = location_data['coordinates']
                point = Point(coords[0], coords[1], srid=4326)
                region = Region.objects.filter(id=item['region']).first()
                
                if region:
                    CropHealthData.objects.create(
                        location=point,
                        ndvi=item['ndvi'],
                        health=item['health'],
                        region=region,
                        recorded_date=item.get('recorded_date', '2024-01-15')
                    )
                    created_count += 1
                else:
                    print(f"Region with id {item['region']} not found")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {created_count} crop health records',
            'count': created_count
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_irrigation_data(request):
    """Create irrigation sources data from JSON"""
    try:
        data = json.loads(request.body)
        created_count = 0
        
        # Handle both single object and array of objects
        if isinstance(data, list):
            items = data
        else:
            items = data.get('irrigation_sources', [])
            if not items:  # Handle single object
                items = [data]
        
        for item in items:
            location_data = item.get('location', {})
            if location_data.get('type') == 'Point':
                coords = location_data['coordinates']
                point = Point(coords[0], coords[1], srid=4326)
                region = Region.objects.filter(id=item['region']).first()
                
                if region:
                    IrrigationSource.objects.create(
                        location=point,
                        source_type=item['source_type'],
                        capacity=item['capacity'],
                        region=region,
                        operational_status=item.get('operational_status', True)
                    )
                    created_count += 1
                else:
                    print(f"Region with id {item['region']} not found")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {created_count} irrigation source records',
            'count': created_count
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_soil_data(request):
    """Create soil type areas from JSON"""
    try:
        data = json.loads(request.body)
        created_count = 0
        
        # Handle both single object and array of objects
        if isinstance(data, list):
            items = data
        else:
            items = data.get('soil_type_areas', [])
            if not items:  # Handle single object
                items = [data]
        
        for item in items:
            boundary_data = item.get('boundary', {})
            if boundary_data.get('type') == 'Polygon':
                coords = boundary_data['coordinates']
                polygon = Polygon(coords[0], srid=4326)
                region = Region.objects.filter(id=item['region']).first()
                
                if region:
                    SoilTypeArea.objects.create(
                        boundary=polygon,
                        soil_type=item['soil_type'],
                        fertility=item['fertility'],
                        region=region,
                        area_hectares=item.get('area_hectares')
                    )
                    created_count += 1
                else:
                    print(f"Region with id {item['region']} not found")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {created_count} soil type areas',
            'count': created_count
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_climate_data(request):
    """Create climate zones from JSON"""
    try:
        data = json.loads(request.body)
        created_count = 0
        
        # Handle both single object and array of objects
        if isinstance(data, list):
            items = data
        else:
            items = data.get('climate_zones', [])
            if not items:  # Handle single object
                items = [data]
        
        for item in items:
            boundary_data = item.get('boundary', {})
            if boundary_data.get('type') == 'Polygon':
                coords = boundary_data['coordinates']
                polygon = Polygon(coords[0], srid=4326)
                region = Region.objects.filter(id=item['region']).first()
                
                if region:
                    ClimateZone.objects.create(
                        boundary=polygon,
                        zone_name=item['zone_name'],
                        rainfall=item['rainfall'],
                        region=region,
                        avg_temperature=item.get('avg_temperature'),
                        avg_rainfall=item.get('avg_rainfall')
                    )
                    created_count += 1
                else:
                    print(f"Region with id {item['region']} not found")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {created_count} climate zones',
            'count': created_count
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_road_data(request):
    """Create road network from JSON"""
    try:
        data = json.loads(request.body)
        created_count = 0
        
        # Handle both single object and array of objects
        if isinstance(data, list):
            items = data
        else:
            items = data.get('road_network', [])
            if not items:  # Handle single object
                items = [data]
        
        for item in items:
            path_data = item.get('path', {})
            if path_data.get('type') == 'LineString':
                coords = path_data['coordinates']
                linestring = LineString(coords, srid=4326)
                region = Region.objects.filter(id=item['region']).first()
                
                if region:
                    RoadNetwork.objects.create(
                        path=linestring,
                        road_type=item['road_type'],
                        condition=item['condition'],
                        name=item.get('name'),
                        region=region,
                        length_km=item.get('length_km')
                    )
                    created_count += 1
                else:
                    print(f"Region with id {item['region']} not found")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {created_count} road segments',
            'count': created_count
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)