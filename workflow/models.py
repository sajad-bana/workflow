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