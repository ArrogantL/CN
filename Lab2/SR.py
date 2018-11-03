import threading
from queue import Queue

from GBN import *

# 接受窗口
recvN = 2
# 发送窗口
sendN = 3
# 序号空间
seqSpace = recvN + sendN

# 多线程参数
# cache：发送方，未ACK的分组的缓存
# timerlist：计时器列表，对应每一个发送窗口位置
# pend：发送方窗口满而等待发送的分组
# recvCache：接收方缓存
# recvOrder：接受方接受记录，成功接受的窗口位置
searg = {"seqSpace": seqSpace, "recvN": recvN, "sendN": sendN,
         "base": 0, "nextseqnum": 0,
         "cache": [DATAGRAM()] * seqSpace,
         "timerlist": [-1] * seqSpace,
         "pend": Queue(),
         "recvBase":0,
         "recvCache":[DATAGRAM()] * seqSpace,
         "recvOrder":[False]*seqSpace}


def sr(host, port, thost, tport):
    # sr主程序。facade设计模式的命令行。
    s = initSocket(host, port)
    s.connect((thost, tport))
    # 命令缓存
    q = Queue()
    # 实质上的主进程
    threading.Thread(target=procceedThread, args=[s, q]).start()
    while True:
        # 读取控制台信息connect  send close  3个命令
        s = input("Enter command:\n").split(' ', 1)
        q.put((s[0], s[1] + '0'))
        q.put((s[0], s[1] + '1'))
        q.put((s[0], s[1] + '2'))
        q.put((s[0], s[1] + '3'))
        q.put((s[0], s[1] + '4'))
        q.put((s[0], s[1] + '5'))
        q.put((s[0], s[1] + '6'))
        q.put((s[0], s[1] + '7'))
        q.put((s[0], s[1] + '8'))


def procceedThread(s, q):
    # 实质上的主进程，即使发送方，也能当接收方。实现双向传输
    threading.Thread(target=recvThread, args=[s]).start()
    threading.Thread(target=sendThread, args=[s]).start()
    while True:
        try:
            data = q.get(block=True, timeout=5)
        except:
            continue
        if data[0] == "send":
            searg["pend"].put(data[1])
        else:
            assert False





def sendThread(s):
    # 作为发送方式发送数据
    time=0
    while True:
        if searg["nextseqnum"] >= searg['base'] or searg["nextseqnum"] < (searg["base"] + searg["sendN"]) % searg[
            'seqSpace']:
            try:
                data = searg["pend"].get(block=True, timeout=5)
            except:
                continue
            dgram = DATAGRAM()
            dgram.data = data
            dgram.seqnum = searg["nextseqnum"]
            searg["timerlist"][dgram.seqnum] = 1
            searg["cache"][searg["nextseqnum"]] = dgram
            searg["nextseqnum"] = (searg["nextseqnum"] + 1) % searg["seqSpace"]

            print("Send:", dgram.data, "nextseqnumTo:", searg["nextseqnum"])

            s.send(dgram.toBytes())
        sleep(1)
        # 计时器每隔2次发送，就唤醒一次。重发所有没有ack的分组
        time+=1
        if time==2:
            for i in range(searg["sendN"]):
                j = (searg["base"] + i) % searg['seqSpace']

                timer=searg["timerlist"]

                if timer[j]==1:
                    dgram=searg["cache"][j]
                    print("Resend:", dgram.data, "nextseqnumTo:", searg["nextseqnum"])
                    s.send(dgram.toBytes())
            time=0

def recvThread(s):
    # 作为接收方时接收数据发送ACK，同时作为发送方接受ACK
    pcount=0
    while True:
        recpkt = s.recv(10000)
        recpkt = recpkt.decode("UTF-8").split('\n')
        #发送方接受ack
        if recpkt[0] == 'ACK':
            ack=int(recpkt[1])
            searg["timerlist"][ack]=0
            # 更新base、timerlist
            for i in range(searg["sendN"]):
                j=(searg["base"]+i)%searg['seqSpace']
                timer = searg["timerlist"]
                if  searg["timerlist"][j]!=0:
                    searg["base"]=j
                    break
                searg["timerlist"][j]=-1
            print("ACKed:" + recpkt[1], "base+To:", searg["base"])

        elif recpkt[0] == 'data':
            #接收方收到数据
            rcvseqnum = int(recpkt[1])
            rcvchecksum = int(recpkt[2])
            rcvdata = recpkt[3]

            #out of order buffer
            searg["recvCache"][rcvseqnum]=rcvdata
            searg["recvOrder"][rcvseqnum]=True
            da = ("ACK\n" + str(rcvseqnum) + "\n\n").encode("UTF-8")
            #recvbase、 recvOrder更新
            for i in range(searg["recvN"]):
                j=(searg["recvBase"]+i)%searg['seqSpace']
                if not searg["recvOrder"][j]:
                    searg["recvBase"]=j
                    pcount+=1
                    break
                searg["recvOrder"][j]=False
            print("ACK:" + str(rcvseqnum), "data：", recpkt[3],"recvbaseTo",searg["recvBase"])
            # 模拟分组丢失，模5丢失ack
            if pcount==5:
                print("forbidACK:" + str(rcvseqnum), "data：", recpkt[3])
                pcount=0
                continue
            s.send(da)
        else:
            print(recpkt)
            assert False

if __name__ == '__main__':
    threading.Thread(target=sr, args=["127.0.0.1", 8080, "127.0.0.1", 8081]).start()
    # connect 127.0.0.1 8081
