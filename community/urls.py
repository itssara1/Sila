from django.urls import path
from . import views as v

urlpatterns = [
    path("", v.home, name="home"),
    path("teams/", v.explore, name="explore"),
    path("teams/new/", v.team_create, name="team_create"),
    path("teams/mine/", v.my_teams, name="my_teams"),
    path("teams/<int:pk>/", v.team_detail, name="team_detail"),
    path("teams/<int:pk>/applicants/", v.applicants, name="applicants"),
    path("teams/<int:pk>/close/", v.close_team, name="close_team"),
    path("roles/<int:pk>/apply/", v.apply, name="apply"),
    path("applications/", v.applications, name="applications"),
    path("applications/<int:pk>/withdraw/", v.withdraw, name="withdraw"),
    path(
        "applications/<int:pk>/<str:decision>/",
        v.application_decide,
        name="application_decide",
    ),
    path("people/<int:pk>/", v.person, name="person"),
    path("people/<int:pk>/cv/", v.resume, name="resume"),
    path("learn/", v.learn, name="learn"),
    path("learn/skills/", v.teaching, name="teaching"),
    path("learn/request/<int:pk>/", v.learning_create, name="learning_create"),
    path("learn/requests/", v.learning_requests, name="learning_requests"),
    path(
        "learn/requests/<int:pk>/<str:decision>/",
        v.learning_decide,
        name="learning_decide",
    ),
    path("messages/", v.inbox, name="inbox"),
    path("messages/<int:pk>/", v.chat, name="chat"),
    path("messages/<int:pk>/feed/", v.chat_messages, name="chat_messages"),
    path("messages/<int:pk>/send/", v.chat_send, name="chat_send"),
]
