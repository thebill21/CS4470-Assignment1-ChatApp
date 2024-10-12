import socket  # Importing socket library for network communication
import threading  # Importing threading to handle multiple clients concurrently
import sys  # Importing sys to handle command-line arguments and system functions

# Global variables
connections = {}  # Dictionary to store active connections in the format {id: (socket, address)}
peer_port = None  # Global variable to store the port this instance is listening on
connection_id_counter = 1  # Global counter for connection IDs
available_ids = []  # List of reusable connection IDs
connections_lock = threading.Lock()  # Lock to prevent race conditions on shared connection data

# List of available commands and the command manual
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
    """Display the available command options."""
    print(command_manual)

def get_my_ip():
    """Retrieve and display the correct local IP address."""
    try:
        # Open a dummy socket to an external server (Google's public DNS at 8.8.8.8)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to the server (no actual data is sent)
        s.connect(('8.8.8.8', 80))
        # Get the IP address of the local machine
        ip_address = s.getsockname()[0]
        s.close()  # Close the socket after retrieving the IP
    except Exception as e:
        # If there's an error, default to localhost
        print(f"Error retrieving IP: {e}")
        ip_address = "127.0.0.1"
    print(f"IP Address: {ip_address}")
    return ip_address

def get_my_port():
    """Display the port this instance is listening on."""
    print(f"Listening on Port: {peer_port}")

def assign_connection_id():
    """Assign a reusable connection ID or create a new one if none are available."""
    global connection_id_counter
    if available_ids:  # Reuse an ID if available
        return available_ids.pop(0)
    else:  # Otherwise, create a new ID
        connection_id = connection_id_counter
        connection_id_counter += 1
        return connection_id

def handle_client(client_socket, client_address):
    """Handle messages from a connected client."""
    global connection_id_counter
    print(f"Connection from {client_address} established.")  # Notify that a client has connected

    try:
        # Receive the listening port from the client
        listening_port = client_socket.recv(1024).decode('utf-8')  # Receive the client's listening port as a string
        print(f"Peer listening on port {listening_port}")

        # Assign an ID starting from 1 for the new connection
        with connections_lock:
            connection_id = assign_connection_id()
            connections[connection_id] = (client_socket, (client_address[0], listening_port))

        # Infinite loop to listen for messages from the client
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')  # Receive up to 1024 bytes of data from the client
                if message:  # If a valid message is received
                    print(f"Message received from {client_address[0]}:{listening_port}\nMessage: {message}")
                else:  # If no message is received, break the loop (connection closed)
                    break
            except Exception as e:
                print(f"Error receiving message from {client_address}: {e}")
                break

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")

    # Remove the client after disconnection
    client_socket.close()  # Close the client's socket

    # Check if the connection still exists in the dictionary before deleting it
    with connections_lock:
        if connection_id in connections:
            del connections[connection_id]  # Remove the client from the connections dictionary
            available_ids.append(connection_id)  # Make the ID reusable
            print(f"Connection with {client_address} terminated.")  # Notify that the client disconnected

def connect_to_peer(destination, port):
    """Establish a connection to a remote peer if one does not already exist."""
    with connections_lock:
        # Check if a connection to the destination IP and port already exists
        for conn_data in connections.values():
            existing_ip, existing_port = conn_data[1]
            if existing_ip == destination and existing_port == port:
                print(f"Error: Already connected to {destination}:{port}")
                return  # Prevent duplicate connections

    try:
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket
        peer_socket.connect((destination, int(port)))  # Connect to the destination IP and port
        print(f"Connected to {destination}:{port}.")  # Confirm successful connection

        # Send this peer's listening port to the connected peer
        peer_socket.sendall(str(peer_port).encode())  # Send our own listening port as a string

        # Add the connection to the dictionary using destination IP and port
        with connections_lock:
            connection_id = assign_connection_id()
            connections[connection_id] = (peer_socket, (destination, port))

        # Start a new thread to listen for messages from the connected peer
        threading.Thread(target=handle_peer_messages, args=(peer_socket, destination, port)).start()

    except Exception as e:  # Handle connection errors
        print(f"Failed to connect to {destination}:{port}. Error: {e}")

def list_connections():
    """Display a numbered list of all active connections."""
    print("ID: IP Address      Port")  # Display header
    with connections_lock:
        for conn_id, conn_data in connections.items():  # Loop through all active connections
            ip, port = conn_data[1]  # Extract the IP and listening port of each connection
            print(f"{conn_id}: {ip}      {port}")  # Display the connection ID, IP, and port

def terminate_connection(conn_id):
    """Terminate the connection with the specified ID."""
    with connections_lock:
        if conn_id in connections:  # Check if the connection ID exists
            try:
                connections[conn_id][0].close()  # Close the connection's socket
                del connections[conn_id]  # Remove the connection from the dictionary
                available_ids.append(conn_id)  # Reuse the connection ID
                print(f"Connection {conn_id} terminated.")  # Notify that the connection has been terminated
            except Exception as e:
                print(f"Error terminating connection {conn_id}: {e}")
        else:
            print(f"No such connection with ID: {conn_id}")  # Error message if the connection ID doesn't exist

def send_message(conn_id, message):
    """Send a message to the specified connection ID."""
    with connections_lock:
        if conn_id in connections:  # Check if the connection ID exists
            connections[conn_id][0].sendall(message.encode())  # Send the message to the corresponding peer
            print(f"Message sent to connection {conn_id}.")  # Confirm message sent
        else:
            print(f"No such connection with ID: {conn_id}")  # Error message if the connection ID doesn't exist

def exit_program():
    """Close all connections and notify all peers of the disconnection before terminating the program."""
    # Notify all connected peers that this peer is exiting
    with connections_lock:
        for conn_id, conn_data in list(connections.items()):
            try:
                # Send a disconnection message to the peer
                conn_data[0].sendall("exit".encode())
            except Exception as e:
                print(f"Error sending exit message to peer {conn_data[1]}: {e}")

        # Now terminate the connections
        for conn_id in list(connections.keys()):
            terminate_connection(conn_id)  # Terminate each connection

        connections.clear()  # Clear the connections dictionary
        print("All connections closed. Exiting program.")  # Notify that all connections have been closed
    sys.exit(0)  # Exit the program

def handle_peer_messages(peer_socket, peer_ip, peer_port):
    """Listen for messages from a connected peer and handle disconnections."""
    while True:
        try:
            message = peer_socket.recv(1024).decode('utf-8')  # Receive up to 1024 bytes of data
            if message == "exit":  # If the peer is exiting
                print(f"Peer at {peer_ip}:{peer_port} has exited the chat.")
                break  # Exit the loop and close the connection
            elif message:  # If a valid message is received
                print(f"Message received from {peer_ip}:{peer_port}\nMessage: {message}")  # Display the message
            else:  # If no message is received, break the loop (connection closed)
                break
        except Exception as e:
            print(f"Error receiving message from {peer_ip}:{peer_port}: {e}")
            break

    # Remove the peer after disconnection
    peer_socket.close()  # Close the peer's socket
    # Find the connection ID associated with this peer and remove it
    with connections_lock:
        for conn_id, conn_data in list(connections.items()):
            if conn_data[1] == (peer_ip, peer_port):
                if conn_id in connections:  # Extra check to avoid KeyError if already deleted
                    del connections[conn_id]  # Remove the peer from the connections dictionary
                    available_ids.append(conn_id)  # Reuse the connection ID
                    print(f"Connection with {peer_ip}:{peer_port} terminated.")  # Notify that the peer disconnected
                break

def accept_clients(server_socket):
    """Accept incoming client connections and handle them in separate threads."""
    while True:
        client_socket, client_address = server_socket.accept()  # Wait for a client to connect
        print(f"New connection from {client_address}")  # Notify of the new connection
        # Start a new thread to handle the client
        threading.Thread(target=handle_client, args=(client_socket, client_address)).start()

def main():
    """Main function to start the server and handle user commands."""
    global peer_port  # Access the global peer_port variable

    if len(sys.argv) != 2:  # Ensure the correct number of command-line arguments is provided
        print("Usage: python chat.py <port>")  # Display usage information if incorrect arguments are provided
        sys.exit(1)  # Exit the program with an error

    peer_port = int(sys.argv[1])  # Store the provided port number

    # Start the server to listen for incoming connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket
    server_socket.bind(('', peer_port))  # Bind the socket to the provided port
    server_socket.listen(5)  # Listen for up to 5 incoming connections
    print(f"Server listening on port {peer_port}...")  # Confirm the server is listening

    # Start a thread to accept incoming client connections
    threading.Thread(target=accept_clients, args=(server_socket,)).start()

    # Command interface loop
    while True:
        command = input(">> ").strip().split()  # Prompt user for a command
        if len(command) == 0:  # Check if the input is empty
            continue  # If empty, ignore and continue waiting for valid input
        if command[0] not in commands:  # If the command is not valid
            print("Invalid command. Type 'help' for a list of available commands.")  # Notify of invalid command
            continue  # Skip to the next command

        # Handle each command
        if command[0] == 'help':
            show_help()  # Show the list of commands
        elif command[0] == 'myip':
            get_my_ip()  # Display the local IP address
        elif command[0] == 'myport':
            get_my_port()  # Display the port number
        elif command[0] == 'connect':
            if len(command) == 3:
                connect_to_peer(command[1], command[2])  # Connect to the specified peer
            else:
                print("Usage: connect <destination> <port no>")  # Show usage if arguments are incorrect
        elif command[0] == 'list':
            list_connections()  # List all active connections
        elif command[0] == 'terminate':
            if len(command) == 2 and command[1].isdigit():
                terminate_connection(int(command[1]))  # Terminate the specified connection
            else:
                print("Usage: terminate <connection id>")  # Show usage if arguments are incorrect
        elif command[0] == 'send':
            if len(command) > 2 and command[1].isdigit():
                send_message(int(command[1]), " ".join(command[2:]))  # Send a message to the specified connection
            else:
                print("Usage: send <connection id> <message>")  # Show usage if arguments are incorrect
        elif command[0] == 'exit':
            exit_program()  # Close all connections and exit the program

if __name__ == '__main__':
    main()  # Run the main function when the script is executed