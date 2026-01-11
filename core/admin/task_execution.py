from django.contrib import admin
from core.models import TaskExecution

@admin.register(TaskExecution)
class TaskExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'process_execution', 'status', 'started_at')
    list_filter = ('status', 'task')
    search_fields = ('task__name',)
    readonly_fields = ('started_at', 'finished_at')
    
    fieldsets = (
        ('Execution Info', {
            'fields': ('process_execution', 'task', 'status')
        }),
        ('Data', {
            'fields': ('input_payload', 'output_payload'),
            'classes': ('collapse',)
        }),
        ('Error', {
            'fields': ('error',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'finished_at')
        }),
    )