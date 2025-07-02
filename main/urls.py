from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chat, name='chat'),
    path('sites/<slug:slug>/', views.view_site, name='view_site'),
    # path('assign-task/', views.assign_task, name='assign_task'),
]
