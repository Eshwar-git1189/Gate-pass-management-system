from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Student, GatepassRequest
from .serializers import StudentSerializer, GatepassRequestSerializer

# Student CRUD
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

# Gatepass Request CRUD
class GatepassRequestViewSet(viewsets.ModelViewSet):
    queryset = GatepassRequest.objects.all()
    serializer_class = GatepassRequestSerializer

    # Custom action to approve/reject
    def update_status(self, request, pk=None):
        gatepass = self.get_object()
        status_choice = request.data.get("status")
        if status_choice not in ['Approved', 'Rejected']:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        gatepass.status = status_choice
        gatepass.save()
        return Response({"status": gatepass.status})
