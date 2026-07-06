from django.urls import path

from.views import home_index, lokfuehrer_index, dispatcher_index, fahrt_beenden_view

urlpatterns = [
    path('', home_index, name='home'),
    path('lokfuehrer/', lokfuehrer_index, name='lokfuehrer'),
    path('dispatcher/', dispatcher_index, name='dispatcher'),
    path('fahrt/beenden/<int:fahrt_id>/', fahrt_beenden_view, name='fahrt_beenden'),
]
