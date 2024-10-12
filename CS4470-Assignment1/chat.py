import socket  # Importing socket library for creating network connections and communication
import threading  # Importing threading library to handle multiple client connections simultaneously
import sys  # Importing sys library to access command-line arguments and system functions

# Global variables
connections = {}  # Dictionary to keep track of active connections in the format {id: (socket, (ip, port))}
peer_port = None  # Variable to store the port number this server instance is listening on
connection_id_counter = 1  # Counter to assign unique connection IDs for each new connection
available_ids = []  # List of reusable connection IDs, used when connections are terminated
connections_lock = threading.Lock()  # A lock to prevent race conditions when accessing shared connection data

# List of available commands and the command manual for the user
commands = ['help', 'myip', 'myport', 'connect', 'list', 'terminate', 'send', 'exit']
command_manual = """
Available commands:
1. help: Display information about the available user interface options or command manual.
2. myip: Display the IP address of this process.
3. myport: Display the port on which this process is listening for incoming connections.
4. connect <destination> <port no>: Establish a new TCP connection to the specified <destination> at the specified <port no>.
5. list: Display a numbered list of all the connections this process is part of.
6. terminate <connection id.>: Terminate the connection listed under the specified number when LIST is used to display all connections.
7. send <connection id> <message>: Send the message to the host on the connection that is designated by the number.
8. exit: Close all connections and terminate this process.
"""

def show_help():
    """Display the available command options by printing the command manual."""
    print(command_manual)

def get_my_ip():
    """Retrieve and display the IP address of the machine."""
    try:
        # Create a UDP socket (this does not establish a connection)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use the socket to connect to an external server to determine the local IP address
        s.connect(('8.8.8.8', 80))
        # Get the IP address from the socket's information
        ip_address = s.getsockname()[0]
        s.close()  # Close the socket after retrieving the IP address
    except Exception as e:
        # If there is an error, fallback to localhost and print the error message
        print(f"Error retrieving IP: {e}")
        ip_address = "127.0.0.1"
    print(f"IP Address: {ip_address}")
    return ip_address

def get_my_port():
    """Display the port number that the current instance is listening on."""
    print(f"Listening on Port: {peer_port}")

def assign_connection_id():
    """Assign a connection ID by reusing available IDs or creating a new one."""
    global connection_id_counter
    if available_ids:  # Check if there are any reusable connection IDs
        # Return and remove the first reusable ID from the list
        return available_ids.pop(0)
    else:
        # If no reusable IDs, use the next available number from the counter
        connection_id = connection_id_counter
        connection_id_counter += 1  # Increment the counter for the next connection
        return connection_id

def handle_client(client_socket, client_address):
    """
    Manage communication with a connected client.
    - Receive the client's listening port.
    - Store the client's information.
    - Continuously listen for messages from the client.
    """
    print(f"Connection from {client_address} established.")  # Notify that a client has connected
    try:
        # Receive the listening port from the client, which indicates where it can receive messages
        listening_port = client_socket.recv(1024).decode('utf-8')
        print(f"Peer listening on port {listening_port}")
        # Assign a unique connection ID for the new client
        with connections_lock:  # Lock the access to shared resources to avoid race conditions
            connection_id = assign_connection_id()
            # Store the client's socket and its IP and listening port
            connections[connection_id] = (client_socket, (client_address[0], listening_port))

        # Loop to continuously listen for incoming messages from the client
        while True:
            try:
                # Receive a message from the client (up to 1024 bytes)
                message = client_socket.recv(1024).decode('utf-8')
                if message:  # If a message is received, display it
                    print(f"Message received from {client_address[0]}:{listening_port}\nMessage: {message}")
                else:  # If no message is received, assume the connection is closed
                    break
            except Exception as e:  # Catch any exceptions while receiving messages
                print(f"Error receiving message from {client_address}: {e}")
                break
    except Exception as e:  # Handle any initial connection errors
        print(f"Error handling client {client_address}: {e}")

    # Once the connection is closed, clean up the client's resources
    client_socket.close()
    with connections_lock:  # Lock the access to shared resources for thread safety
        if connection_id in connections:  # Check if the connection is still listed
            del connections[connection_id]  # Remove the connection from the dictionary
            available_ids.append(connection_id)  # Add the ID back to the reusable pool
            print(f"Connection with {client_address} terminated.")  # Notify that the connection has been terminated

def connect_to_peer(destination, port):
    """
    Establish a connection to another peer by creating a socket connection.
    - Check if a connection already exists to avoid duplicate connections.
    - Start a new thread to handle incoming messages from the peer.
    """
    with connections_lock:  # Lock the access to shared resources
        # Check if the connection already exists to the same destination and port
        for conn_data in connections.values():
            existing_ip, existing_port = conn_data[1]
            if existing_ip == destination and existing_port == port:
                print(f"Error: Already connected to {destination}:{port}")
                return

    try:
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
        peer_socket.connect((destination, int(port)))  # Connect to the specified destination and port
        print(f"Connected to {destination}:{port}.")
        peer_socket.sendall(str(peer_port).encode())  # Send the local listening port to the peer

        # Assign a unique ID and store the connection
        with connections_lock:
            connection_id = assign_connection_id()
            connections[connection_id] = (peer_socket, (destination, port))

        # Start a thread to listen for messages from this peer
        threading.Thread(target=handle_peer_messages, args=(peer_socket, destination, port)).start()
    except Exception as e:  # Catch any connection errors
        print(f"Failed to connect to {destination}:{port}. Error: {e}")

def list_connections():
    """Display a list of all active connections by iterating through the connections dictionary."""
    print("ID: IP Address      Port")
    with connections_lock:  # Lock the access to shared resources
        for conn_id, conn_data in connections.items():
            ip, port = conn_data[1]  # Get the IP and port from the connection data
            print(f"{conn_id}: {ip}      {port}")  # Display the connection ID, IP, and port

def terminate_connection(conn_id):
    """
    Gracefully terminate a connection by sending a termination notice.
    - Notify the peer before closing the socket.
    - Update the connections dictionary.
    """
    with connections_lock:  # Lock the access to shared resources
        if conn_id in connections:  # Verify that the connection ID exists
            try:
                # Notify the peer that the connection is being terminated
                connections[conn_id][0].sendall("terminate".encode())
                connections[conn_id][0].close()  # Close the socket connection
                del connections[conn_id]  # Remove the connection from the dictionary
                available_ids.append(conn_id)  # Add the connection ID back to the reusable pool
                print(f"Connection {conn_id} terminated.")
            except Exception as e:  # Handle any termination errors
                print(f"Error terminating connection {conn_id}: {e}")
        else:
            print(f"No such connection with ID: {conn_id}")

def send_message(conn_id, message):
    """Send a message to the specified connection ID, if it exists."""
    with connections_lock:  # Lock the access to shared resources
        if conn_id in connections:  # Verify the connection ID
            connections[conn_id][0].sendall(message.encode())  # Send the message to the peer
            print(f"Message sent to connection {conn_id}.")
        else:
            print(f"No such connection with ID: {conn_id}")

def exit_program():
    """
    Close all connections and terminate the program.
    - Notify all connected peers that the local instance is exiting.
    - Terminate all connections gracefully.
    """
    # Notify all peers that this instance is exiting
    for conn_id, conn_data in list(connections.items()):
        try:
            conn_data[0].sendall("exit".encode())  # Inform the peer about the exit
        except Exception as e:
            print(f"Error sending exit message to peer {conn_data[1]}: {e}")

    # Terminate each connection individually
    for conn_id in list(connections.keys()):
        terminate_connection(conn_id)

    connections.clear()  # Clear the connections dictionary
    print("All connections closed. Exiting program.")
    sys.exit(0)  # Exit the program

def handle_peer_messages(peer_socket, peer_ip, peer_port):
    """
    Listen for messages from a connected peer.
    - Handle different types of messages (e.g., termination, exit).
    - Clean up resources when the connection is closed.
    """
    while True:
        try:
            # Wait for a message from the peer
            message = peer_socket.recv(1024).decode('utf-8')
            if message == "exit":  # If the peer is exiting
                print(f"Peer at {peer_ip}:{peer_port} has exited the chat.")
                break
            elif message == "terminate":  # Handle a termination message
                print(f"Connection with {peer_ip}:{peer_port} is terminated by the server.")
                break
            elif message:  # If a regular message is received
                print(f"Message received from {peer_ip}:{peer_port}\nMessage: {message}")
            else:  # If no message is received, the connection may be closed
                break
        except ConnectionResetError:  # Handle connection reset errors gracefully
            print(f"Error receiving message from {peer_ip}:{peer_port}: Connection reset by peer.")
            break
        except Exception as e:  # Catch other exceptions
            print(f"Error receiving message from {peer_ip}:{peer_port}: {e}")
            break

    # Clean up after the connection is closed
    peer_socket.close()
    with connections_lock:
        # Remove the peer from the connections dictionary if it exists
        for conn_id, conn_data in list(connections.items()):
            if conn_data[1] == (peer_ip, peer_port):
                if conn_id in connections:
                    del connections[conn_id]
                    available_ids.append(conn_id)
                    print(f"Connection with {peer_ip}:{peer_port} terminated.")
                break

def accept_clients(server_socket):
    """
    Accept incoming client connections and handle them in separate threads.
    - Each client connection is handled by a new thread to allow concurrent connections.
    """
    while True:
        client_socket, client_address = server_socket.accept()  # Wait for an incoming connection
        print(f"New connection from {client_address}")  # Notify about the new connection
        # Start a new thread to manage the connected client
        threading.Thread(target=handle_client, args=(client_socket, client_address)).start()

def main():
    """
    Main function to start the server and handle user commands.
    - Set up the server to listen for incoming connections.
    - Create a user interface loop to process commands.
    """
    global peer_port  # Access the global peer_port variable
    if len(sys.argv) != 2:  # Verify that a port number has been provided
        print("Usage: python chat.py <port>")  # Display usage instructions
        sys.exit(1)
    peer_port = int(sys.argv[1])  # Assign the specified port number
    # Create a server socket to listen for incoming connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', peer_port))  # Bind the server socket to the specified port
    server_socket.listen(5)  # Allow up to 5 concurrent connections
    print(f"Server listening on port {peer_port}...")
    # Start a thread to accept incoming client connections
    threading.Thread(target=accept_clients, args=(server_socket,)).start()
    # Command interface loop for processing user commands
    while True:
        command = input(">> ").strip().split()
        if len(command) == 0:
            continue  # Ignore empty commands
        if command[0] not in commands:
            print("Invalid command. Type 'help' for a list of available commands.")
            continue
        # Process each command based on the user's input
        if command[0] == 'help':
            show_help()
        elif command[0] == 'myip':
            get_my_ip()
        elif command[0] == 'myport':
            get_my_port()
        elif command[0] == 'connect':
            if len(command) == 3:
                connect_to_peer(command[1], command[2])
            else:
                print("Usage: connect <destination> <port no>")
        elif command[0] == 'list':
            list_connections()
        elif command[0] == 'terminate':
            if len(command) == 2 and command[1].isdigit():
                terminate_connection(int(command[1]))
            else:
                print("Usage: terminate <connection id>")
        elif command[0] == 'send':
            if len(command) > 2 and command[1].isdigit():
                send_message(int(command[1]), " ".join(command[2:]))
            else:
                print("Usage: send <connection id> <message>")
        elif command[0] == 'exit':
            exit_program()

if __name__ == '__main__':
    main()