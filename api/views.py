from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.db.models import Q
from portal.models import (
    UserProfile, Staff, Farmer, Farm, MonitoringVisit, 
    Project, District, FarmVisit, versionTbl
)
from .serializers import (
    StaffLoginSerializer, StaffSerializer, FarmerSerializer, 
    FarmerCreateSerializer, FarmSerializer, FarmCreateSerializer,
    MonitoringVisitSerializer, MonitoringVisitCreateSerializer,
    ProjectSerializer, ProjectCreateSerializer, MilestoneSerializer,
    ComplianceCheckSerializer, FollowUpActionSerializer, InfrastructureSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json

def staff_exists_required(func):
    """
    Decorator to check if staff exists
    """
    def wrapper(self, request, *args, **kwargs):
        staff_id = request.data.get('userid') or request.query_params.get('userid')
        if not staff_id:
            return Response({'msg': 'userid is required', 'data': []}, status=status.HTTP_400_BAD_REQUEST)
        
        if not Staff.objects.filter(id=staff_id, is_active=True).exists():
            return Response({'msg': 'Staff not found or inactive', 'data': []}, status=status.HTTP_404_NOT_FOUND)
        
        return func(self, request, *args, **kwargs)
    return wrapper


@method_decorator(csrf_exempt, name='dispatch')
class versionTblView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            status ={}
            status["status"] =False

            if data["version"] :
                if versionTbl.objects.filter(version=data["version"]).exists():
                    status["status"] =  1
                    status["msg"] =  "sucessful"
                else:
                    status["status"] =  0
                    status["msg"] =  "not sucessful"
                    
            else:
                status["status"] =  0
                status["msg"] =  "not sucessful"

        except Exception as e:
            
            status["status"] =  0
            status["msg"] =  "Error Occured!"
            status["data"] =str(e),
            raise e
        return JsonResponse(status, safe=False)



class StaffLoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    @swagger_auto_schema(
        operation_description="Staff login with username and password",
        request_body=StaffLoginSerializer,
        responses={200: "Login successful", 400: "Invalid credentials", 500: "Internal Server Error"}
    )
    def post(self, request):
        """
        Staff login using username and password
        
        Args:
            username (str): staff username
            password (str): staff password
            
        Returns:
            Response: staff data or error message
        """
        try:
            serializer = StaffLoginSerializer(data=request.data)
            if serializer.is_valid():
                username = serializer.validated_data['username']
                password = serializer.validated_data['password']
                
                # Authenticate user using Django's authentication system
                user = authenticate(username=username, password=password)
                
                if user is not None:
                    # Check if user has a staff profile with valid role
                    staff_profile = UserProfile.objects.filter(
                        user=user,
                        role__in=['admin', 'project_manager', 'field_officer']
                    ).first()
                    
                    if staff_profile:
                        staff = Staff.objects.filter(user_profile=staff_profile, is_active=True).first()
                        if staff:
                            staff_serializer = StaffSerializer(staff)
                            return Response({
                                'msg': 'Login successful',
                                'data': staff_serializer.data,
                                'status': 1
                            }, status=status.HTTP_200_OK)
                        else:
                            return Response({
                                'msg': 'Staff account not found or inactive',
                                'data': [],
                                'status': 0
                            }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            'msg': 'User does not have staff privileges',
                            'data': [],
                            'status': 0
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'msg': 'Invalid username or password',
                    'data': [],
                    'status': 0
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'msg': serializer.errors,
                'data': [],
                'status': 0
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': [],
                'status': 0
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FarmerAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Fetch all farmers data by district",
        responses={200: FarmerSerializer(many=True), 404: "No farmers found", 500: "Internal Server Error"}
    )
    def get(self, request, district):
        """
        Fetch all farmers data by district
        
        Args:
            district (str): district name
            
        Returns:
            Response: farmers data or error message
        """
        try:
            farmers = Farmer.objects.filter(
                user_profile__district__name=district,
                is_deleted=False
            )
            
            if farmers.exists():
                serializer = FarmerSerializer(farmers, many=True)
                return Response({
                    'msg': 'Farmers data fetched successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'msg': f'No farmers found in {district}',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Create a new farmer",
        request_body=FarmerCreateSerializer,
        responses={201: "Farmer created successfully", 400: "Invalid data", 500: "Internal Server Error"}
    )
    def post(self, request):
        """
        Create a new farmer
        
        Returns:
            Response: success message or error
        """
        try:
            serializer = FarmerCreateSerializer(data=request.data)
            if serializer.is_valid():
                farmer = serializer.save()
                return Response({
                    'msg': 'Farmer created successfully',
                    'data': {'farmer_id': farmer.id}
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'msg': serializer.errors,
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FarmAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Fetch all farms data by district",
        responses={200: FarmSerializer(many=True), 404: "No farms found", 500: "Internal Server Error"}
    )
    def get(self, request, district):
        """
        Fetch all farms data by district
        
        Args:
            district (str): district name
            
        Returns:
            Response: farms data or error message
        """
        try:
            farms = Farm.objects.filter(
                farmer__user_profile__district__name=district,
                is_deleted=False
            )
            
            if farms.exists():
                serializer = FarmSerializer(farms, many=True)
                return Response({
                    'msg': 'Farms data fetched successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'msg': f'No farms found in {district}',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Create a new farm with spatial data",
        request_body=FarmCreateSerializer,
        responses={201: "Farm created successfully", 400: "Invalid data", 500: "Internal Server Error"}
    )
    def post(self, request):
        """
        Create a new farm with boundary coordinates
        
        Returns:
            Response: success message or error
        """
        try:
            serializer = FarmCreateSerializer(data=request.data)
            if serializer.is_valid():
                farm = serializer.save()
                return Response({
                    'msg': 'Farm created successfully',
                    'data': {
                        'farm_id': farm.id,
                        'farm_code': farm.farm_code
                    }
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'msg': serializer.errors,
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(e)
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MonitoringVisitAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Fetch all monitoring visits by district",
        responses={200: MonitoringVisitSerializer(many=True), 404: "No monitoring visits found", 500: "Internal Server Error"}
    )
    def get(self, request, district):
        """
        Fetch all monitoring visits by district
        
        Args:
            district (str): district name
            
        Returns:
            Response: monitoring visits data or error message
        """
        try:
            monitoring_visits = MonitoringVisit.objects.filter(
                farm__farmer__user_profile__district__name=district
            ).order_by('-date_of_visit')
            
            if monitoring_visits.exists():
                serializer = MonitoringVisitSerializer(monitoring_visits, many=True)
                return Response({
                    'msg': 'Monitoring visits data fetched successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'msg': f'No monitoring visits found in {district}',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Create a new monitoring visit",
        request_body=MonitoringVisitCreateSerializer,
        responses={201: "Monitoring visit created successfully", 400: "Invalid data", 500: "Internal Server Error"}
    )
    def post(self, request):
        """
        Create a new monitoring visit
        
        Returns:
            Response: success message or error
        """
        try:
            serializer = MonitoringVisitCreateSerializer(data=request.data)
            if serializer.is_valid():
                monitoring_visit = serializer.save()
                return Response({
                    'msg': 'Monitoring visit created successfully',
                    'data': {
                        'visit_id': monitoring_visit.visit_id,
                        'id': monitoring_visit.id
                    }
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'msg': serializer.errors,
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Fetch all projects",
        responses={200: ProjectSerializer(many=True), 404: "No projects found", 500: "Internal Server Error"}
    )
    def get(self, request):
        """
        Fetch all projects
        
        Returns:
            Response: projects data or error message
        """
        try:
            projects = Project.objects.filter(is_deleted=False)
            
            if projects.exists():
                serializer = ProjectSerializer(projects, many=True)
                return Response({
                    'msg': 'Projects data fetched successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'msg': 'No projects found',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Create a new project",
        request_body=ProjectCreateSerializer,
        responses={201: "Project created successfully", 400: "Invalid data", 500: "Internal Server Error"}
    )
    def post(self, request):
        """
        Create a new project
        
        Returns:
            Response: success message or error
        """
        try:
            serializer = ProjectCreateSerializer(data=request.data)
            if serializer.is_valid():
                project = serializer.save()
                return Response({
                    'msg': 'Project created successfully',
                    'data': {
                        'project_id': project.id,
                        'project_code': project.code
                    }
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'msg': serializer.errors,
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FollowUpActionAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Create follow-up action for monitoring visit",
        request_body=FollowUpActionSerializer,
        responses={201: "Follow-up action created successfully", 400: "Invalid data", 500: "Internal Server Error"}
    )
    def post(self, request):
        """
        Create follow-up action for monitoring visit
        
        Returns:
            Response: success message or error
        """
        try:
            serializer = FollowUpActionSerializer(data=request.data)
            if serializer.is_valid():
                follow_up_action = serializer.save()
                return Response({
                    'msg': 'Follow-up action created successfully',
                    'data': {'id': follow_up_action.id}
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'msg': serializer.errors,
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InfrastructureAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Create infrastructure detail for monitoring visit",
        request_body=InfrastructureSerializer,
        responses={201: "Infrastructure detail created successfully", 400: "Invalid data", 500: "Internal Server Error"}
    )
    def post(self, request):
        """
        Create infrastructure detail for monitoring visit
        
        Returns:
            Response: success message or error
        """
        try:
            serializer = InfrastructureSerializer(data=request.data)
            if serializer.is_valid():
                infrastructure = serializer.save()
                return Response({
                    'msg': 'Infrastructure detail created successfully',
                    'data': {'id': infrastructure.id}
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'msg': serializer.errors,
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MilestoneAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Fetch milestones by project",
        responses={200: MilestoneSerializer(many=True), 404: "No milestones found", 500: "Internal Server Error"}
    )
    def get(self, request, project_id):
        """
        Fetch milestones by project
        
        Args:
            project_id (int): project ID
            
        Returns:
            Response: milestones data or error message
        """
        try:
            milestones = Milestone.objects.filter(
                project_id=project_id,
                is_deleted=False
            ).order_by('due_date')
            
            if milestones.exists():
                serializer = MilestoneSerializer(milestones, many=True)
                return Response({
                    'msg': 'Milestones data fetched successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'msg': 'No milestones found for this project',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Create a new milestone",
        request_body=MilestoneSerializer,
        responses={201: "Milestone created successfully", 400: "Invalid data", 500: "Internal Server Error"}
    )
    def post(self, request):
        """
        Create a new milestone
        
        Returns:
            Response: success message or error
        """
        try:
            serializer = MilestoneSerializer(data=request.data)
            if serializer.is_valid():
                milestone = serializer.save()
                return Response({
                    'msg': 'Milestone created successfully',
                    'data': {'id': milestone.id}
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'msg': serializer.errors,
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ComplianceCheckAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Fetch compliance checks by project",
        responses={200: ComplianceCheckSerializer(many=True), 404: "No compliance checks found", 500: "Internal Server Error"}
    )
    def get(self, request, project_id):
        """
        Fetch compliance checks by project
        
        Args:
            project_id (int): project ID
            
        Returns:
            Response: compliance checks data or error message
        """
        try:
            compliance_checks = ComplianceCheck.objects.filter(
                project_id=project_id,
                is_deleted=False
            ).order_by('due_date')
            
            if compliance_checks.exists():
                serializer = ComplianceCheckSerializer(compliance_checks, many=True)
                return Response({
                    'msg': 'Compliance checks data fetched successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'msg': 'No compliance checks found for this project',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staff_exists_required
    @swagger_auto_schema(
        operation_description="Create a new compliance check",
        request_body=ComplianceCheckSerializer,
        responses={201: "Compliance check created successfully", 400: "Invalid data", 500: "Internal Server Error"}
    )
    def post(self, request):
        """
        Create a new compliance check
        
        Returns:
            Response: success message or error
        """
        try:
            serializer = ComplianceCheckSerializer(data=request.data)
            if serializer.is_valid():
                compliance_check = serializer.save()
                return Response({
                    'msg': 'Compliance check created successfully',
                    'data': {'id': compliance_check.id}
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'msg': serializer.errors,
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'msg': str(e),
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)