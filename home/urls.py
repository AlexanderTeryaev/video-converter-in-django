from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload_file', views.upload_file, name='upload_file'),
    path('get_status', views.get_status, name='get_status'),
    path('terms', views.terms, name='terms'),
    path('policy', views.policy, name='policy'),
    path('features', views.features, name='features'),
]
