import re

from .utils import istext

class Grep (object):
  def __init__ (self, filepath, needle):
    self.filepath = filepath
    self.needle = needle
    
  def replace (self, rstr, rlines):
    fh = open(self.filepath, 'rb')
    newlines = ''
    
    linenum = 0
    while 1:
      line = fh.readline()
      if line:
        if (linenum in rlines):
          newlines += bytearray(self.needle.sub(rstr, line), 'utf-8')
          
        else:
          newlines += bytearray(line)
          
        linenum += 1
        
      else:
        break
        
    fh.close()
    fh = open(self.filepath, 'wb')
    fh.write(newlines)
    fh.close()
    
  def results (self):
    ret = []
    fh = open(self.filepath, 'rb')
    if istext(fh.read(512)):
      fh.seek(0)
      linenum = 0
      while 1:
        line = fh.readline()
        if line:
          for match in self.needle.finditer(line):
            ret.append({
              'line': linenum,
              'start': match.start(),
              'end': match.end()
            })
            
          linenum += 1
          
        else:
          break
          
    fh.close()
    
    return ret
    