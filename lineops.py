import re
from preset import *
from utils import *

def update_styles(styles, CONF):
  def matching(x):
    for es in CONF["skip_style"]:
      if es in x:
        return False
    for ns in CONF["apply_style"]: #need to match to apply style options
      if ns in x:
        for ts in CONF["top_style"]: #need to match to apply vertical positioning
          if ts in x:
            return "top"
        return True
    return False
  
  def color_apply(field):
    if apply(field) and len(CONF[field]) == 4:
      return True
    return False

  for s in styles:
    match = matching(s.name.lower())
    if match:
      if apply('fontsize'): s.fontsize = CONF['fontsize']
      if apply('fontname'): s.fontname = CONF['fontname']
      if apply('bold'): s.bold = CONF['bold']
      if apply('italic'): s.italic = CONF['italic']
      if apply('underline'): s.underline = CONF['underline']
      if apply('strike_out'): s.strike_out = CONF['strike_out']

      if apply('scale_x'): s.scale_x = CONF['scale_x']
      if apply('scale_y'): s.scale_y = CONF['scale_y']
      if apply('spacing'): s.spacing = CONF['spacing']
      if apply('angle'): s.angle = CONF['angle']

      if apply('border_style'): s.border_style = CONF['border_style']
      if apply('outline'): s.outline = CONF['outline']
      if apply('shadow'): s.shadow = CONF['shadow']

      if apply('alignment'): s.alignment = CONF['alignment']
      if apply('margin_l'): s.margin_l = CONF['margin_l']
      if apply('margin_r'): s.margin_r = CONF['margin_r']
      if apply('encoding'): s.encoding = CONF['encoding']

      if color_apply('primary_color'): 
        s.primary_color.r = CONF['primary_color'][0]
        s.primary_color.g = CONF['primary_color'][1]
        s.primary_color.b = CONF['primary_color'][2]
        s.primary_color.a = CONF['primary_color'][3]
      if color_apply('secondary_color'): 
        s.secondary_color.r = CONF['secondary_color'][0]
        s.secondary_color.g = CONF['secondary_color'][1]
        s.secondary_color.b = CONF['secondary_color'][2]
        s.secondary_color.a = CONF['secondary_color'][3]
      if color_apply('outline_color'): 
        s.outline_color.r = CONF['outline_color'][0]
        s.outline_color.g = CONF['outline_color'][1]
        s.outline_color.b = CONF['outline_color'][2]
        s.outline_color.a = CONF['outline_color'][3]
      if color_apply('back_color'): 
        s.back_color.r = CONF['back_color'][0]
        s.back_color.g = CONF['back_color'][1]
        s.back_color.b = CONF['back_color'][2]
        s.back_color.a = CONF['back_color'][3]
      if match == "top":
        if apply('top_margin_v'): s.margin_v = CONF['top_margin_v']
      else:
        if apply('margin_v'): s.margin_v = CONF['margin_v']

  return styles


def doc_update_styles(doc, subsets, CONF):
  #replace font subsets
  def matching(x, strList):
    for str in strList:
      if str in x: return str
    return False

  if subsets:
    for s in doc.styles:
      match = matching(s.fontname, list(subsets.keys()))
      if match:
        s.fontname = subsets[match]

  doc.sections['Script Info']['LayoutResX'] = doc.info['PlayResX']
  doc.sections['Script Info']['LayoutResY'] = doc.info['PlayResY']
  doc.styles = update_styles(doc.styles, CONF) #update styles

  return doc


def doc_strip_styles(doc, CONF):
  # strip styles
  def matching(x):
    x = x.lower()
    for str in CONF["strip_style"]:
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

def regexOps(lines, handle_ruby, dont_replace_line):
  res = []
  for i in range(len(lines)):
    if handle_ruby and r'\fscx50\fscy50' in lines[i]:
      lines[i] = re.sub(r'\\fscx50\\fscy50(\\fsp\d*)?', fr'\\fscx50\\fscy50\\fsp{handle_ruby}', lines[i], count=1)
      lines[i+1] = re.sub(r'(\\fsp\d*)?}', fr'\\fsp{handle_ruby}' + '}', lines[i+1], count=1)
      # lines[i] = lines[i].replace(r'\fscx50\fscy50', fr'\fscx50\fscy50\fsp{handle_ruby}', 1)
      # lines[i+1] = lines[i+1].replace('}', fr'\fsp{handle_ruby}' + '}', 1)
    for set in CONF['replace_line']:
      if dont_replace_line and CONF['dont_replace_line'] in lines[i]:
        continue
      lines[i] = re.sub(set[0], set[1], lines[i])
    res.append(lines[i])

  return res

def doc_trim_end(doc, timedelta):
  trim_line = False
  for i in range(len(doc.events)-1):
    # print(f"Start: {doc.events[i].start}")
    # print(f"End: {doc.events[i].end}")
    difference = abs(doc.events[i+1].start-doc.events[i].end)
    sec_difference = difference.total_seconds()
    if sec_difference > timedelta:
      print(f"Diff(sec): {sec_difference}")
      trim_line = i+1
      break
  
  if trim_line:
    for i in range(trim_line, len(doc.events)):
      doc.events[i].style = 'DELETE'

  doc.events = list(filter(lambda x: x.style != 'DELETE', doc.events))

  return doc