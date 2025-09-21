from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from .models import *


class GeoAdmin(gis_admin.GISModelAdmin):
    default_lon = -1  # Default longitude
    default_lat = 6   # Default latitude (adjust for Ghana)
    default_zoom = 7  # Default zoom level
# Region Resource
class RegionResource(resources.ModelResource):
    class Meta:
        model = Region
        import_id_fields = ['code']
        fields = ('id', 'name', 'code', 'created_at', 'updated_at')

# District Resource
class DistrictResource(resources.ModelResource):
    region = fields.Field(
        column_name='region',
        attribute='region',
        widget=ForeignKeyWidget(Region, 'name')
    )
    
    class Meta:
        model = District
        import_id_fields = ['code']
        fields = ('id', 'name', 'code', 'region', 'created_at', 'updated_at')

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
        widget=ForeignKeyWidget(District, 'name')
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
    
    class Meta:
        model = Farmer
        import_id_fields = ['national_id']
        fields = ('id', 'user_profile', 'national_id', 'farm_size', 'years_of_experience', 'primary_crop', 'secondary_crops', 'cooperative_membership', 'extension_services')

# Farm Resource
class FarmResource(resources.ModelResource):
    farmer = fields.Field(
        column_name='farmer',
        attribute='farmer',
        widget=ForeignKeyWidget(Farmer, 'national_id')
    )
    
    class Meta:
        model = Farm
        import_id_fields = ['farm_code']
        fields = ('id', 'farmer', 'name', 'farm_code', 'area_hectares', 'soil_type', 'irrigation_type', 'irrigation_coverage', 'status', 'registration_date')

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
        fields = ('id', 'name', 'code', 'description', 'start_date', 'end_date', 'status', 'total_budget', 'manager')

# Loan Resource
class LoanResource(resources.ModelResource):
    farmer = fields.Field(
        column_name='farmer',
        attribute='farmer',
        widget=ForeignKeyWidget(Farmer, 'national_id')
    )
    
    project = fields.Field(
        column_name='project',
        attribute='project',
        widget=ForeignKeyWidget(Project, 'code')
    )
    
    class Meta:
        model = Loan
        import_id_fields = ['loan_id']
        fields = ('id', 'farmer', 'project', 'loan_id', 'amount', 'purpose', 'application_date', 'approval_date', 'interest_rate', 'term_months', 'status', 'collateral_details')

# MangoVariety Resource
class MangoVarietyResource(resources.ModelResource):
    class Meta:
        model = MangoVariety
        fields = ('id', 'name', 'scientific_name', 'description', 'maturity_period', 'yield_potential')

# FarmCrop Resource
class FarmCropResource(resources.ModelResource):
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(Farm, 'farm_code')
    )
    
    variety = fields.Field(
        column_name='variety',
        attribute='variety',
        widget=ForeignKeyWidget(MangoVariety, 'name')
    )
    
    class Meta:
        model = FarmCrop
        fields = ('id', 'farm', 'variety', 'planting_date', 'planting_density', 'total_trees', 'expected_yield')

# FarmInput Resource
class FarmInputResource(resources.ModelResource):
    class Meta:
        model = FarmInput
        fields = ('id', 'name', 'type', 'description', 'unit', 'unit_cost')

# InputDistribution Resource
class InputDistributionResource(resources.ModelResource):
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(Farm, 'farm_code')
    )
    
    input_item = fields.Field(
        column_name='input_item',
        attribute='input_item',
        widget=ForeignKeyWidget(FarmInput, 'name')
    )
    
    distributed_by = fields.Field(
        column_name='distributed_by',
        attribute='distributed_by',
        widget=ForeignKeyWidget(Staff, 'staff_id')
    )
    
    class Meta:
        model = InputDistribution
        fields = ('id', 'farm', 'input_item', 'quantity', 'distribution_date', 'distributed_by', 'notes')

# FarmVisit Resource
class FarmVisitResource(resources.ModelResource):
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(Farm, 'farm_code')
    )
    
    conducted_by = fields.Field(
        column_name='conducted_by',
        attribute='conducted_by',
        widget=ForeignKeyWidget(Staff, 'staff_id')
    )
    
    class Meta:
        model = FarmVisit
        fields = ('id', 'farm', 'visit_date', 'conducted_by', 'purpose', 'observations', 'recommendations', 'next_visit_date', 'latitude', 'longitude', 'accuracy')

# Tree Resource
class TreeResource(resources.ModelResource):
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(Farm, 'farm_code')
    )
    
    variety = fields.Field(
        column_name='variety',
        attribute='variety',
        widget=ForeignKeyWidget(MangoVariety, 'name')
    )
    
    class Meta:
        model = Tree
        import_id_fields = ['tree_id']
        fields = ('id', 'farm', 'tree_id', 'variety', 'planting_date', 'status', 'height', 'circumference', 'age')

# Harvest Resource
class HarvestResource(resources.ModelResource):
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(Farm, 'farm_code')
    )
    
    variety = fields.Field(
        column_name='variety',
        attribute='variety',
        widget=ForeignKeyWidget(MangoVariety, 'name')
    )
    
    recorded_by = fields.Field(
        column_name='recorded_by',
        attribute='recorded_by',
        widget=ForeignKeyWidget(Staff, 'staff_id')
    )
    
    class Meta:
        model = Harvest
        fields = ('id', 'farm', 'harvest_date', 'variety', 'quantity', 'quality_grade', 'recorded_by', 'notes')

# Sale Resource
class SaleResource(resources.ModelResource):
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(Farm, 'farm_code')
    )
    
    recorded_by = fields.Field(
        column_name='recorded_by',
        attribute='recorded_by',
        widget=ForeignKeyWidget(Staff, 'staff_id')
    )
    
    class Meta:
        model = Sale
        fields = ('id', 'farm', 'sale_date', 'buyer', 'quantity', 'price_per_kg', 'total_amount', 'recorded_by', 'notes')

# Admin Classes
@admin.register(Region)
class RegionAdmin(ImportExportModelAdmin):
    resource_class = RegionResource
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('created_at',)

@admin.register(District)
class DistrictAdmin(ImportExportModelAdmin):
    resource_class = DistrictResource
    list_display = ('name', 'region', 'code')
    list_filter = ('region',)
    search_fields = ('name', 'code', 'region__name')

@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    resource_class = UserProfileResource
    list_display = ('user', 'role', 'phone_number', 'district')
    list_filter = ('role', 'district', 'gender')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')

@admin.register(Staff)
class StaffAdmin(ImportExportModelAdmin):
    resource_class = StaffResource
    list_display = ('staff_id', 'user_profile', 'designation', 'date_joined', 'is_active')
    list_filter = ('designation', 'is_active', 'date_joined')
    search_fields = ('staff_id', 'user_profile__user__username', 'designation')
    filter_horizontal = ('assigned_districts',)

@admin.register(Farmer)
class FarmerAdmin(ImportExportModelAdmin):
    resource_class = FarmerResource
    list_display = ('national_id', 'user_profile', 'farm_size', 'primary_crop', 'extension_services')
    list_filter = ('primary_crop', 'extension_services', 'years_of_experience')
    search_fields = ('national_id', 'user_profile__user__username', 'primary_crop')

@admin.register(Farm)
class FarmAdmin(GeoAdmin, ImportExportModelAdmin):
    resource_class = FarmResource
    list_display = ('name', 'farm_code', 'farmer', 'area_hectares', 'status', 'registration_date')
    list_filter = ('status', 'soil_type', 'irrigation_type', 'registration_date')
    search_fields = ('name', 'farm_code', 'farmer__national_id')
    readonly_fields = ('farm_code',)

@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    resource_class = ProjectResource
    list_display = ('name', 'code', 'start_date', 'end_date', 'status', 'total_budget')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('name', 'code', 'description')
    # filter_horizontal = ('participating_farmers',)

@admin.register(ProjectParticipation)
class ProjectParticipationAdmin(ImportExportModelAdmin):
    list_display = ('farmer', 'project', 'enrollment_date', 'status')
    list_filter = ('status', 'enrollment_date')
    search_fields = ('farmer__national_id', 'project__name')

@admin.register(Loan)
class LoanAdmin(ImportExportModelAdmin):
    resource_class = LoanResource
    list_display = ('loan_id', 'farmer', 'amount', 'status', 'application_date', 'approval_date')
    list_filter = ('status', 'application_date', 'approval_date')
    search_fields = ('loan_id', 'farmer__national_id', 'purpose')
    readonly_fields = ('loan_id',)

@admin.register(LoanDisbursement)
class LoanDisbursementAdmin(ImportExportModelAdmin):
    list_display = ('loan', 'amount', 'disbursement_date', 'stage')
    list_filter = ('disbursement_date', 'stage')
    search_fields = ('loan__loan_id', 'transaction_reference')

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(ImportExportModelAdmin):
    list_display = ('loan', 'amount', 'repayment_date')
    list_filter = ('repayment_date',)
    search_fields = ('loan__loan_id', 'transaction_reference')

@admin.register(MangoVariety)
class MangoVarietyAdmin(ImportExportModelAdmin):
    resource_class = MangoVarietyResource
    list_display = ('name', 'scientific_name', 'maturity_period', 'yield_potential')
    search_fields = ('name', 'scientific_name')

@admin.register(FarmCrop)
class FarmCropAdmin(ImportExportModelAdmin):
    resource_class = FarmCropResource
    list_display = ('farm', 'variety', 'planting_date', 'total_trees', 'expected_yield')
    list_filter = ('variety', 'planting_date')
    search_fields = ('farm__farm_code', 'variety__name')

@admin.register(FarmInput)
class FarmInputAdmin(ImportExportModelAdmin):
    resource_class = FarmInputResource
    list_display = ('name', 'type', 'unit', 'unit_cost')
    list_filter = ('type',)
    search_fields = ('name', 'type')

@admin.register(InputDistribution)
class InputDistributionAdmin(ImportExportModelAdmin):
    resource_class = InputDistributionResource
    list_display = ('farm', 'input_item', 'quantity', 'distribution_date')
    list_filter = ('distribution_date', 'input_item__type')
    search_fields = ('farm__farm_code', 'input_item__name')

@admin.register(FarmVisit)
class FarmVisitAdmin(ImportExportModelAdmin):
    resource_class = FarmVisitResource
    list_display = ('farm', 'visit_date', 'conducted_by', 'purpose')
    list_filter = ('visit_date', 'conducted_by')
    search_fields = ('farm__farm_code', 'purpose', 'conducted_by__staff_id')

@admin.register(FarmPhoto)
class FarmPhotoAdmin(ImportExportModelAdmin):
    list_display = ('farm', 'photo_type', 'taken_at')
    list_filter = ('photo_type', 'taken_at')
    search_fields = ('farm__farm_code', 'caption')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 200px; max-width: 200px;" />'
        return "No image"
    image_preview.allow_tags = True

@admin.register(Tree)
class TreeAdmin(GeoAdmin, ImportExportModelAdmin):
    resource_class = TreeResource
    list_display = ('tree_id', 'farm', 'variety', 'planting_date', 'status')
    list_filter = ('status', 'variety', 'planting_date')
    search_fields = ('tree_id', 'farm__farm_code', 'variety__name')
    readonly_fields = ('tree_id',)

@admin.register(TreeMonitoring)
class TreeMonitoringAdmin(ImportExportModelAdmin):
    list_display = ('tree', 'monitor_date', 'status', 'monitored_by')
    list_filter = ('monitor_date', 'status')
    search_fields = ('tree__tree_id', 'monitored_by__staff_id')

@admin.register(Harvest)
class HarvestAdmin(ImportExportModelAdmin):
    resource_class = HarvestResource
    list_display = ('farm', 'harvest_date', 'variety', 'quantity', 'quality_grade')
    list_filter = ('harvest_date', 'quality_grade', 'variety')
    search_fields = ('farm__farm_code', 'variety__name')

@admin.register(Sale)
class SaleAdmin(ImportExportModelAdmin):
    resource_class = SaleResource
    list_display = ('farm', 'sale_date', 'buyer', 'quantity', 'total_amount')
    list_filter = ('sale_date',)
    search_fields = ('farm__farm_code', 'buyer')

@admin.register(SatelliteImage)
class SatelliteImageAdmin(ImportExportModelAdmin):
    list_display = ('farm', 'image_date', 'image_type', 'ndvi_value')
    list_filter = ('image_date', 'image_type')
    search_fields = ('farm__farm_code', 'source')

@admin.register(DroneImage)
class DroneImageAdmin(ImportExportModelAdmin):
    list_display = ('farm', 'flight_date', 'image_type', 'operator')
    list_filter = ('flight_date', 'image_type')
    search_fields = ('farm__farm_code', 'operator__staff_id')

@admin.register(SensorData)
class SensorDataAdmin(ImportExportModelAdmin):
    list_display = ('farm', 'sensor_type', 'value', 'unit', 'recorded_at')
    list_filter = ('sensor_type', 'recorded_at')
    search_fields = ('farm__farm_code', 'sensor_id')

@admin.register(Notification)
class NotificationAdmin(ImportExportModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'sent_at', 'read')
    list_filter = ('notification_type', 'sent_at', 'read')
    search_fields = ('recipient__user__username', 'title', 'message')

@admin.register(MessageTemplate)
class MessageTemplateAdmin(ImportExportModelAdmin):
    list_display = ('name', 'message_type', 'is_active')
    list_filter = ('message_type', 'is_active')
    search_fields = ('name', 'subject')

@admin.register(AuditLog)
class AuditLogAdmin(ImportExportModelAdmin):
    list_display = ('user', 'action_type', 'model_name', 'timestamp')
    list_filter = ('action_type', 'model_name', 'timestamp')
    search_fields = ('user__username', 'model_name', 'object_id')
    readonly_fields = ('user', 'action_type', 'model_name', 'object_id', 'details', 'timestamp')

@admin.register(SystemSetting)
class SystemSettingAdmin(ImportExportModelAdmin):
    list_display = ('key', 'value', 'is_public', 'updated_at')
    list_filter = ('is_public',)
    search_fields = ('key', 'description')

@admin.register(DataExport)
class DataExportAdmin(ImportExportModelAdmin):
    list_display = ('requested_by', 'export_format', 'model_name', 'status', 'requested_at')
    list_filter = ('export_format', 'status', 'requested_at')
    search_fields = ('requested_by__username', 'model_name')
    readonly_fields = ('requested_by', 'requested_at', 'completed_at', 'status')