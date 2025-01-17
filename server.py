import os
import socket
import ssl
import sys
import threading
import struct
import time
import configparser

BUFFER_SIZE = 1024
SERVER_FILE = "serverfile"

# TODO: Buggy after some time, Not everything is transmitted
def handle_list(conn, args):
    #conn.send(b'150 Opening ASCII mode data connection for file list.\n')
    #home_directory = os.path.expanduser('~')
    os.chdir(os.path.abspath(SERVER_FILE))
    files = os.listdir(os.getcwd())
    #send number of files over
    conn.sendall(str(len(files)).encode('utf-8') +b'\r\n')

    for file in files:
        file_info = os.stat(file)
        file_mode = oct(file_info.st_mode)[-3:]
        file_size = file_info.st_size
        file_time = file_info.st_mtime
        file_date = time.strftime('%b %d %H:%M', time.gmtime(file_time))
        file_name = file.encode('utf-8') + b'\r\n'
        conn.sendall(file_mode.encode('utf-8') + b' 1 user user ' + str(file_size).encode('utf-8') + b' ' + file_date.encode('utf-8') + b' ' + file_name)

    if not files:
        conn.sendall(b'226 No files in directory.\n')
    os.chdir("../")

def handle_upload(conn, args):
    filename = args[1]
    filesize = int(args[2])
    os.chdir(os.path.abspath(SERVER_FILE))
    if os.path.exists(filename):
        conn.sendall(b'T')
        conn.sendall(b'File already exists! Overwrite? Y/N')
        # get response Y/N
        response = conn.recv(BUFFER_SIZE).decode('utf-8')
        if response.upper() == 'Y':
            print(f'Uploading {filename} ({filesize} bytes)')
            bytes_received = 0
            print("\nReceiving...")
            with open(os.path.join(os.getcwd(), filename), 'wb') as f:
                while bytes_received < filesize:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        break
                    f.write(data)
                    bytes_received += BUFFER_SIZE
            print("Upload successful")
            os.chdir("../")
            conn.sendall(b'200 Upload done')
        elif response.upper() == 'N':
            os.chdir("../")
            conn.sendall(b'Upload cancelled!')
    else:
        conn.sendall(b'F')
        conn.sendall(b'150 File does not already exist, Uploading')
        print(f'Uploading {filename} ({filesize} bytes)')
        bytes_received = 0
        print("\nReceiving...")
        with open(os.path.join(os.getcwd(), filename), 'wb') as f:
            while bytes_received < filesize:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)
                bytes_received += BUFFER_SIZE
        print("Upload successful")
        os.chdir("../")
        conn.sendall(b'200 Upload done')


def handle_download(conn, args):
    filename = args[1]
    os.chdir(os.path.abspath(SERVER_FILE))
    if os.path.exists(filename):
        filesize = os.path.getsize(filename)
        conn.sendall(str(f"SIZE {filesize}").encode('utf-8'))
        bytes_sent = 0
        print("\nSending...")
        with open(filename, 'rb') as f:
            while bytes_sent < filesize:
                data = f.read(BUFFER_SIZE)
                conn.sendall(data)
                bytes_sent += BUFFER_SIZE
        print("Download sent")
        os.chdir("../")
        conn.sendall(b'200 Download done')
    else:
        conn.sendall(b'550 File not found.')
        os.chdir("../")



def handle_delete(conn, args):
    filename = args[1]
    os.chdir(os.path.abspath(SERVER_FILE))
    os.remove(filename)
    conn.sendall(b'200 Delete done')


def handle_rename(conn, args):
    os.chdir(os.path.abspath(SERVER_FILE))
    old_filename = args[1]
    new_filename = args[2]
    if os.path.exists(old_filename):
        os.rename(old_filename, new_filename)
        os.chdir("../")
        conn.sendall(f"completed".encode('utf-8'))
    else:
        conn.sendall(b'550 File not found.')
        os.chdir("../")

def handle_quit(conn, args):
    conn.sendall(b'Quitting')
    conn.close()
    return True


def handle_user(conn, args):
    conn.sendall(b'230 Login successful.\n')


def handle_pwd(conn, args):
    current_dir = os.getcwd()
    conn.sendall(f'257 "{current_dir}" is the current directory.\n'.encode())
    handle_list(conn, args)

def handle_port(conn, args):
    conn.sendall(b'200 OK\n')

def handle_cwd(conn, args):
    directory = os.path.abspath(args[1])
    if not directory.startswith(os.path.abspath(SERVER_FILE)):
        conn.sendall(b'550 Permission denied.\n')
        return
    else:
        os.chdir(directory)
        conn.sendall(b'200 OK\n')

def handle_help(conn, args):
    conn.sendall(b'\n214 List of executable commands:\nLIST: List files\nUPLD <file_name>:  '
              b'Upload file\nDWLD <file_name>: Download file\nDELF <file_name>: Delete file\nRNTO <old_name> '
              b'<new_name>: Rename file\nQUIT: Exit')

commands = {
    'LIST': handle_list,
    'UPLD': handle_upload,
    'DWLD': handle_download,
    'DELF': handle_delete,
    'RNTO': handle_rename,
    'QUIT': handle_quit,
    'USER': handle_user,
    'PWD': handle_pwd,
    'TYPE': lambda conn, args: conn.sendall(b'200 OK\n'),
    'PORT': handle_port,
    'CDUP': lambda conn, args: conn.sendall(b'200 OK\n'),
    'CWD' : handle_cwd,
    'HELP': handle_help,
}


def handle_connection(conn):
    conn.sendall(b'220 Welcome to the FTP server.\n')

    while True:
        try:
            data = conn.recv(BUFFER_SIZE).decode()
            print(f'Server received: {data}')
            if not data:
                break
            args = data.split()
            command = args[0]
            print(f'Command: {command}')
            if command in commands:
                if command == 'QUIT':
                    conn.sendall(b'Closing Connection')
                    conn.close()
                    break
                commands[command](conn, args)
            else:
                conn.sendall(b'Invalid command.\n')
        except ConnectionResetError:
            print('Connection closed by client')
            break
        except OSError as e:
            print("OS Error: {0}".format(e))
            break

        # For FTP client testing
        #handle_pwd(conn, [])
        #handle_list(conn, [])

        #if command != 'QUIT':
        #    handle_list(conn, args)


def main():
    # Get command line arguments
    try:
        port = int(sys.argv[1])
    except IndexError:
        pass

    config = configparser.ConfigParser()
    config.read('./config/config.ini')

    # SSL certificate and key
    cert = config['SSL']['cert']
    key = config['SSL']['key']

    # If port is not specified, use default port
    if len(sys.argv) < 2:
        port = int(config['FTPSERVER']['port'])

    # print(cert, key)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # context.load_cert_chain("./SSL/certificate.pem", "./SSL/privatekey.pem")
    context.load_cert_chain(cert,key)

    #port = 2001
    server = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_side=True)
    # server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(1)
    print("Listening on port", port)

    while True:
        try:
            conn, addr = server.accept()
            print("Connected to", addr)
            # Create a new thread to handle the connection
            threading.Thread(target=handle_connection, args=(conn,)).start()
        except KeyboardInterrupt:
            print("Shutting down server")
            server.close()
            return


if __name__ == '__main__':
    main()
