# coding=utf-8
import socket
import threading
import sys

HOST = '0.0.0.0'
PORT = 8081
MAX_CONNECT=50

def initSocket(host, port):
    proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxySocket.bind((host, port))
    proxySocket.listen(MAX_CONNECT)
    print('Server start at: %s:%s' % (host, port))
    print('wait for connection...')
    return proxySocket


def parseHttpHead(data):
    """
    接受http请求报文，加入ifms。
    并解析出来服务类型、
    :param data:
    :return:
    """
    data = data.decode("UTF-8")
    dataLines = data.split("\r\n")
    firstLine = dataLines[0]
    firstLine = firstLine.split(' ')
    hh = HttpHead()
    hh.method = firstLine[0]
    hh.url = firstLine[1].split(":")[0]
    hh.httpVersion = firstLine[2]
    for l in range(len(dataLines) - 1):
        para = dataLines[l + 1].split(': ', 1)
        if para[0] == "Cookie":
            hh.cookie = para[1]
        if para[0] == "Host":
            hh.host = para[1].split(":")[0]

    return hh


class HttpHead:
    def __init__(self):
        self.method = ''
        self.url = ''
        self.host = "127.0.0.1"
        self.cookie = ''
        self.httpVersion = ''



def connnect2Server(HttpHead):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HttpHead.host, 80))
    return s


def proxyThread(localSocket):
    print("Start proxy")
    #localSocket.setblocking(0)
    #设定惯例标准4k大小
    httpParam = localSocket.recv(0x1000)
    if len(httpParam) < 3:
        print("None request")
        print("RClose %s" % localSocket)
        localSocket.close()
        return

    print("Succeed Received request..")

    print(httpParam.decode("UTF-8"))


    HttpHead = parseHttpHead(httpParam)
    print("Succeed HeadParse")
    if HttpHead.method == "CONNECT":
        print("CONNECT TYPE!")
        print("RClose %s" % localSocket)
        localSocket.close()
        return


    print("Connect remoteServer")
    remoteSocket = connnect2Server(HttpHead)
    remoteSocket.send(httpParam)
    print("Succeed connect to remoteServer")
    channel(localSocket, remoteSocket, True)
    threading.Thread(target=channel, args=(localSocket, remoteSocket, False)).start()



def channel(localSocket,remoteSocket,direction):
    while True:
        if direction:
            httpParam=localSocket.recv(0x1000)
            if len(httpParam)==0:
                break
            remoteSocket.send(httpParam)
        else:
            httpParam = remoteSocket.recv(0x1000)
            if len(httpParam) == 0:
                break
            localSocket.send(httpParam)
    localSocket.shutdown(socket.SHUT_RDWR)
    remoteSocket.shutdown(socket.SHUT_RDWR)
    remoteSocket.close()
    localSocket.close()

def proxyServer(host, port):
    proxySocket = initSocket(host, port)
    while True:
        localSocket, localAddress = proxySocket.accept()
        print("\nStart connect %s", localAddress)
        p = threading.Thread(target=proxyThread, args=[localSocket]).start()





if __name__ == '__main__':
    proxyServer(HOST, PORT)
