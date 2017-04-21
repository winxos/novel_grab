from novel_grab.novel_grab import Downloader
from threading import Thread

class A:
    b=[]
    def __init__(self):
        self.a = 0
        self.c = []
if __name__ == "__main__":
    d = A()
    b = A()
    print(id(d))
    print(id(b))
    print(id(d.a))
    print(id(b.a))
    d.a = 5
    print(id(d.a))
    print(id(b.a))
    print(id(d.b))
    print(id(b.b))
    d.b=[1]
    b.b=[2]
    print(id(d.b))
    print(id(b.b))
    print(id(d.c))
    print(id(b.c))

    b=Downloader()
    print(b.set_url("http://book.zongheng.com/showchapter/510426.html"))
    print(b.items)
    b.start()

    c=Downloader()
    print(c.set_url("http://book.zongheng.com/showchapter/221579.html"))
    print(c.items)
    c.start()