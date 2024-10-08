import aiohttp
from aiohttp import FormData
import logging
from preset import *
from utils import *
from pathlib import Path

log = logging.getLogger(__name__)


############ UPLOAD ############

async def upload(output_dir_path, jimaku_id, jimaku_api_key, status_dir_path):
  subs = [f for f in output_dir_path.iterdir() if f.suffix == ".srt" or f.suffix == ".ass"]
  if len(subs) == 0:
    log.error(f"No subs to upload")
    exit(1)
  url = fr"https://jimaku.cc/api/entries/{jimaku_id}/upload"
  headers = {
      # 'Content-Type': "multipart/form-data",
      'Authorization': jimaku_api_key
  }
  # files = {}
  # for sub in subs:
  #   files[sub.name] = open(sub.name, 'rb')
  status = "nothing"
  formdata = FormData(quote_fields=False)
  for sub in subs:
    formdata.add_field('file', open(sub.name, 'rb'), filename=sub.name)
  async with aiohttp.ClientSession() as session:
    try:
      async with session.post(url, data=formdata, headers=headers) as res:
          if res.status == 200:
            data = await res.json()
            log.info(f"Upload response:\n{data}")
            if data["errors"] > 0:
              status = "upload_failed"
              log.warning(f"An error occurred during the upload")
            else:
              status = "upload_succeeded"
              log.info("Upload succeeded")
          else:
            log.error(f"Status Code: {res.status}")
            log.error(f"Response: {res}")
    except aiohttp.ClientConnectorError as e:
      status = "upload_failed"
      log.error('Connection Error', str(e))
  if status == "nothing":
    log.error('Failed Request')
    status = "upload_failed"

  # for sub in subs:
  #   files[sub.name].close()
  if not status_dir_path:
    status_dir_path = output_dir_path

  status_dir_path = Path(status_dir_path)
  new_folder = status_dir_path.joinpath(status)
  new_folder.mkdir(exist_ok=True)
  for sub in subs:
    sub.replace(new_folder / sub.name)
