# arich_project/arich_app/serializers.py
from rest_framework import serializers
from .models import Fishpond, Harvest, FishType


class FishpondSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fishpond
        fields = '__all__'

class HarvestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Harvest
        fields = '__all__'


class FishTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FishType
        fields = '__all__'