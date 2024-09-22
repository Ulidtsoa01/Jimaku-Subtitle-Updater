import os
from pathlib import Path
import subprocess
import json
import re
import time
import sys
import ass
import argparse
import requests
from datetime import datetime
import asyncio
from preset import *

############ DEFAULTS ############

STRIP_STYLES = ["cn", "ch", "zh", "sign", "staff", "credit", "note", "screen", "title", "comment", "ruby", "furi" "scr", "cmt", "info", "next episode", "stf", "op_sc", "op_tc"]
TC_TRACK = ["cht", "tc", "繁"]
NORMAL_STYLE = ["dial", "text", "bottom", "down", "top", "up"]
TOP_STYLE = ["2", "top", "up"]
EXCLUDE_STYLE = ["op", "ed"]

CONF = {
  'extract': True,
  'mode': 'CN',
  'linefixes': True,
  'linebreak': False,
  'upload': False,
  'chinese': "CHS"
}

############ Shared ############

parser = argparse.ArgumentParser()
parser.add_argument('folder', nargs='?', default=os.getcwd())
parser.add_argument('-p', '--preset')  
parser.add_argument('-s', '--strict', action='store_true')    
args = parser.parse_args()
# pyfile_path = os.path.dirname(os.path.realpath(__file__))
DIRPATH = Path(args.folder)
DIRNAME = DIRPATH.resolve()
STRICT = args.strict
os.chdir(DIRNAME)
if args.strict and not Path("ignore.conf").is_file():
  print("ignore.conf not present")
  exit(0)

EXTRACTED_FILES = []
EXTRACTED_FILEPATHS = []

def apply(confField):
  if confField in CONF and (CONF[confField] or CONF[confField] is 0):
    return True
  return False

def setConf(presetname):
  global STRIP_STYLES, NORMAL_STYLE, EXCLUDE_STYLE

  for p in PRESET.keys():
    if p == presetname:
      for setting in PRESET[p].keys():
        CONF[setting] = PRESET[p][setting]
      log(f"PRESET FOUND: {p}")

      if apply("STRIP_STYLES"): STRIP_STYLES+=CONF["STRIP_STYLES"]
      if apply("NORMAL_STYLE"): NORMAL_STYLE+=CONF["NORMAL_STYLE"]
      if apply("EXCLUDE_STYLE"): EXCLUDE_STYLE+=CONF["EXCLUDE_STYLE"]

      return True
  return False

def log(line):
  if STRICT:
    with open("upload.log", 'a', encoding="utf-8") as f:
      f.write(f"{line}\n")
      f.close()
  
  print(line)

############ CN ############

#(CHT)|(CHS)|(TC)|(SC)|(JP)
#separators optional
#2-4 groups
def cn_file_rename(sub):
  tags = "((CH[TS])|([TS]C)|(JP))"
  tagstring1 = fr"(\[{tags}.?{tags}.?{tags}?.?{tags}?\])"
  tagstring2 = fr"( {tags}.?{tags}.?{tags}?.?{tags}?\])"
  tagstring3 = fr"(\.{tags}{tags}?)"
  reg1 = re.search(tagstring1, sub, re.IGNORECASE)
  reg2 = re.search(tagstring2, sub, re.IGNORECASE)
  reg3 = re.search(tagstring3, sub, re.IGNORECASE)
  if reg3:
    sub = sub.replace(reg3.group(1), "")
  elif reg2:
    sub = sub.replace(reg2.group(1), "]")
  elif reg1:
    sub = sub.replace(reg1.group(1), "")

  chinese = CONF["chinese"]
  if f"[{CONF['chinese']}, JPN]" not in sub and "[JPN]" not in sub:
    sub = sub.replace(".ass", "")
    sub+=fr"[{CONF['chinese']}, JPN].ass"
  return sub

def cn_update_styles(styles):
  def matching(x):
    # global EXCLUDE_STYLE, NORMAL_STYLE, TOP_STYLE
    for es in EXCLUDE_STYLE:
      if es in x:
        return False
    for ns in NORMAL_STYLE: #need to match to apply style options
      if ns in x:
        for ts in TOP_STYLE: #need to match to apply vertical positioning
          if ts in x:
            return "top"
        return True
    return False

  for s in styles:
    match = matching(s.name.lower())
    if match:
      if apply('fsize'): s.fontsize = CONF['fsize']
      if apply('fname'): s.fontname = CONF['fname']
      if apply('outline'): s.outline = CONF['outline']
      if apply('spacing'): s.spacing = CONF['spacing']
      if match == "top":
        if apply('vertical_top'): s.margin_v = CONF['vertical_top']
      else:
        if apply('vertical'): s.margin_v = CONF['vertical']

  return styles

def cn_doc_clean(doc, subsets):
  # strip styles
  def matching(x):
    x = x.lower()
    for str in STRIP_STYLES:
      if str in x: return True
    return False

  keepStyles = []
  removeStyles = []
  for i in range(len(doc.styles)):
    name = doc.styles[i].name
    if matching(name): 
      removeStyles.append(name)
    else: 
      keepStyles.append(name)
  doc.styles = list(filter(lambda x: x.name in keepStyles, doc.styles))
  
  #replace font subsets
  for s in doc.styles:
    if s.fontname in list(subsets.keys()):
      s.fontname = subsets[s.fontname]

  doc.sections['Script Info']['LayoutResX'] = doc.info['PlayResX']
  doc.sections['Script Info']['LayoutResY'] = doc.info['PlayResY']
  doc.styles = cn_update_styles(doc.styles) #update styles

  # strip lines
  def filterEvents(x):
    a = x.style not in removeStyles
    b = True
    if apply("strip_dialogue"):
      for i in CONF["strip_dialogue"]:
        if re.fullmatch(i, x.dump()): 
          b = False
          break
    
    return True if a and b else False
    
  doc.events = list(filter(filterEvents, doc.events))

  return doc

def parse_subset(lines):
  subsets = {}
  for line in lines:
    match = re.match("; Font Subset: (.{8}) - (.*)", line, re.IGNORECASE)
    if(match):
      subsets[match.group(1)] = match.group(2)
    if(re.search(r"\[V4\+? Styles\]", line)):
      return subsets
  
  return False

def regexOps(lines):
  # print(CONF['replace_line'][0][0])
  # print(CONF['replace_line'][0][1])
  res = []
  for line in lines:
    for set in CONF['replace_line']:
      line = re.sub(fr"{set[0]}", fr"{set[1]}", fr"{line}")
    res.append(line)

  return res

def cn_clean():
  # file renaming
  # only apply to extracted files if extracting is on
  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  extractWhich =  EXTRACTED_FILES if CONF['extract'] else extracted_subs
  for sub in extractWhich:
    old = sub
    sub = cn_file_rename(sub)
    if sub != old:
      if sub in extracted_subs:
        os.remove(sub)
        log(f"Replace dual file of same name: {sub}")
      os.rename(old, sub)
  

  # handle new file
  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  for sub in extracted_subs:
    log(f"Working on sub file: {sub}")
    # if "[JPN]" in sub:
    #   continue

    # handle subsets and line fixes
    with open(sub, 'r', encoding='utf-8-sig') as f:
      doc = ass.parse(f)
      f.seek(0)
      lines = f.readlines()
      subsets = parse_subset(lines)
      doc = cn_doc_clean(doc, subsets)
      f.close()

    # create second file with [JPN] appended
    jpnsub = sub.replace(f"[{CONF['chinese']}, JPN]", "[JPN]")
    if jpnsub in extracted_subs:
      os.remove(jpnsub)
      log(f"Replace [JPN] file of same name: {jpnsub}")

    with open(jpnsub, "x" , encoding='utf_8_sig') as f:
      doc.dump_file(f)
      f.close()
    
    # run replace_line regexes
    if apply('replace_line'):
      with open(jpnsub, 'r', encoding="utf-8-sig") as f:
        lines = f.readlines()
        f.close()
      lines = regexOps(lines)
      with open(jpnsub, 'w', encoding="utf-8-sig") as f:
        f.write(''.join(lines))
        f.close()
      
      log(f"Apply replace_line regexes: {CONF['replace_line']}")
    


############ TS ############

def ts_regexOps(lines):
    res = []
    x = None
    y = None
    for line in lines:
      if line.startswith("Style: Default"):
        line = "Style: Default,A-OTF Maru Folk Pro B,42,&H00FFFFFF,&H000000FF,&H00000000,&H7F000000,-1,0,0,0,100,100,0,0,1,2,2,1,0,0,0,1\n"
      res.append(line)
      # if not x:
      #   x = re.search(r'PlayResX: (\d{1,4})', line)
      # if not y:
      #   y = re.search(r'PlayResY: (\d{1,4})', line)
      #   if x and y:
      #     res.append(f"LayoutResX: {x.group(1)}\n")
      #     res.append(f"LayoutResY: {y.group(1)}\n")

    return res

def ts_fix_styling():
  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  for sub in extracted_subs:
    with open(sub, 'r', encoding="utf_8_sig") as f:
      doc = ass.parse(f)
      doc.sections['Script Info']['LayoutResX'] = doc.info['PlayResX']
      doc.sections['Script Info']['LayoutResY'] = doc.info['PlayResY']
      f.close()

    with open(sub, "w" , encoding='utf_8') as f:
      doc.dump_file(f)
      f.close()
    
    with open(sub, 'r', encoding="utf_8_sig") as f:
      lines = f.readlines()
      lines = ts_regexOps(lines)
      f.close()
    
    with open(sub, 'w', encoding="utf_8") as f:
      f.write(''.join(lines))
      f.close()

############ EXTRACT ############

def extract_subs(mkv):
  mkv_json = json.loads(subprocess.check_output([
    'ffprobe',
    "-v",
    "quiet",
    "-print_format",
    "json",
    "-show_streams",
    "-select_streams",
    "s",
    mkv.resolve()
  ])) # ffprobe -v quiet -print_format json -show_streams -select_streams s file.mkv

  if not mkv_json.get("streams"):
    log(f"No subtitle streams to extract: {mkv.resolve()}")
    exit(1)
  index = []
  codec_name = []
  num_extracted = 0

  def matching(x):
    #skip traditional chinese tracks
    for m in TC_TRACK:
      if m in x:
        return True
       
    return False

  for s in mkv_json["streams"]:
    title = ""
    if "title" in s["tags"]: title = s["tags"]["title"]
    if CONF['mode'] == 'CN' and (num_extracted > 0 or matching(title.lower())):
      log(f"Skipped extracting track: {title}")
      continue
    index.append(s["index"]) 

    if s["codec_name"] == "subrip":
      codec_name.append("srt")
    else:
      codec_name.append(s["codec_name"])
    num_extracted += 1
    

  commands = ['mkvextract', mkv.resolve(), "tracks"]
  for i in range(len(index)):
    EXTRACTED_FILEPATHS.append(DIRPATH.joinpath(f"{mkv.stem}.{codec_name[i]}"))
    EXTRACTED_FILES.append(f"{mkv.stem}.{codec_name[i]}")
    commands.append(f"{index[i]}:{mkv.stem}.{codec_name[i]}")

  subprocess.run(commands) # mkvextract "C:\Coding\input.mkv" tracks 2:name.ass 3:name.srt

############ UPLOAD ############

async def upload():
  subs = [f for f in DIRPATH.iterdir() if f.suffix == ".srt" or f.suffix == ".ass"]
  if len(subs) == 0:
    log(f"No subs to upload")
    exit(1)
  url = fr"https://jimaku.cc/api/entries/{CONF['jimaku_id']}/upload"
  headers = {
      # 'Content-Type': "multipart/form-data",
      'Authorization': JIMAKU_API_KEY
  }
  files = {}
  for sub in subs:
    files[sub.name] = open(sub.name, 'rb')
  status = "nothing"
  res = None
  try:
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, lambda: requests.post(url, files=files, headers=headers))
    # res = requests.post(url, files=files, headers=headers)
    if res:
      data = res.json()
      log(f"Upload response:\n{data}")
      if data["errors"] > 0:
        status = "failed"
        log(f"An error occurred during the upload")
      else:
        status = "uploaded"
        log("Upload succeeded")
    else:
      status = "failed"
      log(f"No response")
  except requests.exceptions.RequestException:
    status = "failed"
    log('HTTP Request failed')
    log(f"Status Code: {res.status_code}")
    log(f"RES: {res}")
  
  for sub in subs:
    files[sub.name].close()

  new_folder = DIRPATH.joinpath(status)
  new_folder.mkdir(exist_ok=True)
  for sub in subs:
    sub.rename(new_folder / sub.name)


############ MAIN ############

if __name__ == '__main__':
  log(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  log(f"Applying to directory: {DIRNAME}")
  if args.preset:
    setConf(args.preset)
  else:
    setConf(DIRPATH.name)

  mkvs = [f for f in DIRPATH.iterdir() if f.suffix == ".mkv"]

  if CONF['extract']:
    if STRICT:
      ignorePath = Path("ignore.conf")
      if ignorePath.is_file():
        with open("ignore.conf", 'r', encoding="utf-8") as f:
          lines = f.read().splitlines()
          f.close()
        mkvs = list(filter(lambda x: x.name not in lines, mkvs))
    if len(mkvs) == 0:
      log(f"ERROR: no mkv to extract")
      exit(1)

    extracted_mkvs = []
    for mkv in mkvs:
      extract_subs(mkv)
      extracted_mkvs.append(mkv)
    
    if STRICT:
      with open("ignore.conf", 'a', encoding="utf-8") as f:
        for path in extracted_mkvs:
          f.write(f"{path.name}\n")
        f.close()

  if CONF['linefixes']:
    if CONF['mode'] == 'CN':
      cn_clean()
    elif CONF['mode'] == 'TS':
      ts_fix_styling()

  if CONF['upload'] and apply('jimaku_id'):
    asyncio.run(upload())

  # fix_styling()
  print("\nEND OF SCRIPT!!!!!!!!!!!!!\n")
  # time.sleep(10)


