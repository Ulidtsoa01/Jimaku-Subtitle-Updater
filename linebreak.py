import MeCab
import os
import ass
import re
from sudachipy import tokenizer, dictionary
from collections import deque

REDO_LINEBREAK = True
MAX_RATIO = 2.5 # max acceptable ratio of length of strings before/after linebreak position
MAX_LENGTH = 20 # must add linebreak if line is at least this length
MIN_LENGTH = 16 # don't add linebreak unless line is at least this length

START_PUNC = """『「(（《｟[{"'“¿""" + """'“"¿([{-『「（〈《〔【｛［｟＜<‘“〝※"""
END_PUNC =   """'"・.。!！?？:：”>＞⦆)]}』」）〉》〕】｝］’〟／＼～〜~;；─―–-➡""" + """＊,，、…"""
REPLACE_PUNC = """　"""
PUNC = START_PUNC + END_PUNC + REPLACE_PUNC

HIRAGANA_WO = "を"
ROUND2 = '.*[るどたよにではがも]$'
ROUND3 = '.*[のとな]$'
unable_to_break = '[てか]' # unable to break on bc of parser

# don't break if next word is this
POST = '[るどたよにではがも]|'+'[のとな]|'+'[しれんかねだわて]|なく|です|ない|べき|から|言[いえ]|思[いえ]|いう|する|けれど|とっ'
# TODO: don't break after if word is this
PREFIX = 'お'


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
      print(f"Event {event_num}: {line[0:i+1]}---{line[i+1:] if i+1 < len(line) else ''}")
      print(f"Parsed line: {parsed_line[0:p+1]}---{parsed_line[p+1:] if p+1 < len(parsed_line) else ''}")
      print(e.args)


    word = Word(text, j, tagless_end_index, type)
    sentence.append(word)
    i = end_index + 1
    j += increment_j
  
  for i in range(len(sentence)-1):
    sentence[i].next = sentence[i+1]
  sentence[len(sentence)-1].next = False

  return sentence

def add_linebreak(line, parsed_line, event_num, min_length=MIN_LENGTH, max_length=MAX_LENGTH, redo_linebreak=REDO_LINEBREAK, max_ratio=MAX_RATIO):
  """
  Process:
    - round 1a, 1b, 1c - break around IDEOGRAPHIC SPACE->PUNC->を
    - round 2 - break around particles 
    - round 3 - break around risker particles
    - TODO: round 4 - break around kanji words
  TODO: lower ratio after each iteration. round 4 is unlocked after a certain ratio

  additional notes about parser:
    - spaces will split words

  :line: event line in ass file.  Ex: "大人の高さまで　背が伸びたらわかる？\n"
  :parsed_line: event line parsed into words. Ex: ['大人', 'の', '高', 'さ', 'まで', ' ', '背', 'が', '伸び', 'たら', 'わかる', ' ']
  """ 
  line_length = 0
  for i in parsed_line:
    line_length+=len(i)
  if (not redo_linebreak and re.search(r'\\N', line)) or line_length < min_length:
    return line
  if redo_linebreak:
    line = line.replace('\\N', '')

  sentence = parse_sentence(line, parsed_line, event_num)
  # print(' '.join(str(item) for item in sentence)) 
  # print([str(w) for w in sentence]) 

  def calc_ratio(left, right):
    if left == 0 or right == 0:
      return 100
    if left > right:
      return round(left/right, 1)
    return round(right/left, 1)

  best = False
  debug = "0"
  while not best:
    # round 1a: ideographic space
    candidate = list(filter(lambda x: x.type == "replace_punc", sentence))
    for x in candidate:
      x.ratio = calc_ratio(x.start - 1, line_length - x.end)
    candidate = list(filter(lambda x: x.ratio <= max_ratio, candidate))
    if candidate:
      best = min(candidate, key=lambda x: x.ratio)
      best.after = 'replace'
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
    eligible_words = list(filter(df, sentence))

    # round 1c: を
    candidate = list(filter(lambda x: x.text == 'を', eligible_words))
    for x in candidate:
      x.ratio = calc_ratio(x.end, line_length - x.end)
    candidate = list(filter(lambda x: x.ratio <= max_ratio, candidate))
    if candidate:
      best = min(candidate, key=lambda x: x.ratio)
      best.after = True
      debug = "1c"
      break

    # round 2: particles
    candidate = list(filter(lambda x: bool(re.search(ROUND2, x.text)), eligible_words))
    for x in candidate:
      x.ratio = calc_ratio(x.end, line_length - x.end)
    candidate = list(filter(lambda x: x.ratio <= max_ratio, candidate))
    if candidate:
      best = min(candidate, key=lambda x: x.ratio)
      best.after = True
      debug = "2"
      break

    # round 3: risker particles
    candidate = list(filter(lambda x: bool(re.search(ROUND3, x.text)), eligible_words))
    for x in candidate:
      x.ratio = calc_ratio(x.end, line_length - x.end)
    candidate = list(filter(lambda x: x.ratio <= max_ratio, candidate))
    if candidate:
      best = min(candidate, key=lambda x: x.ratio)
      best.after = True
      debug = "3"
      break

    # no linebreak added
    if line_length <= max_length:
      return line

    break
  
  pl = ' '.join(parsed_line)
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
    line+= "{" + f"R{debug}|{pl}" +  "}"
  else:
    line+= "{" + f"MISSED|{pl}" +  "}"


  return line


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



def clean_for_sudachipy(string):
  """Remove tags and linebreaks. To make word matching simpler, replace all punc with space"""
  string = re.sub(r'\\N', '', string)
  string = re.sub(r'{.*}', '', string)
  table = str.maketrans(PUNC, ' '*len(PUNC))
  return string.translate(table)

def run_linebreak():
  tokenizer_obj = dictionary.Dictionary(dict_type="full").create()
  modeC = tokenizer.Tokenizer.SplitMode.C

  # clean up [Linebreak] files
  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  for sub in extracted_subs:
    linebreak_sub = re.sub("(\[Linebreak\])?\.ass", "[Linebreak].ass", sub)
    if linebreak_sub in extracted_subs and linebreak_sub != sub:
      os.remove(linebreak_sub)
      print(f"Replace [Linebreak] file of same name: {linebreak_sub}")
      # extracted_subs.remove(linebreak_sub)



  extracted_subs = [f for f in os.listdir() if f.endswith(".ass")]
  for sub in extracted_subs:
    with open(sub, 'r', encoding='utf-8-sig') as f:
      doc = ass.parse(f)
    
    # for i in range(20):
    for i in range(len(doc.events)):
      line = doc.events[i].text
      parsed_line = [m.surface() for m in tokenizer_obj.tokenize(clean_for_sudachipy(line), modeC)]
      result = add_linebreak(line, parsed_line, i+1)
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

    # print(line)