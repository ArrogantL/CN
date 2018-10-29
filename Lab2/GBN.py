import socket
import threading
from queue import Queue
from time import sleep
class DATAGRAM():
    def __init__(self):
        self.seqnum = -1
        self.data= ''
        self.checksum=-1
    def toBytes(self):
        return ("data\n"+str(self.seqnum) +"\n" + str(self.checksum) +"\n" + self.data).encode("UTF-8")


N=2
seqSpace=N+1

searg={"seqSpace":seqSpace,"N":N, "base":0, "nextseqnum":0, "cache": [DATAGRAM()] * seqSpace, "timer":False, "pend":Queue()}

def initSocket(host, port):
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM, socket.getprotobyname('udp'))
    s.bind((host, port))
    print('Server start at: %s:%s' % (host, port))
    print('wait for connection...')
    return s
def gbn(host,port,thost,tport):
    s=initSocket(host,port)
    s.connect((thost,tport))
    q = Queue()
    p2 = threading.Thread(target=serverThread, args=[s,q]).start()
    while True:
        #读取控制台信息connect  send close  3个命令
        s = input("Enter command:\n").split(' ',1)
        q.put((s[0],s[1]+'0'))
        q.put((s[0], s[1]+'1'))
        q.put((s[0], s[1]+'2'))
        q.put((s[0], s[1]+'3'))
        q.put((s[0], s[1]+'4'))
        q.put((s[0], s[1] + '5'))
        q.put((s[0], s[1] + '6'))
        q.put((s[0], s[1] + '7'))
        q.put((s[0], s[1] + '8'))



def serverThread(s,q):
    threading.Thread(target=timerThread, args=[s]).start()
    threading.Thread(target=recACKThread, args=[s]).start()
    threading.Thread(target=sendThread, args=[s]).start()
    while True:
        try:
            data=q.get(block=True, timeout=5)
        except:
            continue
        if data[0]=="send":
            searg["pend"].put(data[1])
        else:
            assert False

def sendThread(s):
    while True:
        if searg["nextseqnum"]>=searg['base'] or searg["nextseqnum"] < (searg["base"] + searg["N"])%searg['seqSpace']:
            try:
                data = searg["pend"].get(block=True, timeout=5)
            except:
                continue
            dgram = DATAGRAM()
            dgram.data = data
            dgram.seqnum = searg["nextseqnum"]
            searg["cache"][searg["nextseqnum"]] = dgram
            searg["nextseqnum"] = (searg["nextseqnum"] + 1) % searg["seqSpace"]
            print("Send:", dgram.data, "nextseqnumTo:",searg["nextseqnum"])
            s.send(dgram.toBytes())


            if searg["base"] == searg["nextseqnum"]:
                print("Finish")
                searg['timer'] = False
            else:
                searg['timer'] = True
        sleep(1)

def timerThread(s):
    count=0
    while True:
        while searg['timer']==True:
            print("Timer:",count,)
            if count>=5:
                searg['timer']=True
                nextseqnum=searg["nextseqnum"]
                base=searg["base"]
                print("base:",base)
                print("nextseqnum:",nextseqnum)
                for i in range((nextseqnum-base)%searg['seqSpace']):
                    m=(base + i)%searg['seqSpace']
                    print("Resend:",m,searg["cache"][m].data)

                    s.send(searg["cache"][m].toBytes())
                break
            count+=1
            sleep(0.1)
        count=0
        sleep(0.1)

def recACKThread(s):
    exceptseqnum = 0
    pcount=0
    while True:
        recpkt=s.recv(10000)
        recpkt=recpkt.decode("UTF-8").split('\n')
        if recpkt[0]=='ACK' :
            ack = (int(recpkt[1]) + 1) % searg['seqSpace']
            if ack > searg["base"]:
                searg["base"] = ack
            print("ACKed:" + recpkt[1], "base+To:",searg["base"] )
            if searg["base"]==searg["nextseqnum"]:
                searg["timer"]=False
            else:
                searg["timer"]=True
        elif recpkt[0]=='data':
            rcvseqnum = int(recpkt[1])
            rcvchecksum = int(recpkt[2])
            rcvdata = recpkt[3]
            da = ("ACK\n" + str(exceptseqnum) + "\n\n").encode("UTF-8")
            print("ACK:" + str(exceptseqnum), "data：", recpkt[3])
            if pcount==5:

                print("forbidACK:" + str(exceptseqnum), "data：", recpkt[3])
                pcount=0
                continue
            s.send(da)
            if rcvseqnum == exceptseqnum:
                pcount+=1
                exceptseqnum = (1+exceptseqnum)%searg['seqSpace']
        else:
            print(recpkt)
            assert False


def getacknum(recpkt):
    return recpkt.decode("UTF-8")




if __name__ == '__main__':
    threading.Thread(target=gbn, args=["127.0.0.1",8080,"127.0.0.1",8081]).start()
    #connect 127.0.0.1 8081