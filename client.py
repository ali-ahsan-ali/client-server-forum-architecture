# Code by Ali Ali - z5207397 
import sys
from socket import *
import time
import os
import threading
import queue
import ast


# Global variables about the client. This is the username and password of This
# specific client instance. This user is sent to the client with every command
# so that it can tell what resources is created by what user and how to keep 
# track of who has the authority to do what within the forums
global_username = ""

# This is a global variable to know if the heartbeat thread needs to keep asking 
# for a heartbeat or to stop and finish its infinite loop asking for heartbeats,
# joining back with the main thread to execute/send a command request to a 
# server
heartbeat_needed = True


# This reads each byte one by one and stops when it reaches a new line which 
# indicates to the server that the packet has reached its end point and anything 
# after is to not be considered as part of the same request or stream or packet
def get_response(clientSocket):
    response = b""
    while 1:
        new = clientSocket.recv(1)
        if new == b"\n":
            break
        if new == b"":
            break
        else:
            response += new
    response = response.decode('utf-8')
    return response

def death_condition(response):
    if response == "Server is shutting down":
        print("Server is shutting down")
        clientSocket.close()
        os._exit(0)
    if not response:
        print("Socket is dead. Server is down")
        clientSocket.close()
        os._exit(0)

# This is a function that constantly asks the server if they are alive. If the 
# response is that the server is shutting down, it will shut down the socket
# from the client side and close the program. if it recieves an alive response
# it waits another second and sends the heartbeat packet again. if it recieves
# not response then it also shuts down, this is when the server closes the 
# socket due to a server side error.

def heartbeat(clientSocket):
    global heartbeat_needed
    while heartbeat_needed:
        clientSocket.send("are you alive\n".encode('utf-8'))
        response = get_response(clientSocket)
        death_condition(response)
        time.sleep(0.2)

# Asks the user for an input and is a thread that just waits on an input
def get_input(q):
    command = input(
        "Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT," +
        " UPD, DWN, RMV, XIT, SHT: ")
    q.put(command)


# Authenticates a client. Asks for a username to send to a server, if it exists
# in server database, sends a password to check if match. If new user, sends 
# password to log in as new user. 
def authentication(clientSocket):
    global global_username
    authentication = True
    while authentication:
        username = input("Please enter username: ")
        clientSocket.send((username + "\n").encode('utf-8'))
        response = get_response(clientSocket)
        # death_condition(response)
        if response == "User already logged in":
            print(response)
            continue
        if response == "Enter Password For New User":
            print(response)
            password = username = input("Please enter Password: ")
            clientSocket.send((password + "\n").encode('utf-8'))
            global_username = username
            authentication = False
            print(get_response(clientSocket))
            break
            # ask to make new password and add to credentials file
        elif response == "Wrong Password":
            print("wrong Password")
        elif response == "Send Password":
            print("Valid user")
            password = input("Please enter Password: ")
            clientSocket.send((password + "\n").encode('utf-8'))
            response = get_response(clientSocket)
            # death_condition(response)
            if response == "Wrong Password":
                print(response)
                continue
            elif response == "Authenticated":
                print(response)
                authentication = False
                global_username = username
                break 

# Infinite while loop. First thing it does is set heartbeat_needed as true, as 
# it needs to check if the server is alive. It then splits off into two threads.
# one that constantly checks to see if the server is alive and one that waits 
# for the user to put an input in. Once the client recieves an input it joins 
# the threads back, sends the command to the server, if it is a special 
# command that needs more information such as sending of a file after the
# command, the client does so. It then prints the server response to the user 
# or interprets the messages as intented such as turning strings back into a 
# list. Use a queue rather than returning can returning from a thread gets 
# extremely message and rather use a queue
def client_command_sending(clientSocket):
    global heartbeat_needed
    global global_username
    while 1:
        heartbeat_needed = True
        client_input = threading.Thread(
            target=get_input, args=(q,))
        
        pulse = threading.Thread(target=heartbeat, args=(clientSocket,))
        client_input.start()
        pulse.start()

        client_input.join()
        heartbeat_needed = False
        pulse.join()
        command = q.get()
        argument = command.split(" ")
        info = command + " " + global_username
        clientSocket.send(info.encode('utf-8'))
        response = get_response(clientSocket)

        if response == "Enter the correct number of commands" or \
            response == "Thread does not exist" or \
            response == "Enter the correct number of commands":
            print(response)
            continue

        if argument[0] != "LST" and argument[0] != "RDT" \
                and argument[0] != "UDP" and argument[0] != "DWN":
            print(response)

        if response == "Server is shutting down":
            print("\nShutting down client as server has shut down")
            clientSocket.close()
            break

        if argument[0] == "LST":
            if response == "No Threads":
                print(response)
            else:
                print("List of Active threads:")
                response = ast.literal_eval(response)
                for x in response:
                    print(x)
        elif argument[0] == "XIT":
            print("Exiting forums")
            clientSocket.close()
            break
        elif argument[0] == "RDT":
            if response == "No messages in thread":
                print(response)
            else:
                print("List of messages in thread:")
                response = ast.literal_eval(response)
                for x in response:
                    print(x)
        elif argument[0] == "UDP":
            if response == "File uploaded already":
                print(response)
                continue

            # Send file as bytes split up
            length = os.path.getsize(argument[2])
            clientSocket.send((str(length) + "\n").encode('utf-8'))

            with open(argument[2], "rb") as f:
                d = f.read()
                clientSocket.sendall(d)
                f.close()

            response = clientSocket.recv(1024).decode('utf-8')
            print(response)
        elif argument[0] == "DWN":
            if response == "File requested within Thread does not exist":
                print(response)
                continue

            size = int(response)
            l = clientSocket.recv(1024)
            total = len(l)
            file = open(argument[2], "wb")
            while(l):
                file.write(l)
                if (size - total) < 1024:
                    l = clientSocket.recv((size - total) )
                    total = total + len(l)
                elif (total < size):
                    l = clientSocket.recv(1024)
                    total = total + len(l)
                    # print(l, total, size)
                else:
                    break
            file.close()
            response = clientSocket.recv(1024).decode('utf-8')
            print(response)
          



# Main program to be elaborated on above
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Incorrect client starting method")
        os._exit(0)
    # Creates a socket and attempts to connect it to the server
    q = queue.Queue()
    serverIP = sys.argv[1]
    serverPort = int(sys.argv[2])
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverIP, serverPort))

    # Authenticates the client
    authentication(clientSocket)
    # Sends client commands to the server correctly 
    client_command_sending(clientSocket)
    
    