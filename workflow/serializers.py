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