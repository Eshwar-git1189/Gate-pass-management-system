from django.urls import path
from .views import (StudentListCreateAPIView, GatepassListCreateAPIView, ApprovalActionAPIView,
                    WardenGatepassListAPIView, SecurityGatepassDetailAPIView, SecurityLogTimeAPIView)


urlpatterns = [
    path('students/', StudentListCreateAPIView.as_view()),
    path('gatepasses/', GatepassListCreateAPIView.as_view()),
    path('approval/<uuid:token>/<str:action>/', ApprovalActionAPIView.as_view(), name='approval-action'),
    path('warden/gatepasses/', WardenGatepassListAPIView.as_view(), name='warden-gatepass-list'),
    path('security/verify/<uuid:id>/', SecurityGatepassDetailAPIView.as_view(), name='security-verify'),
    path('security/log/<uuid:pk>/<str:action>/', SecurityLogTimeAPIView.as_view(), name='security-log-time'),
]
