"""Independent algorithm models. These tests are NOT HDL or hardware simulation."""
from collections import deque
class FIFOModel:
    def __init__(self,depth):
        if depth<2 or depth&(depth-1):raise ValueError('power-of-two depth')
        self.depth=depth;self.q=deque();self.dropped=0
    def cycle(self,push=None,pop=False):
        # pop sees pre-cycle valid/data; simultaneous full pop+push is permitted.
        item=self.q.popleft() if pop and self.q else None
        if push is not None:
            if len(self.q)<self.depth:self.q.append(push)
            else:self.dropped=min(0xffffffff,self.dropped+1)
        return item
class QuadModel:
    plus={(0,1),(1,3),(3,2),(2,0)}
    def __init__(self):self.old=0;self.pos=0;self.illegal=0
    def step(self,ab,z=False):
        if not 0<=ab<=3:raise ValueError('ab')
        if ab==self.old:pass
        elif (self.old,ab) in self.plus:self.pos+=1
        elif (ab,self.old) in self.plus:self.pos-=1
        else:self.illegal+=1
        self.old=ab
        return self.pos
class AxisPacketModel:
    def __init__(self,n=256):self.n=n;self.count=0;self.hold=None;self.half=0
    def put(self,r):
        if self.hold is not None:raise RuntimeError('not ready')
        self.hold=r;self.half=0
    def output(self):
        if self.hold is None:return None
        b=self.hold.pack();data=int.from_bytes(b[self.half*8:self.half*8+8],'little')
        return data,255,bool(self.half and(self.count==self.n-1 or self.hold.kind==0x7f))
    def cycle(self,ready):
        o=self.output()
        if o is not None and ready:
            if self.half:
                self.count=0 if o[2] else self.count+1;self.hold=None;self.half=0
            else:self.half=1
        return o

def spi_frame(read,address,value=0):
    if not 0<=address<8192 or not 0<=value<256:raise ValueError('SPI range')
    word=(int(bool(read))<<23)|(address<<8)|value
    return [(word>>i)&1 for i in range(23,-1,-1)]
