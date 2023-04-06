import math
from trio import MemoryReceiveChannel, MemorySendChannel, WouldBlock, sleep
import time
from pythonosc import udp_client
from Controllers.Throttle import throttle
#from dataclasses import dataclass

IDLE = 0
SHOCK = 1
VIBE = 2


class TouchPoint:
    def __init__(self, address: str, ids: list[int], intensity: float, method: int, duration: int, timeout: int, looping: bool, shouldUnmute: bool) -> None:
        self.address = address
        self.touchpointIntensity = intensity
        self.method = method
        self.duration = duration
        self.timeout = timeout
        self.lastActiveTime = 0
        self.state = IDLE
        self.ids = ids
        self.looping = looping
        self.lastIntensity = 0
        self.shouldUnmute = shouldUnmute

    def sendAction(self, active: float):
        normalOutput = {'ids': self.ids, 'intensity': self.touchpointIntensity*100*active, 'duration': self.duration, 'method': self.method, 'puppetActive': False}
        # TODO: add async task to reset intensity and method to IDLE after timeout
        if not active > 0.05:
            normalOutput['intensity'] = 0
            normalOutput['method'] = IDLE
        self.lastIntensity = normalOutput['intensity']
        if normalOutput['intensity'] > 0:
            self.lastActiveTime = time.time()
        return normalOutput 
    
    def resendAction(self):
        normalOutput = {'ids': self.ids, 'intensity': self.lastIntensity, 'duration': self.duration, 'method': self.method, 'puppetActive': False}
        # if normalOutput['intensity'] > 0:
        #     self.lastActiveTime = time.time()
        return normalOutput
            

    
    

# class TouchPointShocker:
#     def __init__(self, id: int, intensity: float) -> None:
#         self.id = id
#         self.intensity = intensity
        
#     def __dict__(self):
#         return {'id': self.id, 'intensity': self.intensity}

class TouchPointActions:
    def __init__(self, config, MemoryOut: MemorySendChannel, MemoryIn: MemoryReceiveChannel, oscClient: udp_client.SimpleUDPClient):
        self.config = config
        self.prefix = config['osc']['parameterPrefix']
        self.multiplier = .1
        self.panelMultiplier = 0
        self.panelMultiplierActive = False
        self.outputMultiplier = .1
        self.touchpoints = {} # dict of TouchPoints
        self.memoryOut = MemoryOut
        self.memoryIn = MemoryIn
        self.client = oscClient
        self.isMuted = False
        self.isAFK = False
        self.VRCEmote = 0
        self.touchDisabled = False
        for tp in self.config['osc']['touchpoints']:   
                # If duration exists, use it, otherwise use 100
                if 'duration' in tp.keys():
                    duration = tp['duration']
                else:
                    duration = 300

                if 'looping' in tp.keys():
                    looping = tp['looping']
                else:
                    looping = True

                if 'unmute' in tp.keys():
                    shouldUnmute = tp['unmute']
                else:
                    shouldUnmute = True

                self.addTouchpoint(self.prefix + tp['address'], tp['ids'], tp['intensity'], tp['method'], duration, config['osc']['touchpointTimeout'], looping, shouldUnmute)
            

    async def afkCheck(self):
        if self.isAFK or self.VRCEmote == 203 or self.touchDisabled:
            return True
        else: 
            return False
        
    @throttle(seconds=0.75)
    async def tryUnmute(self, touchpoint_address: str):
        if not await self.afkCheck() and self.isMuted and self.config['osc']['unmuteOnTouch']:
            print(f"Unmuting from touchpoint {touchpoint_address}")
            # check if the touchpoint has unmutung enabled
            if touchpoint_address in self.touchpoints.keys():
                if not self.touchpoints[touchpoint_address].shouldUnmute:
                    print(f"Touchpoint {touchpoint_address} has unmute disabled")
                    return
            self.client.send_message("/input/Voice",0)
            await sleep(0.05)
            self.client.send_message("/input/Voice",1)
            await sleep(0.05)
            self.client.send_message("/input/Voice",0)
        

    async def touch(self, address: str, activate: float|bool):
        if activate:
            try:
                await self.tryUnmute(address)
            except TypeError:
                # Throttled function returned None
                pass
        if address in self.touchpoints.keys():
            if not await self.afkCheck():
                await self.sendAction(self.touchpoints[address].sendAction(activate))
        else:
            print(f"Touchpoint {address} not found in config")
                

    def addTouchpoint(self, address: str, ids: list, intensity: float, method: int, duration: int, timeout: int, looping: bool, shouldUnmute: bool):
        self.touchpoints[address] = TouchPoint(address, ids, intensity, method, duration, timeout, looping, shouldUnmute)
            
    # async def removeTouchpoint(self, address: str, id: str):
    #     pass

    async def setIntensity(self, address: str, intensity: float):
        self.multiplier = intensity
        await self.processOutputMultiplier()

    async def muteStatus(self, address: str, mute: bool):
        self.isMuted = mute

    async def setAFK(self, address: str, afk: bool):
        self.isAFK = afk

    async def touchPointLoop(self):
        while True:
            # Loop through current active touchpoints and re-send their action
            # If it's been longer than the timeout, send an action with intensity 0
            for touchpoint in self.touchpoints.values():
                if touchpoint.lastIntensity > 0 and touchpoint.looping:
                    if time.time() - touchpoint.lastActiveTime > touchpoint.timeout:
                        await self.sendAction(touchpoint.sendAction(0))
                    else:
                        await self.sendAction(touchpoint.resendAction())
            await sleep(0.01)

    async def sendAction(self, action: dict):
        if not await self.afkCheck():
            action['intensity'] *= self.outputMultiplier
            #await self.memoryOut.send(action)
            if action['intensity'] > 0.5:
                await self.memoryOut.send(action)
            else:
                try:
                    self.memoryOut.send_nowait(action)
                except WouldBlock:
                    pass
        else:
            print(f"AFK! Not sending: {action}")

    async def setVRCEmote(self, address: str, value: int):
        self.VRCEmote = value

    async def setTouchDisabled(self, address: str, value: bool):
        self.touchDisabled = value
    
    async def processOutputMultiplier(self):
        if self.panelMultiplierActive:
            self.outputMultiplier = self.multiplier * self.panelMultiplier
        else:
            self.outputMultiplier = self.multiplier

    async def setPanelIntensity(self, address: str, value: float):
        self.panelMultiplier = value
        print(f"Panel multiplier set to {value}")
        await self.processOutputMultiplier()

    async def setPanelIntensityEnabled(self, address: str, value: bool):
        self.panelMultiplierActive = value
        await self.processOutputMultiplier()
        