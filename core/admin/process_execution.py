from django.contrib import admin
from core.models import ProcessExecution

@admin.register(ProcessExecution)
class ProcessExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'process', 'status', 'started_at', 'finished_at')
    list_filter = ('status', 'process')
    search_fields = ('id', 'process__name')
    readonly_fields = ('started_at', 'finished_at')
    
    fieldsets = (
        ('Execution Info', {
            'fields': ('process', 'status')
        }),
        ('Data', {
            'fields': ('input_payload', 'state'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'finished_at')
        }),
    )