#!/usr/bin/env python
# coding: utf-8

import os
import configparser
import argparse
import logging
import progressbar
import dropbox
from functools import partial
from pathos.multiprocessing import Pool

BAR = progressbar.ProgressBar()




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

    f = partial(self.worker_copy_fun, src=src, tgt=target)

    if 1:
      p = Pool()
      p.map(f, sources)
    else:
      for s in filter(filt, BAR(sources)):
        f(s)

  def worker_copy_fun(self, source, src, tgt):
    """Copy from Dropbox to local
    
    Args:
      source (str) -- Dropbox absolute path
      src (str) -- Dropbox absolute parent path
      tgt (str) -- Destination parent string
    """

    t = source.replace(src, tgt)
    print(source + " -> " + t)
    return

    if not os.path.exists(t):
      os.makedirs(os.path.dirname(t), exist_ok=True)
      meta = dbx.files_download_to_file(t, source)


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
  config.read("../secrets/dropbox-env.ini.nogit")
  access_token = config['DEFAULT']['DROPBOX_ACCESS_TOKEN']

  dbx = MyDropbox(access_token)
  dbx.dirs_download_to_file(args.src, args.tgt)
