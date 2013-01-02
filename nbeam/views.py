import os
import shutil
import codecs
import string
import hashlib
import mimetypes

mimetypes.init()
text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
_null_trans = string.maketrans("", "")

def hashstr (value):
  value = '::NeutronBeam::' + value
  return hashlib.sha256(value).hexdigest()
  
def istext (s):
  if "\0" in s:
    return 0

  if not s:  # Empty files are considered text
    return 1

  # Get the non-text characters (maps a character to itself then
  # use the 'remove' option to get rid of the text characters.)
  t = s.translate(_null_trans, text_characters)

  # If more than 30% non-text characters, then
  # this is considered a binary file
  if len(t)/len(s) > 0.30:
    return 0
    
  return 1
  
def mimetype (fp):
  mt, enc = mimetypes.guess_type(fp)
  if mt is None:
    mt = 'application/octet-stream'
    
  return mt
  
def delete (config, rdata):
  fp = config['dir'] + rdata['file']
  if os.path.isdir(fp):
    shutil.rmtree(path)
    
  else:
    os.remove(fp)
    
  return {'status': 'ok', 'fid': rdata['fid']}
  
def rename_file (config, rdata):
  fp = config['dir'] + rdata['file']
  fid = hashstr(config['key'] + rdata['file'])
  
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
  return {'file': f, 'read_only': False}
  
def list_dir (config, rdata):
  show_hidden = False
  r = ['<ul class="jqueryFileTree" style="display: none;">']
  d = config['dir'] + rdata['dir']
  fdlist = os.listdir(d)
  fdlist.sort()
  
  files = []
  dirs = []
  
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
        e = os.path.splitext(f)[1][1:] # get .ext and remove dot
        files.append((e,rf,f))
        
  for d in dirs:
    did = hashstr(config['key'] + d[0])
    r.append('<li class="directory collapsed" id="dir_%s" title="%s/"><a href="#" onclick="hide_right_menu()" data-beam="%s" rel="%s/">%s</a></li>' % (did, d[0], rdata['beam'], d[0], d[1]))
    
  for f in files:
    fid = hashstr(config['key'] + f[1])
    r.append(
      '<li class="file ext_%s" title="%s"><a href="#" data-title="%s" rel="%s" data-beam="%s" data-rel="%s" onclick="hide_right_menu()" oncontextmenu="return beam_right_menu(event, \'file\', \'%s\')">%s</a></li>' % 
      (f[0], f[1], f[2], fid, rdata['beam'], f[1], fid, f[2])
    )
    
  r.append('</ul>')
  return ''.join(r)
  