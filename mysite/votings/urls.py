from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('votings/', views.VotingsListView.as_view(), name="votings_list"),
    path('create_voting/', views.CreateVotingView.as_view(), name="create_voting"),
    path('voting_manual/', views.VotingManualView.as_view(), name="voting_manual"),
    path('votings/<str:v_id>/', views.VotingPageView.as_view(), name="voting_page"),
    path('votings/<str:v_id>/messages/', views.VotingMessagesView.as_view(), name="voting_messages"),
    path('program/', views.ProgramView.as_view(), name="program")
]
