from django.urls import path
from ProyectoRepoApp import views

urlpatterns = [
    path('', views.home,name="home"),
    path('registro/<int:pk>', views.registro, name="registro"),
]