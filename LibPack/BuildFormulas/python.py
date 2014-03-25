import libpack_utils as utils
import os
from subprocess import CalledProcessError

name = "python"
version = "2.7.6"
source = {"type":"archive", "url":
          "http://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz"}
depends_on = []
patches = ["python_pyconfig", "python_pyconfig2"]

def build(libpack):

    if libpack.toolchain.startswith("vc"):

        old_dir = os.getcwd()
        os.chdir("PCbuild")

        if libpack.toolchain == "vc12":
            if utils.check_update("python.vcproj", "python.vcxproj"):
                utils.run_cmd("devenv", ["/upgrade", "pcbuild.sln"])

        try:
            print("\nBuilding release...\n")
            libpack.vcbuild("pcbuild.sln", "Release", "Win32")
        except CalledProcessError as e:
            #ignore errors because we don't need the modules that
            #fail to build
            print(e)

        try:
            print("\nBuilding debug...\n")
            libpack.vcbuild("pcbuild.sln", "Debug", "Win32")
        except CalledProcessError as e:
            #ignore errors because we don't need the modules that
            #fail to build
            print(e)

        os.chdir(old_dir)


def install(libpack): 
    files = utils.copytree("Include", libpack.path, "include\\python2.7")
    files.extend(utils.copyfiles(["PC\\pyconfig.h"], libpack.path, "include\\python2.7"))

    utils.run_cmd("7z", ["a", "-r", "-x!*.pyc", libpack.path + "\\bin\\python27.zip", 
                         ".\\Lib\\*"],
                  silent=True)
    files.append("bin\\python27.zip")

    files.extend(utils.copyfiles(["PCbuild\\python27.lib", "PCbuild\\python27_d.lib"],
                                 libpack.path, "lib"))

    files.extend(utils.copyfiles(["PCbuild\\python.exe", "PCbuild\\python_d.exe",
                                  "PCbuild\\*.dll", "PCbuild\\*.pyd"], libpack.path, "bin"))

    libpack.manifest_add(name, version, files)

