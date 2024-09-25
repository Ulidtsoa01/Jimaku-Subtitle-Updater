from preset import *

def apply(confField):
  if confField in CONF and (CONF[confField] or CONF[confField] is 0):
    return True
  return False

def log(line):
  if CONF['strict']:
    with open("upload.log", 'a', encoding="utf-8") as f:
      f.write(f"{line}\n")
      f.close()
  
  print(line)