# Code by Ali Ali - z5207397 
import sys
from socket import *
import os
# This import below is just for testing cases where i do not want to entire
# remove a file for testing purposes but is hopefully commented out during 
# submission
# from send2trash import send2trash
import threading
import select
import ipaddress

# Theses are tge global variables. Although it is usually considered poor 
# styling to have global variables. It is necessary in the case of 
# multithreading. I keep track of all clients, threads, uploads and users to be
# fed to a thread so they can check whether or not a user is logged in or a 
# thread/upload exists within the server 
t_lock = threading.Condition()
clients = []
users = []
forum_threads = []
forum_threads_uploads = []

# This reads each byte one by one and stops when it reaches a new line which 
# indicates to the server that the packet has reached its end point and anything 
# after is to not be considered as part of the same request or stream or packet    

def get_req(connectionSocket):
    req = b""
    while 1:
        new = connectionSocket.recv(1)
        if new == b"\n":
            break
        if new == b"":
            break
        else:
            req += new
    req = req.decode('utf-8')
    return req

# Reads all the lines in the file and returns it as a list
def read_file(fname):
    with open(fname, "r") as infile:
        lines = infile.readlines()
    return lines

# Finds the maximum msg number of a file 
def max_msg_num(fname):
    count = 0
    lines = read_file(fname)
    for pos, line in enumerate(lines):
        split = line.split(" ")
        if split[0].isnumeric():
            count = max(count, int(split[0]))
    return count + 1

# Deletes a message with the correct message number. Error checking for deletion
# is done within the DLT function or function thats use this function and not 
# within this function. I.e if msg_num is integer or not is checked elsewhere
def del_message(fname, msg_num):
    lines = read_file(fname)
    with open(fname, "w") as outfile:
        for pos, line in enumerate(lines):
            split = line.split(" ")
            if split[0] == msg_num:
                continue
            elif pos != 0 and split[0] > msg_num:
                if split[0].isnumeric():
                    split[0] = str(int(split[0]) - 1)
                else:
                    split[0] = split[0]
                write = ""
                for i, x in enumerate(split):
                    if i == len(split) - 1:
                        write += x
                    else:
                        write += x + " "
                outfile.write(write)
            else:
                outfile.write(line)

# Edits a messages within a file given a msg_num and a msg
def edit_message(fname, msg_num, msg):
    lines = read_file(fname)
    with open(fname, "w") as outfile:
        for pos, line in enumerate(lines):
            split = line.split(" ")
            if split[0] == msg_num:
                outfile.write(msg)
            else:
                outfile.write(line)

# Checks to see if a msg number exists within a file
def check_message(fname, msg_num):
    lines = read_file(fname)
    for pos, line in enumerate(lines):
        split = line.split(" ")
        if split[0] == msg_num:
            return True
    return False

# Checks to see if the msg_number has been written by the user inputted
def check_message_user(fname, msg_num, user):
    lines = read_file(fname)
    for pos, line in enumerate(lines):
        if line[0] == msg_num:
            words = line.split(" ")
            if words[1][:-1] != user:
                return False
    return True

# Checks if a forum exists in the server
def check_forum_not_exists(forum):
    return forum not in forum_threads

# Checks if the command is valid. Checks if the forum does not already exists
# Creates a thread with that name, appending it to the forum_threads list
# Returns an appropriate message to the client and prints info to the server
def CRT(command, connectionSocket):
    global forum_threads
    # Checks
    if (len(command) != 3):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    elif (command[1] in forum_threads):
        print("Thread does not exist")
        connectionSocket.send(
            "Thread already exists\n".encode('utf-8'))
    else:
        # Opens the file, writes the user who created it and sends confirmation 
        # message
        file = open(command[1], "w")
        file.write(command[2] + "\n")
        connectionSocket.send(
            ("Thread " + command[1] + " created by " + command[2] + "\n")
            .encode('utf-8'))
        file.close()
        print("Thread " + command[1] + " created")
        forum_threads.append(command[1])

# Checks if command is in correct format. Checks if forum exists.
# If all is ok, writes a message to the thread with the correct msg number
def MSG(command, connectionSocket):
    global forum_threads
    # Checks
    if (len(command) < 4):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    elif (check_forum_not_exists(command[1])):
        print("Thread does not exist")
        connectionSocket.send(
            "Thread does not exist\n".encode('utf-8'))
    else:
        # Writes the message to a file with the correct message number
        length = len(command)
        message = ""
        for x in range(2, length - 1):
            message += command[x] + " "
        message += "\n"
        msg_num = max_msg_num(command[1])
        payload = str(msg_num) + " " + \
            command[length-1] + ": " + message
        file = open(command[1], "a")
        file.write(payload)
        file.close()
        connectionSocket.send(
            ("Sent message to " + command[1] + ": " + payload).encode('utf-8'))
        print("Sent message to " + command[1])

# Does appropriate checks, msg_num is int, MSG num exists, thread exists, user 
# can edit the message and  valid command format. Then DLTS the message
def DLT(command, connectionSocket):
    global forum_threads
    # Checks
    if (len(command) != 4):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    elif (check_forum_not_exists(command[1])):
        print("Thread does not exist")
        connectionSocket.send(
            "Thread does not exist\n".encode('utf-8'))
    elif command[2].isnumeric() == False:
        print("Msg num must be an integer")
        connectionSocket.send(
            "Msg num must be an integer\n".encode('utf-8'))
    elif check_message(command[1], command[2]) == False:
        print("Msg num does not exist")
        connectionSocket.send(
            "Msg num does not exist\n".encode('utf-8'))
        # check to see if message is there
    elif check_message_user(command[1], command[2], command[3]) == False:
        print("Insufficient Permissions")
        connectionSocket.send(
            "You do not have permission to delete another persons message\n"
            .encode('utf-8'))
    else:
        # Deletes the message
        del_message(command[1], command[2])
        connectionSocket.send(
            ("MSG deleted from " + command[1] + " \n").encode('utf-8'))
        print("MSG deleted")

# Does error checks. edits the message within thread
def EDT(command, connectionSocket):
    global forum_threads
    # Checks
    if (len(command) < 5):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    elif command[2].isnumeric() == False:
        print("Msg num must be an integer")
        connectionSocket.send(
            "Msg num must be an integer\n".encode('utf-8'))
    elif (check_forum_not_exists(command[1])):
        print("Thread does not exist")
        connectionSocket.send(
            "Thread does not exist\n".encode('utf-8'))
    elif check_message(command[1], command[2]) == False:
        print("Msg num does not exist")
        connectionSocket.send(
            "Msg num does not exist\n".encode('utf-8'))
        # check to see if message is there
    elif check_message_user(command[1], command[2],
                            command[len(command) - 1]) == False:
        print("Insufficient Permissions")
        connectionSocket.send(
            "You do not have permission to edit another persons message\n"
            .encode('utf-8'))
    else:
        #Edits the message
        length = len(command)
        message = ""
        for x in range(3, length - 1):
            message += command[x] + " "
        message += "\n"
        payload = command[2] + " " + \
            command[length-1] + ": " + message
        edit_message(command[1], command[2], payload)
        connectionSocket.send(
            ("MSG number " + command[2] + " in thread" + command[1]
                + " has been edited\n")
            .encode('utf-8'))
        print("MSG Edited")

# Does error checks. Lists all threads
def LST(command, connectionSocket):
    global forum_threads
    # Checks
    if (len(command) != 2):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    else:
        # Turns forums list into a string to send to the client to build it back
        # up as a list and interpret
        print("Sent list of threads")
        files = os.listdir()
        send = []
        for x in files:
            if str(x) in forum_threads:
                send.append(x)
        data = str(send)
        if len(send) == 0:
            connectionSocket.send(("No Threads\n").encode('utf-8'))
        else:
            connectionSocket.send((data + "\n").encode('utf-8'))

# Does error checks. Shows all info of a thread.
def RDT(command, connectionSocket):
    global forum_threads
    # Checks
    if (len(command) != 3):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    elif (check_forum_not_exists(command[1])):
        print("Thread does not exist")
        connectionSocket.send(
            "Thread does not exist\n".encode('utf-8'))
    else:
        # Sends list as a string to be reconverted to list and intepreted at 
        # Client
        print("RDT info sent")
        lines = read_file(command[1])
        if len(lines) == 1:
            connectionSocket.send(("No messages in thread\n").encode('utf-8'))
        else:
            connectionSocket.send((
                str(lines[1:]) + "\n").encode('utf-8'))

# Does error checks. Uploads a file to the thread requested
# Loops when recieving to ensure the entire file is recieved as it can be larger
# than the file buffer
def UDP(command, connectionSocket):
    global forum_threads
    global forum_threads_uploads
    if (len(command) != 4):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    elif (check_forum_not_exists(command[1])):
        print("Thread does not exist")
        connectionSocket.send(
            "Thread does not exist\n".encode('utf-8'))
    elif(str(command[1] + "-" + command[2]) in forum_threads_uploads):
        print("File with that name has already been uploaded to thread")
        connectionSocket.send(
            "File uploaded already\n".encode('utf-8'))
    else:
        connectionSocket.send(
            "Thread exists\n".encode('utf-8'))

        size = get_req(connectionSocket)
        size = int(size)

        l = connectionSocket.recv(1024)
        total = len(l)
        file = open(command[1] + "-" + command[2], "wb")
        forum_threads_uploads.append(str(command[1] + "-" + command[2]))

        # Sends file in chunks of 1024 bytes to be recieved by client
        while(l):
            file.write(l)
            if (size - total) < 1024:
                l = connectionSocket.recv((size - total) )
                total = total + len(l)
            elif (total < size):
                l = connectionSocket.recv(1024)
                total = total + len(l)
                # print(l, total, size)
            else:
                break
        file.close()

        file = open(command[1], "a")
        payload = command[3] + " uploaded " + command[2] + "\n"
        file.write(payload)
        file.close()

        connectionSocket.send(
            "File uploaded sucessfully to thread".encode('utf-8'))
        print("Sent file to thread: " + command[1] + "\n")

# Does error checks. Sends the entire file to the client.
def DWN(command, connectionSocket):
    global forum_threads
    global forum_threads_uploads
    if (len(command) != 4):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    elif (check_forum_not_exists(command[1])):
        print("Thread does not exist")
        connectionSocket.send(
            "Thread does not exist\n".encode('utf-8'))
    elif ((command[1] + "-" + command[2]) not in forum_threads_uploads):
        print("File does not exist")
        connectionSocket.send(
            "File requested within Thread does not exist\n".encode('utf-8'))
    else:
        # Send file as bytes
        length = os.path.getsize(command[1] + "-" + command[2])
        connectionSocket.send((str(length) + "\n").encode('utf-8'))

        with open(command[1] + "-" + command[2], "rb") as f:
            d = f.read()
            connectionSocket.sendall(d)
            f.close()

        print("Sent file from thread " + command[1] + " to user " + command[3])
        connectionSocket.send(
            ("Sent file from thread " + command[1] + "\n").encode('utf-8'))

# Does error checks. Removes a thread from the server, including all uploads
# to the threads.
def RMV(command, connectionSocket):
    global forum_threads
    global forum_threads_uploads
    if (len(command) != 3):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    elif (check_forum_not_exists(command[1])):
        print("Thread does not exist")
        connectionSocket.send(
            "Thread does not exist\n".encode('utf-8'))
    else:
        with open(command[1]) as f:
            first_line = f.readline().strip()

        if first_line != command[2]:
            connectionSocket.send(
                "You do not have permission to remove another persons thread\n"
                .encode('utf-8'))
        else:
            files = [f for f in os.listdir(
                '.') if os.path.isfile(f)]

            thread_name_len = len(command[1])

            for f in files:
                if (f[0:thread_name_len] == command[1]
                        and f[thread_name_len:thread_name_len + 1] == "-"):
                    if f in forum_threads_uploads:
                        forum_threads_uploads.remove(f)
                        # send2trash(f)
                    os.remove(f)
            forum_threads.remove(command[1])
            # send2trash(command[1])
            os.remove(command[1])
            print(
                "removed file and all info related to the thread" + command[1])
            connectionSocket.send(
                ("RMV of thread " + command[1] + " is sucessful\n")
                .encode('utf-8'))

# Exits the user. Removes from list of active users. Removes from active sockets
def XIT(command, connectionSocket):
    global clients
    global users
    if (len(command) != 2):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    else:
        print("XIT Sucess")
        clients.remove(connectionSocket)
        users.remove(command[1])
        connectionSocket.send(
            "XIT sucessful\n".encode('utf-8'))

# Shuts down the entire server after telling all sockets it is shutting down
def SHT(command, connectionSocket):
    global forum_threads
    global forum_threads_uploads
    global clients
    if (len(command) != 3):
        print("Invalid command format")
        connectionSocket.send(
            "Enter the correct number of commands\n".encode('utf-8'))
    elif (command[1] != adminPassword):
        print("Invalid server password for shutdown")
        connectionSocket.send(
            "Incorrect server shutdown password\n".encode('utf-8'))
    else:
        connectionSocket.send(
            "Server is shutting down\n".encode('utf-8'))

        files = [f for f in os.listdir(
            '.') if os.path.isfile(f)]

        thread_name_len = len(command[1])

        # I hope to god i commend out all this stuff here and correctly 
        # remove stuff like the credential file. This is all for testing
        for f in files:
            if (f == "server.py"):
                pass
            if f in forum_threads or f in forum_threads_uploads 
                or f == "credentials.txt":
                # send2trash(f)
                os.remove(f)
        for c in clients:
            c.send(
                "Server is shutting down\n".encode('utf-8'))
        print("Server is shutting down")
        os._exit(0)

# The large function for the entire handing of a client (after authentication)
# It recieves a command from the client. It checks which command it is and 
# takes appropriate action. If a heartbeat command to check if server alive, it 
# sends a message saying that it is. If it is an actual command, it locks all 
# resources, executes the command from the functions above and then unlocks it 
# notifying the next thread that resources are ready to use.
def handle_client_commands(connectionSocket):
    global forum_threads
    global forum_threads_uploads
    global clients
    global t_lock
    while 1:
        try:
            command = connectionSocket.recv(1024).decode('utf-8')
        except OSError:
            print(
                "Tried recieving on a socket that was dead. \
                Its ok, the server is shutting down \
                or we arent gnna receive on that socket anymore since i \
                will break (ending the thread) and remove it from the\
                client list")
            clients.remove(connectionSocket)
            # cant remove the user unless we map it correctly but we are 
            # assuming graceful closure so there isnt a need to worry about this
            break

        # if socket is closed and it recieves 0
        if not command:
            break

        if command == "are you alive\n":
            connectionSocket.send("alive\n".encode('utf-8'))
            continue

        command = command.split(" ")
        print(command[len(command) - 1] +
                  " issued " + command[0] + " command")
        with t_lock:
            if command[0] == "CRT":
                CRT(command, connectionSocket)
            elif command[0] == "MSG":
                MSG(command, connectionSocket)
            elif command[0] == "DLT":
                DLT(command, connectionSocket)
            elif command[0] == "EDT":
                EDT(command, connectionSocket)
            elif command[0] == "LST":
                LST(command, connectionSocket)
            elif command[0] == "RDT":
                RDT(command, connectionSocket)
            elif command[0] == "UDP":
                UDP(command, connectionSocket)
            elif command[0] == "DWN":
                DWN(command, connectionSocket)
            elif command[0] == "RMV":
                RMV(command, connectionSocket)
            elif command[0] == "XIT":
                XIT(command, connectionSocket)
            elif command[0] == "SHT":
                SHT(command, connectionSocket)
            else:
                connectionSocket.send(
                    "Valid command please\n".encode('utf-8'))
                print("Invalid command")
            t_lock.notify()

def get_credentials():
    credentials = []
    file = open("credentials.txt", "r")
    all_info = file.read()
    line = all_info.split("\n")
    for x in line:
        x = x.split(" ")
        credentials.append(x)
    return credentials

# Authenticates a user. Locks all resources until user authenticates as the 
# assignment spec states that only one user can authenticate at any time. This 
# does mean a user who enver authenticates can hang the entire server but the 
# workaround for this is that there is a timeout on authentication which can be 
# implemented in an extension. Does no checks for special character as it 
# just assumes that any input is one word so it iwll take any one word input and
# comapre it with the credential file, meaning there is no need for a check of 
#  itting criteria.

# No need to do SHT handling there
# " it’s fine. U can assume the authentication process is not interrupted"

def authenticate(connectionSocket):
    global forum_threads
    global t_lock
    global users
    with t_lock:
        authentication = True
        while authentication:
            username = get_req(connectionSocket)
            credentials = get_credentials()
            if username in users:
                connectionSocket.send(
                    "User already logged in\n".encode('utf-8'))
                print("User already logged in, new connection cannot log " +
                        "in with that user")
                continue
            username_check = False
            for user_pass in credentials:
                # passwords are sperated by a space
                if len(user_pass) != 2:
                    continue
                check = False
                [user, password] = user_pass
                if user == username:
                    username_check = True
                    connectionSocket.send("Send Password\n".encode('utf-8'))
                    print("Ask for Password. Valid Username")
                    passWord = get_req(connectionSocket)
                    if (password == passWord):
                        print("Authenticated")
                        if username in users:
                            connectionSocket.send(
                                "Already logged in, try another account\n"
                                .encode('utf-8'))
                            continue
                        connectionSocket.send(
                            "Authenticated\n".encode('utf-8'))
                        authentication = False
                        break
                    else:
                        print("Incorrect password")
                        connectionSocket.send(
                            "Wrong Password\n".encode('utf-8'))
                        break
            if username_check == False:
                print("Add Password to create a new account")
                connectionSocket.send(
                    "Enter Password For New User\n".encode('utf-8'))
                passWord = get_req(connectionSocket)
                file = open("credentials.txt", "a")
                file.write("\n" + username + " " + passWord)
                authentication = False
                connectionSocket.send(
                    "Created New User\n".encode('utf-8'))
        
        users.append(username)
        print(username + " has just logged in")
        t_lock.notify()

# This is the function that first authenticates the client connection then 
# puts it through an infinite loop wwaiting for requests and dealing with them 
# Each thread is running this specific function.
def handle_client(connectionSocket):
    authenticate(connectionSocket)
    handle_client_commands(connectionSocket)

# This is the main function. It sets a welcoming socket at a sertain IP and 
# PORT. After doing so, it accepts connection, creates a thread and 
# authenticates/handles_requests. Does this for every new connection. The server 
# is tested for the assignment with 3 different clients, but i set it as 99 just 
# in case. IT HAS TO BE RESTRICTED SINCE THERE IS NEVER INFINITE RESOURCES. This
# can be changes any time necessary to whatever number needed. I  assumed 99.
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Valid number of commands pls")
        exit(0)
    serverPort = int(sys.argv[1])
    adminPassword = sys.argv[2]
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('localhost', serverPort))

    serverSocket.listen(99)
    print("Server is ready")
    running = threading.Event()
    running.set()

    while 1:
        (connectionSocket, (ip, port)) = serverSocket.accept()
        print("Accepted new connection")
        clients.append(connectionSocket)
        handle_interaction = threading.Thread(
            target=handle_client, args=(connectionSocket,))
        handle_interaction.daemon = True
        handle_interaction.start()
