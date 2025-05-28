from machine import Pin, Timer
import rp2
import time

from rp2 import StateMachine

class SegmentDisplay():
    
    def __init__(self, latch_pin=4, clock_pin=5,data_pin=6, is_red=True):
        
        self.latch=Pin(latch_pin, Pin.OUT)
        self.clock=Pin(clock_pin, Pin.OUT)
        self.data=Pin(data_pin, Pin.OUT)
        self.is_red=is_red
        
    def show(self, value):
       
        if not isinstance(value, str):
            digit=f'{int(value):03}'
        else:
            digit=value
            
        for i in range(len(digit)):
            self._post(digit[len(digit)-1-i])    
            
        #Latch the current segment data
        self.latch.low()
        self.latch.high()#Register moves storage register on the rising edge of RCK
        
#         if self.is_red:
#             print("| ",digit," |")
#         else:
#             print("                | ",digit," |")
        
        
    def _post(self, digit):
        #print("postNubmer: ",number)
        a=1<<0
        b=1<<6
        c=1<<5
        d=1<<4
        e=1<<3
        f=1<<1
        g=1<<2
        dp=1<<7
        if   digit == '1': segments =     b | c
        elif digit == '2': segments = a | b |     d | e |     g
        elif digit == '3': segments = a | b | c | d |         g
        elif digit == '4': segments =     b | c |         f | g
        elif digit == '5': segments = a |     c | d     | f | g
        elif digit == '6': segments = a |     c | d | e | f | g
        elif digit == '7': segments = a | b | c
        elif digit == '8': segments = a | b | c | d | e | f | g
        elif digit == '9': segments = a | b | c | d     | f | g
        elif digit == '0': segments = a | b | c | d | e | f
        elif digit == ' ': segments = 0
        elif digit == 'c': segments = g | e | d
        elif digit == '-': segments = g
        elif digit == '\\': segments = f | g | c
        elif digit == '/': segments = e | g | b
        else : segments = False
        
        #if (segments != dp):
        y=0
        while(y<8):
                self.clock.low()
                #print(segments & 1 << (7-y))
                self.data.value(segments & 1 << (7-y))
                self.clock.high()
                y += 1

red_display = SegmentDisplay(8,9,10,True)
green_display=SegmentDisplay(11,12,13,False)

def celebrate(is_red):       
    counters.off()
        
    if is_red:
        rep=0
        green_display.show('   ')
        while rep<5:
            red_display.show('///')
            time.sleep(0.5)
            red_display.show('\\\\\\')
            time.sleep(0.5)
            rep+=1
    else:
        rep=0
        red_display.show('   ')
        while rep<5:
            green_display.show('///')
            time.sleep(0.5)
            green_display.show('\\\\\\')
            time.sleep(0.5)
            rep+=1
 
    Counter.red=0
    Counter.green=0
    
     
    red_display.show(Counter.red)
    green_display.show(Counter.green)
    
    counters.on()

@rp2.asm_pio()
def button_debounce():
    wrap_target()
    label('isone')
    wait(0, pin, 0)      # the pin is 1, wait for it to become 0
    set(x, 61)          # prepare to test the pin for 31 times
    
    label('checkone')
    jmp(pin, 'isone')     # if the pin has returned to 1, start over
    jmp(x_dec, 'checkone')  # decrease the time to wait
    jmp('iszero')        # the pin has definitively become 0
     
    label('iszero')
    wait(1, pin, 0)      # the pin is 0, wait for it to become 1
    set(x, 61)          # prepare to test the pin for 31 times
    
    label('checkzero')
    jmp(pin, 'stillone')  # check if the pin is still 1

    label('stillone')
    jmp(x_dec, 'checkzero') # decrease the time to wait, or the pin has definitively become 1
    
    irq(rel(0))  # Trigger an interrupt when debounce is complete           
     
    wrap()
 
class Counter:
    max=1000 
    red=0
    green=0
    red_changed=True
    green_changed=True
    
    
    def __init__(self, sm, is_red):
        self.is_red = is_red
        self.sm=sm
        self.sm.active(1)
        self.sm.irq(handler=self._pin_change) 

    def _pin_change(self, sm):

        if self.is_red:
            Counter.red += 1
            Counter.red_changed=True

        else:
            Counter.green += 1
            Counter.green_changed=True
            
    def active(self, value):
        self.sm.active(value)
        
    def restart(self):
        self.sm.restart()
            
class Counters:
    def __init__(self):
        self.counters=[]
        
    def add(self,click_counter):
        self.counters.append(click_counter)
        
    def on(self):
        for c in self.counters:
            c.active(1)
            c.restart()          
    
    def off(self):
        for c in self.counters:
            c.active(0)
        

counters = Counters()

# create and add red counters
counters.add(Counter(StateMachine(0, button_debounce, freq=10000
                                   , in_base=Pin(16, Pin.IN, Pin.PULL_UP))
                                   , True))
counters.add(Counter(StateMachine(1, button_debounce, freq=10000
                                   , in_base=Pin(17, Pin.IN, Pin.PULL_UP))
                                   , True))
counters.add(Counter(StateMachine(2, button_debounce, freq=10000
                                   , in_base=Pin(18, Pin.IN, Pin.PULL_UP))
                                   , True))  

# create and add green counters
counters.add(Counter(StateMachine(4, button_debounce, freq=10000
                                   , in_base=Pin(5, Pin.IN, Pin.PULL_UP))
                                   , False))
counters.add(Counter(StateMachine(5, button_debounce, freq=10000
                                   , in_base=Pin(6, Pin.IN, Pin.PULL_UP))
                                   , False))
counters.add(Counter(StateMachine(6, button_debounce, freq=10000
                                   , in_base=Pin(7, Pin.IN, Pin.PULL_UP))
                                   , False))    


def refresh(timer):
    if Counter.red_changed:
        if Counter.red>=Counter.max:
            celebrate(True)
        else:
            red_display.show(Counter.red)
        Counter.red_changed=False
    
    if Counter.green_changed:  
        if Counter.green>=Counter.max:
            celebrate(False)
        else:
            green_display.show(Counter.green)
        Counter.green_changed=False        
  

refresh_timer = Timer(-1)
refresh_timer.init(period=100, mode=Timer.PERIODIC, callback=refresh)
 
 
# Read accumulated value
try:
    while True:
        pass 
except KeyboardInterrupt:
    counters.off()