from preset import *
import re

def apply(confField):
  if confField in CONF and (CONF[confField] or CONF[confField] is 0):
    return True
  return False

def update_styles(styles):
  def matching(x):
    for es in CONF["SKIP_STYLE"]:
      if es in x:
        return False
    for ns in CONF["APPLY_STYLE"]: #need to match to apply style options
      if ns in x:
        for ts in CONF["TOP_STYLE"]: #need to match to apply vertical positioning
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
        if apply('vertical_top'): s.margin_v = CONF['vertical_top']
      else:
        if apply('vertical'): s.margin_v = CONF['vertical']

  return styles

def doc_clean(doc, subsets):
  # strip styles
  def matching(x):
    x = x.lower()
    for str in CONF["STRIP_STYLES"]:
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
  doc.styles = update_styles(doc.styles) #update styles

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