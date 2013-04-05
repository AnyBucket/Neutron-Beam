import os
import json
import datetime

import peewee

JOB_TYPES = (
  ('search', 'Search'),
  ('replace', 'Replace'),
)

STATUS_TYPES = (
  ('created', 'Created'),
  ('running', 'Running'),
  ('finished', 'Finished'),
  ('cancelled', 'Cancelled'),
  ('failed', 'Failed'),
)

def initialize_db (db_path):
  DB = peewee.SqliteDatabase(db_path)
  DB.connect()
  
  class File (peewee.Model):
    path = peewee.CharField(max_length=1024)
    realtime_id = peewee.CharField(max_length=255, null=True, default=None)
    
    def __unicode__ (self):
      return os.path.basename(self.path)
      
    class Meta:
      database = DB
      
  class Job (peewee.Model):
    jtype = peewee.CharField(max_length=25, choices=JOB_TYPES)
    email = peewee.CharField(max_length=255)
    status = peewee.CharField(max_length=25, choices=STATUS_TYPES, default='created')
    indata = peewee.TextField(null=True, default=None)
    outdata = peewee.TextField(null=True, default=None)
    
    created = peewee.DateTimeField(default=datetime.datetime.now)
    completed = peewee.DateTimeField(null=True, default=None)
    
    def set_data (self, obj, attr='in'):
      if attr == 'out':
        self.outdata = json.dumps(obj, sort_keys=True, indent=2)
        
      else:
        self.indata = json.dumps(obj, sort_keys=True, indent=2)
        
    def get_data (self, attr='in'):
      if attr == 'out':
        if self.outdata:
          return json.loads(self.outdata)
          
      else:
        if self.indata:
          return json.loads(self.indata)
          
      return None
      
    def __unicode__ (self):
      return '%d - %s - %s' % (self.id, self.jtype, self.created.strftime('%Y-%m-%d %H:%M:%S'))
      
    class Meta:
      database = DB
      
  class CancelJob (peewee.Model):
    job = peewee.ForeignKeyField(Job, related_name='cancels')
    email = peewee.CharField(max_length=255)
    created = peewee.DateTimeField(default=datetime.datetime.now)
    
    class Meta:
      database = DB
      
  Job.create_table(True)
  CancelJob.create_table(True)
  File.create_table(True)
  
  return {
    'db': DB,
    'JobModel': Job,
    'CancelModel': CancelJob,
    'File': File,
  }
  