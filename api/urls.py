# api/urls.py

from django.urls import path
from . import views




urlpatterns = [
    # --- User URLs ---
    # (Create)
    path('users/register/', views.user_register_view, name='user-register'),
    # (Read)
    path('users/<str:user_id>/', views.user_detail_view, name='user-detail'),
    
    # --- Session URLs ---
    # (Create)
    path('sessions/create/', views.session_create_view, name='session-create'),
    path('sessions/<str:session_id>/events/add/', views.event_add_view, name='event-add'), 
    path('sessions/<str:session_id>/decisions/add/', views.decision_add_view, name='decision-add'), 
    
    # (Update / Game Logic)
    path('sessions/<str:session_id>/submit_turn/', views.session_submit_turn_view, name='session-submit-turn'),
    
    # (Read)
    path('sessions/<str:session_id>/', views.session_detail_view, name='session-detail'),
    path('sessions/<str:session_id>/current_event/', views.session_current_event_view, name='session-current-event'),
    path('sessions/<str:session_id>/decisions/<str:year>/', views.session_decisions_view, name='session-decisions-by-year'),

    # (join)
    path('sessions/<str:session_id>/join/', views.session_join_view, name='session-join'),
]