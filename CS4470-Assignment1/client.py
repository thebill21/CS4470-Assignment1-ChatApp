# Importing the necessary libraries
import socket
import threading

# Defining the IP address and port number
HOST = '127.0.0.1' # Localhost
PORT = 12345 # Port number

# Function to listen for incoming messages from the server
def listen_for_messages(client):
    while True:
        message = client.recv(2048).decode('utf-8')
        if message != '':
            username = message.split(": ")[0]
            content = message.split(": ")[1]

            print(f"[{username}]: {content}")
        else:
            print(f"The message from server is empty.")
            break

# Function to send messages to the server
def send_message(client):
    while True:
        message = input("Enter a message to send to the server: ")
        #client.sendall(message.encode())
        if message != '':
            client.sendall(message.encode())
        else:
            print(f"The message cannot be empty.")
            exit(0)

# Function to communicate with the server
def communicate_with_server(client):
    username = input("Enter your username: ")
    if username != '':
        client.sendall(username.encode())
    else:
        print(f"Username cannot be empty.")
        exit(0) 

    threading.Thread(target=listen_for_messages, args=(client,)).start()
    # threading.Thread(target=send_message, args=(client,)).start()
    send_message(client)

# Main Function
def main():
    # Create a client socket class object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET -> IPv4, SOCK_STREAM -> TCP

    # Connect to the server
    try:
        client.connect((HOST, PORT))
        print(f"Client connected to the server at {HOST}:{PORT}.")
    except:
        print(f"Client failed to connect to the server at {HOST}:{PORT}.")
        return

    communicate_with_server(client)

if __name__ == '__main__':
    main()