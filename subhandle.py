import os
import os.path
import subprocess
import json
import re
import time
import sys
import ass
import argparse


############ CONFIG ############

PRESET = {
  '[Nekomoe kissaten&LoliHouse] Monogatari Series - Off & Monster Season': {
    'fsize': 80,
    'vertical': 54
  },
  '[Kitauji] Shikanoko': {
    'fsize': 0,
    'vertical': 0,
    'strip_line': ["^8.*$"]
  },
  'example': {
    'fsize': None,
    'fname': 'aaaa',
    'vertical': None,
    'vertical_top': None,
    'outline': None,
    'strip_line': ["^0.*$", "^8.*$"],
    'extract': True,
    'mode': 'CN',
    'upload': False,
  },
  '[dellater]': {
    'fsize': -600,
    'vertical': 999999,
    'vertical_top': -1000000,
    'strip_line': ["^0.*$", "^8.*$"],
    'extract': False,
    'mode': 'CN',
    'upload': False,
  }
}
STRIP_STYLES = ["cn", "ch", "zh", "sign", "staff", "credit", "note", "screen", "title", "comment", "ruby", "scr", "cmt", "info"]
JIMAKU_API_KEY = ''

############ DEFAULTS ############
CONF = {
  'extract': True,
  'mode': 'CN',
  'linebreak': False,
  'upload': False
}

############ Shared ############


EXTRACTED = []

def apply(confField):
  if confField in CONF and CONF[confField]:
    return True
  return False

parser = argparse.ArgumentParser()
parser.add_argument('file')
parser.add_argument('-p', '--preset')      
args = parser.parse_args()
# if len(sys.argv) > 1:
#   DIRNAME = os.path.normpath(sys.argv[1])
# else:
#   DIRNAME = os.path.dirname(os.path.realpath(__file__))
DIRNAME = args.file
os.chdir(DIRNAME)

def setConf(presetname):
  for p in PRESET.keys():
    if p == presetname:
      for setting in PRESET[p].keys():
        CONF[setting] = PRESET[p][setting]
      return True
  return False

############ CN ############

def cn_file_rename(sub):
  if "[CHS_JP&CHT_JP]" in sub.upper():
    sub = sub.replace("[CHS_JP&CHT_JP]", "")
  if " CHS&CHT]" in sub.upper():
    sub = sub.replace(" CHS&CHT]", "]")

  sub = sub.replace("[CHS, JPN]", "")
  sub = sub.replace(".ass", "")
  sub+="[CHS, JPN].ass"
  return sub

def cn_update_styles(styles):
  def matching(x):
    match = ["dial", "text", "bottom"] #need to match to apply style options
    matchTop = ["2", "top"] #need to match to apply vertical positioning
    for m in match:
      if m in x:
        for mt in matchTop:
          if mt in x:
            return "top"
        return True
       
    return False


  for s in styles:
    match = matching(s.name.lower())
    if match:
      if apply('fsize'): s.fontsize = CONF['fsize']
      if apply('fname'): s.fontname = CONF['fname']
      if apply('outline'): s.outline = CONF['outline']
      if match == "top":
        if apply('vertical_top'): s.margin_v = CONF['vertical_top']
      else:
        if apply('vertical'): s.margin_v = CONF['vertical']

  return styles

def cn_doc_clean(doc):
  # strip styles and lines
  def in_STRIP_STYLES(x):
    x = x.lower()
    for str in STRIP_STYLES:
      if str in x: return True
    return False

  keepStyles = []
  removeStyles = []
  for i in range(len(doc.styles)):
    name = doc.styles[i].name
    if in_STRIP_STYLES(name): 
      removeStyles.append(name)
    else: 
      keepStyles.append(name)

  doc.styles = list(filter(lambda x: x.name in keepStyles, doc.styles))
  doc.styles = cn_update_styles(doc.styles)

  def filterEvents(x):
    a = x.style not in removeStyles
    b = True
    if apply("strip_line"):
      for i in CONF["strip_line"]:
        if re.fullmatch(i, x.dump()):
          b = False
          break
    
    return True if a and b else False
    
  doc.events = list(filter(filterEvents, doc.events))

  return doc

def parse_subset(lines):
  for line in lines:
    print(line)
    if(re.fullmatch("[V4\+? Styles]", line)):
      print("TRUE")
      break

def cn_clean():
  # file renaming
  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  for sub in EXTRACTED:
    old = sub
    sub = cn_file_rename(sub)
    if sub != old:
      if sub in extracted_subs:
        os.remove(sub)
        print(f"Replace dual file of same name: {sub}")
      os.rename(old, sub)
  

  # handle new file
  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  for sub in extracted_subs:
    print(f"Working on: {sub}")
    # if "[JPN]" in sub:
    #   continue

    with open(sub, 'r', encoding='utf-8-sig') as f:
      doc = ass.parse(f)
      lines = f.readlines()
      subsets = parse_subset(lines)
      doc = cn_doc_clean(doc)
    
    sub = sub.replace("[CHS, JPN]", "[JPN]")
    if sub in extracted_subs:
      os.remove(sub)
      print(f"Replace [JPN] file of same name: {sub}")

    with open(sub, "x" , encoding='utf_8_sig') as f:
      doc.dump_file(f)


def cn_extract_subs(mkv):
  
  mkv_json = json.loads(subprocess.check_output([
    'ffprobe',
    "-v",
    "quiet",
    "-print_format",
    "json",
    "-show_streams",
    "-select_streams",
    "s",
    mkv
  ])) # ffprobe -v quiet -print_format json -show_streams -select_streams s input.mkv

  if not mkv_json.get("streams"):
    raise Exception("No subtitle streams to extract? Can't do any syncing. {}".format(mkv))
  index = []
  codec_name = []
  num_extracted = 0

  def matching(x):
    match = ["cht", "tc", "繁"] #skip these tracks
    for m in match:
      if m in x:
        return True
       
    return False

  for s in mkv_json["streams"]:
    title = s["tags"]["title"]
    if num_extracted == 0 and not matching(title.lower()):
      index.append(s["index"]) 
      codec_name.append(s["codec_name"])
      num_extracted += 1


  # filename = mkv.replace(".mkv", "[CHS, JPN]")
  filename = mkv.replace(".mkv", "")
  commands = ['mkvextract', DIRNAME+'\\'+mkv, "tracks"]
  for i in range(len(index)):
    EXTRACTED.append(f"{filename}.{codec_name[i]}")
    commands.append(f"{index[i]}:{filename}.{codec_name[i]}")

  subprocess.run(commands) # mkvextract "C:\Coding\input.mkv" tracks 2:name.ass 3:name.srt


############ TS ############

def ts_regexOps(lines):
    res = []
    x = None
    y = None
    for line in lines:
      if line.startswith("Style: Default"):
        line = "Style: Default,A-OTF Maru Folk Pro B,42,&H00FFFFFF,&H000000FF,&H00000000,&H7F000000,-1,0,0,0,100,100,0,0,1,2,2,1,0,0,0,1\n"
      res.append(line)
      if not x:
        x = re.search('PlayResX: (\d{1,4})', line)
      if not y:
        y = re.search('PlayResY: (\d{1,4})', line)
        if x and y:
          res.append(f"LayoutResX: {x.group(1)}\n")
          res.append(f"LayoutResY: {y.group(1)}\n")

    return res

def ts_fix_styling():
  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  for sub in extracted_subs:
    with open(sub, 'r', encoding="utf-8") as f:
      lines = f.readlines()
    lines = ts_regexOps(lines)
    with open(sub, 'w', encoding="utf-8") as f:
      # f.write('\r\n'.join(lines))
      f.write(''.join(lines))

def ts_extract_subs(mkv):
  filename = mkv.replace(".mkv", "")

  subprocess.run([
    'mkvextract',
    DIRNAME+'\\'+mkv,
    "tracks",
    f"2:{filename}.ass",
    f"3:{filename}.srt"
  ]) # mkvextract "C:\Coding\input.mkv" tracks 2:name.ass 3:name.srt

############ MAIN ############

if __name__ == '__main__':
  parser.add_argument('filename')
  if args.preset:
    setConf(args.preset)
  else:
    setConf(os.path.basename(DIRNAME))

  mkvs = [f for f in os.listdir() if f.endswith(".mkv")]
  if len(mkvs) == 0:
    print(f"ERROR: mkv not found")
    input("press enter to exit...")
    exit(1)

  if CONF['extract']:
    for mkv in mkvs:
      if CONF['mode'] == 'CN':
        cn_extract_subs(mkv)
      elif CONF['mode'] == 'TS':
        ts_extract_subs(mkv)
  
  if CONF['mode'] == 'CN':
    cn_clean()
  elif CONF['mode'] == 'TS':
    ts_fix_styling()
    
  # fix_styling()
  print("\nSuccess!\n")
  time.sleep(10)


