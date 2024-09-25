import requests
import asyncio
from preset import *
from utils import *

############ UPLOAD ############

async def upload(output_dir_path, jimaku_id, jimaku_api_key):
  subs = [f for f in output_dir_path.iterdir() if f.suffix == ".srt" or f.suffix == ".ass"]
  if len(subs) == 0:
    log(f"No subs to upload")
    exit(1)
  url = fr"https://jimaku.cc/api/entries/{jimaku_id}/upload"
  headers = {
      # 'Content-Type': "multipart/form-data",
      'Authorization': jimaku_api_key
  }
  files = {}
  for sub in subs:
    files[sub.name] = open(sub.name, 'rb')
  status = "nothing"
  res = None
  try:
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, lambda: requests.post(url, files=files, headers=headers))
    # res = requests.post(url, files=files, headers=headers)
    if res:
      data = res.json()
      log(f"Upload response:\n{data}")
      if data["errors"] > 0:
        status = "failed"
        log(f"An error occurred during the upload")
      else:
        status = "uploaded"
        log("Upload succeeded")
    else:
      status = "failed"
      log(f"No response")
  except requests.exceptions.RequestException:
    status = "failed"
    log('HTTP Request failed')
    log(f"Status Code: {res.status_code}")
    log(f"RES: {res}")
  
  for sub in subs:
    files[sub.name].close()

  new_folder = output_dir_path.joinpath(status)
  new_folder.mkdir(exist_ok=True)
  for sub in subs:
    sub.rename(new_folder / sub.name)
