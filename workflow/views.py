from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
from django.contrib.auth.models import User
from .models import WorkflowDocument, ApprovalRecord
from .serializers import (
    WorkflowDocumentSerializer, 
    ApprovalRecordSerializer, 
    CustomTokenObtainPairSerializer,
    UserSerializer
)
from .permissions import WorkflowPermission

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class WorkflowDocumentViewSet(viewsets.ModelViewSet):
    queryset = WorkflowDocument.objects.all().order_by('-created_at')
    serializer_class = WorkflowDocumentSerializer
    permission_classes = [WorkflowPermission]
    
    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = {'request': self.request}
        
        if self.action in ['update', 'partial_update']:
            instance = self.get_object()
            user_role = self.get_user_role(self.request.user)
            
            if instance.current_stage == 'FILLING':
                if user_role == 1 and instance.current_filler_step == 1:
                    kwargs['fields'] = ['field1', 'field2', 'field3', 'field4', 
                                       'current_stage', 'current_filler_step', 
                                       'can_edit', 'can_approve']
                elif user_role == 2 and instance.current_filler_step == 2:
                    kwargs['fields'] = ['field1', 'field2', 'field3', 'field4',
                                       'field5', 'field6', 'field7', 'field8',
                                       'current_stage', 'current_filler_step',
                                       'can_edit', 'can_approve']
                    kwargs['readonly_fields'] = ['field1', 'field2', 'field3', 'field4']
                elif user_role == 3 and instance.current_filler_step == 3:
                    kwargs['fields'] = [f'field{i}' for i in range(1, 12)] + \
                                      ['current_stage', 'current_filler_step',
                                       'can_edit', 'can_approve']
                    kwargs['readonly_fields'] = [f'field{i}' for i in range(1, 9)]
        
        return super().get_serializer(*args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user_role = self.get_user_role(request.user)
        
        if instance.current_stage == 'FILLING':
            if user_role == 1 and instance.current_filler_step == 1:
                required_fields = ['field1', 'field2', 'field3', 'field4']
                if all(request.data.get(field) for field in required_fields):
                    instance.current_filler_step = 2
            elif user_role == 2 and instance.current_filler_step == 2:
                required_fields = ['field5', 'field6', 'field7', 'field8']
                if all(request.data.get(field) for field in required_fields):
                    instance.current_filler_step = 3
            elif user_role == 3 and instance.current_filler_step == 3:
                required_fields = ['field9', 'field10', 'field11']
                if all(request.data.get(field) for field in required_fields):
                    instance.current_stage = 'APPROVAL'
                    instance.save()
                    self.create_approval_records(instance)
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        document = self.get_object()
        
        if document.current_stage != 'APPROVAL':
            return Response(
                {'error': 'Document not in approval stage'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approval = ApprovalRecord.objects.filter(
            document=document,
            approver=request.user
        ).first()
        
        if not approval:
            return Response(
                {'error': 'You are not an approver for this document'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        action_type = request.data.get('action')
        comments = request.data.get('comments', '')
        
        if action_type == 'approve':
            approval.status = 'APPROVED'
            approval.approved_at = timezone.now()
            approval.comments = comments
            approval.save()
            
            # Check if all approvers have approved
            all_approvals = ApprovalRecord.objects.filter(document=document)
            if all(a.status == 'APPROVED' for a in all_approvals):
                document.current_stage = 'COMPLETED'
                document.save()
                
        elif action_type == 'reject':
            approval.status = 'REJECTED'
            approval.comments = comments
            approval.save()
            
            # Reset document to filling stage
            document.current_stage = 'FILLING'
            document.current_filler_step = 1
            document.save()
            
            # Reset all approvals
            ApprovalRecord.objects.filter(document=document).update(
                status='PENDING',
                comments='',
                approved_at=None
            )
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        document = self.get_object()
        data = {
            'document_id': document.id,
            'current_stage': document.current_stage,
            'current_filler_step': document.current_filler_step,
            'all_fields_filled': document.are_all_fields_filled(),
            'approvals': ApprovalRecordSerializer(
                document.approvals.all(), 
                many=True
            ).data if document.current_stage in ['APPROVAL', 'COMPLETED'] else []
        }
        return Response(data)
    
    def create_approval_records(self, document):
        # Get all users from ApproverGroup and the three filler users
        approver_users = []
        
        # Add users from groups
        for group_name in ['FillerGroup1', 'FillerGroup2', 'FillerGroup3', 'ApproverGroup']:
            users = User.objects.filter(groups__name=group_name)
            approver_users.extend(users)
        
        # Fallback for testing - add specific users
        for username in ['user1', 'user2', 'user3', 'user4']:
            user = User.objects.filter(username=username).first()
            if user and user not in approver_users:
                approver_users.append(user)
        
        # Create approval records
        for user in approver_users:
            ApprovalRecord.objects.get_or_create(
                document=document,
                approver=user,
                defaults={'status': 'PENDING'}
            )
    
    def get_user_role(self, user):
        perm = WorkflowPermission()
        return perm.get_user_role(user)

class CurrentUserView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        user_role = WorkflowPermission().get_user_role(request.user)
        data = serializer.data
        data['role'] = user_role
        return Response(data)