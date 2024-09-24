############ DEFAULTS ############

MODE = {
  'CN': {
    "SKIP_MKV_TRACK": ["cht", "tc", "繁"], #skips extracting traditional chinese tracks
    "STRIP_STYLES": ["cn", "ch", "zh", "sc", "tc", "sign", "staff", "credit", "note", "screen", "title", "comment", "ruby", "furi", "scr", "cmt", "info", "next episode", "stf"],
    "APPLY_STYLE": ["dial", "text", "bottom", "down", "top", "up"],
    "TOP_STYLE": ["2", "top", "up"],
    "SKIP_STYLE": ["op", "ed"],
    "OLD_LANG_TAG": "CHS",
    "NEW_LANG_TAG": "JPN",
    'append_filename': "",
  },
  'simple': {
    "SKIP_MKV_TRACK": [],
    "STRIP_STYLES": [],
    "APPLY_STYLE": [],
    "TOP_STYLE": [],
    "SKIP_STYLE": [],
    'append_filename': "[EDIT]",
  }
}

CONF = {
  'mode': "CN",
  'extract': True,
  'lineops': True,
  'linebreak': False,
  'upload': False,
}

############ USER CONFIG ############

PRESET = {
  'encoded': {
    'mode': 'TS'
  },
  '[Nekomoe kissaten&LoliHouse] Monogatari Series - Off & Monster Season': {
    'fontsize': 80,
    'vertical': 54,
    'upload': True,
    'jimaku_id': 6152,
  },
  '[Billion Meta Lab]': {
    'fontsize': 80,
    'vertical': 54,
    'chinese': "CHT",
    'outline': 3,
    'extract': False,
  },
  'example': {
    'fontsize': None,
    'vertical': None,
    'vertical_top': None,
    'strip_dialogue': ["^0.*$", "^8.*$"], #NOTE: "Dialogue: " is not included in the dump
    'replace_line': [["Style: Jp.*", "Style: Jp,Droid Sans Fallback,75,&H00FFFFFF,&H00FFFFFF,&H00A766FF,&H64FFFFFF,-1,0,0,0,100,100,1.5,0,1,3,4.5,2,15,15,30,1"]],
    'extract': True,
    'mode': 'CN',
    'upload': False,
    'jimaku_id': 0,
    'chinese': "CHS",
    'STRIP_STYLES': ["op", "ed", "dorama", "default"],
    'NORMAL_STYLE': ["default"],
    'primary_color': [0, 0, 0, 0],
  },
  '.extract': {
    'fontsize': 80,
    'vertical': 54,
    'spacing': 0.0,
    'primary_color': [0, 0, 0, 0],
    # 'jimaku_id': 2059,
    # 'strip_dialogue': ["^.*,LIVE,.*$"],
    # 'replace_line': [["Style: JP.*", "Style: Jp,Droid Sans Fallback,75,&H00FFFFFF,&H00FFFFFF,&H00A766FF,&H64FFFFFF,-1,0,0,0,100,100,1.5,0,1,3,4.5,2,15,15,30,1"]],
    # 'chinese': "CHS",
    'extract': True,
    'linefixes': True,
    'mode': 'simple',
    'upload': False,
    # 'STRIP_STYLES': ["text"],
    # 'NORMAL_STYLE': ["jp"],
  }
}

# Only used for uploading
JIMAKU_API_KEY = ''

# Only used for extracting (r needs to be in front of the quotes)
PATH_TO_FFPROBE= r"" #Ex: r"C:\<insert>\ffmpeg\bin\ffprobe.exe"
PATH_TO_MKVEXTRACT= r"" #Ex: r"C:\Program Files\MKVToolNix\mkvextract.exe"