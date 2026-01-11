from django.contrib import admin
from core.models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'agent', 'created_at')
    list_filter = ('agent',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'agent', 'description')
        }),
        ('Mapping Configuration', {
            'fields': ('input_mapping', 'output_mapping'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )