from rest_framework import serializers
from .models import Student, GatepassRequest

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class GatepassRequestSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)

    class Meta:
        model = GatepassRequest
        fields = '__all__'
