from django.urls import path
from .views import (GatepassListCreateAPIView, ApprovalActionAPIView,
                    WardenGatepassListAPIView, WardenGatepassActionAPIView, SecurityGatepassDetailAPIView, SecurityLogTimeAPIView, WardenDashboardView, StudentRequestView, StudentGatepassListView, SecurityDashboardView, UserLoginView, redirect_after_login)


urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('redirect/', redirect_after_login, name='redirect-after-login'),
    path('gatepasses/', GatepassListCreateAPIView.as_view()),
    path('approval/<uuid:token>/<str:action>/', ApprovalActionAPIView.as_view(), name='approval-action'),
    path('warden/gatepasses/', WardenGatepassListAPIView.as_view(), name='warden-gatepass-list'),
    path('warden/gatepasses/<uuid:pk>/<str:action>/', WardenGatepassActionAPIView.as_view(), name='warden-gatepass-action'),
    path('warden/dashboard/', WardenDashboardView.as_view(), name='warden-dashboard'),
    path('student/request/', StudentRequestView.as_view(), name='student-request'),
    path('student/gatepasses/', StudentGatepassListView.as_view(), name='student-gatepass-list'),
    path('security/dashboard/', SecurityDashboardView.as_view(), name='security-dashboard'),
    path('security/verify/<uuid:id>/', SecurityGatepassDetailAPIView.as_view(), name='security-verify'),
    path('security/log/<uuid:pk>/<str:action>/', SecurityLogTimeAPIView.as_view(), name='security-log-time'),
]
