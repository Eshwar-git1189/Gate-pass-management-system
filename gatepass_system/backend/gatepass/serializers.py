from rest_framework import serializers
from .models import Student, Parent, Gatepass, Approval

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = "__all__"

class StudentSerializer(serializers.ModelSerializer):
    parents = ParentSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = "__all__"

class ApprovalSerializer(serializers.ModelSerializer):
    parent = ParentSerializer(read_only=True)

    class Meta:
        model = Approval
        fields = "__all__"

class GatepassSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)

    class Meta:
        model = Gatepass
        fields = "__all__"
