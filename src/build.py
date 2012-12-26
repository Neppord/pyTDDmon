import zipfile

if __name__ == "__main__" :
    tmp = file('pytddmon.py', 'w')
    tmp.write('#! /usr/bin/env python\n')
    tmp.close()
    zipfile.PyZipFile('pytddmon.py', 'a').writepy('pytddmon/.')
