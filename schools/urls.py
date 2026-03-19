from django.urls import path
from . import views

urlpatterns = [
    path('healthz/', views.healthz, name='healthz'),
    path('map/', views.map_view, name='map'),  # main map
    path('region/', views.region_view, name='region'),  # new region page
    path('schools-data/', views.schools_data, name='schools-data'),
    path('school-detail/', views.school_detail, name='school-detail'),
    path('climate-surface/', views.climate_surface, name='climate_surface'),
    path('climate-metadata/', views.climate_metadata, name='climate_metadata'),
    path('api/', views.api_index, name='api_index'),
    path('api/counties/', views.counties_api, name='counties_api'),
    path('api/counties/geojson/', views.counties_geojson_api, name='counties_geojson_api'),
    path('api/subcounties/list/', views.subcounties_list_api, name='subcounties_list_api'),
    path('api/schools/', views.schools_api, name='schools_api'),
    path('api/subcounties/', views.subcounties_api, name='subcounties_api'),
    path('api/climate/', views.climate_api, name='climate_api'),
]
