PRESET = {
  'encoded': {
    'mode': 'TS'
  },
  '[Nekomoe kissaten&LoliHouse] Monogatari Series - Off & Monster Season': {
    'fsize': 80,
    'vertical': 54,
    'upload': True,
    'jimaku_id': 6152,
  },
  '[Billion Meta Lab]': {
    'fsize': 80,
    'vertical': 54,
    'chinese': "CHT",
    'outline': 3,
    'extract': False,
  },
  'example': {
    'fsize': None,
    'fname': None,
    'outline': None,
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
    'NORMAL_STYLE': ["default"]
  },
  '.extract': {
    'fsize': 80,
    'vertical': 54,
    'spacing': 0.0,
    # 'jimaku_id': 2059,
    # 'strip_dialogue': ["^.*,LIVE,.*$"],
    # 'replace_line': [["Style: JP.*", "Style: Jp,Droid Sans Fallback,75,&H00FFFFFF,&H00FFFFFF,&H00A766FF,&H64FFFFFF,-1,0,0,0,100,100,1.5,0,1,3,4.5,2,15,15,30,1"]],
    # 'chinese': "CHS",
    'extract': False,
    'linefixes': True,
    'mode': 'CN',
    'upload': False,
    'STRIP_STYLES': ["text"],
    'NORMAL_STYLE': ["jp"],
  }
}
JIMAKU_API_KEY = ''