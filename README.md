# Jimaku Subtitle Updater  



A script to adjust dual language subtitle files from Chinese fansub groups.

  

## Usage

### Command-line Arguments

    subhandle.py <folder path>
   
| Option | Description |
|--|--|
| \<folder path\> | Defaults to the parent folder of `subhandle.py` 
| -p, --preset | Defaults to the name of \<folder path\>.
| -s, --strict | Makes the script immediately quit if no `ignore.conf` file is found in the folder. Writes a log to `upload.log`. When extract is true, do not extract any files specified by `ignore.conf` and append the names of any extracted `.mkv` files to `ignore.conf`.
 

### CONF, MODE, and PRESET

These are specified in `preset.py`. CONF specifies the default options. Selecting a MODE makes its options override CONF. Selecting a PRESET makes its options override CONF and MODE. There are options specific to MODE: CN.

### Extraction
Extract subs from every `.mkv` file in the folder using mkvextract and ffprobe for stream info.

| Option | Description |
|--|--|
| skip_mkv_track | (string array): If any value has a partial match in the track name, the track is skipped for extracting.
| normalize_filename | (boolean): Names of extracted files will have full-width characters converted to half-width ones. Forbidden characters in filenames are handled as `{'<': '＜', '>': '＞', ':': ' - ', '/': '／', '\\': '＼', '|': '｜', '?': '？', '*': ''}`.


### Update Lines
Apply style changes and line replacements to every `.ass` file in the folder. If the output filename is the same as an existing file in the folder, that file will be overwritten.

#### Output Filename
| Option | Description |
|--|--|
| append_filename | (string): Append the value to the output filename.
| old_lang_tag | (string): (CN only) The file without updated lines is appended with [old_lang_tag, new_lang_tag], while a second file with them is appended with [new_lang_tag].
| new_lang_tag | (string): (CN only) The file without updated lines is appended with [old_lang_tag, new_lang_tag], while a second file with them is appended with [new_lang_tag].

####  Line Replacements
| Option | Description |
|--|--|
| strip_style | (string array): If any value has a partial match in the style name, every line of the style is stripped from the file.
| strip_dialogue | (string array, regex): If any regex pattern has a match in the line, the line is stripped from the file.
| replace_line | (array of string arrays, regex): For each sub-array, the first element specifies a regex pattern and the second element specifies what to replace *each* pattern match with in the line.
| 

#### Restyling
| Option | Description |
|--|--|
| apply_style | (string array): If any value has a partial match in the style name, apply changes to the style.
| top_style | (string array): If any value has a partial match in the style name for a style that is already going to be changed, apply top_margin_v instead of margin_v.
| skip_style | (string array): If any value has a partial match in the style name, don't apply changes to the style (overrides apply_style).
| fontsize, fontname, bold, italic, underline, strike_out, scale_x, scale_y, spacing, angle, outline, shadow, alignment, margin_l, margin_r, encoding | (string or numeric): Update the corresponding style field.
| primary_color, secondary_color, outline_color, back_color | (array of four numbers): Update the corresponding style field. Value is specified by RGBA color values in an array.
| margin_v, top_margin_v | See top_style.


  

## Install

  
```

git clone https://github.com/Ulidtsoa01/Jimaku-Subtitle-Updater.git

cd Jimaku-Subtitle-Updater

pip install -r requirements.txt

```
  

## Setup


1. (Extract only) Install MKVToolNix and add mkvextract (`C:\Program Files\MKVToolNix`) to path or fill in `PATH_TO_FFPROBE` in `preset.py`

2. (Extract only) Install ffmpeg and add ffprobe (`ffmpeg\bin`) to path or fill in `PATH_TO_MKVEXTRACT` in `preset.py`

3. Replace `<Insert path to subhandle.py file here>` in `subhandle.bat`
