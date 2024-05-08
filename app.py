
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from flask_session import Session
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import logging
import itertools
from operator import itemgetter
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'  
Session(app)  # Initialize the Flask-Session extension

UPLOAD_FOLDER = 'uploads'  
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

cred = credentials.Certificate('chit-chat-firebase-adminsdk.json')
firebase_admin.initialize_app(
        cred,
        {'storageBucket': 'chit-chat-7b3c9.appspot.com'}
    )
db = firestore.client()

socketio = SocketIO(app)

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        display_name = request.form.get('display_name')
        status = "available"  # default status when registering
        profile_picture_url = "../images/defaultprofile"  # default profile picture URL

        try:
            user = auth.create_user(email=email, password=password, display_name=display_name)
            user_data = {'email': email,
                         'display_name': display_name,
                         'status': status,
                         'profile_picture_url': profile_picture_url
                         }
            db.collection('users').document(user.email).set(user_data)
            flash('User created successfully', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Failed to create user: {str(e)}', 'error')
            return redirect(url_for('register'))
        
        #####


        #####
    return render_template('register.html')

# Login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.get_user_by_email(email)
            
            session['curr_user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('chat'))
        except Exception as e:
            flash(f'Login failed: {e}', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/chat')
def chat():
    # Assuming you have a way to get the current user ID
    curr_user = session.get('curr_user')
    return render_template('chat.html', curr_user=curr_user)
    """Chat room page, where users can see and send messages."""
    #return render_template('chat.html')

@app.route('/session_check')
def session_check():
    return jsonify({'current_user': session.get('curr_user', 'No user in session')})


@socketio.on('join')
def on_join(data):
    """Handles a user joining a messaging room."""
    curr_user = session.get('curr_user')

    if not curr_user:
        emit('error', 'You must be logged in to join a room.')
        return
    
    receiver_user = data.get('receiver_user')

    if not receiver_user:
        emit('error', 'Receiver Email not provided.')
        return
    
    # Create a unique room identifier for the pair
    room_id = f"{min(curr_user, receiver_user)}-{max(curr_user, receiver_user)}"
    
    # Join the room
    join_room(room_id)
    emit('room_joined', {'room_id': room_id})


@socketio.on('message')
def handle_message(data):
    """Handles sending a message to a room."""
    curr_user = session.get('curr_user')
    print(curr_user)

    if not curr_user:
        emit('error', 'You must be logged in to send a message.')
        return

    room_id = data.get('room_id')
    message_content = data.get('message')

    if not room_id or not message_content:
        emit('error', 'Room ID and message content must be provided.')
        return
    
    receiver_user = room_id.replace(curr_user, '') if curr_user in room_id else ''
    receiver_user = receiver_user.strip('-')

    sender_doc = db.collection('users').document(curr_user).get()
    sender_display_name = sender_doc.to_dict().get('display_name', 'Unknown User')

    #timestamp = datetime.now().strftime('%b %d, %Y at %I:%M:%S %p')


    # Save the message to the database
    db.collection('messages').add({
        'sender_user': curr_user,
        'display_name': sender_display_name,
        'receiver_user': receiver_user,  
        'content': message_content,
        'timestamp': firestore.SERVER_TIMESTAMP
    })

    # Emit the message to the room
    emit('new_message', {'sender_user': curr_user, 'display_name': sender_display_name, 'content': message_content}, room=room_id)

############################################################


# Create group chat
@app.route('/create_group_chat', methods=['POST'])
def create_group_chat():
    if 'curr_user' not in session:
        return jsonify({'error': 'You need to log in to create group chats.'}), 403

    #data = request.get_json()
    data = request.get_json(silent=True)
    print("Received data:", data)
    group_name = data.get('group_name')
    members = data.get('members')
    #print("Received group name:", data.get('group_name'))
    #print("Received members list:", data.get('members'))
    
    try:
        group_ref = db.collection('group_chats').add({
            'group_name': group_name,
            'members': members,
            'created_by': session['curr_user'],
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        return jsonify({'message': 'Group chat created successfully!', 'group_id': group_ref.id}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to create group chat: {str(e)}'}), 500
    

# Join group chat
@socketio.on('join_group')
def on_join_group(data):
    """Handles a user joining a group chat room."""
    curr_user = session.get('curr_user')

    if not curr_user:
        emit('error', 'You must be logged in to join a room.')
        return

    group_id = data.get('group_id')

    if not group_id:
        emit('error', 'Group ID not provided.')
        return

    # Join the group chat room
    join_room(group_id)
    emit('group_joined', {'group_id': group_id})

# Handle group messages
@socketio.on('group_message')
def handle_group_message(data):
    """Handles sending a message to a group."""
    curr_user = session.get('curr_user')

    if not curr_user:
        emit('error', 'You must be logged in to send a message.')
        return

    group_id = data.get('group_id')
    message_content = data.get('message')

    if not group_id or not message_content:
        emit('error', 'Group ID and message content must be provided.')
        return

    # Save the message to the database
    db.collection('group_messages').add({
        'sender_user': curr_user,
        'group_id': group_id,
        'content': message_content,
        'timestamp': firestore.SERVER_TIMESTAMP
    })

    # Emit the message to the group
    emit('new_group_message', {'sender_user': curr_user, 'content': message_content}, room=group_id)

# Leave group chat
@socketio.on('leave_group')
def on_leave_group(data):
    """Handles a user leaving a group chat room."""
    group_id = data.get('group_id')
    if group_id:
        leave_room(group_id)
        emit('group_left', {'group_id': group_id})



#################################################################


@socketio.on('leave')
def on_leave(data):
    """Handles a user leaving a messaging room."""
    room_id = data.get('room_id')
    if room_id:
        leave_room(room_id)
        emit('room_left', {'room_id': room_id})

@app.route('/get_messages')
def get_messages():
    receiver_user = request.args.get('receiver_user')
    #print(receiver_user)
    curr_user = session.get('curr_user')
    #print(curr_user)
    messages = []

    # Check if receiver_user has a trailing or leading dash
    if receiver_user.startswith('-') or receiver_user.endswith('-'):
        # Remove the dash from receiver_user
        receiver_user = receiver_user.strip('-')

    print(f"curr_user: {curr_user}, receiver_user: {receiver_user}")

    # Assume messages are stored in a collection where each message document has a sender_id
    messages_query = db.collection('messages').where('sender_user', '==', curr_user).where('receiver_user', '==', receiver_user).stream()
    messages_query2 = db.collection('messages').where('sender_user', '==', receiver_user).where('receiver_user', '==', curr_user).stream()
    all_messages_query = itertools.chain(messages_query, messages_query2)


    for msg in all_messages_query:
    
        msg_data = msg.to_dict()
       
        if msg_data['sender_user'] == curr_user or msg_data['receiver_user'] == curr_user:                
            sender_user = msg_data['sender_user']
        # Get the sender's display name from Firestore
            sender_doc = db.collection('users').document(sender_user).get()

            # Show display name for previous messages
            sender_name = sender_doc.to_dict().get('display_name', 'Unknown User')
            msg_data['sender_name'] = sender_name
            messages.append(msg_data)

    sorted_messages = sorted(messages, key=itemgetter('timestamp'))

    

    return jsonify(sorted_messages)

##########################
@app.route('/get_group_messages')
def get_group_messages():
    group_id = request.args.get('group_id')
    curr_user = session.get('curr_user')
    if not curr_user:
        return jsonify({'error': 'User not logged in'}), 401
    
    messages = []
    try:
        messages_query = db.collection('group_messages').where('group_id', '==', group_id).stream()
        
        for msg in messages_query:
            msg_data = msg.to_dict()
            sender_user = msg_data['sender_user']
            sender_doc = db.collection('users').document(sender_user).get()
            sender_name = sender_doc.to_dict().get('display_name', 'Unknown User')
            msg_data['sender_name'] = sender_name
            messages.append(msg_data)

        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
###################

@app.route('/search_users')
def search_users():
    query = request.args.get('query', '').strip()  # Get the search query from request arguments
    if not query:
        return jsonify([])  # Return an empty list if no query is provided

    users_ref = db.collection('users')
    search_results = []
    # Search for users by display name or email
    users = users_ref.where('display_name', '>=', query).where('display_name', '<=', query + '\uf8ff').stream()
    #search_results.extend([user.to_dict() for user in users])

    # Convert document snapshots to dictionaries and add them to the results list
    for user in users:
        user_data = user.to_dict()
        user_data['status'] = user_data.get('status', 'Unavailable')  # Ensure there is a default status if none is set
        search_results.append(user_data)

    if not search_results:  # Optional: Search by email if no display name matches
        users = users_ref.where('email', '>=', query).where('email', '<=', query + '\uf8ff').stream()
        for user in users:
            user_data = user.to_dict()
            user_data['status'] = user_data.get('status', 'Unavailable')  # Ensure there is a default status if none is set
            search_results.append(user_data)

    return jsonify(search_results)

@app.route('/search_groupchats')
def search_groupchats():
    query = request.args.get('query', '').strip()  # Get the search query from request arguments
    if not query:
        return jsonify([])  # Return an empty list if no query is provided

    groups_ref = db.collection('group_chats')
    search_results = []
    # Search for group chats by group chat name
    groups = groups_ref.where('group_name', '>=', query).where('group_name', '<=', query + '\uf8ff').stream()
    search_results.extend([group.to_dict() for group in groups])

    return jsonify(search_results)

# Route to display the form for editing the profile
@app.route('/profile_edit', methods=['GET'])
def profile_edit():
    user_email = session.get('curr_user')  # Retrieve the user's email from the session
    if user_email:
        try:
            user_ref = db.collection('users').document(user_email)
            user_doc = user_ref.get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                return render_template('profile_edit.html', current_user=user_data)
            else:
                flash('User not found.', 'error')
                return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error accessing user data: {e}', 'error')
            return redirect(url_for('home'))
    else:
        flash('You are not logged in.', 'error')
        return redirect(url_for('login'))



# Route to handle updates to the profile
@app.route('/profile_edit', methods=['POST'])
def update_profile():
    user_email = session.get('curr_user')
    new_display_name = request.form['display_name']
    new_status = request.form['status']
    profile_picture = request.files['profile_picture']

    # Updating user document in Firestore
    user_ref = db.collection('users').document(user_email)
    user_ref.update({
        'display_name': new_display_name,
        'status': new_status,
    })

    # Handle file upload
    if profile_picture and profile_picture.filename != '':
        filename = secure_filename(profile_picture.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)  # Save to a local folder
        profile_picture.save(filepath)  # Save the file locally

        # Upload the file to Firebase Storage and get the URL
        uploaded_url = upload_to_firebase_storage(filepath, filename)
        user_ref.update({
            'profile_picture_url': uploaded_url
        })

        os.remove(filepath)  # Clean up the file from local storage after upload

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile_edit'))  # Redirect back to the profile edit form

def upload_to_firebase_storage(file_path, file_name):
    """Uploads a file to Firebase Storage and returns the public URL."""
    # Reference to the bucket
    bucket = storage.bucket()  # Add your bucket name if not default
    
    # Path within the bucket where the file will be stored
    blob = bucket.blob(file_name)
    
    # Upload the file
    blob.upload_from_filename(file_path)
    
    # Make the blob publicly viewable
    blob.make_public()
    
    # Return the public url
    return blob.public_url


@app.route('/get_user_details')
def get_user_details():
    user_email = request.args.get('email')
    user_ref = db.collection('users').document(user_email)
    user_doc = user_ref.get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        return jsonify({
            'display_name': user_data.get('display_name'),
            'profile_picture_url': user_data.get('profile_picture_url', '/static/images/defaultprofile.jpeg')  
        })
    else:
        return jsonify({'error': 'User not found'}), 404

##########################################################
"""
@app.route('/check_existing_chat', methods=['POST'])
def check_existing_chat():
    data = request.json
    user_id = data.get('user_id')
    contact_id = data.get('contact_id')

    # Check if there are any existing chat entries
    chat_ref = db.collection('chats').where('user_id', '==', user_id).where('contact_id', '==', contact_id).limit(1).stream()
    existing_chat = next(chat_ref, None)

    if existing_chat:
        # Return the existing chat ID
        return jsonify({'chat_id': existing_chat.id})
    else:
        # Create a new chat entry
        new_chat_ref = db.collection('chats').add({
            'user_id': user_id,
            'contact_id': contact_id
        })
        return jsonify({'chat_id': new_chat_ref.id})



@app.route('/get_chats')
def get_chats():
    curr_user = session.get('curr_user')
    if not curr_user:
        return jsonify([])  # Return an empty list if user is not logged in
    
    chats_ref = db.collection('chats').where('participants', 'array_contains', curr_user)
    chats = []
    for chat in chats_ref.stream():
        chat_data = chat.to_dict()
        chat_id = chat.id
        chat_name = chat_data.get('chat_name', 'Chat')
        chats.append({'chat_id': chat_id, 'chat_name': chat_name})

    return jsonify(chats)
"""

"""
@app.route('/get_messages')
def get_messages():
    chat_id = request.args.get('chat_id')
    messages_ref = db.collection('messages').where('chat_id', '==', chat_id).order_by('timestamp', direction='asc')
    messages = []
    for message in messages_ref.stream():
        message_data = message.to_dict()
        messages.append(message_data)
    
    return jsonify(messages)
"""

"""
@app.route('/search_all')
def search_all():
    query = request.args.get('query')
    # Perform search logic for both users and group chats
    # For example, using Firestore
    users_ref = db.collection('users').where('display_name', '>=', query).where('display_name', '<=', query + '\uf8ff').stream()
    group_chats_ref = db.collection('group_chats').where('group_name', '>=', query).where('group_name', '<=', query + '\uf8ff').stream()

    users = [{'type': 'user', 'display_name': doc.to_dict()['display_name'], 'email': doc.id} for doc in users_ref]
    group_chats = [{'type': 'group_chat', 'group_name': doc.to_dict()['group_name'], 'members': doc.to_dict()['members']} for doc in group_chats_ref]

    # Combine the results from both collections
    search_results = users + group_chats

    return jsonify(search_results)
"""


if __name__ == '__main__':
    socketio.run(app, debug=True)
