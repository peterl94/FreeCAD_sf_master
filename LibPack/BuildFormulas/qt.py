import libpack_utils as utils
import os
from sys import platform

name = "qt"
version = "4.8.5"
source = {"type":"archive", "url":
          "http://download.qt-project.org/official_releases"\
          "/qt/4.8/{0}/qt-everywhere-opensource-src-{0}.zip".format(version)}
depends_on = []
patches = ["qt"]

def build(libpack):
    if platform == "win32":
        print("\nBuilding release and debug...\n")

        if libpack.toolchain == "vc12":
            utils.run_shell("configure -opensource -confirm-license "
                            "-platform win32-msvc2012 "
                            "-debug-and-release -mp -no-qt3support "
                            "-no-phonon -no-multimedia -no-declarative-debug "
                            "-nomake tests -nomake examples -nomake demos "
                            "-nomake docs -no-vcproj", env=os.environ)
        else:
            utils.run_shell("configure -opensource -confirm-license "
                            "-debug-and-release -mp -no-qt3support "
                            "-no-phonon -no-multimedia -no-declarative-debug "
                            "-nomake tests -nomake examples -nomake demos "
                            "-nomake docs -no-vcproj", env=os.environ)

        utils.run_cmd("nmake")


def install(libpack):
    if platform == "win32":  
        files = utils.copytree("include", libpack.path, "include", root=False,
                               ignore=utils.ignore_names("phonon",
                                                         "phonon_compat",
                                                         "Qt3Support",
                                                         "QtOpenVG",
                                                         "QtMultimedia",
                                                         "*.pri"))
        files.extend(utils.copytree("src", libpack.path, "src",
                                    ignore=utils.ignore_names_inverse(["*.h"],
                                                                      ["imports",
                                                                       "multimedia",
                                                                       "openvg",
                                                                       "phonon"
                                                                       "qt3support"
                                                                       "plugins"])))
        files.extend(utils.copytree("tools", libpack.path, "tools",
                                    ignore=utils.ignore_names_inverse(["*.h"],[])))

        files.extend(utils.copytree("lib", libpack.path, "lib", root=False,
                                    ignore=utils.ignore_names_inverse(["*.lib"])))
        files.extend(utils.copytree("bin", libpack.path, "bin", root=False,
                                    ignore=utils.ignore_names_inverse(["*.dll",
                                                                       "*.exe"])))
        files.extend(utils.copytree("plugins", libpack.path, "bin\\qtplugins",
                                    ignore=utils.ignore_names_inverse(
                                        ["*.dll"],
                                        ["bearer",
                                         "designer",
                                         "graphicssystems",
                                         "qmltooling"]
                                    )))
        with open(libpack.path + "\\bin\\qt.conf", "wb") as f:
            f.write("[Paths]\nPrefix = ..\nPlugins = qtplugins\n")

        files.append("bin\\qt.conf")

        libpack.manifest_add(name, version, files)

