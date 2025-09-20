from portal.models import *
from rest_framework import serializers


class FarmerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmerdetails
        fields = '__all__'


class TreeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = treeDetails
        fields = '__all__'


class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmdetails
        fields = '__all__'


class TreeInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeInformation
        fields = '__all__'


class TreeMonitoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeMonitoring
        fields = '__all__'


class TreeNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeName
        fields = '__all__'


class TreeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeType
        fields = '__all__'


class FarmsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmdetails
        fields = '__all__'


class TreeSpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeSpecies
        fields = '__all__'


class FruitTreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FruitTree
        fields = '__all__'
