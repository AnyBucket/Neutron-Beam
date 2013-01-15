import re
import os
import time
import glob

from .utils import istext, hashstr, mimetype
from .grep import Grep

def make_needle (opts):
  needle = ''
  flags = re.I
  
  if opts['cs']:
    flags = 0
    
  if opts['re']:
    if opts['ww']:
      needle = re.compile(r"\b" + opts['needle'] + r"\b", flags=flags)
      
    else:
      needle = re.compile(opts['needle'], flags=flags)
      
  else:
    if opts['ww']:
      needle = re.compile(r"\b" + re.escape(opts['needle'] + r"\b"), flags=flags)
      
    else:
      needle = re.compile(re.escape(opts['needle']), flags=flags)
      
  return needle

def do_replace (config, job):
  job.status = 'running'
  job.save()
  replace_opts = job.get_data()
  
  search_job = config['Job'].get(config['Job'].id == replace_opts['search'])
  search_opts = search_job.get_data()
  search_results = search_job.get_data('out')
  needle = make_needle(search_opts)
  
  files_replaced = []
  for r in search_results:
    if job.cancels.count() > 0:
      job.status = 'cancelled'
      job.save()
      print 'Job Cancelled: %d' % job.id
      return 0
      
    fp = config['dir'] + r['rel']
    rlines = [x['line'] for x in r['ranges']]
    grep = Grep(fp, needle)
    grep.replace(replace_opts['replace'], rlines)
    files_replaced.append(r['name'])
    job.set_data(files_replaced, 'out')
    job.save()
    
def do_search (config, job):
  job.status = 'running'
  job.save()
  opts = job.get_data()
  
  needle = make_needle(opts)
  results = []
  
  for root, dirs, files in os.walk(config['dir'] + opts['dir']):
    if opts['glob']:
      files = glob.glob(root + '/' + opts['glob'])
      
    if files:
      for file in files:
        if job.cancels.count() > 0:
          job.status = 'cancelled'
          job.save()
          print 'Job Cancelled: %d' % job.id
          return 0
          
        fp = os.path.join(root, file)
        rel = fp.replace(config['dir'], '')
        uid = hashstr(config['key'] + rel)
        
        if opts['needle']:
          grep = Grep(fp, needle)
          grep_results = grep.results()
          if grep_results:
            results.append({
              'name': os.path.basename(rel),
              'rel': rel,
              'fid': uid,
              'ranges': grep_results,
            })
            
        else:
          results.append({
            'name': os.path.basename(rel),
            'rel': rel,
            'fid': uid,
            'ranges': [],
          })
          
      job.set_data(results, 'out')
      job.save()
      