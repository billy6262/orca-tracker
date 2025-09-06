"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
import app.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    
    # API endpoints
    path('api/reports/<str:start_date>/<str:end_date>/', app.views.get_raw_reports_by_date_range, name='raw-reports-by-date'),
    path('api/sightings/<str:start_date>/<str:end_date>/', app.views.get_sightings_by_date_range, name='sightings-by-date'),
    path('api/sightings/zones/<str:start_date>/<str:end_date>/', app.views.get_sightings_by_zone_count, name='sightings-by-zone-count'),
    path('api/sightings/byhour/<str:start_date>/<str:end_date>/', app.views.get_sightings_count_by_hour, name='sightings-by-hour'),
    path('api/predictions/recent/', app.views.get_predictions_most_recent, name='predictions-most-recent'),

]
