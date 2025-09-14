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