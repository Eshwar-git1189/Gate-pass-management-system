from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Gatepass
from .serializers import GatepassSerializer

class WardenGatepassDetailAPIView(generics.RetrieveAPIView):
    queryset = Gatepass.objects.all()
    serializer_class = GatepassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Gatepass.objects.select_related(
            'student',
            'student__user'
        )

class WardenGatepassActionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, action):
        gatepass = get_object_or_404(Gatepass, pk=pk)
        
        if action == 'approve':
            gatepass.status = 'APPROVED'
            gatepass.warden_approval_time = timezone.now()
            gatepass.warden = request.user
            message = 'Gatepass approved successfully'
        elif action == 'reject':
            gatepass.status = 'REJECTED'
            gatepass.warden_approval_time = timezone.now()
            gatepass.warden = request.user
            message = 'Gatepass rejected successfully'
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gatepass.save()
        return Response({'success': True, 'message': message})

class SecurityGatepassDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            gatepass = Gatepass.objects.select_related(
                'student',
                'student__user'
            ).get(pk=id)
            
            return Response({
                'valid': True,
                'student_name': gatepass.student.user.get_full_name(),
                'registration_number': gatepass.student.registration_number,
                'purpose': gatepass.purpose,
                'status': gatepass.status,
                'exit_time': gatepass.exit_time,
                'expected_return': gatepass.expected_return,
                'return_time': gatepass.return_time
            })
        except Gatepass.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'Invalid gatepass ID'
            })

class SecurityLogTimeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, action):
        gatepass = get_object_or_404(Gatepass, pk=pk)
        now = timezone.now()
        
        if action == 'exit':
            if gatepass.exit_time:
                return Response({
                    'success': False,
                    'message': 'Exit already logged'
                })
            gatepass.exit_time = now
            message = 'Exit time logged successfully'
        elif action == 'return':
            if not gatepass.exit_time:
                return Response({
                    'success': False,
                    'message': 'Exit time not logged yet'
                })
            if gatepass.return_time:
                return Response({
                    'success': False,
                    'message': 'Return already logged'
                })
            gatepass.return_time = now
            message = 'Return time logged successfully'
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gatepass.save()
        return Response({'success': True, 'message': message})