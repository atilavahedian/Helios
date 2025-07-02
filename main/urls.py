from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chat, name='chat'),
    path('launch/', views.launch_site, name='launch_site'),
    path('site/<slug:slug>/', views.view_website, name='view_website'),
    # path('assign-task/', views.assign_task, name='assign_task'),
]
