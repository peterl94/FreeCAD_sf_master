import libpack_utils as utils
import os
from subprocess import CalledProcessError

name = "netgen"
version = "5.1"
source = {"type":"archive",
          "url":"http://sourceforge.net/projects/netgen-mesher/files/netgen-mesher/{0}/netgen-{0}.tar.gz".format(version)}
depends_on = ["oce", "tcl", "tk", "pthreads", "zlib"]
patches = ["netgen_vcproj", "netgen_occ67_1", "netgen_occ67_2",
           "netgen_occ67_3", "netgen_dllexport1", "netgen_dllexport2",
           "netgen_dllexport3", "netgen_dllexport4"]

def build(libpack):

    if libpack.toolchain.startswith("vc"):

        #bit = "32"
        #if libpack.arch == "x64": bit = "64"

        os.environ["INCLUDE"] = os.environ["INCLUDE"] + libpack.path + "\\include;"
        os.environ["INCLUDE"] = os.environ["INCLUDE"] + libpack.path + "\\include\\oce;"
        os.environ["LIB"] = os.environ["LIB"] + libpack.path + "\\lib;"

        os.chdir("windows")

        vcproj = "nglib.vcproj"
        use_env = "/useenv"

        if libpack.toolchain == "vc12":
            vcproj = libpack.upgrade_vcproj("nglib")
            use_env = "/p:UseEnv=true"

        print("\nBuilding release...\n")
        libpack.vcbuild(vcproj, "Release(OCC)", "Win32", [use_env])

        print("\nBuilding debug...\n")
        libpack.vcbuild(vcproj, "Debug", "Win32", [use_env])


def install(libpack):
    files = utils.copyfiles(["nglib\\nglib.h"], libpack.path, "include")

    files.extend(utils.copyfiles(["windows\\nglib\\Debug\\*.lib",
                                  "windows\\nglib\\Release(OCC)\\*.lib"],
                                 libpack.path, "lib"))

    files.extend(utils.copyfiles(["windows\\nglib\\Debug\\*.dll",
                                  "windows\\nglib\\Release(OCC)\\*.dll"],
                                 libpack.path, "bin"))
    files.extend(utils.copytree("libsrc", libpack.path, "include\\netgen", 
                                ignore=utils.ignore_names_inverse(["*.hpp", 
                                                                   "*.h"],
                                                                  [])))

    libpack.manifest_add(name, version, files)

