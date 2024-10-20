# NOTE: use r-strings (r"") if you have backslashes in your values.

############ DEFAULTS ############

MODE = {
  'CN': {
    'extract': True,
    "skip_mkv_track": ["cht", "tc", "繁"], #skips extracting traditional chinese tracks
    "strip_style": ["cn", "ch", "zh", "sc", "tc", "sign", "staff", "credit", "note", "screen", "title", "comment", "ruby", "furi", "scr", "cmt", "info", "next episode", "stf", "注释"],
    "apply_style": ["dial", "text", "bottom", "down", "top", "up"],
    "top_style": ["2", "top", "up"],
    # "skip_style": ["op", "ed"],
    "old_lang_tag": "CHS",
    "new_lang_tag": "JPN",
    'append_filename': "",
  },
  'simple': {
    'append_filename': "[EDIT]",
  },
  'TV': {
    'extract': True,
    # 'handle_ruby': 4, #if \fscx50\fscy50 is present on a line, add \fsp4 to the current and following line
    # 'replace_line': [["Style: Default.*", "Style: Default,A-OTF Maru Folk Pro B,42,&H00FFFFFF,&H000000FF,&H00000000,&H7F000000,-1,0,0,0,100,100,0,0,1,2,2,1,0,0,0,1\n"],
    #                   [r"\\fsc[xy][15]00?", ""],
    #                 ],
    # 'dont_replace_line': '\\fsp'
  },
  'do_nothing': {
    'update_lines': False,
    'normalize_filename': False,
    'parse_subset': False,
  },
}

CONF = {
  'mode': "CN",
  'update_lines': True,
  'linebreak': False,
  'extract': False,
  'upload': False,
  'normalize_filename': True,
  'parse_subset': True,
  "skip_mkv_track": [],
  "strip_style": [],
  "apply_style": [],
  "top_style": [],
  "skip_style": [],
  "new_linebreak_file": True,
  "redo_linebreak": False,
  "debug_linebreak": 0,
  "min_length": 18,
  "max_length": 18,
  "max_ratio": 2.4,
}

############ USER PRESETS ############

PRESET = {
  'encoded': {
    'mode': 'TV',
    'trim_end': 180,
  },
  'uploadonly': {
    'mode': 'do_nothing',
  },
  '[Nekomoe kissaten&LoliHouse] Monogatari Series - Off & Monster Season': {
    'fontsize': 80,
    'margin_v': 54,
    'outline': 3.5,
    'upload': True,
    'jimaku_id': 6152,
  },
  '[Billion Meta Lab]': {
    'fontsize': 80,
    'margin_v': 54,
    'outline': 3,
    'extract': False,
  },
  'example': {
    'fontsize': None,
    'margin_v': None,
    'top_margin_v': None,
    'strip_dialogue': ["^0.*$", "^8.*$"], #NOTE: "Dialogue: " is not included in the dump
    'replace_line': [["Style: Default.*", "Style: Default,A-OTF Maru Folk Pro B,42,&H00FFFFFF,&H000000FF,&H00000000,&H7F000000,-1,0,0,0,100,100,0,0,1,2,2,1,0,0,0,1\n"]],
    'extract': True,
    'mode': 'CN',
    'upload': False,
    'jimaku_id': 0,
    'chinese': "CHS",
    'strip_style': ["op", "ed", "dorama", "default"],
    'apply_style': ["default"],
    'primary_color': [0, 0, 0, 0],
  },
  '.extract': {
    'mode': 'CN',
    # 'fontsize': 36,
    # 'margin_v': 50,
    # 'spacing': 0.0,
    # 'primary_color': [0, 0, 0, 0],
    # 'top_margin_v': 99,
    # 'strip_style': ["歌cn"],
    # 'strip_dialogue': ["^.*,LIVE,.*$"],
    # 'replace_line': [["Style: Default.*", "Style: Jp,Droid Sans Fallback,75,&H00FFFFFF,&H00FFFFFF,&H00A766FF,&H64FFFFFF,-1,0,0,0,100,100,1.5,0,1,3,4.5,2,15,15,30,1"]],
    # 'chinese': "CHS",
    'extract': False,
    'update_lines': True,
    'linebreak': True,
    "new_linebreak_file": True,
    "redo_linebreak": True,
    "debug_linebreak": 2,
    # 'jimaku_id': 1,
    'upload': False,
  },
}

# Only used for uploading
JIMAKU_API_KEY = ''

# Only used for extracting (r needs to be in front of the quotes)
PATH_TO_FFPROBE= r"" #Ex: r"C:\<insert>\ffmpeg\bin\ffprobe.exe"
PATH_TO_MKVEXTRACT= r"" #Ex: r"C:\Program Files\MKVToolNix\mkvextract.exe"