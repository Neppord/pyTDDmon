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
