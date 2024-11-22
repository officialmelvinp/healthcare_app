from django.contrib import admin
from .models import Appointment, AppointmentFeedback

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'date_time', 'status', 'created_at')
    list_filter = ('status', 'date_time', 'doctor')
    search_fields = ('patient__username', 'doctor__username', 'notes')
    date_hierarchy = 'date_time'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('patient', 'doctor', 'date_time', 'status', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AppointmentFeedback)
class AppointmentFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('appointment__patient__username', 'appointment__doctor__username', 'comment')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('appointment', 'rating', 'comment')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

