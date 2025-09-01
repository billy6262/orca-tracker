from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as CoreUserAdmin
from core import models
from data_pipeline import models as dp_models
from data_pipeline.email_retriver import get_emails 


class UserAdmin(CoreUserAdmin):
    """Define the admin pages for users."""
    ordering = ['id']
    list_display = ['email', 'name', 'is_active', 'is_staff', 'is_superuser']
    list_filter = ['is_active', 'is_staff']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important Dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2','name', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )


class RawReportAdmin(admin.ModelAdmin):
    actions = ['fetch_email_reports']
    list_display = ['id', 'timeRecived', 'messageId', 'subject', 'sender', 'processed']
    list_display_links = ['id', 'messageId']
    date_hierarchy = 'timeRecived'
    list_filter = ['timeRecived', 'processed', 'sender']
    search_fields = ['id', 'messageId', 'subject', 'sender', 'body']
    ordering = ['-timeRecived']
    list_per_page = 50

    def fetch_email_reports(self, request, queryset):
        get_emails()
        self.message_user(request, "Email reports fetched and stored.")
    fetch_email_reports.short_description = "Fetch email reports from inbox"


class OrcaSightingAdmin(admin.ModelAdmin):
    list_display = ['id', 'time', 'zone', 'ZoneNumber', 'present', 'count', 'direction', 'sunUp']
    list_display_links = ['id']
    date_hierarchy = 'time'
    list_filter = ['present', 'ZoneNumber', 'direction', 'sunUp', 'isWeekend']
    search_fields = ['id', 'zone', 'direction']
    ordering = ['-time']
    list_per_page = 50
    readonly_fields = ['month', 'dayOfWeek', 'hour', 'reportsIn5h', 'reportsIn24h', 
                      'reportsInAdjacentZonesIn5h', 'reportsInAdjacentPlusZonesIn5h']


class ZoneAdmin(admin.ModelAdmin):
    list_display = ['zoneNumber', 'name', 'get_adjacent_count', 'get_next_adjacent_count']
    list_display_links = ['zoneNumber', 'name']
    search_fields = ['zoneNumber', 'name', 'localities']
    ordering = ['zoneNumber']
    filter_horizontal = ['adjacentZones', 'nextAdjacentZones']
    
    def get_adjacent_count(self, obj):
        return obj.adjacentZones.count()
    get_adjacent_count.short_description = 'Adjacent Zones'
    
    def get_next_adjacent_count(self, obj):
        return obj.nextAdjacentZones.count()
    get_next_adjacent_count.short_description = 'Next Adjacent Zones'


class PredictionAdmin(admin.ModelAdmin):
    list_display = ['id', 'orca_sighting', 'date_created', 'predicted_time', 'predicted_zone', 'confidence']
    list_display_links = ['id']
    date_hierarchy = 'date_created'
    list_filter = ['predicted_zone', 'date_created']
    search_fields = ['id', 'predicted_zone']
    ordering = ['-date_created']
    list_per_page = 50


class ZoneSeasonalityAdmin(admin.ModelAdmin):
    list_display = ['id', 'zone', 'month', 'avg_sightings']
    list_display_links = ['id']
    list_filter = ['zone', 'month']
    search_fields = ['zone__name', 'zone__zoneNumber']
    ordering = ['zone', 'month']
    list_per_page = 50


class ZoneEffortAdmin(admin.ModelAdmin):
    list_display = ['id', 'zone', 'hour', 'avg_sightings']
    list_display_links = ['id']
    list_filter = ['zone', 'hour']
    search_fields = ['zone__name', 'zone__zoneNumber']
    ordering = ['zone', 'hour']
    list_per_page = 50


# Register all models
admin.site.register(models.User, UserAdmin)
admin.site.register(dp_models.RawReport, RawReportAdmin)
admin.site.register(dp_models.OrcaSighting, OrcaSightingAdmin)
admin.site.register(dp_models.Zone, ZoneAdmin)
admin.site.register(dp_models.Prediction, PredictionAdmin)
admin.site.register(dp_models.ZoneSeasonality, ZoneSeasonalityAdmin)
admin.site.register(dp_models.ZoneEffort, ZoneEffortAdmin)
