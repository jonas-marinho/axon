from django.contrib import admin
from core.models import Agent

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'version', 'is_active', 'created_at')
    list_filter = ('is_active', 'version')
    search_fields = ('name', 'role')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'role', 'system_prompt', 'tools_config')
        }),
        ('LLM Configuration', {
            'fields': ('llm_config',)
        }),
        ('Version Control', {
            'fields': ('version', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )