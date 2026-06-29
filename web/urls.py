from django.urls import path
from.views import lokfuehrer_index, dispatcher_index

urlpatterns = [
    path('lokfuehrer/', lokfuehrer_index),
    path('dispatcher/', dispatcher_index)
]
