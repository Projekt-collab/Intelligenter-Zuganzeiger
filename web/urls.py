from django.urls import path
from.views import lokfuehrer_index

urlpatterns = [
    path('lokfuehrer/', lokfuehrer_index)
]  # '' bedeutet die Startseite (Root)]
