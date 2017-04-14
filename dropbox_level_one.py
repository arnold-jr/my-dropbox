#!/usr/bin/env python
# coding: utf-8

import os
import configparser
import argparse
import logging
import dropbox
from dropbox.files import get_metadata

def worker_copy_fun(source, dbx_fun, src_prefix, tgt_prefix):
  """Copy from Dropbox to local
  
  Args:
    dbx -- dropbox instance
    source Iter(str) -- iterable of strings of Dropbox absolute path
    src (str) -- Dropbox absolute parent path
    tgt (str) -- Destination parent string
  """


class MyDropbox(dropbox.Dropbox):

  def get_dbx_file_list(self, dbx_path):
    files = []
    try:
      result = self.files_list_folder(dbx_path, recursive=True)
    except dropbox.exceptions.ApiError:
      return []

    files += result.entries
    while result.has_more:
      result = self.files_list_folder_continue(result.cursor)
      files += result.entries

    return [f.path_lower for f in files
            if isinstance(f, dropbox.dropbox.files.FileMetadata)
            ]

  def dirs_download_to_file(self, src, target, filt=lambda s: True):
    sources = self.get_dbx_file_list(src)
    logging.debug(sources)
    logging.debug("Number of files: {0}".format(len(sources)))

    for source in filter(filt, sources):
      t = source.replace(src, target)
      if not os.path.exists(t):
        os.makedirs(os.path.dirname(t), exist_ok=True)
        meta = self.files_download_to_file(t, source)

  def dirs_upload(self, source_parent, target_parent,
                  filt=lambda s: True, recurse=True):
    """Copy all files in a local directory to Dropbox
    
    Args:
      source_parent (str) -- local path to copy
      target_parent (str) -- Dropbox absolute path to copy
      filt (fun) -- filtering function for paths
      recurse (bool) -- recursively traverse all children of source_parent
    """

    # Keep list of files already present on Dropbox
    target_cache = self.get_dbx_file_list(target_parent)

    for i, p in enumerate(target_cache):
      print(p)
      if i > 10:
        break

    chunk_size = 149000000
    for root, dirs, files in os.walk(source_parent):
      target_prefix = os.path.join(target_parent,
                                   os.path.relpath(root, source_parent))

      for file in filter(filt, files):
        source_path = os.path.join(root, file)
        target_path = os.path.join(target_prefix, file)
        logging.info(source_path + ' --> ' + target_path)

        if target_path.lower() in target_cache:
          logging.info("Target path already present ({0})".format(target_path))
          continue

        with open(source_path, 'rb') as f:
          binary_file = f.read()
          file_size = len(binary_file)

          if file_size >= chunk_size:
            continue
            counter = 0
            result = self.files_upload_session_start(binary_file)
            while counter < file_size:
              cursor = files.UploadSessionCursor(result.session_id, counter)
              self.files_upload_session_append_v2(binary_file, cursor)
              counter += chunk_size
          else:
            self.files_upload(f.read(), target_path)



def read_config():
  config = configparser.ConfigParser()
  config.read(os.path.expandvars("$HOME/.secrets/dropbox-env.ini.nogit"))
  access_token = config['DEFAULT']['DROPBOX_ACCESS_TOKEN']
  return access_token

  # dbx.dirs_download_to_file(args.src, args.tgt)

def get_dbx():
  return MyDropbox(read_config())

def test_dbx_dirs_upload():
  dbx = get_dbx()
  dbx.dirs_upload('/Volumes/storage/amenidc',
                  '/storage-mirror/amenidc')



if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Extends dropbox modulefunctionality.')

  parser.add_argument('src', type=str,
                      help='source path on Dropbox')
  parser.add_argument('tgt', type=str,
                      help='target path on Client')

  parser.add_argument('direction', type=str,
                      choices=['up','down'],
                      help='target path on Client')

  args = parser.parse_args()

  logging.basicConfig(level=logging.DEBUG)

  dbx = get_dbx()
  if args.direction == 'up':
    dbx.dirs_upload(args.src, args.tgt)
  elif args.direction == 'down':
    dbx.dirs_download_to_file(args.src, args.tgt)


