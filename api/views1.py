import base64
import json
import io
from PIL import Image
from django.contrib.gis.geos import Polygon
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.serializers import serialize
from django.db.models.functions.text import Upper
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.fields import empty
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from portal.models import *
from django.core.exceptions import ObjectDoesNotExist
from . import serializers
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from rest_framework.decorators import api_view


# Create your views here.

def getResponse(data, message, status, done):
    res = {}
    if done:
        res["status"] = status
        res["data"] = data
        res["msg"] = message
    else:
        data = {}
        if message is None:
            message = "Please check the data and submit again"
        status = 400
        res["status"] = status
        res["data"] = data
        res["msg"] = message

    return JsonResponse(res)


def validate_user(user_id):
    if not user_id:
        return False
    else:
        return staffTbl.objects.filter(id=user_id).exists()


@method_decorator(csrf_exempt, name='dispatch')
class loginmobileView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False}

            if data["username"] and data["password"]:

                if staffTbl.objects.filter(username=data["username"], password=data["password"]).exists():
                    staff = staffTbl.objects.filter(username=data["username"], password=data["password"]).first()

                    status["status"] = 200
                    status["msg"] = "Login successful"
                    status["data"] = {
                        "first_name": f'{staff.first_name.title()}',
                        "last_name": f'{staff.last_name.title()}',
                        "user_id": f'{staff.id}',
                        "staff_id": f'{staff.staffid}',
                        "group": f'{staff.designation.name}',
                        "district": f'{staff.district}'
                    }
                else:
                    status["status"] = 404
                    status["msg"] = "Login unsuccessful!"
                    status["data"] = {}
            else:
                status["status"] = 404
                status["msg"] = "Login unsuccessful!"
                status["data"] = {}

        except Exception as e:
            status["status"] = 0
            status["msg"] = "Error Occurred!"
            status["data"] = str(e)

        return JsonResponse(status, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class FarmDetailsEndPoint(APIView):
    def post(self, request):
        data = json.loads(request.body)

        with open("test.txt", "a") as f:
            f.write(str(data))

        agent = data["user_id"]
        farmboundary = data["farm_boundary"]
        farmer = data["farmer"]
        farm_area = data["farm_area"]
        society = data["society"]
        uid = data["uid"]

        aa = [(point["longitude"], point["latitude"]) for point in farmboundary]
        farm_geom = Polygon(aa)
        staffid = staffTbl.objects.get(id=agent).id
        staff_id = staffTbl.objects.get(id=agent).staffid
        farmerID = Farmerdetails.objects.get(farmer_code=farmer).id

        data = {
            "farmboundary": str(aa),
            "society": society,
            "geom": farm_geom,
            "farm_area": farm_area,
            "farmerTbl_foreignkey": farmerID,
            "staffTbl_foreignkey": staffid,
            "uid": uid,
            "staff_id": staff_id
        }
        farm_serializer = serializers.FarmsSerializer(data=data)

        if farm_serializer.is_valid():
            farm_serializer.save()
            return JsonResponse("ok", safe=False)
        return JsonResponse("not ok", safe=False)

    def get(self, request):
        status = {}
        status["status"] = False

        user_id = request.GET.get("user_id")
        if not user_id:
            return JsonResponse({"status": 400, "msg": "user_id is required"}, safe=False)

        district = districtStaffTbl.objects.get(staffTbl_foreignkey=user_id).districtTbl_foreignkey

        data = []

        farms = Farmdetails.objects.filter(staffTbl_foreignkey__districtstafftbl__districtTbl_foreignkey=district)

        farm_serializer = serializers.FarmSerializer(farms, many=True)
        farmers_names = []

        for d in farm_serializer.data:
            farmer = Farmerdetails.objects.get(id=d["farmerTbl_foreignkey"])
            farmer_serializer = serializers.FarmerDetailsSerializer(farmer)
            farmers_names.append(farmer_serializer.data)

        for index, farm in enumerate(farms):
            try:
                eok = {}
                if farm.geom:
                    eok["farm_boundary"] = farm.geom.geojson
                else:
                    eok["farm_boundary"] = ""
                eok["farmer_name"] = f"{farmers_names[index]['farmer_fname']} {farmers_names[index]['farmer_lname']}"
                eok["location"] = farm.society
                eok["staff_id"] = farm.staff_id
                eok["farmer_id"] = farmers_names[index]['farmer_code']
                eok["farm_reference"] = farm.farm_code
                if farm.farm_area:
                    eok["farm_size"] = farm.farm_area
                else:
                    eok["farm_size"] = 0
                data.append(eok)
            except Exception as e:
                raise e

        status["status"] = 200
        status["msg"] = "Success"
        status["data"] = data

        print("THE DATA IS :::::::::::::::::::::: {}".format(data))

        return JsonResponse(status, safe=False)

    # def get(self, request):
    #     user = request.data["user_id"]
    #     if validate_user(user):
    #         if not districtTbl.objects.filter(district=request.data["district"]).exists():
    #             return getResponse({}, "There is no farm for this district", 404, False)
    #         district_name = districtTbl.objects.filter(district=request.data["district"]).values()[0]["district"]
    #         farms = Farmdetails.objects.filter(district=district_name)
    #         #farms = Farmdetails.objects.all()
    #
    #         farm_data = []
    #
    #         for farm in farms:
    #             f = {}
    #
    #             if farm.geom:
    #                 f["farm_boundary"] = farm.geom.geojson
    #             else:
    #                 f["farm_boundary"] = ""
    #             f["farmer_ID"] = farm.farmer_ID


class TreeInformationEndpoint(APIView):
    def get(self, request):
        user = request.query_params.get("user_id")
        if validate_user(user):
            trees = TreeInformation.objects.all()
            tree_data = serializers.TreeInformationSerializer(trees, many=True)
            return getResponse(tree_data.data, "Successful", 200, True)


class TreeNameEndpoint(APIView):
    def get(self, request):
        user = request.query_params.get("user_id")
        if validate_user(user):
            trees = TreeName.objects.all()
            tree_data = serializers.TreeNameSerializer(trees, many=True)
            return getResponse(tree_data.data, "Successful", 200, True)


class TreeTypeEndpoint(APIView):
    def get(self, request):
        user = request.query_params.get("user_id")
        if validate_user(user):
            trees = TreeType.objects.all()
            tree_data = serializers.TreeTypeSerializer(trees, many=True)
            return getResponse(tree_data.data, "Successful", 200, True)


@method_decorator(csrf_exempt, name='dispatch')
class TreeDetailsEndpoint(APIView):
    def post(self, request):
        user = request.data["user_id"]
        if validate_user(user):
            serializer = serializers.TreeDetailsSerializer(data=request.data)
            if not serializer.is_valid():
                return JsonResponse({"status": 400, "msg": serializer.errors}, status=400)
            serializer.save()
            return getResponse(serializer.data, "Successful", 201, True)
        else:
            return getResponse({}, "Invalid user", 400, False)

    def get(self, request):
        user_id = request.query_params.get("user_id")
        district = request.query_params.get("district")

        if validate_user(user_id):
            if not districtTbl.objects.filter(district=district).exists():
                return getResponse({}, "There is no tree for this district", 404, False)
            district_name = districtTbl.objects.filter(district=district).values()[0]["district"]
            trees = treeDetails.objects.filter(district=district_name)

            serializer = serializers.TreeDetailsSerializer(trees, many=True)
            tree_data = serializer.data

            return getResponse(tree_data, "Successful", 200, True)
        else:
            return getResponse({}, "Invalid user", 404, False)


class FarmerDetailsEndpoint(APIView):
    def post(self, request):

        pic = request.data["pic_of_farmer"]
        user = request.data["user_id"]
        district_exists = districtTbl.objects.filter(district=request.data["district"]).exists()

        if not district_exists:
            return getResponse({}, "Your district does not exist", 404, False)
        district_name = districtTbl.objects.filter(district=request.data["district"]).values()[0]["district"]

        if pic is not None:
            photo = saveimage(pic, request.data["farmer_contact"])
        else:
            photo = pic
        if validate_user(user):
            request.data["pic_of_farmer"] = photo
            request.data["district"] = district_name

            serializer = serializers.FarmerDetailsSerializer(data=request.data)

            if not serializer.is_valid():
                return JsonResponse({"status": 400, "msg": serializer.errors}, status=400)
            serializer.save()
            return getResponse(serializer.data, "Successful", 201, True)
        else:
            return JsonResponse({"status": 404, "msg": "Invalid"})

    def get(self, request):
        user_id = request.query_params.get("user_id")
        district = request.query_params.get("district")
        if validate_user(user_id):
            if not districtTbl.objects.filter(district=district).exists():
                return getResponse({}, "There is no farmer for this district", 404, False)
            district_name = districtTbl.objects.filter(district=district).values()[0]["district"]
            farmers = Farmerdetails.objects.annotate(
                district_upper=Upper('district')
            ).filter(district_upper=district_name.upper())
            serializer = serializers.FarmerDetailsSerializer(farmers, many=True)

            farmer_data = []

            for farmer in serializer.data:
                farmer_data.append(farmer)
            return getResponse(farmer_data, "Successful", 200, True)
        else:
            return JsonResponse({"status": 404, "msg": "Invalid user"})

    def put(self, request):
        if validate_user(request.data["user_id"]):
            farmer_id = request.data["farmer_id"]
            farmer_detail = Farmerdetails.objects.get(id=farmer_id)
            if not farmer_detail:
                return getResponse({}, "Not Found", 404, False)

            serializer = serializers.FarmerDetailsSerializer(farmer_detail, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            return getResponse(serializer.data, "Updated successfully", 200, True)
        else:
            return JsonResponse({"status": 404, "msg": "Invalid"})

    def delete(self, request):
        if validate_user(request.data["user_id"]):
            farmer_id = request.data["farmer_id"]
            farmer_detail = Farmerdetails.objects.get(id=farmer_id)

            if not farmer_detail:
                return getResponse({}, "Farmer not found", 404, True)

            farmer_detail.delete()
            return getResponse({}, "Deleted successfully", 204, True)
        else:
            return JsonResponse({"status": 404, "msg": "Invalid"})


@api_view(["GET"])
def generateTreesCodes(request):
    tree_without_farm_ref = treeDetails.objects.filter(tree_code__isnull=True)
    check = treeDetails.objects.filter(tree_code__isnull=False)
    all_trees = treeDetails.objects.all()

    print(len(check))

    tree_codes = []

    if len(check) != 0:
        for a in all_trees:
            id = a.tree_code.split("/")
            tree_codes.append(id[-1])
            # Print the last item in the split
        print(f"Last item in the split: {tree_codes[-1]}")

        for index, tree in enumerate(tree_without_farm_ref):
            count = int(tree_codes[-1]) + index + 1

            countz = "{0:0>3}".format(count)
            tree_code = f"ACL/AGF/F/{str(countz)}"

            # Assign the farm code to the farm
            tree.tree_code = tree_code
            tree.save()

        return JsonResponse("done", safe=False)
    else:
        for index, tree in enumerate(tree_without_farm_ref):
            count = index + 1
            countz = "{0:0>3}".format(count)
            tree_code = f"ACL/AGF/T/{str(countz)}"

            # Assign the farm code to the farm
            tree.tree_code = tree_code
            tree.save()

        return JsonResponse("done", safe=False)


@api_view(["GET"])
def generateFarmCodes(request):
    print(int('0001'))
    farms_without_farm_ref = Farmdetails.objects.filter(farm_code__isnull=True)
    check = Farmdetails.objects.filter(farm_code__isnull=False)
    all_farms = Farmdetails.objects.all()

    print(len(check))

    farm_codes = []

    if len(check) != 0:
        for a in all_farms:
            id = a.farm_code.split("/")
            farm_codes.append(id[-1])
            # Print the last item in the split
        print(f"Last item in the split: {farm_codes[-1]}")

        for index, farm in enumerate(farms_without_farm_ref):
            print("FARM ====================== {}".format(farm))

            count = int(farm_codes[-1]) + index + 1

            countz = "{0:0>3}".format(count)
            farm_code = f"ACL/AGF/F/{str(countz)}"

            # Assign the farm code to the farm
            farm.farm_code = farm_code
            farm.save()

        return JsonResponse("done", safe=False)
    else:
        for index, farm in enumerate(farms_without_farm_ref):
            print("FARM ====================== {}".format(farm))

            count = index + 1
            countz = "{0:0>3}".format(count)
            farm_code = f"ACL/AGF/F/{str(countz)}"

            # Assign the farm code to the farm
            farm.farm_code = farm_code
            farm.save()

        return JsonResponse("done", safe=False)


def decodeDesignImage(data):
    try:
        data = base64.b64decode(data.encode('UTF-8'))
        buf = io.BytesIO(data)
        img = Image.open(buf)
        return img
    except:
        return None


def saveimage(image, imgname):
    img = decodeDesignImage(image)
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    data = InMemoryUploadedFile(img_io, field_name=None, name=str(imgname) + ".jpg", content_type='image/jpeg',
                                size=img_io.tell, charset=None)
    return data


class TreeMonitoringEndPoint(APIView):
    def post(self, request):
        user = request.data.get("user_id")

        if not validate_user(user):
            return getResponse({}, "Invalid user", status.HTTP_404_NOT_FOUND, False)

        tree_detail = treeDetails.objects.get(tree_code=request.data["tree_code"])

        data = {
            "tree_code": request.data["tree_code"],
            "tree_foreignKey": tree_detail.id,
            "tree_status": request.data["tree_status"],
            "staff_id": request.data["staff_id"],
            "additional_observation": request.data["additional_observation"]
        }

        serializer = serializers.TreeMonitoringSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return getResponse(serializer.data, "Successful", status.HTTP_201_CREATED, True)
        else:
            return getResponse({}, serializer.errors, status.HTTP_400_BAD_REQUEST, False)

    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not validate_user(user_id):
            return getResponse({}, "Invalid user", status.HTTP_404_NOT_FOUND, False)

        user = get_object_or_404(staffTbl, id=user_id)
        tree_details = treeDetails.objects.filter(district=user.district)
        tree_details_serializer = serializers.TreeDetailsSerializer(tree_details, many=True)

        # Extract tree ids and map them to their corresponding data from tree_details_serializer
        tree_details_map = {tree['id']: tree for tree in tree_details_serializer.data}

        # Filter TreeMonitoring objects using the extracted tree ids
        tree_codes = list(tree_details_map.keys())
        monitored_trees = TreeMonitoring.objects.filter(tree_foreignKey__in=tree_codes)

        monitored_trees_serializer = serializers.TreeMonitoringSerializer(monitored_trees, many=True)

        # Update tree_code in monitored_trees_serializer data with corresponding data from tree_details_map
        for monitored_tree in monitored_trees_serializer.data:
            tree_code = monitored_tree['tree_code']
            monitored_tree.pop("id", None)
            monitored_tree.pop("delete_field", None)
            monitored_tree.pop("tree_foreignKey", None)
            monitored_tree['tree_code'] = tree_details_map.get(tree_code, tree_code)

        if len(monitored_trees_serializer.data) == 0:
            return getResponse({}, "No tree monitored within this district", 400, False)

        return getResponse(monitored_trees_serializer.data, "Successful", 200, True)


class TreeSpeciesEndpoint(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not validate_user(user_id):
            return getResponse({}, "Invalid user", status.HTTP_404_NOT_FOUND, False)

        data = TreeSpecies.objects.all()
        serializer = serializers.TreeSpeciesSerializer(data, many=True)

        return getResponse(serializer.data, "Successful", status.HTTP_200_OK, True)


class FruitTreeEndpoint(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not validate_user(user_id):
            return getResponse({}, "Invalid user", status.HTTP_404_NOT_FOUND, False)

        data = FruitTree.objects.all()
        serializer = serializers.FruitTreeSerializer(data, many=True)

        return getResponse(serializer.data, "Successful", status.HTTP_200_OK, True)

