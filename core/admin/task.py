from django.contrib import admin
from core.models import Task, TaskPermission


class TaskPermissionInline(admin.StackedInline):
    model = TaskPermission
    can_delete = False
    verbose_name_plural = 'Permission'

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


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'agent', 'access_type', 'created_at')
    list_filter = ('agent',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    inlines = [TaskPermissionInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'agent', 'description')
        }),
        ('Mapping Configuration', {
            'fields': ('input_mapping', 'output_mapping', 'output_schema'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def access_type(self, obj):
        return obj.access_type
    access_type.short_description = 'Access Type'