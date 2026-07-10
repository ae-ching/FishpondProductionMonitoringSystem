# arich_project/arich_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('ponds/', views.ponds, name='ponds'),
    path('ponds/create/', views.create_fishpond, name='create_fishpond'),
    path('ponds/delete/<int:pk>/', views.delete_fishpond, name='delete_fishpond'),
    path('ponds/edit/<int:pk>/', views.edit_fishpond, name='edit_fishpond'),
    path('api/ponds/<int:pond_id>/fish-types/', views.get_pond_fish_types, name='get_pond_fish_types'),  # ✅ NEW AJAX ENDPOINT
    path('harvest/', views.harvest, name='harvest'),
    path('harvest/create/', views.create_harvest, name='create_harvest'),
    path('harvest/edit/<int:pk>/', views.edit_harvest, name='edit_harvest'),
    path('harvest/delete/<int:pk>/', views.delete_harvest, name='delete_harvest'),
    path('analytics/', views.analytics, name='analytics'),
    path('prediction/', views.prediction, name='prediction'),
    path('settings/', views.settings, name='settings'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('test-toast/', views.toast_test, name='toast_test'),
    path(
    'api/fishponds/',
    views.fishpond_api,
    name='fishpond_api'
    ),
    path(
    'api/harvests/',
    views.harvest_api,
    name='harvest_api'
    ),
    path(
    'api/fishtypes/',
    views.fishtype_api,
    name='fishtype_api'
    ),
    path(
    'api/predict/',
    views.predict_harvest_api,
    name='predict_harvest_api'
    ),
]