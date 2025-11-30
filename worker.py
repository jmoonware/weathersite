import logging
import threading
import time
import sys,traceback

class Worker:
	def __init__(self,settings=None):
		self.done=False
		self.exception=None
		self.exception_count=0
		self.timeout=5
		self.blocking=True
		self.sync=None # supply a threading lock if needed
		self.loop_count=1 # default is one-shot
		self.loop_interval=1 # s
		self._thread=None
		if settings:
			for k in settings:
				self.__dict__[k]=settings[k]
		self.logger=logging.getLogger(__name__)
		self.settings=settings
		try:
			self.Init() 
		except Exception as ex:
			self._exception_handler(ex,"In Init():")
	def Init(self):
		self.logger.debug("{0} Generic init".format(self))
	def __str__(self):
		return(self.Prefix()+",TO={0},BK={1},LC={2},LI={3})".format(self.timeout,self.blocking,self.loop_count,self.loop_interval))
	def Prefix(self):
		n=self.__repr__()
		name=n.split('.')[-1].split(' ')[0]
		addr=n.split('.')[-1].split(' ')[-1].split('>')[0]
		return("{0}[{1}](DN={2},EC={3}".format(name,addr,self.done,self.exception_count))
	def _exception_handler(self,ex,msg):
		self.done=True 
		self.logger=logging.getLogger(__name__)
		self.logger.error("{0} {1} {2}".format(self,msg,ex))
		exc_type, exc_value, exc_traceback = sys.exc_info()
		self.logger.debug(traceback.format_tb(exc_traceback))
		self.exception=ex
		self.exception_count+=1
#		raise
	def Run(self):
		try:
			if self.Status():
				self.logger.warning("{0} attempting restart".format(self))
				self.Stop()
			if self.loop_count<0 and self.blocking==True:
				self.logger.warning("Negative loop_count can't block")
				self.loop_count=0
			if self.loop_count==0: 
				raise RuntimeError("loop_count=0: nothing to do")
			self._thread=threading.Thread(target=self._loop)
			self._thread.daemon=True
			self.done=False
			self.exception=None
			self._thread.start()
			if self.blocking:
				self._thread.join(self.timeout)
				if self.Status():
					self.logger.warning("{0} blocking join() timeout".format(self))
		except Exception as ex:
			self._exception_handler(ex,"In Run():")
	def Status(self):
		ret=None
		if self._thread!=None:
			ret=self._thread.is_alive()
		return ret
	def Stop(self):
		self.done=True
		if self.Status():
			self._thread.join(self.timeout)
			if self.Status():
				self.logger.error("{0} timeout during join()".format(self))
		else:
			self.logger.debug("{0} no need to stop this command".format(self))
	def _loop(self):
		try:
			self.Enter()
			while not self.done and self.loop_count!=0:
				if self.sync:
					with self.sync: # get lock
						self.Execute()
				else:
					self.Execute()
				# if < 0, reset to -1 forever looping until done
				self.loop_count=max(-1,self.loop_count-1)
				time.sleep(self.loop_interval)
			self.Exit()
		except Exception as ex:
			self._exception_handler(ex,"In _loop:")
	def Execute(self): # override this function for Run()
		self.logger.debug("{0} Execute() is blank".format(self))
	def Enter(self): # override for one-time first things in Run()
		self.logger.debug("{0} Generic Enter".format(self))
		return
	def Exit(self): # override for one-time last things in Run()
		self.logger.debug("{0} Generic Exit".format(self))
		return

