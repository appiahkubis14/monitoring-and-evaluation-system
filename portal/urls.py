from django.urls import path
from portal.auth_views import dashboard_view
from portal.views.farmer import *
from portal.views.farms import *
from portal.views.project import *
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name="account/login.html"), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),


    # Farmer management main page
    path('farmers/',farmer_management, name='farmer_management'),
    
    # Farmer CRUD operations
    path('farmers/list/',farmer_list, name='farmer_list'),
    path('farmers/create/',create_farmer, name='create_farmer'),
    path('farmers/update/<int:farmer_id>/',update_farmer, name='update_farmer'),
    path('farmers/delete/',delete_farmer, name='delete_farmer'),
    path('farmers/detail/<int:farmer_id>/',get_farmer_detail, name='get_farmer_detail'),
    path('farmers/geojson/<int:farmer_id>/',farmer_get_farm_geojson, name='get_farm_geojson'),
    
    # Utilities
    path('farmers/districts/',get_districts, name='get_districts'),
    path('farmers/export/',farmer_export, name='farmer_export'),



     # Farm management main page
    path('farmers/farms/', farm_management, name='farm_management'),

    # Farm CRUD operations
    path('farmers/farms/list/', farm_list, name='farm_list'),
    path('farmers/farms/create/', create_farm, name='create_farm'),
    path('farmers/farms/update/<int:farm_id>/', update_farm, name='update_farm'),
    path('farmers/farms/delete/', delete_farm, name='delete_farm'),
    path('farmers/farms/detail/<int:farm_id>/', get_farm_detail, name='get_farm_detail'),
    path('farmers/farms/geojson/<int:farm_id>/', farrm_get_farm_geojson, name='get_farm_geojson'),
    path('farmers/farms/geojson/all/', get_all_farms_geojson, name='get_all_farms_geojson'),
    
    # Farm statistics and utilities
    path('farmers/farms/stats/', get_farm_stats, name='get_farm_stats'),
    path('farmers/farms/export/', farm_export, name='farm_export'),
    path('farmers/farms/varieties/', get_mango_varieties, name='get_mango_varieties'),
    path('farmers/farms/<int:farm_id>/add-crop/', add_farm_crop, name='add_farm_crop'),


    # Project tracking main pages
    path('projects/', project_tracking, name='project_tracking'),
    path('projects/milestones/', milestones_page, name='project_milestones'),
    path('projects/timeline/', timeline_page, name='project_timeline'),
    path('projects/compliance/', project_tracking, name='project_compliance'),
    path('projects/reports/', project_tracking, name='project_reports'),
    
    # Project CRUD operations
    path('projects/list/', project_list, name='project_list'),
    path('projects/create/', create_project, name='create_project'),
    path('projects/update/<int:project_id>/', update_project, name='update_project'),
    path('projects/delete/', delete_project, name='delete_project'),
    path('projects/detail/<int:project_id>/', get_project_detail, name='get_project_detail'),
    
    # Project participation management
    path('projects/<int:project_id>/add-farmer/', add_farmer_to_project, name='add_farmer_to_project'),
    path('projects/participation/update/<int:participation_id>/', update_project_participation, name='update_project_participation'),
    
    # Project data and utilities
    path('projects/timeline/data/', get_project_timeline, name='get_project_timeline'),
    path('projects/stats/', get_project_stats, name='get_project_stats'),
    path('projects/export/', project_export, name='project_export'),
    path('projects/staff/', get_staff_members, name='get_staff_members'),
    path('projects/<int:project_id>/available-farmers/', get_available_farmers, name='get_available_farmers'),
    
    # Milestones and compliance
    path('projects/<int:project_id>/milestones/', get_milestones, name='get_milestones'),
    path('projects/<int:project_id>/compliance/', get_compliance_data, name='get_compliance_data'),

      path('projects/<int:project_id>/milestones/create/', create_milestone, name='create_milestone'),
    path('projects/milestones/update/<int:milestone_id>/', update_milestone, name='update_milestone'),
    
    # Compliance management
    path('projects/<int:project_id>/compliance-checks/create/', create_compliance_check, name='create_compliance_check'),
    
    # Category management
    path('compliance/categories/', get_compliance_categories, name='get_compliance_categories'),




    #########################################################################################################

    # Milestones URLs
    # path('projects/milestones/page/', views.milestones_page, name='milestones_page'),
    path('projects/milestones/data/', milestones_data, name='milestones_data'),
    path('projects/milestones/summary/', milestones_summary, name='milestones_summary'),
    path('projects/milestones/create/', create_milestone, name='create_milestone'),
    path('projects/milestones/update/<int:milestone_id>/', update_milestone, name='update_milestone'),
    path('projects/milestones/delete/', delete_milestone, name='delete_milestone'),
    path('projects/milestones/<int:milestone_id>/detail/', milestone_detail, name='milestone_detail'),

   # Timeline URLs
path('projects/timeline/page/', timeline_page, name='timeline_page'),
path('projects/timeline/data/', timeline_data, name='timeline_data'),
path('projects/timeline/summary/', timeline_summary, name='timeline_summary')

]
