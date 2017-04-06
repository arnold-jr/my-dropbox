#!/usr/bin/env python
# coding: utf-8

import os
import configparser
import argparse
import logging
import dropbox

def worker_copy_fun(source, dbx_fun, src_prefix, tgt_prefix):
  """Copy from Dropbox to local
  
  Args:
    dbx -- dropbox instance
    source Iter(str) -- iterable of strings of Dropbox absolute path
    src (str) -- Dropbox absolute parent path
    tgt (str) -- Destination parent string
  """


class MyDropbox(dropbox.Dropbox):

  def dirs_download_to_file(self, src, target, filt=lambda s: True):
    files = []
    result = self.files_list_folder(src, recursive=True)
    files += result.entries
    while result.has_more:
      result = self.files_list_folder_continue(result.cursor)
      files += result.entries

    logging.debug(files)
    logging.debug("Number of files: {0}".format(len(files)))

    sources = filter(filt,
      (f.path_lower for f in files
       if isinstance(f, dropbox.dropbox.files.FileMetadata)
       )
    )
    for source in sources:
      t = source.replace(src, target)
      if not os.path.exists(t):
          os.makedirs(os.path.dirname(t), exist_ok=True)
          meta = dbx.files_download_to_file(t, source)

  def dirs_upload(self, source_parent, target_parent,
                  filt=lambda s: True, recurse=True):
    """Copy all files in a local directory to Dropbox
    
    Args:
      source_parent (str) -- local path to copy
      target_parent (str) -- Dropbox absolute path to copy
      filt (fun) -- filtering function for paths
      recurse (bool) -- recursively traverse all children of source_parent
    """

    for root, dirs, files in os.walk(source_parent):
      target_path = os.path.join(target_parent,
                                 os.path.relpath(root, source_parent))
      for file in files:
        print(os.path.join(root,file), ' --> ', os.path.join(target_path, file))



if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Extends dropbox modulefunctionality.')

  parser.add_argument('src', metavar='S', type=str,
                      help='source path on Dropbox')
  parser.add_argument('tgt', metavar='T', type=str,
                      help='target path on Client')

  args = parser.parse_args()

  logging.basicConfig(filename='log.log', level=logging.DEBUG)

  config = configparser.ConfigParser()
  config.read(os.path.expandvars("$HOME/.secrets/dropbox-env.ini.nogit"))
  access_token = config['DEFAULT']['DROPBOX_ACCESS_TOKEN']

  dbx = MyDropbox(access_token)
  # dbx.dirs_download_to_file(args.src, args.tgt)
  dbx.dirs_download_to_file('/Volumes/storage/cs4266', '/storage-mirror/cs4266')
