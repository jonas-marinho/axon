from django.contrib import admin
from core.models import ProcessTransition

@admin.register(ProcessTransition)
class ProcessTransitionAdmin(admin.ModelAdmin):
    list_display = ('process', 'from_task', 'to_task', 'order')
    list_filter = ('process',)
    search_fields = ('condition',)
    
    fieldsets = (
        ('Transition', {
            'fields': ('process', 'from_task', 'to_task', 'order')
        }),
        ('Condition', {
            'fields': ('condition',)
        }),
    )