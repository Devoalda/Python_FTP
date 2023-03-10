import os
import socket
import ssl
import sys
import threading
import struct
import time

BUFFER_SIZE = 1024

def handle_list(conn, args):
    #conn.send(b'150 Opening ASCII mode data connection for file list.\n')
    files = os.listdir(os.getcwd())
    for file in files:
        file_info = os.stat(file)
        file_mode = oct(file_info.st_mode)[-3:]
        file_size = file_info.st_size
        file_time = file_info.st_mtime
        file_date = time.strftime('%b %d %H:%M', time.gmtime(file_time))
        file_name = file.encode('utf-8') + b'\r\n'
        conn.send(file_mode.encode('utf-8') + b' 1 user user ' + str(file_size).encode('utf-8') + b' ' + file_date.encode('utf-8') + b' ' + file_name)

    if not files:
        conn.send(b'226 No files in directory.\n')
    conn.send(b'226 Transfer complete.\n')

def handle_upload(conn, args):
    filename = args[1]
    filesize = int(args[2])
    print(f'Uploading {filename} ({filesize} bytes)')
    with open(filename, 'wb') as f:
        data = conn.recv(4096)
        f.write(data)
    conn.send(b'done')


def handle_download(conn, args):
    filename = args[1]
    filesize = os.path.getsize(filename)
    #conn.send(struct.pack('i', filesize))
    with open(filename, 'rb') as f:
        data = f.read(4096)
        while data:
            conn.send(data)
            data = f.read(4096)
    conn.send(b'done')


def handle_delete(conn, args):
    filename = args[1]
    os.remove(filename)
    conn.send(b'done')


def handle_rename(conn, args):
    old_filename = args[1]
    new_filename = args[2]
    os.rename(old_filename, new_filename)
    conn.send(b'done')


def handle_quit(conn, args):
    conn.send(b'done')
    conn.close()
    return True


def handle_user(conn, args):
    conn.send(b'230 Login successful.\n')


def handle_pwd(conn, args):
    current_dir = os.getcwd()
    conn.send(f'257 "{current_dir}" is the current directory.\n'.encode())
    handle_list(conn, args)

def handle_port(conn, args):
    conn.send(b'200 OK\n')

commands = {
    'LIST': handle_list,
    'UPLD': handle_upload,
    'DWLD': handle_download,
    'DELF': handle_delete,
    'RNTO': handle_rename,
    'QUIT': handle_quit,
    'USER': handle_user,
    'PWD': handle_pwd,
    'TYPE': lambda conn, args: conn.send(b'200 OK\n'),
    'PORT': handle_port,
    'CDUP': lambda conn, args: conn.send(b'200 OK\n'),
}


def handle_connection(conn):
    conn.send(b'220 Welcome to the FTP server.\n')
    while True:
        data = conn.recv(BUFFER_SIZE).decode()
        print(f'Server received: {data}')
        if not data:
            break
        args = data.split()
        command = args[0]
        print(f'Command: {command}')
        if command in commands:
            if commands == handle_quit:
                break
            commands[command](conn, args)
        else:
            conn.send(b'Invalid command.\n')

        # For FTP client testing
        #handle_pwd(conn, [])
        #handle_list(conn, [])

        #if command != 'QUIT':
        #    handle_list(conn, args)


def main():
    # FTP Server should be run with a port number as an argument
    # if len(sys.argv) != 2:
    #    print("Usage: python3 server.py <port>")
    #    return

    #context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    #context.load_cert_chain("certificate.pem", "privatekey.pem")

    port = 2001
    #server = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_side=True)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
