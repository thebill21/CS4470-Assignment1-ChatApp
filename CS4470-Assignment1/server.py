import socket
import threading

HOST = '127.0.0.1' # Localhost
PORT = 12345 # Port number
LISTEN_QUEUE = 5 # Number of clients that can wait for a connection
active_clients = [] # List to store all active clients

# Function to listen for incoming messages from the client
def listen_for_messages(client, username):
    while True:
        message = client.recv(2048).decode('utf-8')
        if message != '':
            final_message = f"{username}: {message}"
            # final_message = f'' + username + ": " + message
            broadcast(final_message)
        else:
            print(f"The message from {username} is empty.")

# Function to send messages to all clients connected to the server
def broadcast(message):
    for client in active_clients:
        send_to_client(message, client[1])

# Function to send messages to a specific client
def send_to_client(message, recipient):
    recipient.sendall(message.encode())

# Function to handle client
def handle_client(client):
    # print(f"Connection from {address[0]}:{address[1]} has been established.")
    while True:
        username = client.recv(2048).decode('utf-8')
        if username != '':
            active_clients.append((username, client))
            break
        else:
            print(f"Client's 'username' is empty.")

    # Create a new thread to listen for messages from the client
    threading.Thread(target=listen_for_messages, args=(client, username, )).start()


# Define main function
def main():
    # Create a server socket class object
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET -> IPv4, SOCK_STREAM -> TCP
    
    # Bind the server to the IP address and port
    try:
        server.bind((HOST, PORT))
        print(f"Server is bound to the IP address {HOST} and port {PORT}.")
    except:
        print("Server failed to bind to the IP address {HOST} and port {PORT}.")
        return
    
    # Listen for incoming connections
    server.listen(LISTEN_QUEUE)
    print(f"Server is listening on {HOST}:{PORT}")

    # While loop to keep listening for incoming connections
    while True:
        # Accept incoming connections
        client, address = server.accept()
        print(f"Connected: {address[0]}:{address[1]}.")

        # Create a new thread to handle the client
        threading.Thread(target=handle_client, args=(client, )).start()



if __name__ == '__main__':
    main()