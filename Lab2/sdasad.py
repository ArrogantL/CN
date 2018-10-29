from GBN import *
if __name__ == '__main__':
    threading.Thread(target=gbn, args=["127.0.0.1",8081,"127.0.0.1",8080]).start()
