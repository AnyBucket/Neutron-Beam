
def start_search (config, rdata):
  job = config['Job']()
  job.jtype = 'search'
  job.email = rdata['email']
  job.set_data({
    'dir': rdata['dir'],
    'needle': rdata['needle'],
    'glob': rdata['glob'],
    'cs': rdata['cs'] == '1',
    'ww': rdata['ww'] == '1',
    're': rdata['re'] == '1',
  })
  
  job.save()
  
  config['q'].put(job.id)
  return {'status': 'ok', 'id': str(job.id)}
  
def start_replace (config, rdata):
  job = config['Job']()
  job.jtype = 'replace'
  job.email = rdata['email']
  job.set_data({
    'replace': rdata['replace'],
    'search': int(rdata['jid']),
  })
  job.save()
  
  config['q'].put(job.id)
  return {'status': 'ok', 'id': str(job.id)}
  
def job_status (config, rdata):
  Job = config['Job']
  j = Job.get(Job.id == int(rdata['jid']))
  
  return {'status': 'ok', 'id': str(j.id), 'status': j.status, 'data': j.get_data('out')}
  
def cancel_job (config, rdata):
  Job = config['Job']
  CancelJob = config['CancelJob']
  
  j = Job.get(Job.id == int(rdata['jid']))
  c = CancelJob(job=j, email=rdata['email'])
  c.save()
  
  return {'status': 'ok', 'jid': str(j.id), 'cid': str(c.id)}
  