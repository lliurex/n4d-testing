import os
import os.path
import threading
import shutil
import pwd
import random
import string
import time
import glob
import pyinotify
from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent

import n4d.server.core


class TicketsManager:
	
	WATCH_DIR="/run/n4d/tickets/"
	ALIVE_TIME=60*30
	SLEEP_TIME=3
	DEBUG=True
	
	def __init__(self):
		
		self.core=n4d.server.core.Core.get_core()
		
		self.tickets={}
		self.validation_errors={}
		
		if not os.path.exists(TicketsManager.WATCH_DIR):
			os.makedirs(TicketsManager.WATCH_DIR)
		
		self.read_old_tickets()
		
		self.start_inotify()
		
	#def init
	
	def dprint(self,data):
		
		self.core.pprint("TicketsManager","%s"%str(data))
		
	#def dprint
	
	def __inotify(self):
		
		
		wm=WatchManager()
		mask=pyinotify.IN_CLOSE_WRITE
			
		class Process_handler(ProcessEvent):
				
			def __init__(self,main):
				
				self.main=main
				
			def process_IN_CLOSE_WRITE(self,event):

				for user in pwd.getpwall():
					if user.pw_name == event.name:
						f=open(event.path+"/"+event.name)
						ticket=f.readlines()[0]
						f.close()
						self.main.tickets[user.pw_name]={}
						self.main.tickets[user.pw_name]["password"]=ticket
						self.main.tickets[user.pw_name]["date"]=time.time()
						break
				
				#self.generate_pam()
				
	
		notifier=Notifier(wm,Process_handler(self))
		wdd=wm.add_watch(TicketsManager.WATCH_DIR,mask,rec=True)
			
		while True:
			try:
					
				notifier.process_events()
				if notifier.check_events():
					notifier.read_events()
				
			except Exception as e:
				print(e)
				notifier.stop()
					
		return False
	
	#def _inotify	
	
	def start_inotify(self):

		t=threading.Thread(target=self.__inotify)
		t.daemon=True
		t.start()

	#def start_inotify
	
	def set_ticket(self,user,password):

		t=time.time()
		
		f=open(TicketsManager.WATCH_DIR+user,"w")
		if password==None:
			password ="".join(random.sample(string.ascii_letters+string.digits, 50))
		f.write(password)
		f.close()
		self.set_perms(user)
		self.tickets[user]={}
		self.tickets[user]["password"]=password
		self.tickets[user]["date"]=t
		
		return True

	#def set_ticket
	
	def create_ticket(self,user):
		
		t=time.time()
		
		ticket_file=TicketsManager.WATCH_DIR + user
		if os.path.exists(ticket_file):
			f=open(ticket_file)
			ticket=f.readline()
			f.close()		
			if user in self.tickets:
				if self.tickets[user]["password"]==ticket:
					return True
		
		f=open(TicketsManager.WATCH_DIR+user,"w")
		
		password ="".join(random.sample(string.ascii_letters+string.digits, 50))
		f.write(password)
		f.close()

		self.set_perms(user)
		self.tickets[user]={}
		self.tickets[user]["password"]=password
		self.tickets[user]["date"]=t

		return True
		
	#def create_ticket
	
	def get_ticket(self,user):
		
		ticket=TicketsManager.WATCH_DIR+user
		
		if not os.path.exists(ticket):
			self.create_ticket(user)
			
		return self.tickets[user]["password"]
		
	#def get_ticket

	
	def read_old_tickets(self):
		
		for item in glob.glob(TicketsManager.WATCH_DIR+"*"):
			try:
				user=item.split("/")[-1]
				f=open(item)
				password=f.readline()
				f.close()
				self.tickets[user]={}
				self.tickets[user]["password"]=password
				self.tickets[user]["date"]=time.time()
			except:
				pass
		#self.dprint(self.tickets)
		
	#def read_old_tickets

	def set_perms(self,user):
		
		prevmask = os.umask(0)
		uid=pwd.getpwnam(user).pw_uid
		path=TicketsManager.WATCH_DIR+user
		os.chown(path,uid,0)
		os.chmod(path,0o460)
		os.umask(prevmask)
		
	#def set_perms
	
	def validate_user(self,user,password):
		
		if user in self.tickets:
			if self.tickets[user]["password"]==password:
				self.validation_errors[user]=0
				return True
			else:
				if user not in self.validation_errors:
					self.validation_errors[user]=0
				self.validation_errors[user]+=1
				time.sleep(self.validation_errors[user]*TicketsManager.SLEEP_TIME)
		
		return False
		
	#def validate_password
	
	
	
#class TicketsManager