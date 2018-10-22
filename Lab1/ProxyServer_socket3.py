# coding=utf-8
import select
import socket
import sys
import threading
import time
import traceback
import _thread

HOST = '0.0.0.0'
PORT = 8080


def initSocket(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(50)
    print('Server start at: %s:%s' % (host, port))
    print('wait for connection...')
    return s


def parseHttpHead(data):
    """
    接受http请求报文，加入ifms。
    并解析出来服务类型、
    :param data:
    :return:
    """
    data = data.decode("UTF-8")
    dataLines = data.splitlines(keepends=False)
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
    print("Succeed HeadParse")
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


def proxyThread(conn):
    conn.setblocking(0)
    try:
        time.sleep(5)
        httpParam = conn.recv(1000000)

        print("Receive request..")
        if len(httpParam) < 3:
            print("None request")
            print("RClose %s" % conn)
            conn.close()
            return
        print("Request\n%s" % httpParam.decode("UTF-8"))
        HttpHead = parseHttpHead(httpParam)
        if HttpHead.method == "CONNECT":
            print("CONNECT TYPE!")
            print("RClose %s" % conn)
            conn.close()
            return

        serverSocket = connnect2Server(HttpHead)
        serverSocket.send(httpParam)
        serverResponse = serverSocket.recv(4000)
        try:
            # print("Respone\n%s"%serverResponse.decode("UTF-8"))
            print("Respone\n")
        except:
            # print("Respone can't decode by UTF-8\n")
            print("Respone wrong\n")
        conn.send(serverResponse)
        serverSocket.close()
        print("Close %s" % conn)
        conn.close()
    except BaseException as e:
        traceback.print_exc(e)


def proxyServer(host, port):
    try:
        s = initSocket(host, port)
        while True:
            conn, addr = s.accept()
            print("\nStart connect %s", addr)
            p = threading.Thread(target=proxyThread, args=[conn]).start()

    except BaseException as e:
        traceback.print_exc(e)
        s.close()
    finally:
        s.close()


if __name__ == '__main__':
    proxyServer(HOST, PORT)
