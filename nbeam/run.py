import os
import sys
import time
import json
import errno
import base64
import signal
import random
import hashlib
import logging
import argparse
from multiprocessing import Process

import tornado.autoreload
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.options import options, enable_pretty_logging

from .version import VERSION_STRING

try:
  import daemon
  
except:
  pass

from .handlers import MainHandler

def started (*args):
  root_logger = logging.getLogger()
  root_logger.setLevel(logging.INFO)
  
  logging.info('Neutron Beam Started')
  
def run_server (config):
  options.logging = 'debug'
  
  if config['daemon']:
    options.log_file_prefix = config['log']
    
  enable_pretty_logging(options=options)
  
  app = Application([(r"/", MainHandler)])
  app.config = config
  app.listen(config['port'])
  if config['reload']:
    tornado.autoreload.start()
    
  fh = open(config['pid'], 'w')
  fh.write('%d' % os.getpid())
  fh.close()
  
  def stopme (s, f):
    loop.stop()
    logging.info('Neutron Beam Stopped')
    
  loop = IOLoop.instance()
  signal.signal(signal.SIGTERM, stopme)
  
  loop.add_callback(started)
  loop.start()
  
def default_config ():
  return {
    'daemon': True,
    'port': 32811,
    'key': '',
    'email': '',
    'dir': '',
  }
  
def generate_key ():
  return base64.b64encode(
    hashlib.sha256( str(random.getrandbits(256)) ).digest(),
    random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])
  ).rstrip('==')
  
def send_kill (pid):
  while is_running(pid):
    os.kill(pid, signal.SIGTERM)
    time.sleep(1)
    
def is_running (pid):
  try:
    os.kill(pid, 0)
    
  except OSError, err:
    if err.errno == errno.ESRCH:
      return False
      
    else:
      raise
    
  else:
    return True
    
def commander ():
  config_default = os.path.join('.config', 'nbeam')
  if os.environ.has_key('HOME'):
    config_default = os.path.join(os.environ['HOME'], '.config', 'nbeam')
    
  cmd_help = "start, stop, restart, status, config (print config), newkey (generate new key)"
  parser = argparse.ArgumentParser(description='Neutron Beam, client to access local files in Neutron Drive.')
  parser.add_argument('command', metavar='command', nargs=1, choices=('start', 'stop', 'restart', 'status', 'config', 'newkey'), help=cmd_help)
  parser.add_argument('-c', '--config', dest='config', default=config_default, help='Config directory path, default: ' + config_default)
  parser.add_argument('-p', '--port', dest='port', type=int, default=None, help='Network port to run client on. Default: 32811')
  parser.add_argument('-f', dest='foreground', action='store_true', default=False, help='Run in the foreground instead of a daemon.')
  parser.add_argument('-r', dest='reload', action='store_true', default=False, help='Reload on code changes. (For Debugging)')
  
  args = parser.parse_args()
  
  if not os.path.exists(args.config):
    os.makedirs(args.config)
    
  cpath = os.path.join(args.config, 'config.json')
  config = default_config()
  if os.path.exists(cpath):
    fh = open(cpath, 'r')
    d = json.load(fh)
    fh.close()
    config.update(d)
    
  if not config['email']:
    config['email'] = raw_input('E-Mail Address: ')
    
    fh = open(cpath, 'w')
    json.dump(config, fh, sort_keys=True, indent=2)
    fh.close()
    
  if not config['dir']:
    config['dir'] = raw_input('Enter your code directory: ')
    if not os.path.exists(config['dir']):
      os.makedirs(config['dir'])
      
  if not config['key'] or args.command[0] == 'newkey':
    config['key'] = generate_key()
    fh = open(cpath, 'w')
    json.dump(config, fh, sort_keys=True, indent=2)
    fh.close()
    
    print "Generated Key:", config['key']
    print "Client port:", config['port']
    
    if args.command[0] == 'newkey':
      return 0
      
  if args.foreground:
    config['daemon'] = False
    
  if args.port:
    config['port'] = args.port
    
  if args.reload:
    config['reload'] = True
    
  else:
    config['reload'] = False
    
  config['pid'] = os.path.join(args.config, 'nbeam.pid')
  config['log'] = os.path.join(args.config, 'nbeam.log')
  
  if args.command[0] == 'config':
    print 'Config Directory: %s' % args.config
    print 'Config File: %s' % cpath
    print json.dumps(config, sort_keys=True, indent=2)
    return 0
    
  if args.command[0] == 'status':
    fh = open(config['pid'], 'r')
    pid = int(fh.read())
    
    if is_running(pid):
      print 'Neutron Beam is running.'
      
    else:
      print 'Neutron Beam is not running.'
      
    return 0
    
  if args.command[0] in ('stop', 'restart'):
    print 'Stopping Neutron Beam ...'
    fh = open(config['pid'], 'r')
    pid = int(fh.read())
    send_kill(pid)
    print 'Neutron Beam Stopped'
    
  if args.command[0] in ('start', 'restart'):
    if not globals().has_key('daemon'):
      config['daemon'] = False
      
    if config['daemon']:
      print 'Neutron Beam Started V%s' % VERSION_STRING
      with daemon.DaemonContext():
        run_server(config)
      
    else:
      print 'Starting Neutron Beam V%s ...' % VERSION_STRING
      run_server(config)
      
