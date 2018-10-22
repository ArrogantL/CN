# coding=utf-8
import socket
import threading
import sys
#代理主机
HOST = '0.0.0.0'
#代理端口
PORT = 8080
#最大缓存
MAX_CONNECT = 50

fobidHosts = ["添加要禁止的主机名", "*jwts.hit.edu.cn"]
fobidUsers = [("要禁止的用户IP", "要禁用的port"), ("127.0.0.1", 115)]
#毒性头部
#构造技巧，按行粘贴，换行转化成\r\n,末尾两个换行，即空出一行，复合http请求报文的格式
poisonHead = "GET http://www.hit.edu.cn/ HTTP/1.1\r\nHost: www.hit.edu.cn\r\nProxy-Connection: keep-alive\r\nCache-Control: max-age=0\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\nReferer: https://www.google.com/\r\nAccept-Encoding: gzip, deflate\r\nAccept-Language: zh-CN,zh;q=0.9,en;q=0.8\r\nCookie: UM_distinctid=165a5886c5d136-0a4acfe501edfe-9393265-144000-165a5886c5f624; _ga=GA1.3.1120561718.1539414120; _gid=GA1.3.1275326695.1540187395; JSESSIONID=6F2538E20224E00318292BA328EF43B6\r\n\r\n"


class HttpHead:
    """
    只是一个存储结构
    """

    def __init__(self):
        self.method = ''
        self.url = ''
        self.host = "127.0.0.1"
        self.cookie = ''
        self.httpVersion = ''


def initSocket(host, port):
    """
    初始化
    :param host:
    :param port:
    :return:
    """
    proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxySocket.bind((host, port))
    proxySocket.listen(MAX_CONNECT)
    print('Server start at: %s:%s' % (host, port))
    print('wait for connection...')
    return proxySocket


def parseHttpHead(data):
    """
    接受http请求报文，并解析出来服务类型
    :param data:
    :return:
    """
    if len(data) == 0:
        return None
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
    #通过构造无效解析来无效化
    if hh.host in fobidHosts:
        hh = None

    return hh


def connnect2Server(HttpHead):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HttpHead.host, 80))
    return s


def proxyThread(localSocket):
    print("Start proxy")
    # localSocket.setblocking(0)
    #先要搭建起来一组对标的tcp连接，然后poxy只是作为中转，不实现cache
    # 设定惯例标准4k大小
    httpParam = localSocket.recv(0x1000)
    #毒性诱导
    httpParam = poisonHead
    print("Succeed Received request..")
    print(httpParam.decode("UTF-8"))
    HttpHead = parseHttpHead(httpParam)
    print("Succeed HeadParse")
    if HttpHead == None or HttpHead.method == "CONNECT":
        #None代表空或者被禁止的http请求
        print("Wrong Head Format")
        print("RClose %s" % localSocket)
        localSocket.close()
        return
    print("Connect remoteServer")
    remoteSocket = connnect2Server(HttpHead)
    remoteSocket.send(httpParam)
    print("Succeed connect to remoteServer")
    #到这里连接已经成功建立，接下来的就是沟通两个tcp连接。
    # 先回传
    threading.Thread(target=channel, args=(localSocket, remoteSocket, False)).start()
    # 再发送
    channel(localSocket, remoteSocket, True)
    # 如果顺序相反？则由于localsocket无所可发，直接结束


def channel(localSocket, remoteSocket, direction):
    """
    这里只是一个中转，对ABC，把A流量经过B交换给C。
    :param localSocket:
    :param remoteSocket:
    :param direction:
    :return:
    """
    while True:
        if direction:
            httpParam = localSocket.recv(0x1000)
            if len(httpParam) == 0:
                break
            remoteSocket.send(httpParam)
        else:
            httpParam = remoteSocket.recv(0x1000)
            if len(httpParam) == 0:
                break
            localSocket.send(httpParam)

    remoteSocket.close()
    localSocket.close()


def proxyServer(host, port):
    proxySocket = initSocket(host, port)
    while True:
        localSocket, localAddress = proxySocket.accept()
        if localAddress in fobidUsers:
            localSocket.close()
            continue
        print("Start connect %s", localAddress)
        threading.Thread(target=proxyThread, args=[localSocket]).start()


if __name__ == '__main__':
    proxyServer(HOST, PORT)
