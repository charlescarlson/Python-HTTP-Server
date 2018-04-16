import select
import socket
import sys
import os

def process_http_request(data, test):
    if test == True:
        data = "GE_ERROR_T /index.html HTTP/1.1\r\nHost: 127.0.0.1:10000\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\nAccept-Encoding: gzip, deflate, br\r\nAccept-Language: en-US,en;q=0.9\r\n\r\n"
    data = repr(data)
    data = data[1:-1]
    data_as_list = data.split("\\n")
    for i in data_as_list:
        index = data_as_list.index(i) 
        i = data_as_list[index][0:-4]
        data_as_list[index] = i
    uri = ""
    for i in data_as_list[0][5:]:
        index = data_as_list[0].index(i)
        end_index = data_as_list[0].index(data_as_list[0][-9])
        if index != end_index:
            uri += i
        else:
            break
    image = False
    if uri[-3:] == "jpg" or uri[-3:] == "png":
        print("URI: " + uri)
        p = "static/" + uri
        if os.path.isfile(p):
            image_length_bytes = os.path.getsize("static/" + uri)
            image = True
        else:
            image_length_bytes = ""
            image = False
            status_code = 404
            return [status_code, "Not Found", image, image_length_bytes]
    if data_as_list[0][0:5] != "GET /":
        status_code = 400
        image_length_bytes = ""
        return [status_code, "Bad Request", image, image_length_bytes]
    if data_as_list[0][-8:] != "HTTP/1.1":
        status_code = 400
        return [status_code, "Bad Request", imamge, image_length_bytes]
    for i in data_as_list[1:-2]:
        index = data_as_list.index(i)
        d = data_as_list[index].split(":")
        if len(d) >= 2:
            status_code = 200
        else:
            status_code = 400
            return [status_code, "Bad Request", image, image_length_bytes]
            break
    path_to_file = "static/" + uri
    if os.path.isfile(path_to_file):
        if image == True:
            print("PATH: " + path_to_file)
            with open(path_to_file, "rb") as f:
                content = f.read()
        else:
            f = open(path_to_file, "r")
            content = ""
            for line in f:
                content += line
            image_length_bytes = ""
        return [status_code, content, image, image_length_bytes]
    else:
        status_code = 404
        image = False
        image_length_bytes = ""
        return [status_code, "Not Found", image, image_length_bytes]

if __name__ == "__main__":
    #
    if len(sys.argv) != 2:
        print('%s <port>' % (sys.argv[0]))
        sys.exit(0)
    
    port = int(sys.argv[1])
    addr = ('127.0.0.1', port)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(addr)
    server_socket.listen(5)

    clients = []
    while True:
        inputs = clients[:]
        inputs.append(server_socket)
        rl ,_ , _ = select.select(inputs, [], [])
        for s in rl:
            if s == server_socket:
                (client_socket, client_addr) = server_socket.accept()
                clients.append(client_socket)
            else:
                assert(s in clients)
                data = s.recv(512)
                data_str = str(data)
                data_str = data_str[2:-1]
                data_test = "GET /index.html HTTP/1.1\r\nHost: 127.0.0.1:10000\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\nAccept-Encoding: gzip, deflate, br\r\nAccept-Language: en-US,en;q=0.9\r\n\r\n"
                status_vector = process_http_request(data_str, False)
                status_code, content, image, image_length_bytes = status_vector[0], status_vector[1], status_vector[2], status_vector[3]
                request_is_valid = False
                if status_code == 200 or status_code == 404:
                    request_is_valid = True
                elif status_code == 400:
                    request_is_valid == False
                print("Status Code: " + str(status_code))
                print("STATUS_VECTOR: " + str(image))
                if request_is_valid and status_code == 200 and image == False:
                    http_reply = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
                    for client in clients:
                        if client == s:
                            http_reply += content
                            client.send(http_reply.encode())    
                            s.close()
                            clients.remove(s)
                if request_is_valid and status_code == 200 and image == True:
                    http_reply = "HTTP/1.1 200 OK\r\nContent-Type: image/gif\r\n\r\n"
                    for client in clients:
                        if client == s:
                            client.send(http_reply.encode())    
                            client.send(content)
                            s.close()
                            clients.remove(s)
                elif request_is_valid and status_code == 404:
                    print("404")
                    http_reply = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
                    for client in clients:
                        if client == s:
                            client.send(http_reply.encode())
                            s.close()
                            clients.remove(s)
                elif request_is_valid == False and status_code == 400:
                    print("400")
                    http_reply = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: %s\r\n\r\n" % image_length_bytes
                    for client in clients:
                        if client == s:
                            client.send(http_reply.encode())
                            s.close()
                            clients.remove(s)
    print('Closing')
    server_socket.close()
