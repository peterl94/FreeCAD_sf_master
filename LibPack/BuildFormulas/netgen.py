import libpack_utils as utils
import os
from subprocess import CalledProcessError

name = "netgen"
version = "4.9.14"
source = {"type":"archive", "url":"http://sourceforge.net/code-snapshots/svn"\
          "/n/ne/netgen-mesher/code/netgen-mesher-code-751-branches-netgen-4.9.zip"}
depends_on = ["oce"]
patches = []

def build(libpack):

    if libpack.toolchain.startswith("vc"):
        #for now, use netgen's pre-compiled dependencies
        if not os.path.exists("..\\ext_libs"):
            os.mkdir("..\\ext_libs")

        bit = "32"
        if libpack.arch == "x64": bit = "64"

        pthread_url = "http://sourceforge.net/projects/netgen-mesher/files"\
                "/netgen-mesher/Additional%20Files/MSVC2008_Libs"\
                "/pthread-w" + bit + ".zip"
        tcl_url = "http://sourceforge.net/projects/netgen-mesher/files"\
                "/netgen-mesher/Additional%20Files/MSVC2008_Libs"\
                "/TclTkTixTogl-w" + bit + ".zip"
        pthread_dirname = os.path.basename(pthread_url).split(".")[0]
        tcl_dirname = os.path.basename(tcl_url).split(".")[0]
        utils.get_source({"type":"archive", "url":pthread_url},
                         "..\\ext_libs", pthread_dirname)
        utils.get_source({"type":"archive", "url":tcl_url},
                         "..\\ext_libs", tcl_dirname)

        patches = ["vcproj", "occ67_1", "occ67_2", "occ67_3", 
                   "dllexport1", "dllexport2", "dllexport3", "dllexport4"]
        for n in patches:
            filename = "..\\patches\\netgen_{0}.diff".format(n)
            utils.apply_patch(os.path.join(os.path.dirname(__file__),
                                           filename))

        os.environ["LIB"] = os.environ["LIB"] + libpack.path + "\\lib"
        os.environ["INCLUDE"] = os.environ["INCLUDE"] + libpack.path \
                + "\\include\\oce;"
        tcl_include = libpack.config.get("Paths", "workspace") \
                + "\\ext_libs\\" + tcl_dirname + "\\include;"
        os.environ["INCLUDE"] = os.environ["INCLUDE"] + tcl_include


        use_env = "/useenv"
        if libpack.toolchain == "vc12":
            use_env = "/p:UseEnv=true"

        print("\nBuilding release...\n")
        libpack.vcbuild("windows\\nglib.sln", "Release(OCC)", "Win32", [use_env])

        print("\nBuilding debug...\n")
        libpack.vcbuild("windows\\nglib.sln", "Debug", "Win32", [use_env])

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

