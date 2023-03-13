import os
import socket
CLIENT_FILE = "clientfile"


# This prints 1 line at first, then the whole list after running the command again
def handle_list(conn, args):
    # Show list of files received from server in response to LIST command
    # Response is a multi-line string
    response = conn.recv(4096).decode('latin-1').strip()

    print(response)
    # Check for multi-line response
    while response.startswith("1"):
        response = conn.recv(4096).decode("latin-1")
        print(response)


def handle_quit(conn, args):
    conn.sendall("QUIT\r\n".encode())
    # Receive response from server
    # Decode bytes to string
    response = conn.recv(1024).decode('utf-8').strip()
    print(response)
    conn.close()
    return True


def handle_DWLD(conn, args):
    # send command over
    filename = args
    conn.sendall(f"DWLD {filename}\r".encode())
    os.chdir(os.path.abspath(CLIENT_FILE))
    filedata = conn.recv(1024)
    print(filedata)
    with open(filename, "wb") as f:
        f.write(filedata)
    os.chdir("../")
    print("File downloaded successfully")


# def handle_dwld(conn, args):
#    filename = args
#    conn.sendall(f"DWLD {filename}\r".encode())

#    filedata = conn.recv(1024)
#    print(filedata)
#    with open(filename, "wb") as f:
#       f.write(filedata)
#    print("File downloaded successfully")

def handle_UPLD(conn, args):
    filename = args
    os.chdir(os.path.abspath(CLIENT_FILE))
    if not os.path.exists(filename):
        print("File does not exist")
    else:
        with open(filename, "rb") as f:
            filedata = f.read(4096)
            file_size = os.path.getsize(filename)
            conn.sendall(f"UPLD {filename} {file_size}\r".encode())
            conn.sendall(filedata)
        response = conn.recv(4096).decode().strip()
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

    response = sock.recv(1024).decode().strip()
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
        elif command.upper() == "RNTO":
            oldName, newName = args.split(" ", 1)
            sock.sendall(f"RNTO {oldName} {newName}\r".encode())
        else:
            print("Invalid command")

    sock.close()


if __name__ == "__main__":
    # FTP Client should be able to define IP and port
    ftp_cient("127.0.0.1", 2001)
