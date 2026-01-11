from django.contrib import admin
from core.models import Process, ProcessPermission, ProcessTransition

class ProcessTransitionInline(admin.TabularInline):
    model = ProcessTransition
    extra = 1
    fk_name = 'process'


class ProcessPermissionInline(admin.StackedInline):
    model = ProcessPermission
    can_delete = False
    verbose_name_plural = 'Permissions'
    
    filter_horizontal = ('allowed_users', 'allowed_groups')
    
    fieldsets = (
        ('Access Control', {
            'fields': ('access_type',)
        }),
        ('Restricted Access (only for access_type=restricted)', {
            'fields': ('allowed_users', 'allowed_groups'),
            'classes': ('collapse',),
        }),
    )

@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ('name', 'entry_task', 'version', 'is_active', 'created_at')
    list_filter = ('is_active', 'version')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    inlines = [ProcessPermissionInline, ProcessTransitionInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description')
        }),
        ('Workflow', {
            'fields': ('entry_task',)
        }),
        ('Version Control', {
            'fields': ('version', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )