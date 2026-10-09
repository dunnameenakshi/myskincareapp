from django.urls import path
from . import views

urlpatterns = [
    path('assess/', views.create_assessment, name='create_assessment'),
    path('recommend/<int:assessment_id>/', views.generate_recommendation, name='generate_recommendation'),
]
