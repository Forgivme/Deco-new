# api/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
import json

from . import services 

# --- User Views ---

@api_view(['POST'])
def user_register_view(request):
    try:
        data = json.loads(request.body)
        nickname = data.get('nickname')
        password = data.get('password')
        
        user_id, user_data = services.create_user(nickname, password)
        user_data.pop('password', None) 
        
        return Response({'userId': user_id, 'user': user_data}, status=status.HTTP_201_CREATED)
    except (ValueError, KeyError) as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Session Views ---

@api_view(['POST'])
def session_create_view(request):
    try:
        data = json.loads(request.body)
        creator_id = data.get('creatorId')
        mode = data.get('mode', 'single_player') # default to single_player if not provided
        
        if not creator_id:
            return Response({'error': 'creatorId is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        session_id, session_data = services.create_session(creator_id, mode)
        return Response({'sessionId': session_id, 'session': session_data}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@api_view(['POST'])
def event_add_view(request, session_id):
    """add event to session API view"""
    try:
        event_data = json.loads(request.body)
        year = event_data.get('year')

        if not year or not isinstance(event_data, dict):
             return Response({'error': 'Request body must be a valid event JSON with a year.'}, status=status.HTTP_400_BAD_REQUEST)

        event_id, new_event_data = services.add_event_to_session(session_id, year, event_data)
        return Response({'eventId': event_id, 'event': new_event_data}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def decision_add_view(request, session_id):
    """add player decision to session API view"""
    try:
        data = json.loads(request.body)
        user_id = data.get('userId')
        year = data.get('year')
        chosen_option_id = data.get('chosenOptionId')

        if not all([user_id, year, chosen_option_id]):
            return Response({'error': 'userId, year, and chosenOptionId are required.'}, status=status.HTTP_400_BAD_REQUEST)

        decision_id, decision_data = services.add_decision_to_session(session_id, user_id, year, chosen_option_id)
        return Response({'decisionId': decision_id, 'decision': decision_data}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def session_submit_turn_view(request, session_id):
    """Process player turn submission and return next event"""
    try:
        data = json.loads(request.body)
        user_id = data.get('userId')
        year = data.get('year')
        chosen_option_id = data.get('chosenOptionId')

        if not all([user_id, year, chosen_option_id]):
            return Response({'error': 'userId, year, and chosenOptionId are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        next_event = services.process_player_decision(session_id, user_id, year, chosen_option_id)
        
        return Response(next_event, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def user_detail_view(request, user_id):
    """Get user detail API view"""
    try:
        user_data = services.get_user_by_id(user_id)
        if user_data:
            return Response(user_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Session Query Views ---

@api_view(['GET'])
def session_detail_view(request, session_id):
    """Get session detail API view"""
    try:
        session_data = services.get_session_by_id(session_id)
        if session_data:
            return Response(session_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['GET'])
def session_current_event_view(request, session_id):
    """Get current event for session API view"""
    try:
        event_data = services.get_current_event_for_session(session_id)
        if event_data:
            return Response(event_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Session or current event not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def session_decisions_view(request, session_id, year):
    """Get all decisions for a specific year in a session API view"""
    try:
        decisions = services.get_all_decisions_for_year(session_id, int(year))
        return Response(decisions, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def session_join_view(request, session_id):
    """Player joins a session API view."""
    try:
        data = json.loads(request.body)
        user_id = data.get('userId')
        if not user_id:
            raise ValueError("userId is required.")
        
        updated_session = services.join_session(session_id, user_id)
        return Response(updated_session, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

