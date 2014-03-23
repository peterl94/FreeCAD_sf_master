import libpack_utils as utils
import os
import shutil

name = "xerces-c"
version = "3.1.1"
source = {"type":"archive", "url":
          "http://mirror.reverse.net/pub/apache//xerces/c/3/sources"\
          "/xerces-c-3.1.1.zip"}
depends_on = []
patches = []
    
def build(libpack):
    
    if libpack.toolchain.startswith("vc"):

        vcproj = ""
        
        if libpack.toolchain == "vc9":

            vcproj = "projects\\Win32\\VC9\\xerces-all\\XercesLib"\
                     "\\XercesLib.vcproj"
            
        elif libpack.toolchain == "vc12":

            vcproj_old = "projects\\Win32\\VC10\\xerces-all\\XercesLib"\
                         "\\XercesLib.vcxproj"

            vcproj = vcproj_old + ".new.vcxproj"

            if utils.check_update(vcproj_old, vcproj):
                shutil.copyfile(vcproj_old, vcproj)
                utils.run_cmd("devenv", ["/upgrade", vcproj])


        print("\nBuilding release...\n")
        libpack.vcbuild(vcproj, "Release", "Win32")

        print("\nBuilding debug...\n")
        libpack.vcbuild(vcproj, "Debug", "Win32")

    
def install(libpack): 
    files = utils.copytree("src\\xercesc", libpack.path, "include\\xercesc",
                           ignore=utils.ignore_names_inverse(["*.h", "*.hpp", "*.c"],
                                                             dir_filter=[]))

    build_dir = ""
    if libpack.toolchain == "vc9":
        build_dir = "Build\\Win32\\VC9\\"
    elif libpack.toolchain == "vc12":
        build_dir = "Build\\Win32\\VC10\\"
    
    files.extend(utils.copytree(build_dir + "Release", libpack.path, "lib",
                                ignore=utils.ignore_names_inverse(["*.lib"]),
                                root=False))
    files.extend(utils.copytree(build_dir + "Debug", libpack.path, "lib",
                                ignore=utils.ignore_names_inverse(["*.lib"]),
                                root=False))
    files.extend(utils.copytree(build_dir + "Release", libpack.path, "bin",
                                ignore=utils.ignore_names_inverse(["*.dll"]),
                                root=False))
    files.extend(utils.copytree(build_dir + "Debug", libpack.path, "bin",
                                ignore=utils.ignore_names_inverse(["*.dll"]),
                                root=False))
    
    libpack.manifest_add(name, version, files)

