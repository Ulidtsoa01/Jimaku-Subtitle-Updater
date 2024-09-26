import aiohttp
import logging
from preset import *
from utils import *

log = logging.getLogger(__name__)


############ UPLOAD ############

async def upload(output_dir_path, jimaku_id, jimaku_api_key):
  subs = [f for f in output_dir_path.iterdir() if f.suffix == ".srt" or f.suffix == ".ass"]
  if len(subs) == 0:
    log.error(f"No subs to upload")
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
  # res = None
  async with aiohttp.ClientSession() as session:
    try:
      async with session.post(url, data=files, headers=headers) as res:
          if res.status == 200:
            data = await res.json()
            log.info(f"Upload response:\n{data}")
            if data["errors"] > 0:
              status = "failed"
              log.warning(f"An error occurred during the upload")
            else:
              status = "uploaded"
              log.info("Upload succeeded")
          else:
            log.error(f"Status Code: {res.status}")
            log.error(f"Response: {res}")
    except aiohttp.ClientConnectorError as e:
      status = "failed"
      log.error('Connection Error', str(e))

  for sub in subs:
    files[sub.name].close()

  new_folder = output_dir_path.joinpath(status)
  new_folder.mkdir(exist_ok=True)
  for sub in subs:
    sub.replace(new_folder / sub.name)
