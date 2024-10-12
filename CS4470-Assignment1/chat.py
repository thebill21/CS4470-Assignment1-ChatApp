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
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip_address = s.getsockname()[0]
        s.close()
    except Exception as e:
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
    if available_ids:
        return available_ids.pop(0)
    else:
        connection_id = connection_id_counter
        connection_id_counter += 1
        return connection_id

def handle_client(client_socket, client_address):
    """Handle messages from a connected client."""
    print(f"Connection from {client_address} established.")
    try:
        listening_port = client_socket.recv(1024).decode('utf-8')
        print(f"Peer listening on port {listening_port}")
        with connections_lock:
            connection_id = assign_connection_id()
            connections[connection_id] = (client_socket, (client_address[0], listening_port))
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    print(f"Message received from {client_address[0]}:{listening_port}\nMessage: {message}")
                else:
                    break
            except Exception as e:
                print(f"Error receiving message from {client_address}: {e}")
                break
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    client_socket.close()
    with connections_lock:
        if connection_id in connections:
            del connections[connection_id]
            available_ids.append(connection_id)
            print(f"Connection with {client_address} terminated.")

def connect_to_peer(destination, port):
    with connections_lock:
        for conn_data in connections.values():
            existing_ip, existing_port = conn_data[1]
            if existing_ip == destination and existing_port == port:
                print(f"Error: Already connected to {destination}:{port}")
                return
    try:
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect((destination, int(port)))
        print(f"Connected to {destination}:{port}.")
        peer_socket.sendall(str(peer_port).encode())
        with connections_lock:
            connection_id = assign_connection_id()
            connections[connection_id] = (peer_socket, (destination, port))
        threading.Thread(target=handle_peer_messages, args=(peer_socket, destination, port)).start()
    except Exception as e:
        print(f"Failed to connect to {destination}:{port}. Error: {e}")

def list_connections():
    """Display a numbered list of all active connections."""
    print("ID: IP Address      Port")
    with connections_lock:
        for conn_id, conn_data in connections.items():
            ip, port = conn_data[1]
            print(f"{conn_id}: {ip}      {port}")

def terminate_connection(conn_id):
    """Gracefully terminate the connection with the specified ID."""
    with connections_lock:
        if conn_id in connections:  # Check if the connection ID exists
            try:
                # Send a disconnection notice to the peer
                connections[conn_id][0].sendall("terminate".encode())  # Inform the client
                # Close the connection's socket
                connections[conn_id][0].close()
                # Remove the connection from the dictionary
                del connections[conn_id]
                available_ids.append(conn_id)  # Reuse the connection ID
                print(f"Connection {conn_id} terminated.")  # Notify that the connection has been terminated
            except Exception as e:
                print(f"Error terminating connection {conn_id}: {e}")
        else:
            print(f"No such connection with ID: {conn_id}")  # Error message if the connection ID doesn't exist

def send_message(conn_id, message):
    with connections_lock:
        if conn_id in connections:
            connections[conn_id][0].sendall(message.encode())
            print(f"Message sent to connection {conn_id}.")
        else:
            print(f"No such connection with ID: {conn_id}")

def exit_program():
    """Close all connections gracefully and terminate the program."""
    # Notify all connected peers that this peer is exiting
    for conn_id, conn_data in list(connections.items()):
        try:
            conn_data[0].sendall("exit".encode())  # Inform peers about the exit
        except Exception as e:
            print(f"Error sending exit message to peer {conn_data[1]}: {e}")

    # Terminate all connections
    for conn_id in list(connections.keys()):
        terminate_connection(conn_id)  # Terminate each connection

    connections.clear()
    print("All connections closed. Exiting program.")
    sys.exit(0)

def handle_peer_messages(peer_socket, peer_ip, peer_port):
    """Listen for messages from a connected peer and handle disconnections."""
    while True:
        try:
            message = peer_socket.recv(1024).decode('utf-8')
            if message == "exit":  # If the peer is exiting
                print(f"Peer at {peer_ip}:{peer_port} has exited the chat.")
                break
            elif message == "terminate":  # Handle terminate message from the server
                print(f"Connection with {peer_ip}:{peer_port} is terminated by the server.")
                break
            elif message:  # If a valid message is received
                print(f"Message received from {peer_ip}:{peer_port}\nMessage: {message}")
            else:
                break
        except ConnectionResetError:  # Catch 'Connection reset by peer' error gracefully
            print(f"Error receiving message from {peer_ip}:{peer_port}: Connection reset by peer.")
            break
        except Exception as e:
            print(f"Error receiving message from {peer_ip}:{peer_port}: {e}")
            break

    # Remove the peer after disconnection
    peer_socket.close()
    with connections_lock:
        for conn_id, conn_data in list(connections.items()):
            if conn_data[1] == (peer_ip, peer_port):
                if conn_id in connections:
                    del connections[conn_id]
                    available_ids.append(conn_id)
                    print(f"Connection with {peer_ip}:{peer_port} terminated.")
                break

def accept_clients(server_socket):
    """Accept incoming client connections and handle them in separate threads."""
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address}")
        threading.Thread(target=handle_client, args=(client_socket, client_address)).start()

def main():
    global peer_port
    if len(sys.argv) != 2:
        print("Usage: python chat.py <port>")
        sys.exit(1)
    peer_port = int(sys.argv[1])
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', peer_port))
    server_socket.listen(5)
    print(f"Server listening on port {peer_port}...")
    threading.Thread(target=accept_clients, args=(server_socket,)).start()
    while True:
        command = input(">> ").strip().split()
        if len(command) == 0:
            continue
        if command[0] not in commands:
            print("Invalid command. Type 'help' for a list of available commands.")
            continue
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