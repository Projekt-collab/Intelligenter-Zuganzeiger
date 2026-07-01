from django.urls import path

from . import views
from.views import lokfuehrer_index, dispatcher_index

urlpatterns = [
    path('lokfuehrer/', lokfuehrer_index, name='lokfuehrer'),
    path('dispatcher/', dispatcher_index, name='dispatcher'),
    path('fahrt/beenden/<int:fahrt_id>/', views.fahrt_beenden_view, name='fahrt_beenden'),
]
