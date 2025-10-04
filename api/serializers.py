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

class DistrictSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    class Meta:
        model = District
        fields = ['id', 'name', 'code', 'region_name']

class UserProfileSerializer(serializers.ModelSerializer):
    district_details = DistrictSerializer(source='district', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'phone_number', 'profile_picture', 'district', 'district_details', 
                 'address', 'date_of_birth', 'gender', 'bank_account_number', 'bank_name']

class StaffLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class StaffSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(read_only=True)
    assigned_districts_details = DistrictSerializer(source='assigned_districts', many=True, read_only=True)
    
    class Meta:
        model = Staff
        fields = ['id', 'user_profile', 'staff_id', 'designation', 'date_joined', 
                 'assigned_districts', 'assigned_districts_details', 'is_active']



##############################################################################################################
class FarmerSerializer(serializers.ModelSerializer):
    # Instead of full UserProfileSerializer, just include needed fields
    district_name = serializers.CharField(source='user_profile.district.name', read_only=True)
    region_name = serializers.CharField(source='user_profile.district.region.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='user_profile.phone_number', read_only=True)
    email = serializers.CharField(source='user_profile.user.email', read_only=True)
    username = serializers.CharField(source='user_profile.user.username', read_only=True)
    
    class Meta:
        model = Farmer
        fields = [
            'id', 'national_id', 'farm_size', 'years_of_experience',
            'primary_crop', 'secondary_crops', 'cooperative_membership', 
            'extension_services', 'district_name', 'region_name', 'full_name',
            'phone_number', 'email', 'username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['national_id', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.user_profile.user.get_full_name()
    



class FarmerCreateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True, max_length=30)
    last_name = serializers.CharField(write_only=True, max_length=30)
    phone_number = serializers.CharField(write_only=True, max_length=15)
    district_name = serializers.CharField(write_only=True)  # Change from district_id
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Farmer
        fields = [
            'first_name', 'last_name', 'phone_number', 'district_name', 'email',
            'national_id', 'farm_size', 'years_of_experience', 'primary_crop',
            'secondary_crops', 'cooperative_membership', 'extension_services'
        ]
    
    def validate_district_name(self, value):
        """Validate district exists by name"""
        if not District.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("District does not exist.")
        return value
    
    def create(self, validated_data):
        try:
            # Extract user data
            first_name = validated_data.pop('first_name')
            last_name = validated_data.pop('last_name')
            phone_number = validated_data.pop('phone_number')
            district_name = validated_data.pop('district_name')  # Get district name
            email = validated_data.pop('email', None)
            
            # Get district by name
            district = District.objects.get(name__iexact=district_name)
            
            # ... rest of create method remains the same
            # Generate email if not provided
            if not email:
                base_email = f"{first_name.lower()}.{last_name.lower()}@farmer.com"
                counter = 1
                email = base_email
                while User.objects.filter(email=email).exists():
                    email = f"{first_name.lower()}.{last_name.lower()}{counter}@farmer.com"
                    counter += 1
            
            # Generate username
            username = f"farmer_{phone_number}"
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1
            
            password = "P@ssw0rd24"  # Default password
            
            # Create User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create UserProfile
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
            
        except District.DoesNotExist:
            raise serializers.ValidationError("District not found.")
        except Exception as e:
            if 'user' in locals():
                user.delete()
            raise serializers.ValidationError(f"Error creating farmer: {str(e)}") 
        


        
######################################################################################################

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
                # Ensure the polygon is closed (first and last points are the same)
                if boundary_coordinates[0] != boundary_coordinates[-1]:
                    boundary_coordinates.append(boundary_coordinates[0])
                
                polygon = Polygon(boundary_coordinates)
            except Exception as e:
                print(f"Polygon creation error: {e}")
                # You might want to raise a validation error here
                raise serializers.ValidationError(f"Invalid boundary coordinates: {str(e)}")
        
        # Create point from latitude/longitude if provided
        if latitude is not None and longitude is not None:
            try:
                location = Point(longitude, latitude, srid=4326)
            except Exception as e:
                print(f"Point creation error: {e}")
                # You might want to raise a validation error here
                raise serializers.ValidationError(f"Invalid coordinates: {str(e)}")
        
        # Initialize region and district codes
        region_code = "UN"
        district_code = "UN"
        
        # Try spatial queries only if we have a valid polygon or location
        spatial_point = None
        if polygon:
            spatial_point = polygon.centroid
        elif location:
            spatial_point = location
        
        if spatial_point:
            try:
                # Find district containing the point
                district_obj = District.objects.filter(
                    geom__isnull=False,
                    geom__contains=spatial_point
                ).first()
                
                if district_obj:
                    district_code = district_obj.code if district_obj.code else "UN"
                    # Get region from district
                    if district_obj.region:
                        region_code = district_obj.region.code if district_obj.region.code else "UN"
                
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
        else:
            # No spatial data, use farmer's district
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
        
        # Create farm with ALL spatial data
        farm_data = {
            'farm_code': farm_code,
            **validated_data
        }
        
        # Save boundary coordinates to boundary_coord field
        if boundary_coordinates:
            farm_data['boundary_coord'] = boundary_coordinates
        
        # Add spatial fields only if they are valid
        if polygon:
            farm_data['boundary'] = polygon
            farm_data['geom'] = polygon  # Save to both boundary and geom fields
        
        if location:
            farm_data['location'] = location
        
        farm = Farm.objects.create(**farm_data)
        
        return farm
    
################################################################################################################################



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