# Jimaku Subtitle Updater

A script to adjust dual language subtitle files from Chinese fansub groups.

## Usage

CN mode renames files.

## Install

```
git clone https://github.com/Ulidtsoa01/Jimaku-Subtitle-Updater.git
cd Jimaku-Subtitle-Updater
pip install -r requirements.txt
```

## Setup

1. Install MKVToolNix and add mkvextract (`C:\Program Files\MKVToolNix`) to path or fill in `PATH_TO_FFPROBE` in `preset.py`
2. Install ffmpeg and add ffprobe (`ffmpeg\bin`) to path or fill in `PATH_TO_MKVEXTRACT` in `preset.py`
3. Replace `<Insert path to subhandle.py file here>` in `subhandle.bat`
