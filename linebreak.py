import os
import ass
import re
import logging
from sudachipy import tokenizer, dictionary

log = logging.getLogger(__name__)


REDO_LINEBREAK = True
MAX_RATIO = 2.5 # max acceptable ratio of length of strings before/after linebreak position
MAX_LENGTH = 20 # must add linebreak if line is at least this length
MIN_LENGTH = 16 # don't add linebreak unless line is at least this length

START_PUNC = """『「(（《｟[{"'“¿""" + """'“"¿([{-『「（〈《〔【｛［｟＜<‘“〝※"""
END_PUNC =   """'"・.。!！?？:：”>＞⦆)]}』」）〉》〕】｝］’〟／＼～〜~;；─―–-➡""" + """＊,，、… """
REPLACE_PUNC = """　"""
PUNC = START_PUNC + END_PUNC + REPLACE_PUNC

HIRAGANA_WO = "を"
ROUND2A = '.*[るどたよにではがも]$|たら|ながら'
ROUND2B = '.*[のなとゃ]$'
ROUND3 = '[てか]|って|いう|から' # まだ

# don't break if next word is this
POST = '[るどたよにではがも]'+'|'+'[のな]'+'|'+'[しれんかねだわてい]|っ.*|から|けれど|なく|です|ない|べき|言[いえ]|思[いえう]|いう|する|とっ' # no と
POST += '|ある|おけ'
HONORIFICS = 'ちゃん|さん'
# TODO: don't break after if word is this
PREFIX = 'お'


class Word:
  def __init__(self, text, start, end, type):
    self.text = text
    self.start = start
    self.end = end
    self.type = type
    self.ratio = False

  def __str__(self):
    return f"{self.text}({self.start},{self.end})"
  
  def __repr__(self):
    return self.text

def parse_sentence(line, parsed_line, event_num):
  sentence = []
  i = 0 # pointer for line
  j = 1 # pointer for tagless line
  p = 0 # pointer for parsed_line
  while i < len(line):
    # pop tags, PUNC, word
    type = 'word'
    text = line[i]
    end_index = i
    tagless_end_index = j
    increment_j = 0
    try:
      if line[i] == "{":
        end = line.find("}", i)
        if end > 0:
          text = line[i:end+1]
          end_index = end
          type = 'tag'
        else:
          raise Exception('No closing } found')
      elif line[i] in PUNC:
        if parsed_line[p] != " ":
          raise Exception('PUNC not matched in parsed line')
        p += 1
        increment_j = 1
        type = 'replace_punc' if line[i] == "　" else 'punc'
      else:
        end = i+len(parsed_line[p])-1
        search_text = line[i:end+1]
        if search_text != parsed_line[p]:
          raise Exception('Word not matched in parsed line')
        else:
          p += 1
          end_index = end
          text = search_text
          increment_j = end_index - i + 1
          tagless_end_index = j + increment_j - 1
    except Exception as e:
      log.error(f"Event {event_num}: {line[0:i+1]}---{line[i+1:] if i+1 < len(line) else ''}")
      log.error(f"Parsed line: {parsed_line[0:p+1]}---{parsed_line[p+1:] if p+1 < len(parsed_line) else ''}")
      log.error(e.args)
      exit(0)


    word = Word(text, j, tagless_end_index, type)
    sentence.append(word)
    i = end_index + 1
    j += increment_j
  
  for i in range(len(sentence)-1):
    if sentence[i+1].type == 'tag' and i < len(sentence)-2:
      sentence[i].next = sentence[i+2]
    else:
      sentence[i].next = sentence[i+1]
    
  sentence[len(sentence)-1].next = ''

  return sentence

def add_linebreak(line, parsed_line, event_num, redo_linebreak=REDO_LINEBREAK, min_length=MIN_LENGTH, max_length=MAX_LENGTH, max_ratio=MAX_RATIO, debug_linebreak=0):
  """
  Process:
    - round 1a, 1b, 1c - break after IDEOGRAPHIC SPACE->PUNC->を
    - round 2a, 2b - break after particles->riskier particles
    - round 3 - break after certain words under conditions
    - round 4 - break after len(word)>1 under conditions
  TODO: lower ratio after each iteration. round 4 is unlocked after a certain ratio
  TODO: check if either side is above max_length post-split
  TODO: lower min_length/max_length/max_ratio if margin or position tag

  additional notes about parser:
    - spaces will split words

  :line: event line in ass file.  Ex: "大人の高さまで　背が伸びたらわかる？\n"
  :parsed_line: event line parsed into words. Ex: ['大人', 'の', '高', 'さ', 'まで', ' ', '背', 'が', '伸び', 'たら', 'わかる', ' ']
  :debug_linebreak: 0 - off, 1 - minimal, 2 - all linebreaks, 3 - verbose  
  """ 
  verbose = False
  if debug_linebreak == 3:
    verbose = True 
  line_length = 0
  parsed_line_str = ' '.join(parsed_line)
  for i in parsed_line:
    line_length+=len(i)
  if (not redo_linebreak and re.search(r'\\N', line)) or line_length < min_length:
    if verbose:
      line += "{" + f"L{str(line_length)}|{parsed_line_str}" + "}"
    return line
  if redo_linebreak:
    line = line.replace('\\N', '')

  sentence = parse_sentence(line, parsed_line, event_num)
  # print(' '.join(str(item) for item in sentence)) 
  # print([str(w) for w in sentence]) 

  original_ratio = max_ratio
  best = False
  debug = "0"
  candidate = []

  def calc_ratio(left, right):
    if left == 0 or right == 0:
      return 100
    if left > right:
      return round(left/right, 1)
    return round(right/left, 1)

  def test_round(key, eligible_words, which, left, right, after):
    best = ''
    candidate = list(filter(key, eligible_words))
    for x in candidate:
      send_left = x.start if which[0] == 's' else x.end
      send_right = x.start if which[1] == 's' else x.end
      x.ratio = calc_ratio(left(send_left), right(send_right))
      x.after = after
    candidate = list(filter(lambda x: x.ratio <= max_ratio, candidate))
    if candidate:
      best = min(candidate, key=lambda x: x.ratio)
    return candidate, best

  while not best:
    # round 1a: ideographic space
    candidate, best = test_round(lambda x: x.type == "replace_punc", sentence, 'se', lambda a : a - 1, lambda b : line_length - b, 'replace')
    # candidate, best = test_round(lambda x: x.type == "replace_punc", sentence, x.start - 1, line_length - x.end, 'replace')
    if candidate:
      debug = "1a"
      break

    # round 1b: punc
    candidate = list(filter(lambda x: x.type == "punc", sentence))
    for x in candidate:
      if x.text in START_PUNC:
        x.ratio = calc_ratio(x.start - 1, line_length - x.start + 1)
        x.after = False
      else:
        x.ratio = calc_ratio(x.end, line_length - x.end)
        x.after = True
    candidate = list(filter(lambda x: x.ratio <= max_ratio, candidate))
    if candidate:
      best = min(candidate, key=lambda x: x.ratio)
      debug = "1b"
      break

    def df(x):
      if x.type == "word":
        if x.next and re.fullmatch(POST, x.next.text):
          # print(f"Skip: {x.next.text}")
          return False
        return True
      return False
    words_only = list(filter(df, sentence))

    # round 1c: を
    candidate, best = test_round(lambda x: x.text == 'を', words_only, 'ee', lambda a : a, lambda b : line_length - b, True)
    if candidate:
      debug = "1c"
      break

    # round 2a: particles
    candidate, best = test_round(lambda x: re.fullmatch(ROUND2A, x.text), words_only, 'ee', lambda a : a, lambda b : line_length - b, True)
    if candidate:
      debug = "2a"
      break

    # round 2b: risker particles
    candidate, best = test_round(lambda x: re.fullmatch(ROUND2B, x.text), words_only, 'ee', lambda a : a, lambda b : line_length - b, True)
    if candidate:
      debug = "2b"
      break

    # for next word
    not_kana = list(filter(lambda x: re.match('[^ぁ-んァ-ン]', x.next.text) if x.next else False, words_only)) # first char not kana
    longer_than_one = list(filter(lambda x: len(x.next.text) > 1 if x.next else False, words_only))
    not_kana_longer_than_one = [x for x in not_kana if x in longer_than_one]
    
    # round 3: certain words with conditions
    candidate, best = test_round(lambda x: re.fullmatch(ROUND3, x.text), not_kana, 'ee', lambda a : a, lambda b : line_length - b, True)
    if candidate:
      debug = "3a"
      break

    candidate, best = test_round(lambda x: re.fullmatch(ROUND3, x.text), longer_than_one, 'ee', lambda a : a, lambda b : line_length - b, True)
    if candidate:
      debug = "3b"
      break

    # round 4: len(word)>1 with conditions
    candidate, best = test_round(lambda x: len(x.text)>1, not_kana_longer_than_one, 'ee', lambda a : a, lambda b : line_length - b, True)
    if candidate:
      debug = "4"
      break

    # no linebreak added
    if line_length <= max_length:
      if verbose:
        line += "\{Skipped\}"
      return line

    max_ratio += .5
    if max_ratio > 5:
      break

  extra = ""
  if verbose:
    extra = f"|L{line_length}|"
    for c in candidate:
      extra += c.text+str(c.ratio)
  
  if best:
    if best.after == 'replace':
      best.text = "\\N"
    elif best.after:
      best.text += "\\N"
    else:
      best.text = "\\N" + best.text
    
    line = ""
    for w in sentence:
      line += w.text
    if debug_linebreak > 1:
      line += "{"
      if max_ratio > original_ratio:
        line += f"M{max_ratio}"
      line +=f"R{debug}{extra if verbose else ''}|{parsed_line_str}" +  "}"
  elif debug_linebreak > 0:
    line+= "{" + f"MISSED{extra if verbose else ''}|{parsed_line_str}" +  "}"

  return line


def clean_for_sudachipy(string):
  """Remove tags and linebreaks. To make word matching simpler, replace all punc with space"""
  string = re.sub(r'\\N', '', string)
  string = re.sub(r'{[^}]*}', '', string)
  table = str.maketrans(PUNC, ' '*len(PUNC))
  return string.translate(table)

def run_doc_linebreak(doc, linebreak_styles, CONF):
  tokenizer_obj = dictionary.Dictionary(dict_type="full").create()
  modeC = tokenizer.Tokenizer.SplitMode.C
  for i in range(len(doc.events)):
    if not doc.events[i].style in linebreak_styles:
      continue
    line = doc.events[i].text
    parsed_line = [m.surface() for m in tokenizer_obj.tokenize(clean_for_sudachipy(line), modeC)]
    result = add_linebreak(line, parsed_line, i+1, redo_linebreak=CONF['redo_linebreak'], min_length=CONF['min_length'], 
                           max_length=CONF['max_length'], max_ratio=CONF['max_ratio'], debug_linebreak=CONF['debug_linebreak'])
    doc.events[i].text = result

  return doc

def run_linebreak(filelist, CONF):
  tokenizer_obj = dictionary.Dictionary(dict_type="full").create()
  modeC = tokenizer.Tokenizer.SplitMode.C

  # clean up [Linebreak] files
  for sub in filelist:
    linebreak_sub = re.sub("(\[Linebreak\])?\.ass", "[Linebreak].ass", sub)
    if linebreak_sub in filelist and linebreak_sub != sub:
      os.remove(linebreak_sub)
      log.info(f"Replace [Linebreak] file of same name: {linebreak_sub}")
      filelist.remove(linebreak_sub)


  for sub in filelist:
    with open(sub, 'r', encoding='utf-8-sig') as f:
      doc = ass.parse(f)
    
    for i in range(len(doc.events)):
      line = doc.events[i].text
      parsed_line = [m.surface() for m in tokenizer_obj.tokenize(clean_for_sudachipy(line), modeC)]
      result = add_linebreak(line, parsed_line, i+1, redo_linebreak=CONF['redo_linebreak'], min_length=CONF['min_length'], 
                             max_length=CONF['max_length'], max_ratio=CONF['max_ratio'], debug_linebreak=CONF['debug_linebreak'])
      doc.events[i].text = result

    linebreak_sub = re.sub("(\[Linebreak\])?\.ass", "[Linebreak].ass", sub)
    with open(linebreak_sub, "w" , encoding='utf_8_sig') as f:
      doc.dump_file(f)
      f.close()  
    


if __name__ == '__main__':
    # wakati = MeCab.Tagger("-Owakati")
    # parsed_line = wakati.parse(clean_for_mecab("asdasd"+PUNC+"asd")).split(r" ")
    tokenizer_obj = dictionary.Dictionary(dict_type="full").create()
    modeC = tokenizer.Tokenizer.SplitMode.C
    sub = ""
    # sub = r"C:\Coding\.extract\[Nekomoe kissaten&LoliHouse] Monogatari Series - Off & Monster Season - 13 [WebRip 1080p HEVC-10bit AAC ASSx2][JPN].ass"
    if sub:
      with open(sub, 'r', encoding='utf-8-sig') as f:
        doc = ass.parse(f)

      parsed_lines = []
      for i in range(len(doc.events)):
        line = doc.events[i].text
        parsed_line = [m.surface() for m in tokenizer_obj.tokenize(clean_for_sudachipy(line), modeC)]
        result = add_linebreak(line, parsed_line, i+1)
        doc.events[i].text = result
        parsed_lines.append(f"Event {i}: "+" ".join(str(x) for x in parsed_line))

      parsed_sub = sub.replace(".ass", "[Parsed].txt")
      with open(parsed_sub, "w" , encoding='utf_8_sig') as f:
          # f.write('\n'.join(str(item) for item in parsed_lines))
          f.write('\n'.join(parsed_lines))
          f.close()
    else:
      for i in [modeC]:
        print([m.surface() for m in tokenizer_obj.tokenize("制服とユニフォーム　バッシュもだ", i)])