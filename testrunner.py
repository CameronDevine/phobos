#!/usr/bin/python3

import os
import glob
import subprocess
import sys

blenderExecutable = 'blender'

# allow override of blender executable (important for CI!)
if len(sys.argv) > 1:
    blenderExecutable = sys.argv[1]

# iterate over each *.test.blend file in the "tests" directory
# and open up blender with the .test.blend file and the corresponding .test.py python script
for file in glob.glob('tests/**/*.test.blend'):
    code = subprocess.call([blenderExecutable, '--addons', 'phobos', '--factory-startup', '-noaudio', '-b', file, '--python', file.replace('.blend', '.py'), '--python-exit-code', '1'])
    if code:
        sys.exit(code)

sys.exit(0)
