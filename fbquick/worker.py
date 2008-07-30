import wx
import threading
import Queue

class WorkerThread(threading.Thread):

  def __init__(self, work_function, callback=None, errback=None):
    threading.Thread.__init__(self)
    self.setDaemon(True)

    self.callback = callback
    self.errback = errback
    self.work_function = work_function
    self.work_queue = Queue.Queue()


  def run(self):
    while True:
      req = self.work_queue.get(True)
      try:
        resp = self.work_function(req)
        self.callback and wx.CallAfter(self.callback, resp)
      except Exception, e:
        self.errback and wx.CallAfter(self.errback, e)

  def addWork(self, work):
    self.work_queue.put_nowait(work)

