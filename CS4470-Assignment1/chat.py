import socket
import threading
import sys

# Global variables
connections = {}  # Store active connections: {id: (socket, address)}
connection_id = 0  # Connection identifier
peer_port = None  # Port for this instance to listen on

# Command options and manual
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
    print(command_manual)

def get_my_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"IP Address: {ip_address}")
    return ip_address

def get_my_port():
    print(f"Listening on Port: {peer_port}")

def handle_client(client_socket, client_address):
    global connection_id
    print(f"Connection from {client_address} established.")
    connections[connection_id] = (client_socket, client_address)
    connection_id += 1

    # Listen for incoming messages
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                # [Change] Updated message format to include the IP and port of the sender
                print(f"Message received from {client_address[0]}:{client_address[1]}\nMessage: {message}")
            else:
                break
        except:
            break

    # Remove client after disconnection
    client_socket.close()
    del connections[connection_id]
    print(f"Connection with {client_address} terminated.")

def connect_to_peer(destination, port):
    try:
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect((destination, int(port)))
        print(f"Connected to {destination}:{port}.")
        connections[len(connections)] = (peer_socket, (destination, port))

        # Start a thread to listen for incoming messages from this peer
        threading.Thread(target=handle_peer_messages, args=(peer_socket, destination, port)).start()
    except Exception as e:
        print(f"Failed to connect to {destination}:{port}. Error: {e}")

def list_connections():
    print("ID: IP Address      Port")
    for conn_id, conn_data in connections.items():
        ip, port = conn_data[1]
        print(f"{conn_id}: {ip}      {port}")

def terminate_connection(conn_id):
    if conn_id in connections:
        connections[conn_id][0].close()
        del connections[conn_id]
        print(f"Connection {conn_id} terminated.")
    else:
        print(f"No such connection with ID: {conn_id}")

def send_message(conn_id, message):
    if conn_id in connections:
        connections[conn_id][0].sendall(message.encode())
        print(f"Message sent to connection {conn_id}.")
    else:
        print(f"No such connection with ID: {conn_id}")

def exit_program():
    for conn in connections.values():
        conn[0].close()
    connections.clear()
    print("All connections closed. Exiting program.")
    sys.exit(0)

def handle_peer_messages(peer_socket, peer_ip, peer_port):
    # [Change] Added peer IP and port information for consistency in message display
    while True:
        try:
            message = peer_socket.recv(1024).decode('utf-8')
            if message:
                # Display message with sender's IP and port
                print(f"Message received from {peer_ip}:{peer_port}\nMessage: {message}")
            else:
                break
        except:
            break

def accept_clients(server_socket):
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

    # Start the server to listen for incoming connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', peer_port))
    server_socket.listen(5)
    print(f"Server listening on port {peer_port}...")

    # Start a thread to accept incoming client connections
    threading.Thread(target=accept_clients, args=(server_socket,)).start()

    # Command interface loop
    while True:
        command = input(">> ").strip().split()
        if command[0] not in commands:
            print("Invalid command. Type 'help' for a list of available commands.")
            continue

        # Handle command execution
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
