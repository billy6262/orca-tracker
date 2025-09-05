from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as CoreUserAdmin
from data_pipeline.prediction_generator import load_models, generate_predictions
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
    actions = ['generate_new_predictions']
    list_display = ['id', 'time', 'zone', 'ZoneNumber', 'present', 'count', 'direction', 'sunUp']
    list_display_links = ['id']
    date_hierarchy = 'time'
    list_filter = ['present', 'ZoneNumber', 'direction', 'sunUp', 'isWeekend']
    search_fields = ['id', 'zone', 'direction']
    ordering = ['-time']
    list_per_page = 50
    readonly_fields = ['month', 'dayOfWeek', 'hour', 'reportsIn5h', 'reportsIn24h', 
                      'reportsInAdjacentZonesIn5h', 'reportsInAdjacentPlusZonesIn5h']
    
    def generate_new_predictions(self, request, queryset):
        for sighting in queryset:
            if sighting.present:
                load_models()
                generate_predictions(sighting)
        self.message_user(request, "New predictions generated for selected sightings.")
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


class ZonePredictionInline(admin.TabularInline):
    """Inline admin for ZonePrediction within PredictionBucket."""
    model = dp_models.ZonePrediction
    extra = 0
    readonly_fields = ['rank', 'is_top_5']
    fields = ['zone', 'zone_number', 'probability', 'rank', 'is_top_5']
    ordering = ['rank']


class PredictionBucketInline(admin.TabularInline):
    """Inline admin for PredictionBucket within PredictionBatch."""
    model = dp_models.PredictionBucket
    extra = 0
    readonly_fields = ['overall_probability']
    fields = ['time_bucket', 'bucket_start_hour', 'bucket_end_hour', 
              'forecast_start_time', 'forecast_end_time', 'overall_probability']
    ordering = ['bucket_start_hour']


class PredictionBatchAdmin(admin.ModelAdmin):
    """Admin for PredictionBatch - the main prediction container."""
    list_display = ['id', 'source_sighting', 'created_at', 'model_version', 'overall_confidence', 'get_bucket_count']
    list_display_links = ['id']
    date_hierarchy = 'created_at'
    list_filter = ['created_at', 'model_version', 'overall_confidence']
    search_fields = ['id', 'source_sighting__id', 'source_sighting__zone']
    ordering = ['-created_at']
    list_per_page = 25
    inlines = [PredictionBucketInline]
    readonly_fields = ['created_at']
    
    def get_bucket_count(self, obj):
        return obj.buckets.count()
    get_bucket_count.short_description = 'Time Buckets'




class PredictionBucketAdmin(admin.ModelAdmin):
    """Admin for PredictionBucket - time-based prediction windows."""
    list_display = ['id', 'batch', 'time_bucket', 'forecast_start_time', 'forecast_end_time', 
                   'overall_probability', 'get_zone_count']
    list_display_links = ['id', 'time_bucket']
    date_hierarchy = 'forecast_start_time'
    list_filter = ['time_bucket', 'batch__created_at', 'batch__overall_confidence']
    search_fields = ['id', 'batch__id', 'time_bucket']
    ordering = ['-batch__created_at', 'bucket_start_hour']
    list_per_page = 50
    inlines = [ZonePredictionInline]
    
    def get_zone_count(self, obj):
        return obj.zone_predictions.count()
    get_zone_count.short_description = 'Zone Predictions'


class ZonePredictionAdmin(admin.ModelAdmin):
    """Admin for ZonePrediction - individual zone probability predictions."""
    list_display = ['id', 'bucket', 'zone', 'probability', 'rank', 'is_top_5', 'get_time_bucket']
    list_display_links = ['id']
    list_filter = ['is_top_5', 'bucket__time_bucket', 'zone', 'bucket__batch__created_at']
    search_fields = ['id', 'zone', 'bucket__batch__id']
    ordering = ['-bucket__batch__created_at', 'bucket__bucket_start_hour', 'rank']
    list_per_page = 100
    
    def get_time_bucket(self, obj):
        return obj.bucket.time_bucket
    get_time_bucket.short_description = 'Time Bucket'


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

# Register the prediction models
admin.site.register(dp_models.PredictionBatch, PredictionBatchAdmin)
admin.site.register(dp_models.PredictionBucket, PredictionBucketAdmin)
admin.site.register(dp_models.ZonePrediction, ZonePredictionAdmin)

# Other models
admin.site.register(dp_models.ZoneSeasonality, ZoneSeasonalityAdmin)
admin.site.register(dp_models.ZoneEffort, ZoneEffortAdmin)
