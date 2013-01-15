import os
import time
import datetime
import multiprocessing
import Queue
import traceback

from .models import initialize_db
from .tasks import do_search, do_replace

TYPE_MAP = {
  'search': do_search,
  'replace': do_replace,
}

class Worker (multiprocessing.Process):
  def __init__ (self, queue, logging, config):
    self._stop = False
    self.logging = logging
    self.queue = queue
    self.config = config
    
    super(Worker, self).__init__()
    
  def run_job (self, jid):
    job = self.Job.get(self.Job.id == jid)
    try:
      TYPE_MAP[job.jtype](self.config, job)
      
    except:
      job.status = 'failed'
      traceback.print_exc()
      
    else:
      if job.status != 'cancelled':
        job.status = 'finished'
        
    finally:
      job.completed = datetime.datetime.now()
      job.save()
      
  def run (self):
    self.logging.info('Starting Worker Process')
    dbObj = initialize_db(self.config['db'])
    self.Job = dbObj['JobModel']
    
    while 1:
      try:
        job_id = self.queue.get(True, 5)
        
      except Queue.Empty:
        pass
      
      else:
        self.run_job(job_id)
        
      if self._stop:
        return 0
        
  def terminate (self):
    self.logging.info('Stopping Worker Process')
    self._stop = True
    time.sleep(2)
    super(Worker, self).terminate()
    