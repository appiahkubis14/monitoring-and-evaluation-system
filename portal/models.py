from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from datetime import date
import uuid
from django.contrib.gis.db.models import GeometryField




# Custom managers for soft delete functionality
class TimeStampManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super(TimeStampManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.alive_only:
            return TimeStampQuerySet(self.model).filter(is_deleted=False)
        return TimeStampQuerySet(self.model)

    def hard_delete(self):
        return self.get_queryset().hard_delete()

class TimeStampQuerySet(models.QuerySet):
    def delete(self):
        return self.update(is_deleted=True)
    
    def hard_delete(self):
        return super(TimeStampQuerySet, self).delete()
    
    def alive(self):
        return self.filter(is_deleted=False)
    
    def dead(self):
        return self.filter(is_deleted=True)

class TimeStampModel(models.Model):
    """
    Abstract base model with timestamp and soft delete functionality
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='%(class)s_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='%(class)s_modified')
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='%(class)s_deleted')
    
    objects = TimeStampManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
    
    def hard_delete(self, *args, **kwargs):
        super(TimeStampModel, self).delete(*args, **kwargs)



class versionTbl(TimeStampModel):
 version = models.IntegerField(blank=True, null=True)


# Region and District Models
class Region(TimeStampModel):
    name = models.CharField(max_length=250, unique=True)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    geom = GeometryField(blank=True, null=True, srid=4326)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Region"
        verbose_name_plural = "Regions"

class District(TimeStampModel):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=250)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    geom = GeometryField(blank=True, null=True, srid=4326)
    
    def __str__(self):
        return f"{self.name} ({self.region.name})"
    

class societyTble(models.Model):
    soceity = models.CharField(max_length=250, unique=True)
    soceity_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    
    
    class Meta:
        verbose_name = "Society"
        verbose_name_plural = "Societies"
        # unique_together = ('district', 'soceity')

# User Profile and Staff Models
class UserProfile(TimeStampModel):
    USER_ROLES = (
        ('admin', 'Admin'),
        ('project_manager', 'Project Manager'),
        ('field_officer', 'Field Officer'),
        ('farmer', 'Farmer'),
        ('stakeholder', 'Stakeholder'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=USER_ROLES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=(('male', 'Male'), ('female', 'Female'), ('other', 'Other')), blank=True, null=True)
    
    # For farmers
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

class Staff(TimeStampModel):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='staff_profile')
    staff_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    date_joined = models.DateField(default=timezone.now)
    assigned_districts = models.ManyToManyField(District, related_name='assigned_staff', blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} - {self.designation}"
    
    class Meta:
        verbose_name = "Staff"
        verbose_name_plural = "Staff"

# Farmer and Farm Models
class Farmer(TimeStampModel):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='farmer_profile')
    national_id = models.CharField(max_length=50, unique=True)
    farm_size = models.FloatField(help_text="Farm size in hectares")
    years_of_experience = models.IntegerField(default=0)
    primary_crop = models.CharField(max_length=100, default="Mango")
    secondary_crops = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    cooperative_membership = models.CharField(max_length=200, blank=True, null=True)
    extension_services = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} - {self.national_id}"
    
    class Meta:
        verbose_name = "Farmer"
        verbose_name_plural = "Farmers"
    
    def save(self, *args, **kwargs):
        if not self.national_id:
            # Generate national ID if not provided
            count = Farmer.objects.count() + 1
            district_code = self.user_profile.district.code if self.user_profile.district and self.user_profile.district.code else "DF"
            self.national_id = f"MNG{district_code}{count:04d}"
        super().save(*args, **kwargs)



class Farm(TimeStampModel):
    FARM_STATUS = (
        ('active', 'Active'),
        ('delayed', 'Delayed'),
        ('critical', 'Critical'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    )
    
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='farms')
    name = models.CharField(max_length=200, blank=True, null=True)
    farm_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    location = gis_models.PointField(geography=True, srid=4326, blank=True, null=True)
    boundary = gis_models.PolygonField(geography=True, srid=4326, blank=True, null=True)
    area_hectares = models.FloatField(validators=[MinValueValidator(0.1)], blank=True, null=True)
    soil_type = models.CharField(max_length=100, blank=True, null=True)
    irrigation_type = models.CharField(max_length=100, blank=True, null=True)
    irrigation_coverage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    status = models.CharField(max_length=20, choices=FARM_STATUS, default='active')
    registration_date = models.DateField(default=timezone.now)
    last_visit_date = models.DateField(blank=True, null=True)
    boundary_coord = ArrayField(ArrayField(models.FloatField()), blank=True, null=True)
    geom = GeometryField(blank=True, null=True, srid=4326)
    validation_status = models.BooleanField(default=False)
    
    # Geo-referencing details
    altitude = models.FloatField(blank=True, null=True)
    slope = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.farm_code}"
    
    class Meta:
        verbose_name = "Farm"
        verbose_name_plural = "Farms"
    
    # def save(self, *args, **kwargs):
    #     if not self.farm_code:
    #         # Generate farm code if not provided
    #         count = Farm.objects.count() + 1
    #         farmer_code = self.farmer.national_id[-4:] if self.farmer.national_id else "0000"
    #         self.farm_code = f"{farmer_code}F{count:02d}"
    #     super().save(*args, **kwargs)
        


class MonitoringVisit(models.Model):
    # Basic Visit Information
    visit_id = models.CharField(max_length=50, unique=True, verbose_name="Visit ID / Reference Number")
    date_of_visit = models.DateField(verbose_name="Date of Visit")
    officer = models.ForeignKey(UserProfile, on_delete=models.PROTECT, verbose_name="Officer Name & ID")
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, verbose_name="Farm Name & ID")
    
    # Farm Information
    farm_boundary_polygon = models.BooleanField(choices=[(True, 'Yes'), (False, 'No')], verbose_name="Farm Boundary Polygon (Yes/No)")
    land_use_classification = models.CharField(max_length=100, verbose_name="Land Use Classification",help_text="Classification of land use (e.g., agricultural, residential, commercial)")
    
    # Accessibility Information
    distance_to_road = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)],verbose_name="Distance to Road (km)",help_text="Distance in kilometers")
    distance_to_market = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)],verbose_name="Distance to Market (km)",help_text="Distance in kilometers")
    proximity_to_processing_facility = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)],verbose_name="Proximity to Processing Facility (km)",help_text="Distance in kilometers"
    )
    
    # Business Relationships
    main_buyers = models.TextField(
        verbose_name="Main Buyers",
        help_text="List of main buyers for the farm products"
    )
    service_provider = models.CharField(
        max_length=200, 
        verbose_name="Service Provider",
        help_text="Primary service provider for the farm"
    )
    cooperatives_affiliated = models.TextField(
        verbose_name="Cooperatives or Farmer Groups Affiliated",
        help_text="List of cooperatives or farmer groups the farm is affiliated with"
    )
    value_chain_linkages = models.TextField(
        verbose_name="Value Chain Linkages",
        help_text="Description of value chain linkages"
    )
    
    # Observations and Assessment
    observations = models.TextField(verbose_name="Observations")
    issues_identified = models.TextField(verbose_name="Issues Identified")
    infrastructure_identified = models.TextField(verbose_name="Infrastructure Identified")
    
    # Recommendations and Follow-up
    recommended_actions = models.TextField(verbose_name="Recommended Actions")
    
    FOLLOW_UP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    follow_up_status = models.CharField(
        max_length=20,
        choices=FOLLOW_UP_STATUS_CHOICES,
        default='pending',
        verbose_name="Follow-Up Status"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Monitoring Visit"
        verbose_name_plural = "Monitoring Visits"
        ordering = ['-date_of_visit', 'visit_id']
    
    def __str__(self):
        return f"{self.visit_id} - {self.date_of_visit}"

class FollowUpAction(models.Model):
    """Optional model for tracking detailed follow-up actions"""
    monitoring_visit = models.ForeignKey(MonitoringVisit, on_delete=models.CASCADE, related_name='follow_up_actions')
    action_description = models.TextField(verbose_name="Action Description")
    responsible_person = models.CharField(max_length=100, verbose_name="Responsible Person")
    deadline = models.DateField(verbose_name="Deadline")
    status = models.CharField(
        max_length=20,
        choices=MonitoringVisit.FOLLOW_UP_STATUS_CHOICES,
        default='pending'
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Follow-Up Action"
        verbose_name_plural = "Follow-Up Actions"
        ordering = ['deadline']
    
    def __str__(self):
        return f"Action for {self.monitoring_visit.visit_id} - {self.responsible_person}"

class Infrastructure(models.Model):
    """Optional model for detailed infrastructure tracking"""
    monitoring_visit = models.ForeignKey(MonitoringVisit, on_delete=models.CASCADE, related_name='infrastructure_details')
    infrastructure_type = models.CharField(max_length=100, verbose_name="Infrastructure Type")
    description = models.TextField(verbose_name="Description")
    condition = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('non_functional', 'Non-Functional'),
        ],
        verbose_name="Condition"
    )
    
    class Meta:
        verbose_name = "Infrastructure Detail"
        verbose_name_plural = "Infrastructure Details"
    
    def __str__(self):
        return f"{self.infrastructure_type} - {self.condition}"



# Project and Loan Management Models
class Project(TimeStampModel):
    PROJECT_STATUS = (
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended'),
    )
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=PROJECT_STATUS, default='planning')
    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    manager = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True, related_name='managed_projects')
    participating_farmers = models.ManyToManyField(Farmer, through='ProjectParticipation', related_name='projects')
    
    def __str__(self):
        return f"{self.name} - {self.code}"
    
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"

class ProjectParticipation(TimeStampModel):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    enrollment_date = models.DateField(default=timezone.now)
    exit_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=(
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
        ('suspended', 'Suspended'),
    ), default='active')
    
    class Meta:
        verbose_name = "Project Participation"
        verbose_name_plural = "Project Participations"
        unique_together = ('farmer', 'project')

class Loan(TimeStampModel):
    LOAN_STATUS = (
        ('applied', 'Applied'),
        ('approved', 'Approved'),
        ('disbursed', 'Disbursed'),
        ('repaying', 'Repaying'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    )
    
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='loans')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='loans', blank=True, null=True)
    loan_id = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    application_date = models.DateField(default=timezone.now)
    approval_date = models.DateField(blank=True, null=True)
    disbursement_date = models.DateField(blank=True, null=True)
    interest_rate = models.FloatField(validators=[MinValueValidator(0)])
    term_months = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='applied')
    collateral_details = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Loan {self.loan_id} - {self.farmer}"
    
    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
    
    def save(self, *args, **kwargs):
        if not self.loan_id:
            # Generate loan ID if not provided
            count = Loan.objects.count() + 1
            farmer_code = self.farmer.national_id[-4:] if self.farmer.national_id else "0000"
            self.loan_id = f"LN{farmer_code}{count:04d}"
        super().save(*args, **kwargs)


class LoanDisbursement(TimeStampModel):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='disbursements')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    disbursement_date = models.DateField()
    stage = models.CharField(max_length=100, help_text="Project stage when disbursed")
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    disbursed_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Disbursement {self.id} - {self.loan}"
    
    class Meta:
        verbose_name = "Loan Disbursement"
        verbose_name_plural = "Loan Disbursements"

class LoanRepayment(TimeStampModel):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    repayment_date = models.DateField()
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    received_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Repayment {self.id} - {self.loan}"
    
    class Meta:
        verbose_name = "Loan Repayment"
        verbose_name_plural = "Loan Repayments"



# Add these models to your portal/models.py file

class Milestone(TimeStampModel):
    """Model for project milestones"""
    MILESTONE_STATUS = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    )
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    completion_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=MILESTONE_STATUS, default='pending')
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                help_text="Weight of this milestone in overall project progress (0-100)")
    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True, 
                                         related_name='dependent_milestones')
    assigned_to = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.project.code}"
    
    class Meta:
        verbose_name = "Milestone"
        verbose_name_plural = "Milestones"
        ordering = ['due_date']
    
    def save(self, *args, **kwargs):
        # Auto-set completion date if status is completed
        if self.status == 'completed' and not self.completion_date:
            self.completion_date = timezone.now().date()
        super().save(*args, **kwargs)

class ComplianceCategory(TimeStampModel):
    """Model for compliance categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                help_text="Weight of this category in overall compliance score (0-100)")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Compliance Category"
        verbose_name_plural = "Compliance Categories"
        ordering = ['name']

class ComplianceCheck(TimeStampModel):
    """Model for compliance checks"""
    COMPLIANCE_STATUS = (
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('na', 'Not Applicable'),
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='compliance_checks')
    category = models.ForeignKey(ComplianceCategory, on_delete=models.CASCADE, related_name='checks')
    name = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    completion_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=COMPLIANCE_STATUS, default='pending')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    assigned_to = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    evidence_required = models.BooleanField(default=False)
    evidence_description = models.TextField(blank=True, null=True)
    auto_check = models.BooleanField(default=False,
                                   help_text="Whether this check can be automatically verified")
    check_frequency = models.CharField(max_length=20, choices=(
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ), default='once')
    
    def __str__(self):
        return f"{self.name} - {self.project.code}"
    
    class Meta:
        verbose_name = "Compliance Check"
        verbose_name_plural = "Compliance Checks"
        ordering = ['due_date']
    
    def save(self, *args, **kwargs):
        # Auto-set completion date if status is passed/failed
        if self.status in ['passed', 'failed'] and not self.completion_date:
            self.completion_date = timezone.now().date()
        super().save(*args, **kwargs)


        # Get compliance check statistics

# Farm Management Models
class MangoVariety(TimeStampModel):
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    maturity_period = models.IntegerField(help_text="Months to maturity")
    yield_potential = models.FloatField(help_text="Tons per hectare")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Mango Variety"
        verbose_name_plural = "Mango Varieties"

class FarmCrop(TimeStampModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='crops')
    variety = models.ForeignKey(MangoVariety, on_delete=models.CASCADE)
    planting_date = models.DateField()
    planting_density = models.IntegerField(help_text="Trees per hectare")
    total_trees = models.IntegerField()
    expected_yield = models.FloatField(help_text="Expected yield in tons per hectare")
    
    def __str__(self):
        return f"{self.variety.name} at {self.farm.name}"
    
    class Meta:
        verbose_name = "Farm Crop"
        verbose_name_plural = "Farm Crops"

class FarmInput(TimeStampModel):
    INPUT_TYPES = (
        ('fertilizer', 'Fertilizer'),
        ('pesticide', 'Pesticide'),
        ('herbicide', 'Herbicide'),
        ('equipment', 'Equipment'),
        ('seedling', 'Seedling'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=INPUT_TYPES)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=20)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        verbose_name = "Farm Input"
        verbose_name_plural = "Farm Inputs"

class InputDistribution(TimeStampModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='input_distributions')
    input_item = models.ForeignKey(FarmInput, on_delete=models.CASCADE)
    quantity = models.FloatField()
    distribution_date = models.DateField()
    distributed_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.input_item.name} to {self.farm.name}"
    
    class Meta:
        verbose_name = "Input Distribution"
        verbose_name_plural = "Input Distributions"

# Monitoring and Data Collection Models
class FarmVisit(TimeStampModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='visits')
    visit_date = models.DateField()
    conducted_by = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='conducted_visits')
    purpose = models.CharField(max_length=200)
    observations = models.TextField()
    recommendations = models.TextField(blank=True, null=True)
    next_visit_date = models.DateField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    accuracy = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return f"Visit to {self.farm.name} on {self.visit_date}"
    
    class Meta:
        verbose_name = "Farm Visit"
        verbose_name_plural = "Farm Visits"
        ordering = ['-visit_date']

class FarmPhoto(TimeStampModel):
    PHOTO_TYPES = (
        ('general', 'General'),
        ('crop', 'Crop'),
        ('pest', 'Pest/Disease'),
        ('infrastructure', 'Infrastructure'),
        ('document', 'Document'),
    )
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='photos')
    visit = models.ForeignKey(FarmVisit, on_delete=models.CASCADE, related_name='photos', blank=True, null=True)
    photo_type = models.CharField(max_length=20, choices=PHOTO_TYPES, default='general')
    image = models.ImageField(upload_to='farm_photos/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    taken_at = models.DateTimeField(default=timezone.now)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return f"Photo of {self.farm.name} - {self.get_photo_type_display()}"
    
    class Meta:
        verbose_name = "Farm Photo"
        verbose_name_plural = "Farm Photos"

class Tree(TimeStampModel):
    TREE_STATUS = (
        ('healthy', 'Healthy'),
        ('stressed', 'Stressed'),
        ('diseased', 'Diseased'),
        ('dead', 'Dead'),
    )
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='trees')
    tree_id = models.CharField(max_length=50, unique=True)
    variety = models.ForeignKey(MangoVariety, on_delete=models.CASCADE)
    planting_date = models.DateField()
    location = gis_models.PointField(geography=True, srid=4326, blank=True, null=True)
    status = models.CharField(max_length=20, choices=TREE_STATUS, default='healthy')
    height = models.FloatField(help_text="Height in meters", blank=True, null=True)
    circumference = models.FloatField(help_text="Circumference in cm", blank=True, null=True)
    age = models.IntegerField(help_text="Age in years", blank=True, null=True)
    
    def __str__(self):
        return f"Tree {self.tree_id} at {self.farm.name}"
    
    class Meta:
        verbose_name = "Tree"
        verbose_name_plural = "Trees"
    
    def save(self, *args, **kwargs):
        if not self.tree_id:
            # Generate tree ID if not provided
            count = Tree.objects.filter(farm=self.farm).count() + 1
            farm_code = self.farm.farm_code
            self.tree_id = f"{farm_code}T{count:04d}"
        super().save(*args, **kwargs)

class TreeMonitoring(TimeStampModel):
    tree = models.ForeignKey(Tree, on_delete=models.CASCADE, related_name='monitoring_records')
    monitor_date = models.DateField()
    monitored_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Tree.TREE_STATUS)
    height = models.FloatField(help_text="Height in meters", blank=True, null=True)
    circumference = models.FloatField(help_text="Circumference in cm", blank=True, null=True)
    health_observations = models.TextField(blank=True, null=True)
    pest_disease_observations = models.TextField(blank=True, null=True)
    treatment_applied = models.TextField(blank=True, null=True)
    ndvi_value = models.FloatField(blank=True, null=True, help_text="Normalized Difference Vegetation Index")
    
    def __str__(self):
        return f"Monitoring of {self.tree.tree_id} on {self.monitor_date}"
    
    class Meta:
        verbose_name = "Tree Monitoring"
        verbose_name_plural = "Tree Monitoring Records"
        ordering = ['-monitor_date']

class Harvest(TimeStampModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='harvests')
    harvest_date = models.DateField()
    variety = models.ForeignKey(MangoVariety, on_delete=models.CASCADE)
    quantity = models.FloatField(help_text="Quantity in kilograms")
    quality_grade = models.CharField(max_length=20, choices=(
        ('grade_a', 'Grade A'),
        ('grade_b', 'Grade B'),
        ('grade_c', 'Grade C'),
    ))
    recorded_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Harvest at {self.farm.name} on {self.harvest_date}"
    
    class Meta:
        verbose_name = "Harvest"
        verbose_name_plural = "Harvests"
        ordering = ['-harvest_date']

class Sale(TimeStampModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='sales')
    sale_date = models.DateField()
    buyer = models.CharField(max_length=200)
    quantity = models.FloatField(help_text="Quantity in kilograms")
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Sale from {self.farm.name} on {self.sale_date}"
    
    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ['-sale_date']
    
    def save(self, *args, **kwargs):
        # Calculate total amount if not provided
        if not self.total_amount and self.quantity and self.price_per_kg:
            self.total_amount = self.quantity * self.price_per_kg
        super().save(*args, **kwargs)

# Remote Sensing and IoT Models
class SatelliteImage(TimeStampModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='satellite_images')
    image_date = models.DateField()
    image_type = models.CharField(max_length=50)
    ndvi_value = models.FloatField(blank=True, null=True)
    evi_value = models.FloatField(blank=True, null=True)
    image_file = models.FileField(upload_to='satellite_images/', blank=True, null=True)
    cloud_cover = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Satellite image for {self.farm.name} on {self.image_date}"
    
    class Meta:
        verbose_name = "Satellite Image"
        verbose_name_plural = "Satellite Images"

class DroneImage(TimeStampModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='drone_images')
    flight_date = models.DateField()
    image_type = models.CharField(max_length=50)
    resolution = models.CharField(max_length=20, blank=True, null=True)
    image_file = models.FileField(upload_to='drone_images/')
    flight_altitude = models.FloatField(blank=True, null=True)
    operator = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True)
    
    def __str__(self):
        return f"Drone image for {self.farm.name} on {self.flight_date}"
    
    class Meta:
        verbose_name = "Drone Image"
        verbose_name_plural = "Drone Images"

class SensorData(TimeStampModel):
    SENSOR_TYPES = (
        ('soil_moisture', 'Soil Moisture'),
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity'),
        ('rainfall', 'Rainfall'),
        ('soil_ph', 'Soil pH'),
    )
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='sensor_data')
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES)
    value = models.FloatField()
    unit = models.CharField(max_length=10)
    recorded_at = models.DateTimeField()
    sensor_id = models.CharField(max_length=50, blank=True, null=True)
    location = gis_models.PointField(geography=True, srid=4326, blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_sensor_type_display()} data for {self.farm.name} at {self.recorded_at}"
    
    class Meta:
        verbose_name = "Sensor Data"
        verbose_name_plural = "Sensor Data"
        ordering = ['-recorded_at']

# Communication and Notification Models
class Notification(TimeStampModel):
    NOTIFICATION_TYPES = (
        ('loan_disbursement', 'Loan Disbursement'),
        ('repayment_reminder', 'Repayment Reminder'),
        ('visit_schedule', 'Visit Schedule'),
        ('alert', 'Alert'),
        ('extension', 'Extension Service'),
        ('weather', 'Weather Advisory'),
        ('pest', 'Pest Alert'),
    )
    
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    related_object_id = models.CharField(max_length=100, blank=True, null=True)
    related_content_type = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.recipient}"
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-sent_at']

class MessageTemplate(TimeStampModel):
    MESSAGE_TYPES = (
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
    )
    
    name = models.CharField(max_length=100)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    subject = models.CharField(max_length=200, blank=True, null=True)
    body = models.TextField()
    variables = models.TextField(help_text="Comma-separated list of variables that can be used in the template", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_message_type_display()})"
    
    class Meta:
        verbose_name = "Message Template"
        verbose_name_plural = "Message Templates"

# System Administration Models
class AuditLog(TimeStampModel):
    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.action_type} on {self.model_name} by {self.user}"
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']

class SystemSetting(TimeStampModel):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    
    def __str__(self):
        return self.key
    
    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

class DataExport(TimeStampModel):
    EXPORT_FORMATS = (
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF'),
        ('shapefile', 'Shapefile'),
    )
    
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    model_name = models.CharField(max_length=100)
    filters = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='data_exports/', blank=True, null=True)
    requested_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=(
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ), default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Export of {self.model_name} by {self.requested_by}"
    
    class Meta:
        verbose_name = "Data Export"
        verbose_name_plural = "Data Exports"
        ordering = ['-requested_at']



##########################################################################################################
#Base Data Models

# Tree Density Data Model
class TreeDensityData(TimeStampModel):
    DENSITY_LEVELS = (
        ('high', 'High'),
        ('medium', 'Medium'), 
        ('low', 'Low'),
    )
    
    location = gis_models.PointField(geography=True, srid=4326)
    density = models.CharField(max_length=10, choices=DENSITY_LEVELS)
    trees_per_hectare = models.IntegerField()
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    recorded_date = models.DateField(default=timezone.now)
    source = models.CharField(max_length=100, blank=True, null=True)
    accuracy = models.FloatField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Tree Density Data"
        verbose_name_plural = "Tree Density Data"

# Crop Health Data Model (NDVI)
class CropHealthData(TimeStampModel):
    HEALTH_LEVELS = (
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'), 
        ('poor', 'Poor'),
    )
    
    location = gis_models.PointField(geography=True, srid=4326)
    ndvi = models.FloatField(validators=[MinValueValidator(-1), MaxValueValidator(1)])
    health = models.CharField(max_length=10, choices=HEALTH_LEVELS)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    recorded_date = models.DateField(default=timezone.now)
    source = models.CharField(max_length=100, blank=True, null=True)
    farm = models.ForeignKey(Farm, on_delete=models.SET_NULL, blank=True, null=True)
    
    class Meta:
        verbose_name = "Crop Health Data"
        verbose_name_plural = "Crop Health Data"

# Irrigation Sources Model
class IrrigationSource(TimeStampModel):
    SOURCE_TYPES = (
        ('river_pump', 'River Pump'),
        ('well', 'Well'),
        ('reservoir', 'Reservoir'),
        ('canal', 'Canal'),
        ('borehole', 'Borehole'),
        ('municipal', 'Municipal'),
    )
    
    CAPACITY_LEVELS = (
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )
    
    location = gis_models.PointField(geography=True, srid=4326)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    capacity = models.CharField(max_length=10, choices=CAPACITY_LEVELS)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, blank=True, null=True)
    operational_status = models.BooleanField(default=True)
    installation_date = models.DateField(blank=True, null=True)
    coverage_area = models.FloatField(help_text="Coverage area in hectares", blank=True, null=True)
    
    class Meta:
        verbose_name = "Irrigation Source"
        verbose_name_plural = "Irrigation Sources"

# Soil Type Model
class SoilTypeArea(TimeStampModel):
    FERTILITY_LEVELS = (
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    )
    
    boundary = gis_models.PolygonField(geography=True, srid=4326)
    soil_type = models.CharField(max_length=100)
    fertility = models.CharField(max_length=10, choices=FERTILITY_LEVELS)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    area_hectares = models.FloatField(blank=True, null=True)
    ph_level = models.FloatField(blank=True, null=True)
    organic_matter = models.FloatField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Soil Type Area"
        verbose_name_plural = "Soil Type Areas"

# Climate Zone Model
class ClimateZone(TimeStampModel):
    RAINFALL_LEVELS = (
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    boundary = gis_models.PolygonField(geography=True, srid=4326)
    zone_name = models.CharField(max_length=100)
    rainfall = models.CharField(max_length=10, choices=RAINFALL_LEVELS)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    avg_temperature = models.FloatField(blank=True, null=True)
    avg_rainfall = models.FloatField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Climate Zone"
        verbose_name_plural = "Climate Zones"

# Road Network Model
class RoadNetwork(TimeStampModel):
    ROAD_TYPES = (
        ('primary_highway', 'Primary Highway'),
        ('secondary_road', 'Secondary Road'),
        ('local_road', 'Local Road'),
        ('rural_track', 'Rural Track'),
    )
    
    CONDITION_LEVELS = (
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('very_poor', 'Very Poor'),
    )
    
    path = gis_models.LineStringField(geography=True, srid=4326)
    road_type = models.CharField(max_length=20, choices=ROAD_TYPES)
    condition = models.CharField(max_length=10, choices=CONDITION_LEVELS)
    name = models.CharField(max_length=200, blank=True, null=True)
    length_km = models.FloatField(blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, blank=True, null=True)
    
    class Meta:
        verbose_name = "Road Network"
        verbose_name_plural = "Road Networks"