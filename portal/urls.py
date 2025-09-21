from django.urls import path
from portal.auth_views import dashboard_view
from portal.views.farmer import *
from portal.views.farms import *
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
]