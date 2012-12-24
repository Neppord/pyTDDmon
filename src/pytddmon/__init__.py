#! /usr/bin/env python
#coding: utf-8

'''
COPYRIGHT (c) 2009, 2010, 2011, 2012
.. in order of first contribution
Olof Bjarnason
    Initial proof-of-concept pygame implementation.
Fredrik Wendt
    Help with Tkinter implementation (replacing the pygame dependency)
Krunoslav Saho
    Added always-on-top to the pytddmon window
Samuel Ytterbrink
    Print(".") will not screw up test-counting (it did before)
    Docstring support
    Recursive discovery of tests
    Refactoring to increase Pylint score from 6 to 9.5 out of 10 (!)
    Numerous refactorings & other improvements
Rafael Capucho
    Python shebang at start of script, enabling "./pytddmon.py" on unix systems
Ilian Iliev
    Use integers instead of floats in file modified time (checksum calc)
    Auto-update of text in Details window when the log changes
Henrik Bohre
    Status bar in pytddmon window, showing either last time tests were
    run, or "Testing..." during a test run


LICENSE
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import os
import optparse
import sys
import re
import unittest
import doctest
import time
import multiprocessing
import fnmatch
import functools
from collections import namedtuple

from gui import TkGUI, import_tkinter, import_tk_font

ON_PYTHON3 = sys.version_info[0] == 3

####
## Core
####

Result = namedtuple(
    "Result",
    (
        "total",
        "passed",
        "time",
    )
)
class Pytddmon:
    "The core class, all functionality is combined into this class"
    def __init__(
        self,
        file_finder,
        monitor,
        project_name="<pytddmon>"
    ):
        self.file_finder = file_finder
        self.project_name = project_name
        self.monitor = monitor
        self.change_detected = False

        # This is not composition this is a functionality.
        # Since Pytddmon Class is a composer it should not have
        # the field it self.
        self.result = Result(
            total=0,
            passed=0,
            time=-1
        )
        self.log = ""
        self.status_message = 'n/a'
        # end of rant, btw pylint agreas with me!
        self.run_tests()

    def run_tests(self):
        """Runs all tests and updates state variables with results."""

        file_paths = self.file_finder()

        # We need to run the tests in a separate process, since
        # Python caches loaded modules, and unittest/doctest
        # imports modules to run them.
        # However, we do not want to assume users' unit tests
        # are thread-safe, so we only run one test module at a
        # time, using processes = 1.
        start = time.time()
        if file_paths:
            pool = multiprocessing.Pool(processes=1)
            results = pool.map(run_tests_in_file, file_paths)
            pool.close()
            pool.join()
        else:
            results = []
        run_time = time.time() - start

        now = time.strftime("%H:%M:%S", time.localtime())
        passed = 0
        total = 0
        module_logs = []  # Summary for each module with errors first
        for packed in results:
            (module, green, number_of, logtext) = packed
            passed += green
            total += number_of
            module_log = "\nLog from " + module + ":\n" + logtext
            if not isinstance(number_of, int) or total.real - green.real > 0:
                module_logs.insert(0, module_log)
            else:
                module_logs.append(module_log)
        total_tests = int(total.real)
        # logging?
        self.log = ""
        self.log += "Monitoring folder %s.\n" % self.project_name
        self.log += "Found %i tests in %i files.\n" % (
            total_tests,
            len(results)
        )
        self.log += "Last change detected at %s.\n" % now
        self.log += "Test run took %.2f seconds.\n" % run_time
        self.log += "\n"
        self.log += ''.join(module_logs)
        # /logging?
        self.status_message = now
        self.result = Result(
            total=total,
            passed=passed,
            time=run_time
        )

    def get_and_set_change_detected(self):
        self.change_detected = self.monitor.look_for_changes()
        return self.change_detected

    def main(self):
        """This is the main loop body"""
        self.change_detected = self.monitor.look_for_changes()
        if self.change_detected:
            self.run_tests()

    def get_log(self):
        """Access the log string created during test run"""
        return self.log

    def get_status_message(self):
        """Return message in status bar"""
        return self.status_message


class Monitor:
    'Looks for file changes when prompted to'

    def __init__(self, file_finder, get_file_size, get_file_modtime):
        self.file_finder = file_finder
        self.get_file_size = get_file_size
        self.get_file_modtime = get_file_modtime
        self.snapshot = self.get_snapshot()

    def get_snapshot(self):
        snapshot = {}
        for file in self.file_finder():
            file_size = self.get_file_size(file)
            file_modtime = self.get_file_modtime(file)
            snapshot[file] = (file_size, file_modtime)
        return snapshot

    def look_for_changes(self):
        new_snapshot = self.get_snapshot()
        change_detected = new_snapshot != self.snapshot
        self.snapshot = new_snapshot
        return change_detected


####
## Finding files
####

class FileFinder:
    "Returns all files matching given regular expression from root downwards"

    def __init__(self, root, regexp):
        self.root = os.path.abspath(root)
        self.regexp = regexp

    def __call__(self):
        return self.find_files()

    def find_files(self):
        "recursively finds files matching regexp"
        file_paths = set()
        for path, _folder, filenames in os.walk(self.root):
            for filename in filenames:
                if self.re_complete_match(filename):
                    file_paths.add(
                        os.path.abspath(os.path.join(path, filename))
                    )
        return file_paths

    def re_complete_match(self, string_to_match):
        "full string regexp check"
        return bool(re.match(self.regexp + "$", string_to_match))

####
## Finding & running tests
####


def log_exceptions(func):
    """Decorator that forwards the error message from an exception to the log
    slot of the return value, and also returns a complexnumber to signal that
    the result is an error."""
    wraps = functools.wraps

    @wraps(func)
    def wrapper(*a, **k):
        "Docstring"
        try:
            return func(*a, **k)
        except:
            import traceback
            return (('Exception(%s)' % a[0]), 0, 1j, traceback.format_exc())
    return wrapper


@log_exceptions
def run_tests_in_file(file_path):
    module = file_name_to_module("", file_path)
    return run_module(module)


def run_module(module):
    suite = find_tests_in_module(module)
    (green, total, log) = run_suite(suite)
    return (module, green, total, log)


def file_name_to_module(base_path, file_name):
    r"""Converts filenames of files in packages to import friendly dot
    separated paths.

    Examples:
    >>> print(file_name_to_module("","pytddmon.pyw"))
    pytddmon
    >>> print(file_name_to_module("","pytddmon.py"))
    pytddmon
    >>> print(file_name_to_module("","tests/pytddmon.py"))
    tests.pytddmon
    >>> print(file_name_to_module("","./tests/pytddmon.py"))
    tests.pytddmon
    >>> print(file_name_to_module("",".\\tests\\pytddmon.py"))
    tests.pytddmon
    >>> print(
    ...     file_name_to_module(
    ...         "/User/pytddmon\\ geek/pytddmon/",
    ...         "/User/pytddmon\\ geek/pytddmon/tests/pytddmon.py"
    ...     )
    ... )
    tests.pytddmon
    """
    symbol_stripped = os.path.relpath(file_name, base_path)
    for symbol in r"/\.":
        symbol_stripped = symbol_stripped.replace(symbol, " ")
    words = symbol_stripped.split()
    # remove .py/.pyw
    module_words = words[:-1]
    module_name = '.'.join(module_words)
    return module_name


def find_tests_in_module(module):
    suite = unittest.TestSuite()
    suite.addTests(find_unittests_in_module(module))
    suite.addTests(find_doctests_in_module(module))
    return suite


def find_unittests_in_module(module):
    test_loader = unittest.TestLoader()
    return test_loader.loadTestsFromName(module)


def find_doctests_in_module(module):
    try:
        return doctest.DocTestSuite(module, optionflags=doctest.ELLIPSIS)
    except ValueError:
        return unittest.TestSuite()


def run_suite(suite):
    def string_io():
        if ON_PYTHON3:
            import io as StringIO
        else:
            import StringIO
        return StringIO.StringIO()
    err_log = string_io()
    text_test_runner = unittest.TextTestRunner(stream=err_log, verbosity=1)
    result = text_test_runner.run(suite)
    green = result.testsRun - len(result.failures) - len(result.errors)
    total = result.testsRun

    if green < total:
        log = err_log.getvalue()
    else:
        log = "All %i tests passed\n" % green

    return (green, total, log)


def parse_commandline():
    """
    returns (files, test_mode) created from the command line arguments
    passed to pytddmon.
    """
    parser = optparse.OptionParser()
    parser.add_option(
        "--log-and-exit",
        action="store_true",
        default=False,
        help='Run all tests, write the results to "pytddmon.log" and exit.')
    (options, args) = parser.parse_args()
    return (args, options.log_and_exit)


def build_monitor(file_finder):
    os.stat_float_times(False)

    def get_file_size(file_path):
        stat = os.stat(file_path)
        return stat.st_size

    def get_file_modtime(file_path):
        stat = os.stat(file_path)
        return stat.st_mtime
    return Monitor(file_finder, get_file_size, get_file_modtime)


def run():
    """
    The main function: basic initialization and program start
    """
    cwd = os.getcwd()

    # Include current work directory in Python path
    sys.path[:0] = [cwd]

    # Command line argument handling
    (static_file_set, test_mode) = parse_commandline()

    # What files to monitor?
    if not static_file_set:
        regex = fnmatch.translate("*.py")
    else:
        regex = '|'.join(static_file_set)
    file_finder = FileFinder(cwd, regex)

    # The change detector: Monitor
    monitor = build_monitor(file_finder)

    # Python engine ready to be setup
    pytddmon = Pytddmon(
        file_finder,
        monitor,
        project_name=os.path.basename(cwd)
    )

    # Start the engine!
    if not test_mode:
        TkGUI(pytddmon, import_tkinter(), import_tk_font()).run()
    else:
        pytddmon.main()
        with open("pytddmon.log", "w") as log_file:
            log_file.write(
                "green=%r\ntotal=%r\n" % (
                    pytddmon.result.passed,
                    pytddmon.result.total
                )
            )

if __name__ == '__main__':
    run()
