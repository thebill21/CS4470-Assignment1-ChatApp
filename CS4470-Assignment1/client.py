# Importing the necessary libraries
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox

# Defining the IP address and port number
HOST = '127.0.0.1' # Localhost
PORT = 12345 # Port number


#=====================================GUI==============================================================
#Create font and color variables
TOP_FRAME_COLOR = 'blue'
MIDDLE_FRAME_COLOR = 'green'
BOTTOM_FRAME_COLOR = 'red'
FONT = 'Times New Roman'
USERNAME_LABEL_COLOR = 'white'
USERNAME_LABEL_BACKGROUND_COLOR='blue'
USERNAME_BUTTON_COLOR = 'white'
USERNAME_BUTTON_BACKGROUND_COLOR = 'blue'
SEND_BUTTON_COLOR = 'white'
SEND_BUTTON_BACKGROUND_COLOR = 'blue'
MESSAGE_BOX_COLOR = 'white'
MESSAGE_BOX_BACKGROUND_COLOR = 'blue'

# Create a client socket class object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET -> IPv4, SOCK_STREAM -> TCP

# Function to update the message box
def update_message_box(message):
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END, message + '\n')
    message_box.config(state=tk.DISABLED)

# Function to connect to the server
def connect():
    # Connect to the server
    try:
        client.connect((HOST, PORT))
        print(f"Client connected to the server at {HOST}:{PORT}.")
        update_message_box(f"Client connected to the server at {HOST}:{PORT}.")
    except:
        messagebox.showerror("Cannot connect to server", f"Client failed to connect to the server at {HOST}:{PORT}.")

    # Send the username to the server
    username = username_textbox.get()
    if username != '':
        client.sendall(username.encode())
    else:
        messagebox.showerror("Invalid Username", f"Username cannot be empty.") 

    threading.Thread(target=listen_for_messages, args=(client,)).start()

    # Disable the username textbox and button after joining chat
    username_textbox.config(state=tk.DISABLED)
    username_button.config(state=tk.DISABLED)

# Function to send a message to the server
def send_message():
    message = message_textbox.get()
    if message != '':
        client.sendall(message.encode())
        message_textbox.delete(0, tk.END)
    else:
        messagebox.showerror("Message Error", f"The message cannot be empty.")

# Create a root window
root = tk.Tk()
# Setting the title and dimensions of the window
root.title("CS 4470 - Assignment 1 - Chat Client")
root.geometry("600x800")
root.resizable(False, False)

# Set the weight of the rows and columns
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=5)
root.grid_rowconfigure(2, weight=2)

# Divide the windows to sections
top_frame = tk.Frame(root, width=600, height=100, bg=TOP_FRAME_COLOR)
top_frame.grid(row=0, column=0, sticky=tk.NSEW)

middle_frame = tk.Frame(root, width=600, height=500, bg=MIDDLE_FRAME_COLOR)
middle_frame.grid(row=1, column=0, sticky=tk.NSEW)

bottom_frame = tk.Frame(root, width=600, height=200, bg=BOTTOM_FRAME_COLOR)
bottom_frame.grid(row=2, column=0, sticky=tk.NSEW)

# Create a label "Username" and input text box and submit button
username_label = tk.Label(top_frame, text="Username:", font=(FONT, 20), bg=USERNAME_LABEL_BACKGROUND_COLOR, fg=USERNAME_LABEL_COLOR)
username_label.pack(side=tk.LEFT, padx=10, pady=10)

username_textbox = tk.Entry(top_frame, font=(FONT, 20))
username_textbox.pack(side=tk.LEFT, padx=15, pady=10)

username_button = tk.Button(top_frame, text="Join Chat", font=(FONT, 20), bg=USERNAME_BUTTON_BACKGROUND_COLOR, fg=USERNAME_BUTTON_COLOR,  command=connect)
username_button.pack(side=tk.RIGHT, padx=10, pady=10)

# Create an entry box to send messages with button
message_textbox = tk.Entry(bottom_frame, font=(FONT, 20))
message_textbox.pack(side=tk.LEFT, padx=10, pady=10)

send_button = tk.Button(bottom_frame, text="Send", font=(FONT, 20), bg=SEND_BUTTON_BACKGROUND_COLOR, fg=SEND_BUTTON_COLOR, command=send_message)
send_button.pack(side=tk.RIGHT, padx=10, pady=10)

# Create a message box to display messages
message_box = scrolledtext.ScrolledText(middle_frame, wrap=tk.WORD, width=40, height=20, font=(FONT, 20), bg=MESSAGE_BOX_BACKGROUND_COLOR, fg=MESSAGE_BOX_COLOR)
message_box.config(state=tk.DISABLED)
message_box.pack(side=tk.TOP ,padx=10, pady=10)
#=====================================GUI==============================================================

# # Defining the IP address and port number
# HOST = '127.0.0.1' # Localhost
# PORT = 12345 # Port number



# Function to listen for incoming messages from the server
def listen_for_messages(client):
    while True:
        message = client.recv(2048).decode('utf-8')
        if message != '':
            username = message.split(": ")[0]
            content = message.split(": ")[1]

            update_message_box(f"[{username}]: {content}")
        else:
            messagebox.showerror("Message Error" ,f"The message from server is empty.")
            break

# # Function to send messages to the server
# def send_message(client):
#     while True:
#         message = input("Enter a message to send to the server: ")
#         #client.sendall(message.encode())
#         if message != '':
#             client.sendall(message.encode())
#         else:
#             print(f"The message cannot be empty.")
#             exit(0)

# # Function to communicate with the server
# def communicate_with_server(client):
#     username = input("Enter your username: ")
#     if username != '':
#         client.sendall(username.encode())
#     else:
#         print(f"Username cannot be empty.")
#         exit(0) 

#     threading.Thread(target=listen_for_messages, args=(client,)).start()
#     # threading.Thread(target=send_message, args=(client,)).start()
#     send_message(client)

# Main Function
def main():

    root.mainloop()

    # # Create a client socket class object
    # client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET -> IPv4, SOCK_STREAM -> TCP

    # # Connect to the server
    # try:
    #     client.connect((HOST, PORT))
    #     print(f"Client connected to the server at {HOST}:{PORT}.")
    # except:
    #     print(f"Client failed to connect to the server at {HOST}:{PORT}.")
    #     return

    # communicate_with_server(client)

if __name__ == '__main__':
    main()