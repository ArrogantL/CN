import threading

from SR import sr

if __name__ == '__main__':
    threading.Thread(target=sr, args=["127.0.0.1", 8081, "127.0.0.1", 8080]).start()
    # connect 127.0.0.1 8081