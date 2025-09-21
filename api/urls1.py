from django.urls import path
from . import views
from django.contrib import admin 
from django.contrib.auth.views import LogoutView
import json
app_name = 'mapApp'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/login/', views.loginmobileView.as_view()),
    path('api/v1/farmer/', views.FarmerDetailsEndpoint.as_view()),
    path('api/v1/tree/', views.TreeDetailsEndpoint.as_view()),
    path('api/v1/tree-name/', views.TreeNameEndpoint.as_view()),
    path('api/v1/farm/', views.FarmDetailsEndPoint.as_view()),
    path('api/v1/tree-type/', views.TreeTypeEndpoint.as_view()),
    path('api/v1/tree-information/', views.TreeInformationEndpoint.as_view()),
    path('api/v1/tree-monitoring/', views.TreeMonitoringEndPoint.as_view()),
    path('api/v1/tree-species/', views.TreeSpeciesEndpoint.as_view()),
    path('api/v1/fruit-tree/', views.FruitTreeEndpoint.as_view()),
    path('api/v1/generate_farm_code', views.generateFarmCodes),
    path('api/v1/generate_tree_code', views.generateTreesCodes),
 ]
