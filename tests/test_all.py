from twisted.trial.runner import TrialRunner, TrialSuite
from twisted.trial.reporter import TreeReporter

from test_common import *

def run_tests():
    suite = TrialSuite()
    suite.addTest(CommonTestCase())

    runner = TrialRunner(TreeReporter)
    runner.run(suite)

if __name__ == '__main__':
    run_tests()
