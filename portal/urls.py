from django.urls import path
from portal.auth_views import dashboard_view
from portal.views.farmer import *
from portal.views.farms import *
from portal.views.project import *
from portal.views.loans import *
from portal.views.dashboard import *
from portal.views.monitoring import *
from portal.views.map import *
from portal.views.base_data import *
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', landing_page, name='dashboard'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name="account/login.html"), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),



    #dashboard

    path('dashboard/overview/', monitoring_dashboard, name='monitoring_dashboard'),
   
    path('api/performance-analysis/', performance_analysis_api, name='performance_analysis_api'),
    path('api/projects/', project_list, name='project_list'),
    path('api/farmers/', farmer_list, name='farmer_list'),
    path('api/loans/', loan_management, name='loan_management'),
    # path('compliance/', compliance_checks, name='compliance_checks'),
    # path('reports/', generate_reports, name='generate_reports'),
    # path('export/', export_data, name='export_data'),

    # Farmer management main page
    path('farmers/',farmer_management, name='farmer_management'),
    
    # Farmer CRUD operations
    path('farmers/list/',farmer_list, name='farmer_list'),
    path('farmers/create/',create_farmer, name='create_farmer'),
    path('farmer/create/', create_farmers, name='create_farmers'),
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
    path('farmers/farm/create/', create_farms, name='create_farms'),
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
    path('projects/staff/', get_staff_members_project, name='get_staff_members'),
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
    path('projects/timeline/summary/', timeline_summary, name='timeline_summary'),


    ###################################################################################################################

    path('loans/applications/', loan_management, name='loan_applications'),
    
    # Loan CRUD operations
    path('loans/applications/list/', loan_list, name='loan_list'),
    path('loans/applications/create/', create_loan, name='create_loan'),
    path('loans/applications/update/<int:loan_id>/', update_loan, name='update_loan'),
    path('loans/applications/delete/', delete_loan, name='delete_loan'),
    path('loans/applications/detail/<int:loan_id>/', get_loan_detail, name='get_loan_detail'),

    # Loan approval/rejection
    path('loans/applications/approve/<int:loan_id>/', approve_loan, name='approve_loan'),
    path('loans/applications/disburse/<int:loan_id>/', disburse_loan, name='disburse_loan'),
    path('loans/applications/reject/<int:loan_id>/', reject_loan, name='reject_loan'),
    
    # Loan data and utilities
    path('loans/applications/stats/', get_loan_stats, name='get_loan_stats'),
    path('loans/applications/export/', loan_export, name='loan_export'),
    path('loans/applications/available-farmers/', get_available_farmers_for_loan, name='get_available_farmers_for_loan'),
    path('loans/applications/active-projects/', get_active_projects, name='get_active_projects'),



    ##################################################################################################################

    # Loan Disbursement URLs
    path('loans/disbursements/',disbursement_list_page, name='disbursement_list_page'),
    path('loans/disbursements/data/',disbursement_list, name='disbursement_list'),
    path('loans/disbursements/detail/<int:disbursement_id>/',disbursement_detail, name='disbursement_detail'),
    path('loans/disbursements/loan-options/',get_loans_with_disbursements, name='get_loans_with_disbursements'),


    ##################################################################################################################

    path('loans/repayments/', repayment_tracking, name='repayment_tracking'),
    
    # Repayment CRUD operations
    path('repayments/list/', repayment_list, name='repayment_list'),
    path('repayments/create/', create_repayment, name='create_repayment'),
    path('repayments/update/<int:repayment_id>/', update_repayment, name='update_repayment'),
    path('repayments/delete/', delete_repayment, name='delete_repayment'),
    path('repayments/detail/<int:repayment_id>/', get_repayment_detail, name='get_repayment_detail'),
    
    # Repayment data and utilities
    path('repayments/stats/', get_repayment_stats, name='get_repayment_stats'),
    path('repayments/export/', repayment_export, name='repayment_export'),
    path('repayments/repayable-loans/', get_repayable_loans, name='get_repayable_loans'),

    ##################################################################################################################
    path('monitoring/', render_monitoring_page, name='render_monitoring_page'),
    path('visits/', monitoring_visit_list, name='monitoring_visit_list'),
    path('visits/create/', create_monitoring_visit, name='create_monitoring_visit'),
    path('visits/detail/<int:visit_id>/', monitoring_visit_detail, name='monitoring_visit_detail'),
    path('visits/update/<int:visit_id>/', update_monitoring_visit, name='update_monitoring_visit'),
    path('visits/delete/<int:visit_id>/', delete_monitoring_visit, name='delete_monitoring_visit'),
    path('visits/export/', export_monitoring_visits, name='export_monitoring_visits'),
    
    # AJAX URLs
    path('ajax/get-farms/', get_available_farms, name='get_available_farms'),
    path('ajax/get-officers/', get_available_officers, name='get_available_officers'),
    
    # Follow-up Actions URLs
    path('visits/<int:visit_id>/follow-up/', create_follow_up_action, name='create_follow_up_action'),
    path('follow-up/<int:action_id>/update/', update_follow_up_action, name='update_follow_up_action'),

    ################################################################################################################

    path('map/', interactive_map, name='interactive_map'),
    path('map/data/', get_farm_data, name='get_farm_data'),
    path('map/farm/<int:farm_id>/update-boundary/', update_farm_boundary, name='update_farm_boundary'),
    path('map/farm/<int:farm_id>/validate-boundary/', validate_farm_boundary, name='validate_farm_boundary'),
    # path('map/search/', search_farms, name='search_farms'),

    #################################################################################################################

    # Base data endpoints
    path('api/tree-density/', get_tree_density_data, name='tree_density_data'),
    path('api/crop-health/', get_crop_health_data, name='crop_health_data'),
    path('api/irrigation-sources/', get_irrigation_data, name='irrigation_data'),
    path('api/soil-types/', get_soil_data, name='soil_data'),
    path('api/climate-zones/', get_climate_data, name='climate_data'),
    path('api/road-network/', get_road_data, name='road_data'),
    path('api/regions/', get_regions_list, name='regions_list'),
    path('api/all-agricultural-data/', get_all_agricultural_data, name='all_agricultural_data'),


    #####################################################################################################################

     # POST endpoints for data creation
    path('api/tree-density/create/', create_tree_density_data, name='create_tree_density'),
    path('api/crop-health/create/', create_crop_health_data, name='create_crop_health'),
    path('api/irrigation-sources/create/', create_irrigation_data, name='create_irrigation'),
    path('api/soil-types/create/', create_soil_data, name='create_soil'),
    path('api/climate-zones/create/', create_climate_data, name='create_climate'),
    path('api/road-network/create/', create_road_data, name='create_roads'),

    #############################################################################################################################

    path('api/regions/geojson/', regions_geojson, name='regions_geojson'),
    path('api/districts/geojson/', districts_geojson, name='districts_geojson'),
    # path('api/societies/geojson/', societies_geojson, name='societies_geojson'),
]
