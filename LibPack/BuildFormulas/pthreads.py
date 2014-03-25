import libpack_utils as utils
import os

name = "pthreads"
version = "2.9.1"
source = {"type":"archive", "url":"ftp://sourceware.org/pub/pthreads-win32/pthreads-w32-2-9-1-release.tar.gz"}
depends_on = []
patches = []

def build(libpack):
    
    if libpack.toolchain.startswith("vc"):
        utils.run_cmd("nmake", ["VC"])


def install(libpack):

    files = utils.copyfiles(["pthreadVC2.dll"], libpack.path, "bin")
    files.extend(utils.copyfiles(["pthreadVC2.lib"], libpack.path, "lib"))
    files.extend(utils.copyfiles(["pthread.h", "sched.h"], libpack.path, "include"))

    libpack.manifest_add(name, version, files)
