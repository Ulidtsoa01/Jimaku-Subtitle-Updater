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
import logging
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
parser.add_argument('-u', '--upload', action='store_true', default=False)
parser.add_argument('--jimaku_id', default=False)
parser.add_argument('--status_dir_path', default=False)    
args = parser.parse_args()
# pyfile_path = os.path.dirname(os.path.realpath(__file__))
OUTPUT_DIR_PATH = Path(args.folder)
OUTPUT_DIR_NAME = OUTPUT_DIR_PATH.resolve()
os.chdir(OUTPUT_DIR_NAME)
STRICT = args.strict
CONF['strict'] = STRICT
if args.strict and not Path("ignore.conf").is_file():
  print("ignore.conf not present")
  exit(0)

log = logging
logging.basicConfig(
  encoding='utf-8',
  level=logging.DEBUG,
  handlers=[
    logging.StreamHandler()]
)
if CONF['strict']:
  log.getLogger().addHandler(logging.FileHandler("upload.log"))


EXTRACTED_FILES = []
EXTRACTED_FILEPATHS = []


def setConf(preset_name):  
  if preset_name in PRESET.keys():
    mode_name =  PRESET[preset_name]['mode'] if 'mode' in PRESET[preset_name].keys() else CONF['mode']
    #apply mode before preset
    if mode_name in MODE.keys():
      for setting in MODE[mode_name].keys():
        CONF[setting] = MODE[mode_name][setting]
      log.info(f"MODE FOUND: {mode_name}")
      
    for setting in PRESET[preset_name].keys():
      CONF[setting] = PRESET[preset_name][setting]
    log.info(f"PRESET FOUND: {preset_name}")
    log.debug(CONF)
    return True
  return False

def handleArgs(args):
  global CONF
  if args.upload and args.jimaku_id:
    CONF['upload'] = True
    CONF['jimaku_id'] = args.jimaku_id
    CONF['status_dir_path'] = args.status_dir_path
  return True

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

def run_update_lines():
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
          log.info(f"Replace dual file of same name: {sub}")
        os.rename(old, sub)
    

  # handle .ass files
  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  for sub in extracted_subs:
    log.info(f"Working on sub file: {sub}")


    # handle subsets and lineops
    with open(sub, 'r', encoding='utf-8-sig') as f:
      doc = ass.parse(f)
      f.seek(0)
      lines = f.readlines()
      subsets = parse_subset(lines) if CONF['parse_subset'] else False
      if CONF['strip_style']: doc = doc_strip_styles(doc, CONF)
      doc = doc_update_styles(doc, subsets, CONF)
      if apply('trim_end'): doc = doc_trim_end(doc, CONF['trim_end'])
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
      new_file = re.sub('\.ass$', CONF['append_filename']+'.ass', new_file)


    if new_file in extracted_subs:
      os.remove(new_file)
      log.info(f"Replace [JPN] file of same name: {new_file}")

    with open(new_file, "x" , encoding='utf_8_sig') as f:
      doc.dump_file(f)
      f.close()
    
    # run replace_line regexes
    if apply('replace_line'):
      with open(new_file, 'r', encoding="utf_8_sig") as f:
        lines = f.readlines()
        f.close()
      handle_ruby = CONF['handle_ruby'] if apply('handle_ruby') else False
      dont_replace_line = CONF['dont_replace_line'] if apply('dont_replace_line') else False
      lines = regexOps(lines, handle_ruby, dont_replace_line)
      with open(new_file, 'w', encoding="utf_8_sig") as f:
        f.write(''.join(lines))
        f.close()
      
      log.info(f"Apply replace_line regexes: {CONF['replace_line']}")


def trim_end_srt(timedelta):
  import srt
  extracted_subs = [f for f in os.listdir() if f.endswith(".srt")]
  for sub in extracted_subs:
    log.info(f"Working on sub file: {sub}")
    with open(sub, 'r', encoding="utf_8_sig") as f:
      lines = f.read()
      f.close()
    doc = list(srt.parse(lines))
    trim_line_index = False
    for i in range(len(doc)-1):
      # print(f"Start: {doc.events[i].start}")
      # print(f"End: {doc.events[i].end}")
      difference = abs(doc[i+1].start-doc[i].end)
      sec_difference = difference.total_seconds()
      if sec_difference > timedelta:
        log.info(f"Diff(sec): {sec_difference}")
        trim_line_index = i+1
        break

    if trim_line_index:
      doc = doc[0:trim_line_index]
    srtblock = srt.compose(doc)
    with open(sub, 'w', encoding="utf_8_sig") as f:
      f.write(srtblock)
      f.close()
    

############ EXTRACT ############

  
def get_normalize_filename(string):
  full_width = """　！＂＃＄％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ［＼］＾＿｀ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ｛｜｝"""
  half_width = """ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}"""
  # full2half = ''.join(F2HMAP.get(c, c) for c in string)
  table = str.maketrans(full_width, half_width)
  full2half = string.translate(table)
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
    log.warning(f"No subtitle streams to extract: {mkv.resolve()}")
    return False
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
      log.info(f"Skipped extracting track: {title}")
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
    log.info(f"Normalized name: {extracted_name}")

  commands = ['mkvextract', mkv.resolve(), "tracks"]
  if PATH_TO_MKVEXTRACT:
    commands[0] = Path(PATH_TO_MKVEXTRACT).resolve()
    print("Using mkvextract in:", commands[0])
  for i in range(len(index)):
    EXTRACTED_FILEPATHS.append(OUTPUT_DIR_PATH.joinpath(f"{extracted_name}.{codec_name[i]}"))
    EXTRACTED_FILES.append(f"{extracted_name}.{codec_name[i]}")
    commands.append(f"{index[i]}:{extracted_name}.{codec_name[i]}")

  subprocess.run(commands) # mkvextract "C:\Coding\input.mkv" tracks 2:name.ass 3:name.srt
  return True



############ MAIN ############

if __name__ == '__main__':
  log.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  log.info(f"Applying to directory: {OUTPUT_DIR_NAME}")
  if args.preset:
    setConf(args.preset)
  else:
    setConf(OUTPUT_DIR_PATH.name)
  handleArgs(args)

  mkvs = [f for f in OUTPUT_DIR_PATH.iterdir() if f.suffix == ".mkv"]

  if apply('extract'):
    if STRICT:
      ignorePath = Path("ignore.conf")
      if ignorePath.is_file():
        with open("ignore.conf", 'r', encoding="utf-8") as f:
          lines = f.read().splitlines()
          f.close()
        mkvs = list(filter(lambda x: x.name not in lines, mkvs))
    if len(mkvs) == 0:
      log.error(f"No mkv to extract")
      exit(1)

    extracted_mkvs = []
    for mkv in mkvs:
      is_extracted = extract_subs(mkv, skip_mkv_track=CONF["skip_mkv_track"], normalize_filename=CONF["normalize_filename"])
      if is_extracted:
        extracted_mkvs.append(mkv)
    
    if STRICT:
      with open("ignore.conf", 'a', encoding="utf-8") as f:
        for path in extracted_mkvs:
          f.write(f"{path.name}\n")
        f.close()

  if apply('update_lines'):
    run_update_lines()
    if apply('trim_end'):
      trim_end_srt(CONF['trim_end'])

  if apply('linebreak') and not apply("update_lines"):
    from linebreak import *
    run_linebreak()

  if apply('upload') and apply('jimaku_id'):
    status_dir_path = False
    if apply('status_dir_path'):
      status_dir_path = CONF['status_dir_path']
    asyncio.run(upload(output_dir_path=OUTPUT_DIR_PATH, jimaku_id=CONF['jimaku_id'], jimaku_api_key=JIMAKU_API_KEY, status_dir_path=status_dir_path))

  # fix_styling()
  print("\nEND OF SUBHANDLE.PY\n")
  # time.sleep(10)


