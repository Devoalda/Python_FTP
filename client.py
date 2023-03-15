import os
import socket
CLIENT_FILE = "clientfile"
BUFFER_SIZE = 1024


def handle_list(conn, args):
    num_of_files_received = 0
    num_of_files = int(conn.recv(BUFFER_SIZE).decode('utf-8'))
    print("Total files in directory: "+ str(num_of_files))
    while num_of_files_received < num_of_files:
        file_info = conn.recv(BUFFER_SIZE).decode('utf-8')
        print(file_info)
        num_of_files_received += 1
    response = conn.recv(BUFFER_SIZE).decode('utf-8')
    print(response)

def handle_quit(conn, args):
    conn.sendall("QUIT\r\n".encode())
    # Receive response from server
    # Decode bytes to string
    response = conn.recv(BUFFER_SIZE).decode('utf-8').strip()
    print(response)
    conn.close()
    return True

def handle_DWLD(conn, args):
    # send command over
    filename = args
    conn.sendall(f"DWLD {filename}\r".encode())
    os.chdir(os.path.abspath(CLIENT_FILE))
    filesize = int(conn.recv(BUFFER_SIZE).decode('utf-8'))
    bytes_received = 0

    with open(filename, "wb") as f:
        while bytes_received < filesize:
            data = conn.recv(BUFFER_SIZE)
            f.write(data)
            bytes_received += BUFFER_SIZE
    response = conn.recv(BUFFER_SIZE).decode('utf-8')
    print(response)
    os.chdir("../")

def handle_UPLD(conn, args):
    filename = args
    os.chdir(os.path.abspath(CLIENT_FILE))
    if not os.path.exists(filename):
        print("File does not exist")
    else:
        bytes_sent = 0
        file_size = os.path.getsize(filename)
        conn.sendall(f"UPLD {filename} {file_size}\r".encode())
        #does file exist at the server?
        serverExist = conn.recv(BUFFER_SIZE).decode('utf-8')
        #if server already has the file
        if serverExist == 'T':
            #do you want to overwrite?
            print(conn.recv(BUFFER_SIZE).decode('utf-8'))
            overwrite = input()
            conn.sendall(overwrite.encode('utf-8'))
            #yes, overwrite
            if overwrite.upper() == 'Y':
                with open(filename, "rb") as f:
                    while bytes_sent < file_size:
                        filedata = f.read(BUFFER_SIZE)
                        conn.sendall(filedata)
                        bytes_sent += BUFFER_SIZE
                response = conn.recv(BUFFER_SIZE).decode().strip()
                print(response)
                os.chdir("../")
            #no, dont overwrite
            elif overwrite.upper() == 'N':
                response = conn.recv(BUFFER_SIZE).decode().strip()
                print(response)
                os.chdir("../")
        #server doesnt have the file
        elif serverExist == 'F':
            print(conn.recv(BUFFER_SIZE).decode('utf-8'))
            with open(filename, "rb") as f:
                while bytes_sent < file_size:
                    filedata = f.read(BUFFER_SIZE)
                    conn.sendall(filedata)
                    bytes_sent += BUFFER_SIZE
            response = conn.recv(BUFFER_SIZE).decode().strip()
            print(response)
            os.chdir("../")



def user_input():
    # Get user input
    user_input = input("> ").strip()

    # Parse command and arguments
    if " " in user_input:
        command, args = user_input.split(" ", 1)
    else:
        command, args = user_input, ""

    return command, args


def ftp_cient(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    response = sock.recv(BUFFER_SIZE).decode().strip()
    print(response)

    while True:
        user_input = input("> ").strip()

        if " " in user_input:
            command, args = user_input.split(" ", 1)
        else:
            command, args = user_input, ""

        if command.upper() == "LIST":
            sock.sendall("LIST\r\n".encode())
            handle_list(sock, args)
        elif command.upper() == "QUIT":
            handle_quit(sock, args)
            break
        elif command.upper() == "DWLD":
            handle_DWLD(sock, args)
        elif command.upper() == "UPLD":
            handle_UPLD(sock, args)
        elif command.upper() == "DELF":
            filename = args
            sock.sendall(f"DELF {filename}\r".encode())
            response = sock.recv(BUFFER_SIZE).decode('utf-8')
            print(response)
        elif command.upper() == "RNTO":
            oldName, newName = args.split(" ", 1)
            sock.sendall(f"RNTO {oldName} {newName}\r".encode())
        else:
            print("Invalid command")

    sock.close()


if __name__ == "__main__":
    # FTP Client should be able to define IP and port
    ftp_cient("127.0.0.1", 2001)
