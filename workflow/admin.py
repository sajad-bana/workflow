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