from django.contrib import admin
from core.models import TaskPermission


@admin.register(TaskPermission)
class TaskPermissionAdmin(admin.ModelAdmin):
    list_display = ('task', 'access_type', 'created_at')
    list_filter = ('access_type',)
    search_fields = ('task__name',)
    readonly_fields = ('created_at', 'updated_at')

    filter_horizontal = ('allowed_users', 'allowed_groups')

    fieldsets = (
        ('Task', {
            'fields': ('task',)
        }),
        ('Access Control', {
            'fields': ('access_type',)
        }),
        ('Restricted Access (only for access_type=restricted)', {
            'fields': ('allowed_users', 'allowed_groups'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )