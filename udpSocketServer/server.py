import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      print (data)
      positionMessage = data[15:]
      #print("Got this: "+positionMessage)
      if addr in clients:
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
            
         if 'sendPosition' in data:
            clients[addr]['position']=positionMessage
            #print(clients[addr]['position'])
            #print(addr)
      else:
         if 'connect' in data:
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
            clients[addr]['position'] = {"X": 0, "Y": 0, "Z": 0}
            message = {"cmd": 0, "players":[]} #{"id":addr}}

            p = {}
            p['id'] = str(addr)
            p['color'] = clients[addr]['color']
            p['position']=clients[addr]['position']
            message['players'].append(p)

            GameState = {"cmd": 4, "players":[]}
            for c in clients:
               if (c == addr):
                  message['cmd'] = 3
               else:
                  message['cmd'] = 0

               m = json.dumps(message,separators=(",", ":"))
               player = {}
               player['id'] = str(c)
               player['color']= clients[c]['color']
               player['position']=clients[c]['position']
               GameState['players'].append(player)
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
               print(m)

            m = json.dumps(GameState)
            print(m)
            sock.sendto(bytes(m,'utf8'), addr)

def cleanClients(sock):
   while True:
      droppedClients = []
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
            droppedClients.append(str(c))
      
      message = {"cmd": 2, "droppedPlayers":droppedClients}
      m = json.dumps(message,separators=(",", ":"))
      if (len(droppedClients) > 0):
         for c in clients:
            sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
      
      time.sleep(1)

def gameLoop(sock):
   pktID = 0
   while True:
      GameState = {"cmd": 1, "pktID": pktID, "players": []}
      clients_lock.acquire()
#      print (clients)
      for c in clients:
         player = {}
         
         #print(clients[c]['position'])
         #clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         #clients[c]['position'] = {"X": random.random(), "Y": random.random(), "Z": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         receivedPos=str(clients[c]['position'])
         receivedPosX= (receivedPos.split("(")[-1].split(")")[0].split(",")[0])
         receivedPosY= (receivedPos.split("(")[-1].split(")")[0].split(" ",1)[-1].split(",")[0])
         player['position'] = {"X":receivedPosX,"Y":receivedPosY,"Z":0}
         #print (player['position'])


         GameState['players'].append(player)
      s=json.dumps(GameState,separators=(",", ":"))
      #print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      if (len(clients)>0):
         pktID = pktID +1
      time.sleep(1/60)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
