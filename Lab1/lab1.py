import socket
import threading
import sys

USE_WEBSITE_BLACK_LIST = 0
USE_WEBSITE_WHITE_LIST = 0
USE_IP_BLACKLIST = 0
USE_FISH = 0

black_list = ['jwts.hit.edu.cn']
white_list = ['www.baidu.com']
ip_blacklist = ['127.0.0.1']

fish_request = 'GET http://tool.chinaz.com/pagestatus/ HTTP/1.1\r\nHost: tool.chinaz.com\r\nProxy-Connection: keep-alive\r\nCache-Control: max-age=0\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\nAccept-Encoding: gzip, deflate\r\nAccept-Language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6\r\nCookie: qHistory=aHR0cDovL3Rvb2wuY2hpbmF6LmNvbS9wYWdlc3RhdHVzLytIVFRQ54q25oCB5p+l6K+i; UM_distinctid=1669a3113cf16-0b19da3297da02-8383268-1fa400-1669a3113d05c2; CNZZDATA5082706=cnzz_eid%3D870698534-1540179912-null%26ntime%3D1540179912\r\n\r\n'



def handle(buffer):
    return buffer


def transfer(src, dst, direction):
    while True:
        buffer = src.recv(0x1000)
        if len(buffer) == 0:
            break
        dst.send(handle(buffer))
    src.shutdown(socket.SHUT_RDWR)
    src.close()
    dst.shutdown(socket.SHUT_RDWR)
    dst.close()


class HttpParse(object):
    type = ''
    url = ''
    host = ''
    cookie = ''
    def __init__(self, data):
        lines = data.split('\r\n')
        for line in lines:
            if(line == ''):
                continue
            if line.startswith('GET'):
                self.type = 'GET'
                self.url = line.split(' ')[1]
            elif line.startswith('POST'):
                self.type = 'POST'
                self.url = line.split(' ')[1]
            elif line.startswith('Host:'):
                self.host = line[6:]
            elif line.startswith('Cookie'):
                self.cookie = line
    def get_host(self):
        return self.host
    def get_url(self):
        return self.url


class Cache(object):
    def __init__(self, maxsize = 0x100):
        self.cache = dict()
        self.maxsize = maxsize
    def add(self, key, value):
        if(len(self.cache) > self.maxsize):
            self.cache.clear()
        self.cache[key] = value
        
    def get(self, key):
        try:
            ret = self.cache[key]
        except KeyError, e:
            ret = ''
        return ret



def right_resource(ret):
    return True if ret.startswith('HTTP/1.1 200 OK') else False


def host_visitable(host):
    if USE_WEBSITE_BLACK_LIST and host in black_list:
        return False
    if USE_WEBSITE_WHITE_LIST and host in white_list:
        return True
    return True

def local_ip_usable(local_ip):
    if USE_IP_BLACKLIST and local_ip in ip_blacklist :
        return False
    return True


def proxy(local_socket, direction):
    print("proxy starting")
    buffer = local_socket.recv(0x1000)
    if(USE_FISH):
        buffer = fish_request   
    parse = HttpParse(buffer)
    remote_host = parse.get_host()
    if(not host_visitable(remote_host)):
        print("visit " + remote_host + 'forbidden')
        return
    # print(remote_host)
    print("remote host: " + remote_host + '\n')
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, 80))
    remote_socket.send(buffer)
    print("connect to remote host success")
    threading.Thread(target=transfer, args=(remote_socket, local_socket, False)).start()
    transfer(local_socket, remote_socket, True)


def sync_proxy(local_socket, cache):
    print("proxy starting")
    buffer = local_socket.recv(0x1000)
    if(len(buffer) == 0):
        return
    if(USE_FISH):
        buffer = fish_request
    parse = HttpParse(buffer)
    remote_host = parse.get_host()
    # print(remote_host)
    if(':' in remote_host or remote_host==''):
        print('wrong host name: ' + repr(buffer))
        return
    if(not host_visitable(remote_host)):
        print("visit " + remote_host + 'forbidden')
        return
    print("remote host: " + remote_host + '\n')
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, 80))
    remote_socket.send(buffer)
    buffer = remote_socket.recv(0x1000)
    url = parse.get_url()
    if(right_resource(buffer)):
        cache.add(url, buffer)
    local_socket.send(buffer)
    print("connect to remote host success")
    while True:
        print('recv again')
        request = local_socket.recv(0x1000)
        if(len(request) == 0):
            break
        parse = HttpParse(request)
        url = parse.url
        print("request for :" + url)
        value_in_cache = cache.get(url)
        if value_in_cache != '':
            print(url + 'is in cache')
            local_socket.send(value_in_cache)
        else:
            print(url + 'not in cache')
            remote_socket.send(request) #todo midified
            response = remote_socket.recv(0x1000)
            if(right_resource(response)):
                cache.add(url, response)
            local_socket.send(response)


    # threading.Thread(target=transfer, args=(remote_socket, local_socket, False)).start()
    # transfer(local_socket, remote_socket, True)

    

def server(local_port, max_connection):
    local_host = '0.0.0.0'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((local_host, local_port))
    server_socket.listen(max_connection)
    print '[+] Server started [%s:%d]' % (local_host, local_port)
    while True:
        local_socket, local_address = server_socket.accept()
        src_address = local_socket.getsockname()[0]
        if(not local_ip_usable(src_address)):
            print("you are forbidden to visit internet")
            continue
        print '[+] Detect connection from [%s:%s]' % (local_address[0], local_address[1])
        p = threading.Thread(target=proxy, args=(local_socket, True))

        # p = threading.Thread(target=sync_proxy, args=(local_socket, Cache()))
        p.start()

    print "[+] Releasing resources..."
    remote_socket.shutdown(socket.SHUT_RDWR)
    remote_socket.close()
    local_socket.shutdown(socket.SHUT_RDWR)
    local_socket.close()
    print "[+] Closing server..."
    server_socket.shutdown(socket.SHUT_RDWR)
    server_socket.close()
    print "[+] Server shuted down!"


def main():
    REMOTE_PORT = 80
    MAX_CONNECTION = 0x10
    server(8080, MAX_CONNECTION)


if __name__ == "__main__":
    main()