import os
import base64
import json

from tornado.web import RequestHandler
from tornado.escape import json_encode, json_decode

from .SimpleAES import SimpleAES
from .views  import list_dir, open_file, save_file

class MainHandler (RequestHandler):
  def __init__ (self, *args, **kwargs):
    self.config = args[0].config
    self.aes = SimpleAES(args[0].config['key'])
    self.ALLOWED_TASKS = ('list', 'open', 'save')
    super(MainHandler, self).__init__(*args, **kwargs)
    
  def valid_request (self, rdata):
    if rdata['task'] in self.ALLOWED_TASKS:
      if rdata['email'].lower() == self.config['email'].lower():
        if 'file' in rdata:
          path = rdata['file']
          
        else:
          path = rdata['dir']
          
        path = os.path.normpath(self.config['dir'] + path)
        if path.startswith(self.config['dir']):
          return True
          
    return False
    
  def post (self):
    data = {'status': 'Invalid Request'}
    self.set_header('Content-Type', 'application/json')
    self.set_header('Access-Control-Allow-Origin', '*')
    
    rdata = self.get_argument("request", '')
    try:
      test = base64.decodestring(rdata)
      rdata = self.aes.decrypt(rdata)
      rdata = json_decode(rdata)
      
    except:
      pass
    
    else:
      if self.valid_request(rdata):
        if rdata['task'] == 'list':
          response_data = list_dir(self.config, rdata)
          
        elif rdata['task'] == 'open':
          response_data = open_file(self.config, rdata)
          
        elif rdata['task'] == 'save':
          response_data = save_file(self.config, rdata)
          
        data = {
          'response': response_data,
          'email': self.config['email'],
        }
        
        j = json_encode(data)
        data = {
          'encrypted': self.aes.encrypt(j),
          'beam': rdata['beam'],
          'status': 'ok'
        }
        
    j = json_encode(data)
    self.write(j)
    self.finish()
    