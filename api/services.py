from mysite.firebase_config import db
from datetime import datetime
from django.contrib.auth.hashers import make_password
import uuid
from firebase_admin import firestore

# User services

def create_user(nickname, password):
    """Create a new user with hashed password."""
    if not nickname or not password:
        raise ValueError("Nickname and password are required.")
    
    hashed_password = make_password(password)
    user_ref = db.collection('users').document() 
    user_ref.set({
        'nickname': nickname,
        'password': hashed_password, 
        'createdAt': datetime.utcnow()
    })
    return user_ref.id, user_ref.get().to_dict()

# Session services

def create_session(creator_id, mode='single_player'):
    """Create a new game session."""
    session_id = str(uuid.uuid4()) 
    session_ref = db.collection('sessions').document(session_id)
    
    initial_world_state = {
        'publicTrust': 50,
        'socialCohesion': 50,
        'techRegulation': 30
    }
    
    session_ref.set({
        'createdAt': datetime.utcnow(),
        'currentYear': 2075,
        'mode': mode,
        'participantIds': [creator_id],
        'status': 'lobby',
        'worldState': initial_world_state
    })
    return session_id, session_ref.get().to_dict()

def add_event_to_session(session_id, year, event_data):
    """Add an event to a session."""
    event_ref = db.collection('sessions').document(session_id).collection('events').document(str(year))
    event_ref.set(event_data)
    return event_ref.id, event_ref.get().to_dict()

def add_decision_to_session(session_id, user_id, year, chosen_option_id):
    """Add a player decision to a session."""
    decision_id = f"{user_id}_{year}"  
    decision_ref = db.collection('sessions').document(session_id).collection('decisions').document(decision_id)
    
    decision_ref.set({
        'userId': user_id,
        'year': year,
        'eventId': str(year),
        'chosenOptionId': chosen_option_id,
        'timestamp': datetime.utcnow()
    })
    return decision_ref.id, decision_ref.get().to_dict()


def process_player_decision(session_id, user_id, year, chosen_option_id):
    """Process a player decision. In multiplayer, advance only when all decided.

    Returns a dict with status:
      waiting: not all participants have decided yet
      advanced: year advanced and next event generated
      already_advanced: year already processed by another request
    """
    # 1. Record this player's decision 
    add_decision_to_session(session_id, user_id, year, chosen_option_id)

    session_ref = db.collection('sessions').document(session_id)
    session_doc = session_ref.get()
    if not session_doc.exists:
        raise ValueError(f"Session {session_id} not found")
    session_data = session_doc.to_dict()

    current_year = session_data.get('currentYear')
    participant_ids = session_data.get('participantIds', [])


    if current_year != year:
        # Return current event (already advanced scenario)
        current_event = get_current_event_for_session(session_id)
        return {
            'status': 'already_advanced',
            'currentYear': current_year,
            'event': current_event
        }

    # 2. Fetch current event
    event_ref = session_ref.collection('events').document(str(year))
    event_doc = event_ref.get()
    if not event_doc.exists:
        raise ValueError(f"Event for year {year} not found in session {session_id}")
    event_data = event_doc.to_dict() or {}

    # 3. Collect all decisions for this year
    decisions = get_all_decisions_for_year(session_id, year)
    decided_user_ids = {d.get('userId') for d in decisions}
    remaining = [pid for pid in participant_ids if pid not in decided_user_ids]

    if remaining:  
        return {
            'status': 'waiting',
            'currentYear': year,
            'decisionsReceived': len(decisions),
            'required': len(participant_ids),
            'pending': remaining
        }

    # 4. All decided – aggregate world state changes 
    option_index = {opt.get('optionId'): opt for opt in event_data.get('options', [])}
    aggregated_change = {}
    for d in decisions:
        opt = option_index.get(d.get('chosenOptionId'))
        if not opt:
            continue
        for k, v in (opt.get('worldStateChange') or {}).items():
            aggregated_change[k] = aggregated_change.get(k, 0) + v

    # 5. Apply aggregated change & advance year
    refreshed_doc = session_ref.get()
    refreshed = refreshed_doc.to_dict() or {}
    if refreshed.get('currentYear') != year:
        current_event = get_current_event_for_session(session_id)
        return {
            'status': 'already_advanced',
            'currentYear': refreshed.get('currentYear'),
            'event': current_event
        }

    new_world_state = refreshed.get('worldState', {})
    for key, delta in aggregated_change.items():
        new_world_state[key] = new_world_state.get(key, 0) + delta

    next_year = year + 1
    session_ref.update({
        'worldState': new_world_state,
        'currentYear': next_year
    })

    # 6. Call the AI service to generate the next event (*** This is pseudocode, needs to be replaced with a real AI call in the future ***)
    def call_ai_to_generate_next_event(world_state, year):
        print(f"AI is generating event for year {year} with state: {world_state}")
        return {
            "year": year,
            "description": f"This is a new test event for the year {year}.",
            "options": [
                {"optionId": "A", "text": "New Option A", "worldStateChange": {"publicTrust": 2}},
                {"optionId": "B", "text": "New Option B", "worldStateChange": {"publicTrust": -2}},
            ]
        }

    next_event_data = call_ai_to_generate_next_event(new_world_state, next_year)
    add_event_to_session(session_id, next_year, next_event_data)

    return {
        'status': 'advanced',
        'yearAdvancedTo': next_year,
        'appliedChange': aggregated_change,
        'newWorldState': new_world_state,
        'nextEvent': next_event_data
    }


def get_user_by_id(user_id):
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return None
    user_data = user_doc.to_dict()
    user_data.pop('password', None)
    return user_data

def get_user_by_nickname(nickname):
    """Get user by nickname (for authentication)."""
    users_ref = db.collection('users')
    query = users_ref.where('nickname', '==', nickname).limit(1)
    results = query.stream()
    
    for doc in results:
        return doc.id, doc.to_dict()
    return None, None


# Session query services

def get_session_by_id(session_id):
    """Get session metadata by id."""
    session_ref = db.collection('sessions').document(session_id)
    session_doc = session_ref.get()
    if not session_doc.exists:
        return None
    return session_doc.to_dict()

def get_current_event_for_session(session_id):
    """Get current year's event for a session."""
    session_data = get_session_by_id(session_id)
    if not session_data:
        return None
        
    current_year = session_data.get('currentYear')
    if not current_year:
        return None

    event_ref = db.collection('sessions').document(session_id).collection('events').document(str(current_year))
    event_doc = event_ref.get()

    if not event_doc.exists:
        return None
    return event_doc.to_dict()

def get_all_decisions_for_year(session_id, year):
    """Get all player decisions for a year in a session."""
    decisions_ref = db.collection('sessions').document(session_id).collection('decisions')
    query = decisions_ref.where('year', '==', year)
    results = query.stream()
    
    decisions = []
    for doc in results:
        decisions.append(doc.to_dict())
    return decisions


def join_session(session_id, user_id):
    """Adds a user to a session if it's in the lobby."""
    session_ref = db.collection('sessions').document(session_id)
    session_doc = session_ref.get()
    if not session_doc.exists:
        raise ValueError("Session not found.")
    
    session_data = session_doc.to_dict()
    if session_data.get('status') != 'lobby':
        raise ValueError("Session is not in lobby state.")
    
    session_ref.update({
        'participantIds': firestore.ArrayUnion([user_id])
    })
    return session_ref.get().to_dict()