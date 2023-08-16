import pytest
from ftw import testrunner, errors

def test_lslb(ruleset, test):
      runner = testrunner.TestRunner()
      for stage in test.stages:
          runner.run_stage(stage)
