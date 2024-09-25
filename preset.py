############ DEFAULTS ############

MODE = {
  'CN': {
    "skip_mkv_track": ["cht", "tc", "繁"], #skips extracting traditional chinese tracks
    "strip_style": ["cn", "ch", "zh", "sc", "tc", "sign", "staff", "credit", "note", "screen", "title", "comment", "ruby", "furi", "scr", "cmt", "info", "next episode", "stf"],
    "apply_style": ["dial", "text", "bottom", "down", "top", "up"],
    "top_style": ["2", "top", "up"],
    "skip_style": ["op", "ed"],
    "old_lang_tag": "CHS",
    "new_lang_tag": "JPN",
    'append_filename': "",
  },
  'simple': {
    "skip_mkv_track": [],
    "strip_style": [],
    "apply_style": [],
    "top_style": [],
    "skip_style": [],
    'append_filename': "[EDIT]",
  }
}

CONF = {
  'mode': "CN",
  'extract': True,
  'lineops': True,
  'linebreak': False,
  'upload': False,
  'normalize_filename': True,
  'parse_subset': True,
}

############ USER CONFIG ############

PRESET = {
  'encoded': {
    'mode': 'TS',
  },
  '[Nekomoe kissaten&LoliHouse] Monogatari Series - Off & Monster Season': {
    'fontsize': 80,
    'margin_v': 54,
    'upload': True,
    'jimaku_id': 6152,
  },
  '[Billion Meta Lab]': {
    'fontsize': 80,
    'margin_v': 54,
    'chinese': "CHT",
    'outline': 3,
    'extract': False,
  },
  'example': {
    'fontsize': None,
    'margin_v': None,
    'top_margin_v': None,
    'strip_dialogue': ["^0.*$", "^8.*$"], #NOTE: "Dialogue: " is not included in the dump
    'replace_line': [["Style: Jp.*", "Style: Jp,Droid Sans Fallback,75,&H00FFFFFF,&H00FFFFFF,&H00A766FF,&H64FFFFFF,-1,0,0,0,100,100,1.5,0,1,3,4.5,2,15,15,30,1"]],
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
    'fontsize': 80,
    'margin_v': 54,
    'spacing': 0.0,
    'primary_color': [0, 0, 0, 0],
    # 'jimaku_id': 2059,
    # 'strip_dialogue': ["^.*,LIVE,.*$"],
    # 'replace_line': [["Style: JP.*", "Style: Jp,Droid Sans Fallback,75,&H00FFFFFF,&H00FFFFFF,&H00A766FF,&H64FFFFFF,-1,0,0,0,100,100,1.5,0,1,3,4.5,2,15,15,30,1"]],
    # 'chinese': "CHS",
    'extract': True,
    'linefixes': True,
    'mode': 'CN',
    'upload': False,
    # 'strip_style': ["text"],
  }
}

# Only used for uploading
JIMAKU_API_KEY = ''

# Only used for extracting (r needs to be in front of the quotes)
PATH_TO_FFPROBE= r"" #Ex: r"C:\<insert>\ffmpeg\bin\ffprobe.exe"
PATH_TO_MKVEXTRACT= r"" #Ex: r"C:\Program Files\MKVToolNix\mkvextract.exe"