import math
from trio import MemoryReceiveChannel, MemorySendChannel, WouldBlock, sleep
import time

IDLE = 0
SHOCK = 1
VIBE = 2



class ShockActions:
    def __init__(self, config, MemoryOut: MemorySendChannel, MemoryIn: MemoryReceiveChannel):
        self.config= config
        self.prefix = "/avatar/parameters/"
        self.multiplier = .5
        self.activeIntensity = 0
        self.intensity = 0
        self.duration = 0
        self.method = IDLE
        self.MemoryIn = MemoryIn
        self.MemoryOut = MemoryOut
        self.ids = []
        self.puppetActive = False
    
    async def setMethod(self, address: str, method: int):
        print(f"Got method {method}")
        self.method = method
        await sleep(0)
    
    async def setTarget(self, address: str, enable: bool):
        target = int(address[-1])-1
        try:
            if enable:
                self.ids.append(self.config['OpenShock']['ids'][target])
                print(f"Got target {target}")
            elif self.config['OpenShock']['ids'][target] in self.ids:
                self.ids.remove(self.config['OpenShock']['ids'][target])
                print(f"Removed target {target}")
        except IndexError:
            print(f"Target {target} not found")        
        await sleep(0)
        
    async def run(self, address: str, quick: bool, active: bool):
        print(f"Got run active: {active}, quick: {quick}")
        if active:
            d = self.__dict__()
            if quick[0]:
                d['duration'] /= 10 
            await self.MemoryOut.send(d)
        await sleep(0)
        
    async def setActiveIntensity(self, intensity: float):
        self.activeIntensity = intensity
        await sleep(0)
        
    async def setIntensity(self, address: str, intensity: float):
        self.intensity = intensity
        await sleep(0)
        
    async def setDuration(self, address: str, duration: float):
        self.duration = self.map_with_clamp(duration, 0, 1, 0, 15000)
        await sleep(0)
        
    async def puppetRun(self, address: str, intensity: float):
        
        await self.setActiveIntensity(intensity)
        d = self.__dict__()
        d['duration'] = 0
        d['intensity'] = self.calculateIntensity(True)
        await self.MemoryOut.send(d)
        await sleep(0)
            
    async def setPuppetActive(self, address: str, active: bool):
        print(f"Got puppet active {active}")
        self.puppetActive = active
        d = self.__dict__()
        d['duration'] = 0
        d['intensity'] = self.calculateIntensity(True)
        await self.MemoryOut.send(d)
        await sleep(0)

    def calculateIntensity(self, puppet=False):
        if puppet:
            if self.puppetActive:
                if self.activeIntensity > 0:
                    return self.map_with_clamp(self.activeIntensity, 0, 1, 0, 100*self.multiplier)
                elif self.activeIntensity < 0:
                    return self.map_with_clamp(self.activeIntensity, -1, 0, 25*self.multiplier, 0)
                else: 
                    return 0
            else:
                return 0
        else:
            if self.intensity > 0:
                return self.map_with_clamp(self.intensity, 0, 1, 0, 100*self.multiplier)
            elif self.intensity < 0:
                return self.map_with_clamp(self.intensity, -1, 0, 25*self.multiplier, 0)
            else: 
                return 0

    async def setMultiplier(self, address, multiplier):
        print(f"Got multiplier {multiplier}")
        self.multiplier = multiplier
        await sleep(0)
        
        
    def __dict__(self):
        return {'intensity': self.calculateIntensity(), 'method': self.method, 'ids': self.ids, 'duration': self.duration , 'puppetActive': self.puppetActive}

    # Stolen from @NicoHood and @st42 (github users) in a discussion about the
    # map() function being weird
    # https://github.com/arduino/ArduinoCore-API/issues/51#issuecomment-87432953
    @staticmethod
    def map_with_clamp(x, in_min, in_max, out_min, out_max):
        # if input is smaller/bigger than expected return the min/max out ranges value
        if x < in_min:
            return out_min
        elif x > in_max:
            return out_max

        # map the input to the output range.
        # round up if mapping bigger ranges to smaller ranges
        elif (in_max - in_min) > (out_max - out_min):
            return (x - in_min) * (out_max - out_min + 1) / (in_max - in_min + 1) + out_min
        # round down if mapping smaller ranges to bigger ranges
        else:
            return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min