from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from leaflet.admin import LeafletGeoAdmin
from .models import *

class GeoAdmin(gis_admin.GISModelAdmin):
    default_lon = -1
    default_lat = 6
    default_zoom = 7

# Region Resource
class RegionResource(resources.ModelResource):
    class Meta:
        model = Region
        import_id_fields = ['reg_code']
        fields = ('id', 'region', 'reg_code', 'geom', 'created_at', 'updated_at')

# District Resource
class DistrictResource(resources.ModelResource):
   
    class Meta:
        model = District
        import_id_fields = ['district_code']
        fields = ('id', 'district', 'district_code', 'region', 'geom', 'created_at', 'updated_at')

# UserProfile Resource
class UserProfileResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )
    
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(District, 'district')
    )
    
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'role', 'phone_number', 'district', 'address', 'date_of_birth', 'gender', 'bank_account_number', 'bank_name')

# Staff Resource
class StaffResource(resources.ModelResource):
    user_profile = fields.Field(
        column_name='user_profile',
        attribute='user_profile',
        widget=ForeignKeyWidget(UserProfile, 'user__username')
    )
    
    class Meta:
        model = Staff
        import_id_fields = ['staff_id']
        fields = ('id', 'user_profile', 'staff_id', 'designation', 'date_joined', 'is_active')

# Farmer Resource
class FarmerResource(resources.ModelResource):
    user_profile = fields.Field(
        column_name='user_profile',
        attribute='user_profile',
        widget=ForeignKeyWidget(UserProfile, 'user__username')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(District, 'name')
    )
    
    class Meta:
        model = Farmer
        import_id_fields = ['national_id']
        fields = (
            'id', 'user_profile', 'national_id', 'years_of_experience', 
            'primary_crop', 'secondary_crops', 'cooperative_membership', 
            'extension_services', 'business_name', 'district', 'community',
            'crop_type', 'variety', 'planting_date', 'labour_hired',
            'estimated_yield', 'yield_in_pre_season', 'harvest_date'
        )

# Farm Resource
class FarmResource(resources.ModelResource):
    farmer = fields.Field(
        column_name='farmer',
        attribute='farmer',
        widget=ForeignKeyWidget(Farmer, 'national_id')
    )
    officer = fields.Field(
        column_name='officer',
        attribute='officer',
        widget=ForeignKeyWidget(Staff, 'staff_id')
    )
    
    class Meta:
        model = Farm
        import_id_fields = ['farm_code']
        fields = (
            'id', 'farmer', 'name', 'farm_code', 'area_hectares', 
            'soil_type', 'irrigation_type', 'irrigation_coverage', 'status',
            'registration_date', 'last_visit_date', 'validation_status',
            'location', 'boundary', 'altitude', 'slope', 'main_buyers',
            'land_use_classification', 'accessibility', 'service_provider',
            'farmer_groups_affiliated', 'value_chain_linkages', 'officer'
        )

# Project Resource
class ProjectResource(resources.ModelResource):
    manager = fields.Field(
        column_name='manager',
        attribute='manager',
        widget=ForeignKeyWidget(Staff, 'staff_id')
    )
    
    class Meta:
        model = Project
        import_id_fields = ['code']
        fields = ('id', 'name', 'code', 'description', 'start_date', 'end_date', 
                 'status', 'total_budget', 'manager')

# Admin Classes
# @admin.register(Region)
# class RegionAdmin(ImportExportModelAdmin):
#     resource_class = RegionResource
#     list_display = ('region', 'reg_code', 'created_at')
#     search_fields = ('region', 'reg_code')
#     list_filter = ('created_at',)

# @admin.register(District)
# class DistrictAdmin(ImportExportModelAdmin):
#     resource_class = DistrictResource
#     list_display = ('district', 'region', 'district_code','reg_code')
#     list_filter = ('region',)
#     search_fields = ('district', 'district_code')

# @admin.register(Region)
# class RegionAdmin(ImportExportModelAdmin):
#     resource_class = RegionResource
#     list_display = ('region', 'reg_code', 'created_at')
#     search_fields = ('region', 'reg_code')
#     list_filter = ('created_at',)
    
#     # Leaflet map settings for the geom field - customized for regions
#     settings_overrides = {
#         'DEFAULT_CENTER': (7.9465, -1.0232),  # Ghana coordinates
#         'DEFAULT_ZOOM': 6,  # Slightly more zoomed out for regions
#         'MIN_ZOOM': 1,
#         'MAX_ZOOM': 16,
#     }

# @admin.register(District)
# class DistrictAdmin(ImportExportModelAdmin):
#     resource_class = DistrictResource
#     list_display = ('district', 'region', 'district_code', 'reg_code')
#     list_filter = ('region',)
#     search_fields = ('district', 'district_code')
   
    
    
#     # Leaflet map settings for the geom field
#     settings_overrides = {
#         'DEFAULT_CENTER': (7.9465, -1.0232),  # Ghana coordinates
#         'DEFAULT_ZOOM': 7,
#         'MIN_ZOOM': 1,
#         'MAX_ZOOM': 18,
#     }


from django.contrib.gis import admin
from leaflet.admin import LeafletGeoAdmin
from import_export.admin import ImportExportModelAdmin

admin.site.register(versionTbl)

# Option 1: Use LeafletGeoAdmin as the base and add import-export functionality
@admin.register(Region)
class RegionAdmin(LeafletGeoAdmin, ImportExportModelAdmin):  # Change order
    resource_class = RegionResource
    list_display = ('region', 'reg_code', 'created_at')
    search_fields = ('region', 'reg_code')
    list_filter = ('created_at',)
    
    # Leaflet map settings for the geom field
    settings_overrides = {
        'DEFAULT_CENTER': (7.9465, -1.0232),  # Ghana coordinates
        'DEFAULT_ZOOM': 6,
        'MIN_ZOOM': 1,
        'MAX_ZOOM': 16,
    }

@admin.register(District)
class DistrictAdmin(LeafletGeoAdmin, ImportExportModelAdmin):  # Change order
    resource_class = DistrictResource
    list_display = ('district', 'region', 'district_code', 'reg_code')
    list_filter = ('region',)
    search_fields = ('district', 'district_code')
    # list_select_related = ['region']
    
    # def get_region_name(self, obj):
    #     return obj.region.region
    # get_region_name.short_description = 'Region'
    
    # Leaflet map settings for the geom field
    settings_overrides = {
        'DEFAULT_CENTER': (7.9465, -1.0232),  # Ghana coordinates
        'DEFAULT_ZOOM': 7,
        'MIN_ZOOM': 1,
        'MAX_ZOOM': 18,
    }



@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    resource_class = UserProfileResource
    list_display = ('user', 'role', 'phone_number', 'district')
    list_filter = ('role', 'district', 'gender')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')

@admin.register(Staff)
class StaffAdmin(ImportExportModelAdmin):
    resource_class = StaffResource
    list_display = ('staff_id', 'get_username', 'designation', 'date_joined', 'is_active')
    list_filter = ('designation', 'is_active', 'date_joined')
    search_fields = ('staff_id', 'user_profile__user__username', 'designation')
    filter_horizontal = ('assigned_districts',)
    
    def get_username(self, obj):
        return obj.user_profile.user.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user_profile__user__username'
@admin.register(Farmer)
class FarmerAdmin(ImportExportModelAdmin):
    resource_class = FarmerResource
    list_display = (
        'national_id', 'get_username', 'get_full_name', 'get_district', 
        'primary_crop', 'years_of_experience', 'extension_services', 
        'cooperative_membership', 'farms_count'
    )
    list_filter = (
        'primary_crop', 'extension_services', 'years_of_experience',
        'user_profile__district', 'cooperative_membership'  # Fix filter
    )
    search_fields = (
        'national_id', 'user_profile__user__username', 
        'user_profile__user__first_name', 'user_profile__user__last_name',
        'primary_crop', 'business_name', 'community',
        'user_profile__district__district'  # Add district search
    )
    list_select_related = ('user_profile__user', 'user_profile__district')
    readonly_fields = ('national_id', 'created_at', 'updated_at', 'farms_count', 'get_district')
    date_hierarchy = 'user_profile__user__date_joined'
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'user_profile', 'national_id', 'business_name'
            )
        }),
        ('Location Details', {
            'fields': (
                'get_district', 'community'  # Use get_district instead of district
            )
        }),
        ('Farming Information', {
            'fields': (
                'years_of_experience', 'primary_crop', 'secondary_crops',
                'crop_type', 'variety', 'extension_services'
            )
        }),
        ('Production Details', {
            'fields': (
                'planting_date', 'harvest_date', 'labour_hired',
                'estimated_yield', 'yield_in_pre_season'
            )
        }),
        ('Organizational Information', {
            'fields': (
                'cooperative_membership',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at', 'updated_at', 'farms_count'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_district(self, obj):
        """Display district from user profile"""
        if obj.user_profile and obj.user_profile.district:
            return obj.user_profile.district.district
        return "No district"
    get_district.short_description = 'District'
    get_district.admin_order_field = 'user_profile__district__district'
    
    def get_username(self, obj):
        """Display username"""
        if obj.user_profile and obj.user_profile.user:
            return obj.user_profile.user.username
        return "No username"
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user_profile__user__username'
    
    def get_full_name(self, obj):
        """Display full name"""
        if obj.user_profile and obj.user_profile.user:
            return f"{obj.user_profile.user.first_name} {obj.user_profile.user.last_name}"
        return "No name"
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user_profile__user__first_name'
    
    def farms_count(self, obj):
        """Display number of farms"""
        return obj.farms.count()
    farms_count.short_description = 'Farms Count'



  

@admin.register(Farm)
class FarmAdmin(LeafletGeoAdmin, ImportExportModelAdmin):
    resource_class = FarmResource
    list_display = (
        'farm_code', 'name', 'get_farmer_name', 'get_farmer_national_id',
        'status', 'area_hectares', 'validation_status', 'boundary_preview',
        'registration_date', 'last_visit_date'
    )
    list_filter = (
        'status', 'validation_status', 'soil_type', 'irrigation_type', 
        'registration_date'
    )
    search_fields = (
        'farm_code', 'name', 'farmer__user_profile__user__first_name',
        'farmer__user_profile__user__last_name', 'farmer__national_id'
    )
    readonly_fields = ('farm_code', 'registration_date', 'created_at', 'updated_at')
    date_hierarchy = 'registration_date'
    list_select_related = ('farmer__user_profile__user',)
    
    # Leaflet map settings
    settings_overrides = {
        'DEFAULT_CENTER': (7.9465, -1.0232),  # Ghana coordinates
        'DEFAULT_ZOOM': 7,
        'MIN_ZOOM': 11,
        'MAX_ZOOM': 16,
    }
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'farm_code', 'farmer', 'name', 'status',
                'registration_date', 'last_visit_date', 'validation_status'
            )
        }),
        ('Location Details', {
            'fields': (
                'location', 'boundary', 'geom',
                'area_hectares', 'soil_type', 'altitude', 'slope'
            ),
            'description': 'Click on the map to set location or draw boundary polygon'
        }),
        ('Irrigation & Infrastructure', {
            'fields': (
                'irrigation_type', 'irrigation_coverage',
                'land_use_classification', 'accessibility',
                'proximity_to_processing_plants'
            )
        }),
        ('Business & Organizational', {
            'fields': (
                'main_buyers', 'service_provider',
                'farmer_groups_affiliated', 'value_chain_linkages'
            )
        }),
        ('Field Visit Information', {
            'fields': (
                'officer', 'visit_date', 'observation',
                'issues_identified', 'infrastructure_identified',
                'recommended_actions', 'follow_up_actions'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_farmer_name(self, obj):
        return str(obj.farmer)
    get_farmer_name.short_description = 'Farmer Name'
    get_farmer_name.admin_order_field = 'farmer__user_profile__user__first_name'
    
    def get_farmer_national_id(self, obj):
        return obj.farmer.national_id
    get_farmer_national_id.short_description = 'Farmer ID'
    get_farmer_national_id.admin_order_field = 'farmer__national_id'
    
    def boundary_preview(self, obj):
        if obj.boundary:
            return f"✅ {obj.boundary.num_points} points ({obj.area_hectares or 'N/A'} ha)"
        return "❌ No boundary"
    boundary_preview.short_description = "Boundary"

    # Actions
    actions = ['validate_farms', 'mark_as_active']
    
    def validate_farms(self, request, queryset):
        updated = queryset.update(validation_status=True)
        self.message_user(request, f'{updated} farms validated successfully.')
    validate_farms.short_description = "Validate selected farms"
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} farms marked as active.')
    mark_as_active.short_description = "Mark selected farms as active"

@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    resource_class = ProjectResource
    list_display = ('name', 'code', 'start_date', 'end_date', 'status', 'total_budget', 'get_manager_name')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('name', 'code', 'description', 'manager__user_profile__user__first_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_manager_name(self, obj):
        return str(obj.manager) if obj.manager else "Not assigned"
    get_manager_name.short_description = 'Manager'

# Farm Inline for Farmer Admin
class FarmInline(admin.TabularInline):
    model = Farm
    extra = 0
    fields = ('farm_code', 'name', 'status', 'area_hectares', 'validation_status', 'registration_date')
    readonly_fields = ('farm_code', 'registration_date')
    can_delete = False
    show_change_link = True

# Add inline to FarmerAdmin
FarmerAdmin.inlines = [FarmInline]