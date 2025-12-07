from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import api_views

app_name = 'eventos_api'

urlpatterns = [
    # Login to obtain token
    path('auth/token/', obtain_auth_token, name='api_token_auth'),

    # Events list
    path('events/', api_views.EventoListAPIView.as_view(), name='events-list'),

    # Register for event
    path('events/register/', api_views.InscricaoAPIView.as_view(), name='events-register'),
]
