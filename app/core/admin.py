from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as CoreUserAdmin
from core import models
from data_pipeline import models as dp_models
from data_pipeline.email_retriver import get_emails  # Import your function

# Register your models here.


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

    def fetch_email_reports(self, request, queryset):
        get_emails()
        self.message_user(request, "Email reports fetched and stored.")
    fetch_email_reports.short_description = "Fetch email reports from inbox"


admin.site.register(models.User, UserAdmin)
admin.site.register(dp_models.RawReport, RawReportAdmin)  # Use the custom admin
admin.site.register(dp_models.OrcaSighting)
