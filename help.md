I'll guide you through creating a complete Django REST API app for the workflow system step by step.

## Step 1: Setup Django Project

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required packages
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers

# Create Django project
django-admin startproject workflow_project .

# Create Django app
python manage.py startapp workflow
```

## Step 2: Update Settings

**workflow_project/settings.py** - Add these configurations:

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Add these:
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'workflow',
]

# Add to MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Add this
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add at the end of settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## Step 3: Create Models

**workflow/models.py** - Replace entire file:

```python
from django.db import models
from django.contrib.auth.models import User

class WorkflowStage(models.TextChoices):
    FILLING = 'FILLING', 'Filling Stage'
    APPROVAL = 'APPROVAL', 'Approval Stage'
    COMPLETED = 'COMPLETED', 'Completed'
    
class WorkflowDocument(models.Model):
    # Fields 1-4 (filled by User 1)
    field1 = models.CharField(max_length=255, blank=True, null=True)
    field2 = models.CharField(max_length=255, blank=True, null=True)
    field3 = models.CharField(max_length=255, blank=True, null=True)
    field4 = models.CharField(max_length=255, blank=True, null=True)
    
    # Fields 5-8 (filled by User 2)
    field5 = models.CharField(max_length=255, blank=True, null=True)
    field6 = models.CharField(max_length=255, blank=True, null=True)
    field7 = models.CharField(max_length=255, blank=True, null=True)
    field8 = models.CharField(max_length=255, blank=True, null=True)
    
    # Fields 9-11 (filled by User 3)
    field9 = models.CharField(max_length=255, blank=True, null=True)
    field10 = models.CharField(max_length=255, blank=True, null=True)
    field11 = models.CharField(max_length=255, blank=True, null=True)
    
    # Workflow control fields
    current_stage = models.CharField(
        max_length=20, 
        choices=WorkflowStage.choices,
        default=WorkflowStage.FILLING
    )
    current_filler_step = models.IntegerField(default=1)
    
    # Tracking fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_documents', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Document {self.id} - {self.current_stage}"
    
    def are_all_fields_filled(self):
        required_fields = [f'field{i}' for i in range(1, 12)]
        return all(getattr(self, field) for field in required_fields)

class ApprovalRecord(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    
    document = models.ForeignKey(WorkflowDocument, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    comments = models.TextField(blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['document', 'approver']
    
    def __str__(self):
        return f"{self.approver.username} - {self.document.id} - {self.status}"
```

## Step 4: Create Serializers

**workflow/serializers.py** - Create new file:

```python
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import WorkflowDocument, ApprovalRecord

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        readonly_fields = kwargs.pop('readonly_fields', None)
        
        super().__init__(*args, **kwargs)
        
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        
        if readonly_fields is not None:
            for field_name in readonly_fields:
                if field_name in self.fields:
                    self.fields[field_name].read_only = True

class WorkflowDocumentSerializer(DynamicFieldsModelSerializer):
    approvals = serializers.SerializerMethodField(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    can_edit = serializers.SerializerMethodField(read_only=True)
    can_approve = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = WorkflowDocument
        fields = '__all__'
    
    def get_approvals(self, obj):
        if obj.current_stage in ['APPROVAL', 'COMPLETED']:
            return ApprovalRecordSerializer(obj.approvals.all(), many=True).data
        return []
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user:
            from .permissions import WorkflowPermission
            perm = WorkflowPermission()
            return perm.can_user_edit(request.user, obj)
        return False
    
    def get_can_approve(self, obj):
        request = self.context.get('request')
        if request and request.user and obj.current_stage == 'APPROVAL':
            from .permissions import WorkflowPermission
            perm = WorkflowPermission()
            user_role = perm.get_user_role(request.user)
            return user_role in [1, 2, 3, 4]
        return False

class ApprovalRecordSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.username', read_only=True)
    
    class Meta:
        model = ApprovalRecord
        fields = ['id', 'approver', 'approver_name', 'status', 'comments', 'approved_at', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
```

## Step 5: Create Permissions

**workflow/permissions.py** - Create new file:

```python
from rest_framework import permissions
from django.contrib.auth.models import Group

class WorkflowPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        user_role = self.get_user_role(user)
        
        if obj.current_stage == 'FILLING':
            if request.method in permissions.SAFE_METHODS:
                return True
            return self.can_user_edit(user, obj)
            
        elif obj.current_stage == 'APPROVAL':
            return user_role in [1, 2, 3, 4]
        
        elif obj.current_stage == 'COMPLETED':
            return request.method in permissions.SAFE_METHODS
        
        return False
    
    def can_user_edit(self, user, obj):
        user_role = self.get_user_role(user)
        
        if obj.current_stage == 'FILLING':
            if user_role == 1 and obj.current_filler_step == 1:
                return True
            elif user_role == 2 and obj.current_filler_step == 2:
                return True
            elif user_role == 3 and obj.current_filler_step == 3:
                return True
        return False
    
    def get_user_role(self, user):
        # Check by group membership
        if user.groups.filter(name='FillerGroup1').exists():
            return 1
        elif user.groups.filter(name='FillerGroup2').exists():
            return 2
        elif user.groups.filter(name='FillerGroup3').exists():
            return 3
        elif user.groups.filter(name='ApproverGroup').exists():
            return 4
        
        # Fallback to username mapping for testing
        role_mapping = {
            'user1': 1,
            'user2': 2,
            'user3': 3,
            'user4': 4,
        }
        return role_mapping.get(user.username, 0)
```

## Step 6: Create Views

**workflow/views.py** - Replace entire file:

```python
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
```

## Step 7: Configure URLs

**workflow/urls.py** - Create new file:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowDocumentViewSet, CustomTokenObtainPairView, CurrentUserView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'documents', WorkflowDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/current-user/', CurrentUserView.as_view(), name='current_user'),
]
```

**workflow_project/urls.py** - Update main URLs:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('workflow.urls')),
]
```

## Step 8: Create Management Command for Setup

**workflow/management/commands/setup_workflow.py** - Create directories and file:

```bash
mkdir -p workflow/management/commands
touch workflow/management/__init__.py
touch workflow/management/commands/__init__.py
```

Then create the command file:

```python
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Setup initial users and groups for workflow'

    def handle(self, *args, **kwargs):
        # Create groups
        groups = ['FillerGroup1', 'FillerGroup2', 'FillerGroup3', 'ApproverGroup']
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)
            self.stdout.write(f'Created group: {group_name}')
        
        # Create users with groups
        users_data = [
            ('user1', 'user1@example.com', 'password123', 'FillerGroup1'),
            ('user2', 'user2@example.com', 'password123', 'FillerGroup2'),
            ('user3', 'user3@example.com', 'password123', 'FillerGroup3'),
            ('user4', 'user4@example.com', 'password123', 'ApproverGroup'),
        ]
        
        for username, email, password, group_name in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email}
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'Created user: {username}')
            
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            self.stdout.write(f'Added {username} to {group_name}')
        
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write('Created superuser: admin')
        
        self.stdout.write(self.style.SUCCESS('Setup completed successfully!'))
```

## Step 9: Run Migrations and Setup

```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run setup command to create users and groups
python manage.py setup_workflow

# Create superuser (optional, already created in setup)
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Step 10: Testing the API

**test_api.py** - Create test script:

```python
import requests
import json

BASE_URL = 'http://localhost:8000/api'

def test_workflow():
    # 1. Login as user1
    print("1. Login as user1...")
    response = requests.post(f'{BASE_URL}/auth/login/', json={
        'username': 'user1',
        'password': 'password123'
    })
    user1_token = response.json()['access']
    
    # 2. Create document
    print("2. Creating document...")
    headers = {'Authorization': f'Bearer {user1_token}'}
    response = requests.post(f'{BASE_URL}/documents/', headers=headers, json={})
    document_id = response.json()['id']
    print(f"Document created with ID: {document_id}")
    
    # 3. User1 fills fields 1-4
    print("3. User1 filling fields 1-4...")
    response = requests.patch(
        f'{BASE_URL}/documents/{document_id}/',
        headers=headers,
        json={
            'field1': 'Data 1',
            'field2': 'Data 2',
            'field3': 'Data 3',
            'field4': 'Data 4'
        }
    )
    print("Fields 1-4 filled")
    
    # 4. Login as user2
    print("4. Login as user2...")
    response = requests.post(f'{BASE_URL}/auth/login/', json={
        'username': 'user2',
        'password': 'password123'
    })
    user2_token = response.json()['access']
    
    # 5. User2 fills fields 5-8
    print("5. User2 filling fields 5-8...")
    headers = {'Authorization': f'Bearer {user2_token}'}
    response = requests.patch(
        f'{BASE_URL}/documents/{document_id}/',
        headers=headers,
        json={
            'field5': 'Data 5',
            'field6': 'Data 6',
            'field7': 'Data 7',
            'field8': 'Data 8'
        }
    )
    print("Fields 5-8 filled")
    
    # 6. Login as user3
    print("6. Login as user3...")
    response = requests.post(f'{BASE_URL}/auth/login/', json={
        'username': 'user3',
        'password': 'password123'
    })
    user3_token = response.json()['access']
    
    # 7. User3 fills fields 9-11
    print("7. User3 filling fields 9-11...")
    headers = {'Authorization': f'Bearer {user3_token}'}
    response = requests.patch(
        f'{BASE_URL}/documents/{document_id}/',
        headers=headers,
        json={
            'field9': 'Data 9',
            'field10': 'Data 10',
            'field11': 'Data 11'
        }
    )
    print("Fields 9-11 filled - Document moved to approval stage")
    
    # 8. User1 approves
    print("8. User1 approving...")
    headers = {'Authorization': f'Bearer {user1_token}'}
    response = requests.post(
        f'{BASE_URL}/documents/{document_id}/approve/',
        headers=headers,
        json={
            'action': 'approve',
            'comments': 'Looks good from my side'
        }
    )
    print("User1 approved")
    
    # Continue with other approvals...
    print("\nWorkflow test completed!")
    print(f"Check document status at: {BASE_URL}/documents/{document_id}/status/")

if __name__ == '__main__':
    test_workflow()
```

## Step 11: Admin Configuration (Optional)

**workflow/admin.py** - Add admin interface:

```python
from django.contrib import admin
from .models import WorkflowDocument, ApprovalRecord

@admin.register(WorkflowDocument)
class WorkflowDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'current_stage', 'current_filler_step', 'created_by', 'created_at']
    list_filter = ['current_stage', 'created_at']
    search_fields = ['id', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ApprovalRecord)
class ApprovalRecordAdmin(admin.ModelAdmin):
    list_display = ['document', 'approver', 'status', 'approved_at']
    list_filter = ['status', 'approved_at']
    search_fields = ['document__id', 'approver__username']
```

## API Endpoints Summary

- **POST** `/api/auth/login/` - Login
- **POST** `/api/auth/refresh/` - Refresh token
- **GET** `/api/auth/current-user/` - Get current user info
- **GET** `/api/documents/` - List all documents
- **POST** `/api/documents/` - Create new document
- **GET** `/api/documents/{id}/` - Get document details
- **PATCH** `/api/documents/{id}/` - Update document fields
- **POST** `/api/documents/{id}/approve/` - Approve/Reject document
- **GET** `/api/documents/{id}/status/` - Get document status

Your workflow Django REST API is now complete! The system handles:
- Multi-stage field filling with specific user permissions
- Automatic stage transitions
- Multi-user approval process
- JWT authentication
- Role-based access control