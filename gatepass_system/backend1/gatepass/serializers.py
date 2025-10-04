from rest_framework import serializers
from .models import Student, Parent, Gatepass, ApprovalToken

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = "__all__"

class StudentSerializer(serializers.ModelSerializer):
    parents = ParentSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = "__all__"

class ApprovalTokenSerializer(serializers.ModelSerializer):
    parent = ParentSerializer(read_only=True)

    class Meta:
        model = ApprovalToken
        fields = ['token', 'gatepass', 'parent', 'created_at', 'expires_at', 'used', 'action_taken']

class GatepassSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    approval_tokens = ApprovalTokenSerializer(many=True, read_only=True)

    class Meta:
        model = Gatepass
        fields = "__all__"
