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
from django.utils import timezone

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
    # User profile related fields
    first_name = serializers.CharField(source='user_profile.user.first_name', read_only=True)
    last_name = serializers.CharField(source='user_profile.user.last_name', read_only=True)
    email = serializers.CharField(source='user_profile.user.email', read_only=True)
    phone_number = serializers.CharField(source='user_profile.phone_number', read_only=True)
    gender = serializers.CharField(source='user_profile.gender', read_only=True)
    date_of_birth = serializers.DateField(source='user_profile.date_of_birth', read_only=True)
    address = serializers.CharField(source='user_profile.address', read_only=True)
    bank_account_number = serializers.CharField(source='user_profile.bank_account_number', read_only=True)
    bank_name = serializers.CharField(source='user_profile.bank_name', read_only=True)
    
    # Location fields
    district_name = serializers.CharField(source='user_profile.district.name', read_only=True)
    region_name = serializers.CharField(source='user_profile.district.region.name', read_only=True)
    
    class Meta:
        model = Farmer
        fields = [
            'id', 'national_id', 'years_of_experience', 'primary_crop', 
            'secondary_crops', 'cooperative_membership', 'extension_services',
            'business_name', 'community', 'crop_type', 'variety', 'planting_date',
            'labour_hired', 'estimated_yield', 'yield_in_pre_season', 'harvest_date',
            'first_name', 'last_name', 'email', 'phone_number', 'gender', 
            'date_of_birth', 'address', 'bank_account_number', 'bank_name',
            'district_name', 'region_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class FarmerCreateSerializer(serializers.ModelSerializer):
    # User data
    first_name = serializers.CharField(write_only=True, max_length=30)
    last_name = serializers.CharField(write_only=True, max_length=30)
    phone_number = serializers.CharField(write_only=True, max_length=15)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    district_name = serializers.CharField(write_only=True)
    
    # User profile optional fields
    gender = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    date_of_birth = serializers.DateField(write_only=True, required=False, allow_null=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    bank_account_number = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=50)
    bank_name = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=100)
    
    class Meta:
        model = Farmer
        fields = [
            # User data
            'first_name', 'last_name', 'phone_number', 'email', 'district_name',
            # User profile data
            'gender', 'date_of_birth', 'address', 'bank_account_number', 'bank_name',
            # Farmer data
            'national_id', 'years_of_experience', 'primary_crop', 'secondary_crops',
            'cooperative_membership', 'extension_services', 'business_name',
            'community', 'crop_type', 'variety', 'planting_date', 'labour_hired',
            'estimated_yield', 'yield_in_pre_season', 'harvest_date'
        ]
    
    def validate_district_name(self, value):
        """Validate district exists by name"""
        if not District.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("District does not exist.")
        return value
    
    def create(self, validated_data):
        try:
            # Extract user data
            user_data = {
                'first_name': validated_data.pop('first_name'),
                'last_name': validated_data.pop('last_name'),
                'phone_number': validated_data.pop('phone_number'),
                'district_name': validated_data.pop('district_name'),
                'email': validated_data.pop('email', None),
            }
            
            # Extract user profile optional data
            profile_data = {
                'gender': validated_data.pop('gender', ''),
                'date_of_birth': validated_data.pop('date_of_birth', None),
                'address': validated_data.pop('address', ''),
                'bank_account_number': validated_data.pop('bank_account_number', ''),
                'bank_name': validated_data.pop('bank_name', ''),
            }
            
            # Get district by name
            district = District.objects.get(name__iexact=user_data['district_name'])
            
            # Generate email if not provided
            email = user_data['email']
            if not email:
                base_email = f"{user_data['first_name'].lower()}.{user_data['last_name'].lower()}@farmer.com"
                counter = 1
                email = base_email
                while User.objects.filter(email=email).exists():
                    email = f"{user_data['first_name'].lower()}.{user_data['last_name'].lower()}{counter}@farmer.com"
                    counter += 1
            
            # Generate username
            username = f"farmer_{user_data['phone_number']}"
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
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            
            # Create UserProfile with all fields
            user_profile = UserProfile.objects.create(
                user=user,
                role='farmer',
                phone_number=user_data['phone_number'],
                district=district,
                gender=profile_data['gender'] or None,
                date_of_birth=profile_data['date_of_birth'],
                address=profile_data['address'] or None,
                bank_account_number=profile_data['bank_account_number'] or None,
                bank_name=profile_data['bank_name'] or None
            )
            
            # Create Farmer with all new fields
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

from django.utils.dateparse import parse_date, parse_datetime
        
######################################################################################################
class FarmSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='farmer.user_profile.user.get_full_name', read_only=True)
    farmer_national_id = serializers.CharField(source='farmer.national_id', read_only=True)
    district_name = serializers.CharField(source='farmer.user_profile.district.name', read_only=True)
    region_name = serializers.CharField(source='farmer.user_profile.district.region.name', read_only=True)
    officer_name = serializers.CharField(source='officer.user_profile.user.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    visit_date = serializers.DateField(write_only=True, required=False, allow_null=True)
    last_visit_date = serializers.DateField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Location fields for display
    boundary_coordinates = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    
    class Meta:
        model = Farm
        fields = [
            'id', 'farmer', 'farmer_name', 'farmer_national_id', 'name', 'farm_code',
            'project', 'project_name', 'main_buyers', 'land_use_classification',
            'has_farm_boundary_polygon', 'accessibility', 'proximity_to_processing_plants',
            'service_provider', 'farmer_groups_affiliated', 'value_chain_linkages',
            'visit_id', 'visit_date', 'officer', 'officer_name', 'observation',
            'issues_identified', 'infrastructure_identified', 'recommended_actions',
            'follow_up_actions', 'area_hectares', 'soil_type', 'irrigation_type',
            'irrigation_coverage', 'boundary_coordinates', 'latitude', 'longitude',
            'altitude', 'slope', 'district_name', 'region_name', 'status',
            'registration_date', 'last_visit_date', 'validation_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_boundary_coordinates(self, obj):
        return obj.boundary_coord if obj.boundary_coord else None
    
    def get_latitude(self, obj):
        return obj.location.y if obj.location else None
    
    def get_longitude(self, obj):
        return obj.location.x if obj.location else None


class DateFieldWithDatetimeSupport(serializers.DateField):
    """Custom DateField that safely handles datetime strings"""
    
    def to_internal_value(self, value):
        if isinstance(value, str):
            # Handle datetime strings by extracting date part
            if 'T' in value:
                try:
                    # Extract date part from ISO datetime string
                    value = value.split('T')[0]
                except (IndexError, AttributeError):
                    pass
            # Also handle datetime strings with space separator
            elif ' ' in value:
                try:
                    value = value.split(' ')[0]
                except (IndexError, AttributeError):
                    pass
        
        return super().to_internal_value(value)


class FarmCreateSerializer(serializers.ModelSerializer):
    boundary_coordinates = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        write_only=True,
        required=False
    )
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    
    # Use custom date fields that handle datetime strings
    visit_date = DateFieldWithDatetimeSupport(write_only=True, required=False)
    last_visit_date = DateFieldWithDatetimeSupport(write_only=True, required=False)
    
    class Meta:
        model = Farm
        fields = [
            'farmer', 'name', 'project', 'main_buyers', 'land_use_classification',
            'accessibility', 'proximity_to_processing_plants', 'service_provider',
            'farmer_groups_affiliated', 'value_chain_linkages', 'visit_id',
            'visit_date', 'officer', 'observation', 'issues_identified',
            'infrastructure_identified', 'recommended_actions', 'follow_up_actions',
            'area_hectares', 'soil_type', 'irrigation_type', 'irrigation_coverage',
            'boundary_coordinates', 'latitude', 'longitude', 'altitude', 'slope',
            'status', 'last_visit_date', 'validation_status'
        ]

        def to_internal_value(self, data):
            """Handle datetime to date conversion before any validation"""
            data = data.copy()
            
            # Handle visit_date conversion
            if 'visit_date' in data and data['visit_date']:
                data['visit_date'] = self._convert_to_date_string(data['visit_date'])
            
            # Handle last_visit_date conversion
            if 'last_visit_date' in data and data['last_visit_date']:
                data['last_visit_date'] = self._convert_to_date_string(data['last_visit_date'])
            
            return super().to_internal_value(data)
        
        def _convert_to_date_string(self, value):
            """Convert various date/datetime formats to date string"""
            if isinstance(value, str):
                # Try parsing as datetime first
                parsed_datetime = parse_datetime(value)
                if parsed_datetime:
                    return parsed_datetime.date().isoformat()
                
                # Try parsing as date
                parsed_date = parse_date(value)
                if parsed_date:
                    return value  # Already a valid date string
                
                # Handle common datetime string formats manually
                if 'T' in value:
                    return value.split('T')[0]
                elif ' ' in value:
                    return value.split(' ')[0]
            
            return value

     # Keep all your existing validate methods the same...
    def validate_visit_date(self, value):
        """Ensure visit date is not in the future"""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Visit date cannot be in the future.")
        return value
    
    def validate_last_visit_date(self, value):
        """Ensure last visit date is not in the future"""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Last visit date cannot be in the future.")
        return value
    
    def validate(self, data):
        """Additional validation for date logic"""
        # Ensure last_visit_date is after visit_date if both provided
        if data.get('last_visit_date') and data.get('visit_date'):
            if data['last_visit_date'] < data['visit_date']:
                raise serializers.ValidationError("Last visit date cannot be before visit date.")
        
        return data
    
    def validate_farmer(self, value):
        """Validate farmer exists and is not deleted"""
        if value.is_deleted:
            raise serializers.ValidationError("Farmer does not exist.")
        return value
    
    def validate_project(self, value):
        """Validate project exists and is not deleted"""
        if value and value.is_deleted:
            raise serializers.ValidationError("Project does not exist.")
        return value
    
    def validate_officer(self, value):
        """Validate officer exists and is not deleted"""
        if value and value.is_deleted:
            raise serializers.ValidationError("Officer does not exist.")
        return value
    
    def validate_area_hectares(self, value):
        """Validate area is at least 0.1 hectares"""
        if value and value < 0.1:
            raise serializers.ValidationError("Area must be at least 0.1 hectares.")
        return value
    
    def validate_irrigation_coverage(self, value):
        """Validate irrigation coverage is between 0 and 100"""
        if value and (value < 0 or value > 100):
            raise serializers.ValidationError("Irrigation coverage must be between 0 and 100.")
        return value
    
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
                # Update has_farm_boundary_polygon field
                validated_data['has_farm_boundary_polygon'] = True
            except Exception as e:
                raise serializers.ValidationError(f"Invalid boundary coordinates: {str(e)}")
        
        # Create point from latitude/longitude if provided
        if latitude is not None and longitude is not None:
            try:
                location = Point(longitude, latitude, srid=4326)
            except Exception as e:
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
            farm_data['geom'] = polygon
        
        if location:
            farm_data['location'] = location
        
        farm = Farm.objects.create(**farm_data)
        
        return farm
################################################################################################################################

class ProjectSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.user_profile.user.get_full_name', read_only=True)
    total_farmers = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'code', 'description', 'start_date', 'end_date',
            'status', 'total_budget', 'manager', 'manager_name', 'total_farmers',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_farmers(self, obj):
        return obj.participating_farmers.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'name', 'code', 'description', 'start_date', 'end_date',
            'status', 'total_budget', 'manager'
        ]
    
    def validate_code(self, value):
        """Validate project code is unique"""
        if Project.objects.filter(code=value).exists():
            raise serializers.ValidationError("Project code already exists.")
        return value
    
    def validate(self, data):
        """Validate date logic"""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data


####################################################################################################################

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

# class ProjectSerializer(serializers.ModelSerializer):
#     manager_name = serializers.CharField(source='manager.user_profile.user.get_full_name', read_only=True)
    
#     class Meta:
#         model = Project
#         fields = '__all__'

# class ProjectCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Project
#         fields = '__all__'
    
#     def create(self, validated_data):
#         # Generate project code
#         project_count = Project.objects.count() + 1
#         project_code = f"PROJ-{project_count:06d}"
        
#         project = Project.objects.create(
#             code=project_code,
#             **validated_data
#         )
        
#         return project

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'

class ComplianceCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceCheck
        fields = '__all__'