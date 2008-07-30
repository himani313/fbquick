import sys

class FBQuickStream:
  softspace = 0
  _file = None
  _error = None
  def write(self, text, fname=sys.executable+'.log'):
    if self._file is None and self._error is None:
      try:
        self._file = open(fname, 'a')
      except Exception, details:
        self._error = details

    if self._file is not None:
      self._file.write(text)
      self._file.flush()

  def flush(self):
    if self._file is not None:
      self._file.flush()

