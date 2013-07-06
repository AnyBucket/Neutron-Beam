import os
import shutil
import codecs
import base64
import urllib
import datetime
import hashlib
import random

from .utils import istext, hashstr, mimetype

TOKENS = {}

def token_valid (token):
  now = datetime.datetime.now()
  for t in TOKENS.keys():
    if TOKENS[t]['expires'] < now:
      del TOKENS[t]
      
  if token in TOKENS:
    return True
    
  return False
  
def token (config, rdata):
  token = base64.b64encode(
    hashlib.sha256( str(random.getrandbits(256)) ).digest(),
    random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])
  ).rstrip('==')
  token = token[:12]
  
  TOKENS[token] = {
    'ip': rdata['ip'],
    'expires': datetime.datetime.now() + datetime.timedelta(minutes=config['view_timeout'])
  }
  return {'status': 'ok', 'token': token}

def upload_file (config, rdata):
  fp = os.path.join(config['dir'] + rdata['dir'], rdata['name'])
  fp = os.path.normpath(fp)
  if fp.startswith(config['dir']):
    if os.path.exists(fp):
      raise Exception("File Already Exists")
      
    fh = open(fp, 'wb')
    fh.write(base64.decodestring(rdata['content']))
    fh.close()
    
    return {'status': 'ok', 'fid': rdata['fid']}
    
  raise Exception("Invalid File Path")
  
def new_dir (config, rdata):
  return new_file(config, rdata, d=True)
  
def new_url (config, rdata):
  return new_file(config, rdata)
  
def new_file (config, rdata, d=False):
  new_rel = os.path.join(rdata['dir'], rdata['name'])
  parent = config['dir'] + rdata['dir']
  fp = os.path.join(parent, rdata['name'])
  
  fp = os.path.normpath(fp)
  if fp.startswith(config['dir']):
    if os.path.exists(fp):
      if d:
        raise Exception("Directory Already Exists")
        
      else:
        raise Exception("File Already Exists")
        
    if d:
      os.mkdir(fp)
      
    else:
      if 'url' in rdata:
        urllib.urlretrieve(rdata['url'], fp)
        
      else:
        fh = open(fp, 'w')
        fh.close()
        
    if rdata['dir'] == '/':
      pid = rdata['beam']
      
    else:
      pid = '#dir_' + hashstr(config['key'] + rdata['dir'][:-1])
      
    return {'status': 'ok', 'fid': hashstr(config['key'] + new_rel), 'rel': new_rel, 'pid': pid}
    
  raise Exception("Invalid File Path")
  
def delete (config, rdata):
  fp = config['dir'] + rdata['file']
  if os.path.isdir(fp):
    shutil.rmtree(fp)
    
  else:
    os.remove(fp)
    
  return {'status': 'ok', 'fid': rdata['fid']}
  
def rename_file (config, rdata):
  fp = config['dir'] + rdata['file']
  fid = hashstr(config['key'] + rdata['file'])
  
  if os.path.isdir(fp):
    parent = os.path.dirname(rdata['file'][:-1])
    
  else:
    parent = os.path.dirname(rdata['file'])
    
  new_rel_path = os.path.join(parent, rdata['name'])
  new_path = config['dir'] + new_rel_path
  os.rename(fp, new_path)
  
  if parent == '/':
    parents = [rdata['beam']]
    
  else:
    parents = ['#dir_' + hashstr(config['key'] + parent)]
    
  new_id = hashstr(config['key'] + new_rel_path)
  ext = os.path.splitext(new_rel_path)[1]
  if ext and ext.startswith('.'):
    ext = ext[1:]
    
  return {'status': 'ok', 'file_id': fid, 'new_id': new_id, 'rel': new_rel_path, 'parents': parents, 'name': rdata['name'], 'ext': ext}
  
def create_realtime (config, rdata):
  fp = config['dir'] + rdata['file']
  File = config['File']
  try:
    file_data = File.get(File.path == rdata['file'])
    
  except File.DoesNotExist:
    file_data = File()
    file_data.path = rdata['file']
    
  finally:
    file_data.realtime_id = rdata['realtime_id']
    file_data.save()
    
  fid = hashstr(config['key'] + rdata['file'])
  return {'status': 'ok', 'file': rdata['file'], 'fid': fid}
  
def stop_realtime (config, rdata):
  fp = config['dir'] + rdata['file']
  File = config['File']
  try:
    file_data = File.get(File.path == rdata['file'])
    
  except File.DoesNotExist:
    pass
  
  else:
    file_data.delete_instance()
    
  fid = hashstr(config['key'] + rdata['file'])
  return {'status': 'ok', 'file': rdata['file'], 'fid': fid}

def save_file (config, rdata):
  fp = config['dir'] + rdata['file']
  fid = hashstr(config['key'] + rdata['file'])
  
  try:
    fh = codecs.open(fp, encoding='utf-8', mode='w')
    fh.write(rdata['content'])
    
  except:
    encoding = chardet.detect(rdata['content'])['encoding']
    fh = codecs.open(fp, encoding=encoding, mode='w')
    fh.write(rdata['content'])
    
  finally:
    fh.close()
    
  return {'status': 'ok', 'file': rdata['file'], 'md5hash': rdata['md5hash'], 'fid': fid}
  
def open_file (config, rdata):
  fp = config['dir'] + rdata['file']
  fid = hashstr(config['key'] + rdata['file'])
  
  fh = open(fp, 'rb')
  if istext(fh.read(512)):
    fh.seek(0)
    
    ext = os.path.splitext(fp)[1]
    if ext and ext.startswith('.'):
      ext = ext[1:]
      
    f = {
      'fileType': 'text',
      'content': fh.read(),
      'id': fid,
      'title': os.path.basename(fp),
      'mimeType': mimetype(fp),
      'fileExtension': ext,
      'rel': rdata['file']
    }
    
  else:
    f = {'fileType': 'binary', 'content': '', 'id': fid}
    
  fh.close()
  File = config['File']
  try:
    file_data = File.get(File.path == rdata['file'])
    
  except File.DoesNotExist:
    f['realtime_id'] = None
    
  else:
    f['realtime_id'] = file_data.realtime_id
    
  return {'file': f, 'read_only': False}
  
def list_dir (config, rdata):
  show_hidden = rdata['show_hidden']
  r = ['<ul class="jqueryFileTree" style="display: none;">']
  d = config['dir'] + rdata['dir']
  fdlist = os.listdir(d)
  fdlist.sort()
  
  files = []
  dirs = []
  
  if 'dirOnly' not in rdata:
    rdata['dirOnly'] = '0'
    
  for f in fdlist:
    go = False
    if f.startswith('.'):
      if show_hidden:
        go = True
        
    else:
      go = True
      
    if go:
      ff = os.path.join(d,f)
      rf = os.path.join(rdata['dir'],f)
      
      if os.path.isdir(ff):
        dirs.append((rf,f))
        
      else:
        if rdata['dirOnly'] != '1':
          e = os.path.splitext(f)[1][1:] # get .ext and remove dot
          files.append((e,rf,f))
          
  for d in dirs:
    did = hashstr(config['key'] + d[0], 'dir')
    if rdata['dirOnly'] == '1':
      r.append(
        '<li class="directory collapsed" title="%s/"><a href="#" rel="%s" data-beam="%s" data-title="%s" data-rel="%s/" onclick="set_sdir_footer(\'%s\')">%s</a></li>' % 
        (d[0], did, rdata['beam'], d[1], d[0], did, d[1])
      )
      
    else:
      r.append(
        '<li class="directory collapsed" id="dir_%s" title="%s/"><a href="#" rel="%s" data-beam="%s" data-title="%s" data-rel="%s/" onclick="hide_right_menu()" oncontextmenu="return beam_right_menu(event, \'dir\', \'%s\')">%s</a></li>' % 
        (did[:-1], d[0], did, rdata['beam'], d[1], d[0], did, d[1])
      )
      
  for f in files:
    fid = hashstr(config['key'] + f[1])
    r.append(
      '<li class="file ext_%s" title="%s"><a href="#" data-title="%s" rel="%s" data-beam="%s" data-rel="%s" onclick="hide_right_menu()" oncontextmenu="return beam_right_menu(event, \'file\', \'%s\')">%s</a></li>' % 
      (f[0], f[1], f[2], fid, rdata['beam'], f[1], fid, f[2])
    )
    
  r.append('</ul>')
  return ''.join(r)
  
