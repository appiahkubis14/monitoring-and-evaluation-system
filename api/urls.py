from django.urls import path
from . import views
from django.contrib import admin 
from django.contrib.auth.views import LogoutView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
import json
# app_name = 'API'

schema_view = get_schema_view(
   openapi.Info(
      title="EXIM Ghana Monitoring and Evaluation System APIs",
      default_version='v1',
      description="API documentation for the Monitoring and Evaluation System",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@monitoringandevaluation.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    #version control
    
    path('v1/version/', views.versionTblView.as_view()),

    # Authentication
    path('v1/staff/login/', views.StaffLoginAPIView.as_view(), name='staff-login'),

      path('v1/regions/', views.RegionAPIView.as_view(), name='regions-list'),
      path('v1/districts/', views.DistrictAPIView.as_view(), name='districts-list'),
    
    # Farmers
    path('v1/farmers/<str:district>/', views.FarmerAPIView.as_view(), name='farmers-by-district'),
    path('v1/farmers/', views.FarmerAPIView.as_view(), name='create-farmer'),

    # Farms
    path('v1/farms/<str:district>/', views.FarmAPIView.as_view(), name='farms-by-district'),
    path('v1/farms/', views.FarmAPIView.as_view(), name='create-farm'),

    # Monitoring Visits
    path('v1/monitoring-visits/<str:district>/', views.MonitoringVisitAPIView.as_view(), name='monitoring-visits-by-district'),
    path('v1/monitoring-visits/', views.MonitoringVisitAPIView.as_view(), name='create-monitoring-visit'),

    # Follow-up Actions
    path('v1/follow-up-actions/', views.FollowUpActionAPIView.as_view(), name='create-follow-up-action'),

    # Infrastructure
    path('v1/infrastructure/', views.InfrastructureAPIView.as_view(), name='create-infrastructure'),
    
    # Projects
    path('v1/projects/', views.ProjectAPIView.as_view(), name='projects'),
    path('v1/projects/<str:district>/', views.ProjectAPIView.as_view(), name='projects-by-district'),

    # Milestones
    path('v1/milestones/<int:project_id>/', views.MilestoneAPIView.as_view(), name='milestones-by-project'),
    path('v1/milestones/', views.MilestoneAPIView.as_view(), name='create-milestone'),

    # Compliance Checks
    path('v1/compliance-checks/<int:project_id>/', views.ComplianceCheckAPIView.as_view(), name='compliance-checks-by-project'),
    path('v1/compliance-checks/', views.ComplianceCheckAPIView.as_view(), name='create-compliance-check'),

    # Documentation
    path('v1/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('v1/swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('v1/version/', views.versionTblView.as_view()),
]