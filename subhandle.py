import os
from pathlib import Path
import subprocess
import json
import re
import time
import sys
import ass
import argparse
from datetime import datetime
import asyncio
from preset import *
from lineops import *
from fileops import *

############ Shared ############

executingDir = Path(__file__).parent.resolve()
print(f"Running in: {executingDir}")
if executingDir.joinpath("secret.py").is_file():
  from secret import secrets
  JIMAKU_API_KEY = secrets.get('JIMAKU_API_KEY', JIMAKU_API_KEY)

parser = argparse.ArgumentParser()
parser.add_argument('folder', nargs='?', default=os.getcwd())
parser.add_argument('-p', '--preset')  
parser.add_argument('-s', '--strict', action='store_true')    
args = parser.parse_args()
# pyfile_path = os.path.dirname(os.path.realpath(__file__))
OUTPUT_DIR_PATH = Path(args.folder)
OUTPUT_DIR_NAME = OUTPUT_DIR_PATH.resolve()
STRICT = args.strict
CONF['strict'] = STRICT
os.chdir(OUTPUT_DIR_NAME)
if args.strict and not Path("ignore.conf").is_file():
  print("ignore.conf not present")
  exit(0)

EXTRACTED_FILES = []
EXTRACTED_FILEPATHS = []


def setConf(preset_name):  
  if preset_name in PRESET.keys():
    mode_name =  PRESET[preset_name]['mode'] if 'mode' in PRESET[preset_name].keys() else CONF['mode']
    #apply mode before preset
    if mode_name in MODE.keys():
      for setting in MODE[mode_name].keys():
        CONF[setting] = MODE[mode_name][setting]
      log(f"MODE FOUND: {mode_name}")
      
    for setting in PRESET[preset_name].keys():
      CONF[setting] = PRESET[preset_name][setting]
    log(f"PRESET FOUND: {preset_name}")
    log(CONF)
    return True
  return False



############ CN ONLY ############

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

  old_tag = CONF["old_lang_tag"]
  new_tag = CONF["new_lang_tag"]
  if fr"[{old_tag}, {new_tag}]" not in sub and fr"[{new_tag}]" not in sub:
    sub = sub.replace(".ass", "")
    sub+=fr"[{old_tag}, {new_tag}].ass"
  return sub

def file_handling():
  # file renaming
  # only apply to extracted files if extracting is on
  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  extractWhich =  EXTRACTED_FILES if CONF['extract'] else extracted_subs

  # rename original file according to language tag conf
  if CONF['mode'] == 'CN':
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


    # handle subsets and lineops
    with open(sub, 'r', encoding='utf-8-sig') as f:
      doc = ass.parse(f)
      f.seek(0)
      lines = f.readlines()
      subsets = parse_subset(lines) if CONF['parse_subset'] else False
      doc = doc_strip_styles(doc, CONF) if CONF['strip_style'] else doc
      doc = doc_update_styles(doc, subsets, CONF)
      f.close()

    # create second file with different name depending on conf
    new_file = sub
    if CONF['mode'] == 'CN':
      old_tag = CONF['old_lang_tag']
      new_tag = CONF['new_lang_tag']
      new_file = sub.replace(f"[{old_tag}, {new_tag}]", f"[{new_tag}]")
    elif apply('append_filename'):
      # new_file = new_file.replace(CONF['append_filename']+'.ass', '.ass')
      new_file = new_file.replace(CONF['append_filename']+'.ass', '.ass')
      print(0, CONF['append_filename']+'.ass$')
      print(1, new_file)
      new_file = re.sub('\.ass$', CONF['append_filename']+'.ass', new_file)
      print(2, new_file)


    if new_file in extracted_subs:
      os.remove(new_file)
      log(f"Replace [JPN] file of same name: {new_file}")

    with open(new_file, "x" , encoding='utf_8_sig') as f:
      doc.dump_file(f)
      f.close()
    
    # run replace_line regexes
    if apply('replace_line'):
      with open(new_file, 'r', encoding="utf-8-sig") as f:
        lines = f.readlines()
        f.close()
      lines = regexOps(lines)
      with open(new_file, 'w', encoding="utf-8-sig") as f:
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

F2HMAP = {'　': ' ', '！': '!', '＂': '"', '＃': '#', '＄': '$', '％': '%', '＆': '&', 
          '＇': "'", '（': '(', '）': ')', '＊': '*', '＋': '+', '，': ',', '－': '-', 
          '．': '.', '／': '/', 
          '０': '0', '１': '1', '２': '2', '３': '3', '４': '4', '５': '5', '６': '6', 
          '７': '7', '８': '8', '９': '9', 
          '：': ':', '；': ';', '＜': '<', '＝': '=', '＞': '>', '？': '?', '＠': '@',
          'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'Ｇ': 'G',
          'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J', 'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N',
          'Ｏ': 'O', 'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T', 'Ｕ': 'U',
          'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z', 
          '［': '[', '＼': '\\', 
          '］': ']', '＾': '^', '＿': '_', '｀': '`',
          'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g',
          'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n',
          'ｏ': 'o', 'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't', 'ｕ': 'u',
          'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z', 
          '｛': '{', '｜': '|', '｝': '}'}

def get_normalize_filename(string):
  full2half = ''.join(F2HMAP.get(c, c) for c in string)
  valid_map = {'<': '＜', '>': '＞', ':': ' - ', '/': '／', '\\': '＼', '|': '｜', '?': '？', '*': ''}
  valid_filename = ''.join(valid_map.get(c, c) for c in full2half)
  return valid_filename
  


def extract_subs(mkv, skip_mkv_track, normalize_filename):
  commands = [
    'ffprobe',
    "-v",
    "quiet",
    "-print_format",
    "json",
    "-show_streams",
    "-select_streams",
    "s",
    mkv.resolve()
  ]
  if PATH_TO_FFPROBE:
    commands[0] = Path(PATH_TO_FFPROBE).resolve()
    print("Using ffprobe in:", commands[0])
  mkv_json = json.loads(subprocess.check_output(commands)) # ffprobe -v quiet -print_format json -show_streams -select_streams s file.mkv

  if not mkv_json.get("streams"):
    log(f"No subtitle streams to extract: {mkv.resolve()}")
    exit(1)
  index = []
  codec_name = []
  num_extracted = 0

  # skip mkv tracks
  def matching(x):
    for m in skip_mkv_track:
      if m in x:
        return True
       
    return False

  for s in mkv_json["streams"]:
    title = ""
    if "title" in s["tags"]: title = s["tags"]["title"]
    if apply("skip_mkv_track") and (num_extracted > 0 or matching(title.lower())):
      log(f"Skipped extracting track: {title}")
      continue
    index.append(s["index"]) 

    if s["codec_name"] == "subrip":
      codec_name.append("srt")
    else:
      codec_name.append(s["codec_name"])
    num_extracted += 1
    
  extracted_name = mkv.stem
  if normalize_filename:
    extracted_name = get_normalize_filename(extracted_name)
    log(f"Normalized name: {extracted_name}")

  commands = ['mkvextract', mkv.resolve(), "tracks"]
  if PATH_TO_MKVEXTRACT:
    commands[0] = Path(PATH_TO_MKVEXTRACT).resolve()
    print("Using mkvextract in:", commands[0])
  for i in range(len(index)):
    EXTRACTED_FILEPATHS.append(OUTPUT_DIR_PATH.joinpath(f"{extracted_name}.{codec_name[i]}"))
    EXTRACTED_FILES.append(f"{extracted_name}.{codec_name[i]}")
    commands.append(f"{index[i]}:{extracted_name}.{codec_name[i]}")

  subprocess.run(commands) # mkvextract "C:\Coding\input.mkv" tracks 2:name.ass 3:name.srt



############ MAIN ############

if __name__ == '__main__':
  log(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  log(f"Applying to directory: {OUTPUT_DIR_NAME}")
  if args.preset:
    setConf(args.preset)
  else:
    setConf(OUTPUT_DIR_PATH.name)

  mkvs = [f for f in OUTPUT_DIR_PATH.iterdir() if f.suffix == ".mkv"]

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
      extract_subs(mkv, skip_mkv_track=CONF["skip_mkv_track"], normalize_filename=CONF["normalize_filename"])
      extracted_mkvs.append(mkv)
    
    if STRICT:
      with open("ignore.conf", 'a', encoding="utf-8") as f:
        for path in extracted_mkvs:
          f.write(f"{path.name}\n")
        f.close()

  if CONF['lineops']:
    file_handling()

  # if CONF['linebreak']:

  if CONF['upload'] and apply('jimaku_id'):
    asyncio.run(upload(output_dir_path=OUTPUT_DIR_PATH, jimaku_id=CONF['jimaku_id'], jimaku_api_key=JIMAKU_API_KEY))

  # fix_styling()
  print("\nEND OF SCRIPT!!!!!!!!!!!!!\n")
  # time.sleep(10)


