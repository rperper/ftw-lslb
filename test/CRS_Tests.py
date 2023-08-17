from subprocess import TimeoutExpired
from ftw import logchecker, testrunner, http
from ftw.ruleset import Input
import pytest
import os

CRS_HEADER = 'X-CRS-Test'

def test_crs(test, logchecker_obj):
    runner = testrunner.TestRunner()
    for stage in test.stages:
        runner.run_stage(stage, logchecker_obj)


class LSLogChecker(logchecker.LogChecker):
    def __init__(self, config):
        super(LSLogChecker, self).__init__()
        self.log_location = self.find_log_location(config)
        self.backwards_reader = BackwardsReader(self.log_location)
        print('Log location: %s'%self.log_location)
        self.start_marker = None
        self.end_marker = None

    def mark_start(self, stage_id):
        self.start_marker = self.find_marker(stage_id)

    def mark_end(self, stage_id):
        self.end_marker = self.find_marker(stage_id)

    def find_marker(self, stage_id):
        stage_id_bytes = stage_id.encode('utf-8')
        header_bytes = CRS_HEADER.encode('utf-8')
        def try_once():
            # self.mark_and_flush_log(stage_id)
            self.backwards_reader.reset()
            return self.backwards_reader.readline() or b''
            
        line = try_once()
        #print('find_marker entry line: %s'%line)
        # while not (header_bytes in line and stage_id_bytes in line):
        #     line = try_once()
        return line

    def get_logs(self):
        logs = []
        # At this point we're already at the end marker
        for line in self.backwards_reader.readlines():
            if line == self.start_marker:
                break

            logs.append(line.decode('cp1252'))
        return logs

    def mark_and_flush_log(self, header_value):
        """
        Send a valid request to the server with a special header that will
        generate an entry in the log. We can use this to flush the log and to
        mark the output so we know where our test output is.
        """
        print('mark_and_flush_log, header_value: %s'%header_value)
        http.HttpUA().send_request(Input(
            headers={
                'Host': 'localhost',
                'User-Agent': 'CRS',
                'Accept': '*/*',
                CRS_HEADER: header_value
            },
            version='HTTP/1.0'))

    @staticmethod
    def find_log_location(config):
        key = 'log_location_linux' 
        # First, try to find the log configuration from config.ini
        if key in config:
            return config[key]
        else:
            # Now we could check for the configuration that was passed
            # on the command line. Unfortunately, we use a default, so we
            # don't know whether it was *actually* on the command line.
            # Let's try to find the Docker container instead.
            import os.path
            import subprocess
            prefix = os.path.join('tests', 'logs')
            log_file_name = 'error.log'
            directory_name = '/usr/local/lslb/logs'
            process = subprocess.Popen(
                'docker ps --format "{{.Names}}"',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            try:
                out, _ = process.communicate(timeout=10)
            except TimeoutExpired:
                out = ''
            return os.path.join(prefix, directory_name, log_file_name)



@pytest.fixture(scope='session')
def logchecker_obj(config):
    return LSLogChecker(config)

# Adapted from https://stackoverflow.com/questions/2301789/how-to-read-a-file-in-reverse-order
class BackwardsReader:
  def __init__(self, file, blksize=4096):
    """initialize the internal structures"""
    self.file = file
    # how big of a block to read from the file...
    self.blksize = blksize
    self.f = open(file, 'rb')
    self.reset()

  def readline(self):
      while self.remaining_size > 0:
          offset = min(self.size, offset + self.blksize)
          self.f.seek(self.size - offset)
          buffer = self.f.read(min(self.remaining_size, self.blksize)).decode('cp1252')
          self.remaining_size -= self.blksize
          lines = buffer.split('\n')
          # The first line of the buffer is probably not a complete line so
          # we'll save it and append it to the last line of the next buffer
          # we read
          if segment is not None:
              # If the previous chunk starts right from the beginning of line
              # do not concat the segment to the last line of new chunk.
              # Instead, yield the segment first
              if buffer[-1] != '\n':
                  lines[-1] += segment
              else:
                  yield segment
          segment = lines[0]
          for index in range(len(lines) - 1, 0, -1):
              if lines[index]:
                  yield lines[index]
      # Don't yield None if the file was empty
      if segment is not None:
          yield segment

  def readlines(self):
      line = self.readline()
      while line:
          yield line
          line = self.readline()
        
  def reset(self):
    # get the file size
    self.f.seek(0, os.SEEK_END)
    self.size = self.remaining_size = self.f.tell()
    self.segment = None
