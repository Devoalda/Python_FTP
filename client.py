import os
from socket import *
import configparser
import ssl
import sys

CLIENT_FILE = "clientfile"
BUFFER_SIZE = 1024


# TODO: Buggy after some time, Not everything is transmitted
def handle_list(conn, args):
    # send command over
    conn.sendall("LIST\r\n".encode())

    num_of_files_received = 0
    num_of_files = 0
    # Receive response from server
    # Decode bytes to string
    response = conn.recv(BUFFER_SIZE).decode('utf-8').strip()
    try:
        num_of_files = int(response)
    except ValueError:
        print(response)
        return

    while num_of_files_received < num_of_files:
        # Print response
        print(conn.recv(BUFFER_SIZE).decode('utf-8').strip())
        num_of_files_received += 1


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
    response = conn.recv(BUFFER_SIZE).decode('utf-8')
    if response.startswith("SIZE"):
        filesize = response[1]
        bytes_received = 0
        with open(filename, "wb") as f:
            while bytes_received < filesize:
                data = conn.recv(BUFFER_SIZE)
                f.write(data)
                bytes_received += BUFFER_SIZE
        response = conn.recv(BUFFER_SIZE).decode('utf-8')
        print(response)
        os.chdir("../")
    else:
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
        # does file exist at the server?
        serverExist = conn.recv(BUFFER_SIZE).decode('utf-8')
        # if server already has the file
        if serverExist == 'T':
            # do you want to overwrite?
            print(conn.recv(BUFFER_SIZE).decode('utf-8'))
            overwrite = input()
            conn.sendall(overwrite.encode('utf-8'))
            # yes, overwrite
            if overwrite.upper() == 'Y':
                with open(filename, "rb") as f:
                    while bytes_sent < file_size:
                        filedata = f.read(BUFFER_SIZE)
                        conn.sendall(filedata)
                        bytes_sent += BUFFER_SIZE
                response = conn.recv(BUFFER_SIZE).decode().strip()
                print(response)
                os.chdir("../")
            # no, dont overwrite
            elif overwrite.upper() == 'N':
                response = conn.recv(BUFFER_SIZE).decode().strip()
                print(response)
                os.chdir("../")
        # server doesnt have the file
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


def handle_HELP(conn, args):
    conn.sendall(f"HELP\r".encode())
    response = conn.recv(BUFFER_SIZE).decode('utf-8')
    print(response.join())


def user_input():
    # Get user input
    user_input = input("> ").strip()

    # Parse command and arguments
    if " " in user_input:
        command, args = user_input.split(" ", 1)
    else:
        command, args = user_input, ""

    return command, args


def ftp_client(host, port, cert):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cert)
    context.check_hostname = False

    sock = context.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname=host)
    try:
        sock.connect((host, port))
        print("Connected to " + host + ":" + str(port))
    except ConnectionRefusedError:
        print("Connection refused by " + host + ":" + str(port))
        return

    response = sock.recv(BUFFER_SIZE).decode().strip()
    print(response)

    while True:
        user_input = input("> ").strip()

        if " " in user_input:
            command, args = user_input.split(" ", 1)
        else:
            command, args = user_input, ""

        if command.upper() == "LIST":
            # sock.sendall("LIST\r\n".encode())
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
        elif command.upper() == "HELP":
            handle_HELP(sock, args)
        else:
            print("Invalid command")

    sock.close()


if __name__ == "__main__":
    # Get command line arguments
    try:
        ip = sys.argv[1]
        port = int(sys.argv[2])
    except IndexError:
        pass

    # Config file
    config = configparser.ConfigParser()
    config.read('./config/config.ini')
    cert = config['SSL']['cert']

    # If no command line arguments, use config file
    if len(sys.argv) == 1:
        print("Using Config.ini")
        # FTP Client should be able to define IP and port
        ip = config['FTPSERVER']['ip']
        port = int(config['FTPSERVER']['port'])


    try:
        ftp_client(ip, port, cert)
    except KeyboardInterrupt:
        print("Client interrupted")
        sys.exit(0)
