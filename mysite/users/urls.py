from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'users'

urlpatterns = [
    path('create_user/', views.CreateUserView.as_view(), name="create_user"),
    path('login/', views.LoginUserView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('<slug:username>/show_profile/', views.ShowProfileView.as_view(), name="show_profile"),
]
