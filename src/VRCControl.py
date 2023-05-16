from Controllers.AsyncDispatcher import AsyncDispatcher
from Controllers.TrioOSCServer import TrioOSCServer
from Controllers.Shocker import ShockActions
from Controllers.TouchPoints import TouchPointActions
from pythonosc.udp_client import SimpleUDPClient
from threading import Thread
from colorama import init, Fore
import asyncio
import trio
from trio_websocket import open_websocket_url, serve_websocket, ConnectionClosed
import time
import os
import socket
import json
import sys

config = {}

# From https://stackoverflow.com/a/42615559
# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

global worker_rec_g, worker_send_g

def checkBindable(host, port, timeout=5.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except:
        return False

async def connectWs(worker_send: trio.MemorySendChannel, worker_receive: trio.MemoryReceiveChannel):
    async with open_websocket_url(f"ws://{config['OpenShock']['host']}:{config['OpenShock']['port']}/ws") as ws:

        # Recieve shocker list from OpenShock websocket
        #shockers = json.loads(await ws.get_message())
        #print(Fore.GREEN + "Successfully connected to OpenShock websocket", Fore.RESET)
        #print(await ws.get_message())

        # We're connected to a websocket, but we don't know if it's OpenShock yet.
        # If we get a list of shockers within a few seconds, we're good to go.
        # Otherwise, we'll assume it's not OpenShock and close the connection.
        try:
            with trio.fail_after(3):
                shockers = json.loads(await ws.get_message())
                print(Fore.GREEN + "Successfully connected to OpenShock websocket", Fore.RESET)
        except trio.TooSlowError:
            print(Fore.RED + "OpenShock websocket connection timed out", Fore.RESET)
            return

        shockParams = None
        lastPingSent = 0
        websocketHealthy = True
        while True:
            try:
                shockParams = worker_receive.receive_nowait()
            except trio.WouldBlock:
                pass
            
            # Every 3 seconds, send a ping and await a pong to see if the websocket is alive
            if time.time() - lastPingSent > 3:
                lastPingSent = time.time()
                try:
                    with trio.fail_after(3):
                        await ws.ping()
                        websocketHealthy = True
                except trio.TooSlowError:
                    websocketHealthy = False
                    print(Fore.RED + "OpenShock websocket ping timed out", Fore.RESET)


            # While ShockActive is true, keep sending shock parameters dict to OpenShock websocket as JSON
            # and when it goes false, send one final message to stop the shock.
            if shockParams is not None and websocketHealthy:
                print(f"Sending: {json.dumps(shockParams)}")
                # for id in shockParams['ids']:
                #     _shockParams = shockParams.copy()
                #     _shockParams.pop('ids')
                #     _shockParams['id'] = id
                #     await ws.send_message(json.dumps(_shockParams))
                await ws.send_message(json.dumps(shockParams))
                if ('puppetActive' in shockParams.keys() and shockParams['puppetActive'] == False) or shockParams['intensity'] == 0 or shockParams['method'] == 0:
                    shockParams = None
            elif not websocketHealthy:
                # print("Draining queued messages...")
                drain = 0
                with trio.move_on_after(1):
                    async for _ in worker_receive:
                        drain += 1
                print(f'Drained {drain} queued messages.')
                await trio.sleep(1)
                
            

            await trio.sleep(0.01)

async def websocketServer(request):
    ws = await request.accept()
    global worker_rec_g, worker_send_g
    while True:
        try:
            shockParams = None
            lastPingSent = 0
            websocketHealthy = True
            while True:
                try:
                    shockParams = worker_rec_g.receive_nowait()
                except trio.WouldBlock:
                    pass
                
                # Every 3 seconds, send a ping and await a pong to see if the websocket is alive
                if time.time() - lastPingSent > 3:
                    lastPingSent = time.time()
                    try:
                        with trio.fail_after(3):
                            await ws.ping()
                            websocketHealthy = True
                    except trio.TooSlowError:
                        websocketHealthy = False
                        print(Fore.RED + "OpenShock websocket ping timed out", Fore.RESET)


                # While ShockActive is true, keep sending shock parameters dict to OpenShock websocket as JSON
                # and when it goes false, send one final message to stop the shock.
                if shockParams is not None and websocketHealthy:
                    print(f"Sending: {json.dumps(shockParams)}")
                    # for id in shockParams['ids']:
                    #     _shockParams = shockParams.copy()
                    #     _shockParams.pop('ids')
                    #     _shockParams['id'] = id
                    #     await ws.send_message(json.dumps(_shockParams))
                    await ws.send_message(json.dumps(shockParams))
                    if ('puppetActive' in shockParams.keys() and shockParams['puppetActive'] == False) or shockParams['intensity'] == 0 or shockParams['method'] == 0:
                        shockParams = None
                elif not websocketHealthy:
                    await trio.sleep(1)
                    
                

                await trio.sleep(0.01)
        except ConnectionClosed:
            print("Connection closed")
            break


async def openshock(worker_send: trio.MemorySendChannel, worker_receive: trio.MemoryReceiveChannel, recursion=0):
    try:
        await connectWs(worker_send, worker_receive)
        #await serve_websocket(websocketServer, None, 8080, ssl_context=None)

    except Exception as e:
        print(Fore.RED + f"OpenShock Socket Exception ({type(e).__name__})")
        print(e)
        print(e.with_traceback(None))
        # If the exception was a HandshakeError, tell the user to make sure the device is on
        if type(e).__name__ == 'HandshakeError':
            print("Make sure the device is on and connected to the same network as the computer.")
            print("If trying to connect to an outside device, ensure their port was properly opened.")
        print(Fore.RESET)
        print('Retrying...')
        await trio.sleep(1)
        await openshock(worker_send, worker_receive, recursion+1)


async def init_main():
    # Read config file (VRCControl.json) if it exists

    if os.path.exists(application_path+'/VRCControl.json'):
        with open(application_path+'/VRCControl.json') as f:
            config.update(json.load(f))
    dispatcher = AsyncDispatcher()
    server = TrioOSCServer((config['osc']['host'],  config['osc']['ListeningPort']), dispatcher)
    if not checkBindable(config['osc']['host'],  config['osc']['ListeningPort']):
        print(Fore.RED + "Failed to bind to port, is another instance running?", Fore.RESET)
        raise SystemExit
    
    osc_client = SimpleUDPClient(config['osc']['host'], config['osc']['SendingPort'])

    cancel_scope = trio.CancelScope()
    with cancel_scope:
        try:
            async with trio.open_nursery() as nursery:
                worker_send, worker_recieve = trio.open_memory_channel(1)
                async with worker_send, worker_recieve:
                    touchPointActions = TouchPointActions(config, worker_send.clone(), worker_recieve.clone(), osc_client)
                    shockerActions = ShockActions(config, worker_send.clone(), worker_recieve.clone())
                    nursery.start_soon(server.start)
                    nursery.start_soon(touchPointActions.touchPointLoop)
                    global worker_rec_g, worker_send_g
                    worker_rec_g = worker_recieve.clone()
                    worker_send_g = worker_send.clone()
                    nursery.start_soon(openshock, worker_send.clone(), worker_recieve.clone())

                    dispatcher.map("/avatar/parameters/OpenShock/PuppetY", shockerActions.puppetRun)
                    dispatcher.map("/avatar/parameters/OpenShock/Intensity", shockerActions.setMultiplier)
                    dispatcher.map("/avatar/parameters/OpenShock/Intensity", shockerActions.setIntensity)
                    dispatcher.map("/avatar/parameters/OpenShock/PuppetActive", shockerActions.setPuppetActive)
                    dispatcher.map("/avatar/parameters/OpenShock/Target*", shockerActions.setTarget)
                    dispatcher.map('/avatar/parameters/OpenShock/Method', shockerActions.setMethod)
                    dispatcher.map('/avatar/parameters/OpenShock/Duration', shockerActions.setDuration)
                    dispatcher.map('/avatar/parameters/OpenShock/ShockQuick', shockerActions.run, True)
                    dispatcher.map('/avatar/parameters/OpenShock/Shock', shockerActions.run, False)

                    for tp in config['osc']['touchpoints']:
                        dispatcher.map(f"{config['osc']['parameterPrefix']}{tp['address']}", touchPointActions.touch)
                    dispatcher.map("/avatar/parameters/MuteSelf", touchPointActions.muteStatus)
                    dispatcher.map("/avatar/parameters/OpenShock/Intensity", touchPointActions.setIntensity)
                    dispatcher.map("/avatar/parameters/AFK", touchPointActions.setAFK)
                    dispatcher.map("/avatar/parameters/OpenShock/TouchDisable", touchPointActions.setTouchDisabled)

                    dispatcher.map("/avatar/parameters/VRCEmote", touchPointActions.setVRCEmote)

                    print("OpenShock VRCControl ready!")
        except RecursionError:
            print(Fore.RED + "Too many connection attempts, giving up.", Fore.RESET)
            raise SystemExit


            
if __name__ == "__main__":
    trio.run(init_main)