from rest_framework import serializers
from django.contrib.auth.models import User
from portal.models import (
    UserProfile, Staff, Farmer, Farm, MonitoringVisit, 
    Project, Region, District, MangoVariety, FarmVisit,
    FollowUpAction, Infrastructure, Milestone, ComplianceCheck
)
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.db.models.functions import Distance
import base64
import uuid
from django.core.files.base import ContentFile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class StaffLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class StaffSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Staff
        fields = '__all__'

class FarmerSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(read_only=True)
    district_name = serializers.CharField(source='user_profile.district.name', read_only=True)
    region_name = serializers.CharField(source='user_profile.district.region.name', read_only=True)
    
    class Meta:
        model = Farmer
        fields = '__all__'

class FarmerCreateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(write_only=True)
    district_id = serializers.IntegerField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False)
    
    class Meta:
        model = Farmer
        fields = [
            'first_name', 'last_name', 'phone_number', 'district_id', 'email',
            'national_id', 'farm_size', 'years_of_experience', 'primary_crop',
            'secondary_crops', 'cooperative_membership', 'extension_services'
        ]
    
    def create(self, validated_data):
        # Extract user data
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        phone_number = validated_data.pop('phone_number')
        district_id = validated_data.pop('district_id')
        email = validated_data.pop('email', f"{first_name}.{last_name}@example.com")
        
        # Create User
        user = User.objects.create_user(
            username=phone_number,
            email=email,
            password=str(uuid.uuid4()),  # Random password
            first_name=first_name,
            last_name=last_name
        )
        
        # Create UserProfile
        district = District.objects.get(id=district_id)
        user_profile = UserProfile.objects.create(
            user=user,
            role='farmer',
            phone_number=phone_number,
            district=district
        )
        
        # Create Farmer
        farmer = Farmer.objects.create(
            user_profile=user_profile,
            **validated_data
        )
        
        return farmer

class FarmSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='farmer.user_profile.user.get_full_name', read_only=True)
    district_name = serializers.CharField(source='farmer.user_profile.district.name', read_only=True)
    region_name = serializers.CharField(source='farmer.user_profile.district.region.name', read_only=True)
    
    class Meta:
        model = Farm
        fields = '__all__'
class FarmCreateSerializer(serializers.ModelSerializer):
    boundary_coordinates = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        write_only=True,
        required=False
    )
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    
    class Meta:
        model = Farm
        fields = [
            'farmer', 'name', 'area_hectares', 'soil_type', 'irrigation_type',
            'irrigation_coverage', 'boundary_coordinates', 'latitude', 'longitude',
            'altitude', 'slope'
        ]
    
    def create(self, validated_data):
        boundary_coordinates = validated_data.pop('boundary_coordinates', None)
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        
        polygon = None
        location = None
        
        # Create polygon from boundary coordinates if provided
        if boundary_coordinates and len(boundary_coordinates) >= 3:
            try:
                polygon = Polygon(boundary_coordinates)
            except Exception as e:
                # If polygon creation fails, continue without it
                print(f"Polygon creation error: {e}")
        
        # Create point from latitude/longitude if provided
        if latitude is not None and longitude is not None:
            try:
                location = Point(longitude, latitude)
            except Exception as e:
                print(f"Point creation error: {e}")
        
        # Initialize region and district codes
        region_code = "UN"
        district_code = "UN"
        
        # Try spatial queries only if we have a valid polygon
        if polygon:
            try:
                polygon_centroid = polygon.centroid
                
                # Find region - using safe approach
                region = Region.objects.filter(geom__isnull=False).first()
                if region:
                    region_code = region.code if region.code else "UN"
                
                # Find district - using safe approach  
                district_obj = District.objects.filter(geom__isnull=False).first()
                if district_obj:
                    district_code = district_obj.code if district_obj.code else "UN"
                    
            except Exception as e:
                print(f"Spatial query error: {e}")
                # Fallback: get from farmer's district
                try:
                    farmer_district = validated_data['farmer'].user_profile.district
                    if farmer_district:
                        district_code = farmer_district.code if farmer_district.code else "UN"
                        if farmer_district.region:
                            region_code = farmer_district.region.code if farmer_district.region.code else "UN"
                except Exception as farmer_error:
                    print(f"Farmer district fallback error: {farmer_error}")
        
        # Generate farm code
        farm_count = Farm.objects.count() + 1
        farm_code = f"ES-{region_code}-{district_code}-{farm_count:06d}"
        
        # Create farm
        farm_data = {
            'farm_code': farm_code,
            'boundary_coord': boundary_coordinates,
            **validated_data
        }
        
        # Add spatial fields only if they are valid
        if polygon:
            farm_data['boundary'] = polygon
            farm_data['geom'] = polygon
        if location:
            farm_data['location'] = location
        
        farm = Farm.objects.create(**farm_data)
        
        return farm

class MonitoringVisitSerializer(serializers.ModelSerializer):
    officer_name = serializers.CharField(source='officer.user.get_full_name', read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    farm_code = serializers.CharField(source='farm.farm_code', read_only=True)
    
    class Meta:
        model = MonitoringVisit
        fields = '__all__'

class MonitoringVisitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoringVisit
        fields = '__all__'
    
    def create(self, validated_data):
        # Generate visit ID
        visit_count = MonitoringVisit.objects.count() + 1
        visit_id = f"VISIT-{visit_count:06d}"
        
        monitoring_visit = MonitoringVisit.objects.create(
            visit_id=visit_id,
            **validated_data
        )
        
        return monitoring_visit

class FollowUpActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUpAction
        fields = '__all__'

class InfrastructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Infrastructure
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.user_profile.user.get_full_name', read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
    
    def create(self, validated_data):
        # Generate project code
        project_count = Project.objects.count() + 1
        project_code = f"PROJ-{project_count:06d}"
        
        project = Project.objects.create(
            code=project_code,
            **validated_data
        )
        
        return project

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'

class ComplianceCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceCheck
        fields = '__all__'