
// Request notification permission
Notification.requestPermission().then(function(permission) {
    if (permission === 'granted') {
        console.log('Notification permission granted.');
    }
});

const selectedMembers = [];


document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const groupMemberInput = document.getElementById('groupMemberInput');
    //const selectedMembers = [];
    const dropdownMenu = document.getElementById('memberDropdown');


    
    /////////////////////////////////////////////////////////////////
    function searchUsers(event, input, list) {
        const query = input.value;
        if (query.length > 0) {
            fetch(`/search_users?query=${query}`)
                .then(response => response.json())
                .then(users => {
                    list.innerHTML = '';
                    users.forEach(user => {
                    
                        const userItem = document.createElement('li');
                        const name = user.display_name || user.email; // Display name or fallback to email
                        userItem.setAttribute('data-email', user.email);

                        userItem.textContent = `${name} - ${user.status}`;
                        userItem.onclick = () => openChat(user.email, user.display_name); // Pass user ID and display name
                        userList.appendChild(userItem);
                    });
                    if (users.length > 0) {
                        list.style.display = 'block';
                    } else {
                        list.style.display = 'none';
                    }
                })
                .catch(error => console.error('Error:', error));
        } else {
            list.innerHTML = '';
            list.style.display = 'none';
        }
    }
    
    
    
/*
    function searchGroups(event, input, list) {
        const query = input.value;
        if (query.length > 0) {
            fetch(`/search_groupchats?query=${query}`)
                .then(response => response.json())
                .then(group_chats => {
                    list.innerHTML = '';
                    group_chats.forEach(group => {
                    
                        const groupItem = document.createElement('li');
                        groupItem.textContent = group.group_name; // Display name or fallback to email
                        groupItem.setAttribute('data-group_name', group.group_name);
                        groupItem.onclick = () => openGroupChat(group.group_name, group.members); // Pass user ID and display name
                        groupList.appendChild(groupItem);
                    });
                    if (group_chats.length > 0) {
                        list.style.display = 'block';
                    } else {
                        list.style.display = 'none';
                    }
                })
                .catch(error => console.error('Error:', error));
        } else {
            list.innerHTML = '';
            list.style.display = 'none';
        }
    }
    */
    /*
    function searchAll(event) {
        const query = searchInput.value;
        if (query.length > 0) {
            Promise.all([
                fetch(`/search_all?query=${query}`).then(res => res.json()),
            
            ]).then(([users, group_chats]) => {
                dropdownMenu.innerHTML = ''; // Clear previous results
                if (users.length + group_chats.length > 0) {
                    users.forEach(user => {
                        const userItem = createUserListItem(user);
                        dropdownMenu.appendChild(userItem);
                    });
                    group_chats.forEach(group => {
                        const groupItem = createGroupListItem(group);
                        dropdownMenu.appendChild(groupItem);
                    });
                    dropdownMenu.style.display = 'block';
                } else {
                    dropdownMenu.style.display = 'none';
                }
            }).catch(error => {
                console.error('Error:', error);
                dropdownMenu.style.display = 'none';
            });
        } else {
            dropdownMenu.innerHTML = '';
            dropdownMenu.style.display = 'none';
        }
    }
    

    function createUserListItem(user) {
        const item = document.createElement('li');
        item.textContent = user.display_name || user.email;
        item.setAttribute('data-email', user.email);
        item.onclick = () => openChat(user.email, user.display_name);
        return item;
    }

    function createGroupListItem(group) {
        const item = document.createElement('li');
        item.textContent = group.group_name;
        item.setAttribute('data-group_name', group.group_name);
        item.onclick = () => openGroupChat(group.group_name, group.members);
        return item;
    }

    searchInput.addEventListener('keyup', searchAll);

    */
/////////////////////////

    function searchMembers(event, input, list){
        const query = input.value;
        if (query.length > 0) {
            fetch(`/search_users?query=${query}`)
                .then(response => response.json())
                .then(users => {
                    //const dropdownMenu = document.getElementById('memberDropdown');
                    list.innerHTML = ''; // Clear previous results
                    if (users.length > 0) {
                        list.style.display = 'block'; // Show the dropdown
                        users.forEach(user => {
                            let userItem = document.createElement('li');
                            userItem.textContent = user.display_name || user.email;
                            userItem.setAttribute('data-email', user.email);
                            
                            userItem.addEventListener('click', () => {
                                if (!selectedMembers.some(member => member.email === user.email)) {
                                    selectedMembers.push(user); // Add user to selected members
                                    updateSelectedMembersUI(); // Update the UI to reflect the selection
                                }
                                list.style.display = 'none'; // Optionally hide the dropdown after selection
                            });

                            list.appendChild(userItem);
                        });
                    } else {
                        list.style.display = 'none'; // Hide the dropdown if no users found
                    }   
                })
                .catch(error => console.log('Error:', error));
        } else {
            document.getElementById('memberDropdown').innerHTML = '';
            document.getElementById('memberDropdown').style.display = 'none'; // Hide the dropdown if input is empty
        }
    }


    // Search input event listeners
    searchInput.addEventListener('keyup', function(event) {
        searchUsers(event, this, document.getElementById('userList'));
    });

    //searchInput.addEventListener('keyup', function(event) {
    //    searchGroups(event, this, document.getElementById('userList'));
   //});

    groupMemberInput.addEventListener('keyup', function(event) {
        searchMembers(event, this, dropdownMenu);
    });

    // Dropdown menu click event
    dropdownMenu.addEventListener('click', function(event) {
        if (event.target.tagName === 'LI') {
            const userEmail = event.target.getAttribute('data-email');
            if (!selectedMembers.some(member => member.email === userEmail)) {
                const userDisplayName = event.target.textContent;
                selectedMembers.push({email: userEmail, display_name: userDisplayName});
                updateSelectedMembersUI(); 
            }
        }
    });

    // UI update for selected members
    function updateSelectedMembersUI() {
        const membersList = document.getElementById('selectedMembers');
        membersList.innerHTML = '';
        selectedMembers.forEach(member => {
            const memberItem = document.createElement('div');
            memberItem.textContent = member.display_name || member.email;
            membersList.appendChild(memberItem);
        });
        console.log("Current selected members:", selectedMembers);
    }
    

    // Additional event handlers
    const settingButton = document.getElementById('settingButton');
    settingButton.addEventListener('click', function() {
        document.getElementById('settingOptions').classList.toggle('show');
    });

    const logoutButton = document.getElementById('logoutButton');
    logoutButton.addEventListener('click', function() {
        console.log('Logout functionality to be implemented');
    });

    const createGroupChatButton = document.getElementById('createGroupChatButton');
    createGroupChatButton.addEventListener('click', toggleCreateGroupChatForm);

    const modal = document.getElementById('createGroupChatModal');
    document.getElementById('closeModal').addEventListener('click', function() {
        modal.style.display = 'none';
    });

    document.getElementById('createGroupChat').addEventListener('click', function() {
        createGroupChat(
            document.getElementById('groupName').value, 
            selectedMembers
        );
        modal.style.display = 'none';
    });

    
});

// WebSocket connections
const socket = io.connect(window.location.origin);
let currentRoom = '';

function showNotification(title, body) {
    if (Notification.permission === 'granted') {
        new Notification(title, { body: body });
    }
}


socket.on('new_message', (data, curr_user) => {
    const messagesDiv = document.querySelector('.messages');
    
    //const isCurrentUser = data.sender_user === curr_user;
    const isCurrentUser = data.sender_user === sessionStorage.getItem('curr_user');
    const senderName = isCurrentUser ? 'You' : data.display_name;
    console.log("DisplayP_name", data.display_name);
    console.log("curr user", curr_user);

    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message');
    messageContainer.classList.add(isCurrentUser ? 'sent' : 'received'); // Add 'sent' or 'received' class based on the message sender

    const messageContent = document.createElement('p');
    messageContent.classList.add('message-content');
    messageContent.textContent = `${senderName}: ${data.content}`;

    const messageTimestamp = document.createElement('span');
    messageTimestamp.classList.add('message-timestamp');
    messageTimestamp.textContent = formatTimestamp(Date.now()); // Use current timestamp


    messageContainer.appendChild(messageContent);
    messageContainer.appendChild(messageTimestamp);

    messagesDiv.appendChild(messageContainer);

    // Scroll to the bottom of the messagesDiv
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    // Show notification
    if (Notification.permission === 'granted') {
        new Notification('New Message', {
            body: `From: ${data.display_name}\n${data.content}`,
        });
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(function(permission) {
            if (permission === 'granted') {
                new Notification('New Message', {
                    body: `From: ${data.display_name}\n${data.content}`,
                });
            }
        });
    }
});


socket.on('room_joined', (data) => {
    currentRoom = data.room_id;
});

socket.on('error', (message) => alert(`Error: ${message}`));



function openChat(email, userName) {
    document.getElementById('receiver').value = email;
    document.getElementById('contactName').textContent = userName; // Set the contact's name

    // Attempt to fetch the user's details including the profile picture
    fetch(`/get_user_details?email=${encodeURIComponent(email)}`)
        .then(response => response.json())
        .then(userDetails => {
            const contactImage = document.getElementById('contactImage');
            contactImage.src = userDetails.profile_picture_url || '../images/defaultprofile.jpeg'; // Use a default image if no URL is provided
            //contactImage.alt = `${userName}'s Profile Picture`;
        })
        .catch(error => console.error('Error fetching user details:', error));
        
    const messagesDiv = document.querySelector('.messages');
    messagesDiv.innerHTML = ''; // Clear previous messages

    fetch(`/get_messages?receiver_user=${email}`)

        .then(response => response.json())
        .then(messages => {
            if (messages.length === 0) {
                messagesDiv.innerHTML = '<p>No messages yet.</p>';
            } else {
                messages.forEach(msg => {
                    //console.log('Message sender_user:', msg.sender_user);
                    //console.log('Current user ID:', sessionStorage.getItem('curr_user'));
                    //curr_user = sessionStorage.getItem('curr_user')

                    const isSentByCurrentUser = msg.sender_user === curr_user
                    const senderName = isSentByCurrentUser ? 'You' : msg.sender_name;
                    const messageContainer = document.createElement('div');
                    messageContainer.classList.add('message');
                    messageContainer.classList.add(isSentByCurrentUser ? 'sent' : 'received'); // Add 'sent' or 'received' class based on the message sender
                    
                    const messageContent = document.createElement('p');
                    messageContent.classList.add('message-content');
                    messageContent.textContent = `${senderName}: ${msg.content}`;
                    
                    const messageTimestamp = document.createElement('span');
                    messageTimestamp.classList.add('message-timestamp');
                    messageTimestamp.textContent = formatTimestamp(msg.timestamp); // Format the timestamp
                    
                    messageContainer.appendChild(messageContent);
                    messageContainer.appendChild(messageTimestamp);
                    
                    messagesDiv.appendChild(messageContainer);
                });
            }
        })
        .catch(error => console.log('Error fetching messages:', error));

    // Join a unique room for this conversation
    const currentUser = sessionStorage.getItem('curr_user');
    const room_id = `${Math.min(currentUser, email)}-${Math.max(currentUser, email)}`;
    socket.emit('join', { room_id, receiver_user: email }); // Trigger the join event with data
}


function formatTimestamp(timestamp) {
    // Convert timestamp to a Date object
    const date = new Date(timestamp);

    // Get date components
    const month = date.toLocaleString('en-us', { month: 'long' });
    const day = date.getDate();
    const year = date.getFullYear();
    
    // Get time components
    let hours = date.getHours();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // Handle midnight
    const minutes = date.getMinutes();
    const seconds = date.getSeconds();

    // Format the timestamp
    const formattedTimestamp = `${month} ${day}, ${year} at ${hours}:${minutes}:${seconds} ${ampm}`;

    return formattedTimestamp;
}

/////////////////
//// Work on get messages
/////////////////
/*
function openGroupChat(group_name, membersList) {
    document.getElementById('groupName').value = group_name;
    document.getElementById('selectedMembers').textContent = membersList; // Set the contact's name

    const groupsDiv = document.querySelector('.group_chats');
    groupsDiv.innerHTML = ''; // Clear previous messages

    fetch(`/get_messages?receiver_email=${email}`)
        .then(response => response.json())
        .then(messages => {
            if (messages.length === 0) {
                messagesDiv.innerHTML = '<p>No messages yet.</p>';
            } else {
                messages.forEach(msg => {
                    const isCurrentUser = msg.sender_user === sessionStorage.getItem('curr_user');
                    const senderName = isCurrentUser ? 'You' : msg.sender_name;
                    const messageParagraph = document.createElement('p');
                    messageParagraph.textContent = `${senderName}: ${msg.content}`;
                    messagesDiv.appendChild(messageParagraph);
                });
            }
        })
        .catch(error => console.log('Error fetching messages:', error));

    // Join a unique room for this conversation
    const currentUser = sessionStorage.getItem('curr_user');
    const room_id = `${Math.min(currentUser, email)}-${Math.max(currentUser, email)}`;
    socket.emit('join', { room_id, receiver_user: email }); // Trigger the join event with data
}

*/
function sendMessage(event) {
    event.preventDefault(); // Prevent the default form submission
    const receiverEmail = document.getElementById('receiver').value;
    const messageInput = document.getElementById('messageInput');
    const messageContent = messageInput.value;

    socket.emit('message', { room_id: currentRoom, message: messageContent });

    messageInput.value = ''; // Clear the input after sending
}


function toggleCreateGroupChatForm() {
    const modal = document.getElementById('createGroupChatModal');
    modal.style.display = 'block';

    const closeButton = document.getElementById('closeModal');
    closeButton.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    const createButton = document.getElementById('createGroupChat');
    createButton.onclick = function() {
        createGroupChat(new Event('submit'));  // Manually pass a new event
        modal.style.display = 'none';
    };
}


function createGroupChat(event) {
    event.preventDefault();
    const groupName = document.getElementById('groupName').value;
    const groupMembers = selectedMembers;
    console.log({ groupName, groupMembers });
    // Here you can save the group name and members to your database
    fetch('/create_group_chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            group_name: groupName,
            members: groupMembers,
        })
    })
    .then(response => response.json())
    .then(data => {
        alert('Group chat created successfully!');

        // Optionally, update the UI to display the new group chat
    })
    .catch(error => {
        error.response.json().then(err => {
            alert('Failed to create group chat: ' + err.error);
        });
        //alert(data);

    });
}
