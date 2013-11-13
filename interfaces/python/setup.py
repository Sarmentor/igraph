#!/usr/bin/env python
try:
    from setuptools import setup
    build_py = None
except ImportError:
    from distutils.core import setup
    try:
        from distutils.command.build_py import build_py_2to3 as build_py
    except ImportError:
        from distutils.command.build_py import build_py

from distutils.core import Extension
from distutils.file_util import copy_file
from distutils.util import get_platform
from sys import argv, version_info, exit
import os.path
import glob
from os import mkdir
from shutil import copy2
from subprocess import Popen, PIPE

LIBIGRAPH_FALLBACK_INCLUDE_DIRS = ['/tmp/include/igraph']
LIBIGRAPH_FALLBACK_LIBRARIES = ['igraph']
LIBIGRAPH_FALLBACK_LIBRARY_DIRS = ['/tmp/lib']

if version_info < (2, 5):
    print("This module requires Python >= 2.5")
    exit(0)

def get_output(command):
    """Returns the output of a command returning a single line of output"""
    p = Popen(command, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.stdin.close()
    p.stderr.close()
    line=p.stdout.readline().strip()
    p.wait()
    if type(line).__name__ == "bytes":
        line = str(line, encoding="utf-8")
    return line, p.returncode
    
def detect_igraph_include_dirs(default = LIBIGRAPH_FALLBACK_INCLUDE_DIRS, \
        static = False):
    """Tries to detect the igraph include directory"""
    cmd = "pkg-config igraph --cflags"
    if static:
        cmd += " --static"
    line, exit_code = get_output(cmd)
    if exit_code > 0 or len(line) == 0:
        return default
    opts=line.split()
    return [opt[2:] for opt in opts if opt.startswith("-I")]

def detect_igraph_libraries(default = LIBIGRAPH_FALLBACK_LIBRARIES, \
        static = False):
    """Tries to detect the libraries that igraph uses"""
    cmd = "pkg-config igraph --libs"
    if static:
        cmd += " --static"
    line, exit_code = get_output(cmd)
    if exit_code>0 or len(line) == 0:
        return default
    opts=line.split()
    return [opt[2:] for opt in opts if opt.startswith("-l")]
    
def detect_igraph_library_dirs(default = LIBIGRAPH_FALLBACK_LIBRARY_DIRS, \
        static = False):
    """Tries to detect the igraph library directory"""
    cmd = "pkg-config igraph --libs"
    if static:
        cmd += " --static"
    line, exit_code = get_output(cmd)
    if exit_code>0 or len(line) == 0:
        return default
    opts=line.split()
    return [opt[2:] for opt in opts if opt.startswith("-L")]

def find_static_library(library_name, library_path):
    variants = ["lib{0}.a", "{0}.a", "{0}.lib", "lib{0}.lib"]
    extra_libdirs = ["/usr/local/lib64", "/usr/local/lib",
            "/usr/lib64", "/usr/lib", "/lib64", "/lib"]

    for path in extra_libdirs:
        if path not in library_path and os.path.isdir(path):
            library_path.append(path)

    for path in library_path:
        for variant in variants:
            full_path = os.path.join(path, variant.format(library_name))
            if os.path.isfile(full_path):
                return full_path

sources=glob.glob(os.path.join('src', '*.c'))
include_dirs=[]
library_dirs=[]
libraries=[]
extra_objects=[]
extra_link_args=[]
static_extension=False

if "--static" in argv:
    argv.remove("--static")
    static_extension=True

if "--no-pkg-config" in argv:
    argv.remove("--no-pkg-config")
    libraries.append("igraph")
    if static:
        # Educated guess.
        libraries.extend(["xml2", "z", "m"])
else:
    line, exit_code = get_output("pkg-config igraph")
    if exit_code>0:
        print("Using default include and library paths for compilation")
        print("If the compilation fails, please edit the LIBIGRAPH_FALLBACK_*")
        print("variables in setup.py or include_dirs and library_dirs in ")
        print("setup.cfg to point to the correct directories and libraries")
        print("where the C core of igraph is installed")
        print("")

    include_dirs.extend(detect_igraph_include_dirs(static=static_extension))
    library_dirs.extend(detect_igraph_library_dirs(static=static_extension))
    libraries.extend(detect_igraph_libraries(static=static_extension))

print("Include path: %s" % " ".join(include_dirs))
print("Library path: %s" % " ".join(library_dirs))

if static_extension:
    print("Linking statically to igraph.")
    extra_link_args.append("-static")
    for library_name in libraries[:]:
        static_lib = find_static_library(library_name, library_dirs)
        if static_lib:
            libraries.remove(library_name)
            extra_objects.append(static_lib)

igraph_extension = Extension('igraph._igraph', sources, \
  library_dirs=library_dirs, libraries=libraries, \
  include_dirs=include_dirs, \
  extra_objects=extra_objects, extra_link_args=extra_link_args)
       
description = """Python interface to the igraph high performance graph
library, primarily aimed at complex network research and analysis.

Graph plotting functionality is provided by the Cairo library, so make
sure you install the Python bindings of Cairo if you want to generate
publication-quality graph plots.

See the `Cairo homepage <http://cairographics.org/pycairo>`_ for details.

From release 0.5, the C core of the igraph library is **not** included
in the Python distribution - you must compile and install the C core
separately. Windows installers already contain a compiled igraph DLL,
so they should work out of the box. Linux users should refer to the
`igraph homepage <http://igraph.org>`_ for
compilation instructions (but check your distribution first, maybe
there are pre-compiled packages available). OS X Snow Leopard users may
benefit from the disk images in the Python Package Index.

Unofficial installers for 64-bit Windows machines and/or different Python
versions can also be found `here <http://www.lfd.uci.edu/~gohlke/pythonlibs>`_.
Many thanks to the maintainers of this page!
"""

plat = get_platform()
options = dict(
    name = 'python-igraph',
    version = '0.7',
    description = 'High performance graph data structures and algorithms',
    long_description = description,
    license = 'GNU General Public License (GPL)',

    author = 'Tamas Nepusz',
    author_email = 'tamas@cs.rhul.ac.uk',

    ext_modules = [igraph_extension],
    package_dir = {'igraph': 'igraph'},
    packages = ['igraph', 'igraph.test', 'igraph.app', 'igraph.drawing',
        'igraph.remote', 'igraph.vendor'],
    scripts = ['scripts/igraph'],
    test_suite = "igraph.test.suite",

    headers = ['src/igraphmodule_api.h'],

    platforms = 'ALL',
    keywords = ['graph', 'network', 'mathematics', 'math', 'graph theory', 'discrete mathematics'],
    classifiers = [
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'Intended Audience :: Science/Research',
      'Operating System :: OS Independent',
      'Programming Language :: C',
      'Programming Language :: Python',
      'Topic :: Scientific/Engineering',
      'Topic :: Scientific/Engineering :: Information Analysis',
      'Topic :: Scientific/Engineering :: Mathematics',
      'Topic :: Scientific/Engineering :: Physics',
      'Topic :: Scientific/Engineering :: Bio-Informatics',
      'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

if "macosx" in plat and "bdist_mpkg" in argv:
    # OS X specific stuff to build the .mpkg installer
    options["data_files"] = [ \
            ('/usr/local/lib', [os.path.join('..', '..', 'fatbuild', 'libigraph.0.dylib')])
    ]

if version_info > (3, 0):
    if build_py is None:
        options["use_2to3"] = True
    else:
        options["cmdclass"] = { "build_py": build_py }

setup(**options)
