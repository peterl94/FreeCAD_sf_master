import libpack_utils as utils
import os

name = "pyside"
version = "1.2.1"
source = {"type":"archive", "url":
          "http://download.qt-project.org/official_releases/pyside"\
          "/pyside-qt4.8+1.2.1.tar.bz2"}
depends_on = ["python", "qt", "shiboken"]
patches = ["pyside_sbk_fix", "pyside_rel_path1", "pyside_rel_path2"]

def build(libpack):
    if not os.path.exists("cmake_build"):
        os.mkdir("cmake_build")

    os.chdir("cmake_build")

    if not os.path.exists("debug"):
        os.mkdir("debug")

    if not os.path.exists("release"):
        os.mkdir("release")

    tmp_install = os.path.join(libpack.config.get("Paths", "workspace"),
                               "tmp_install")

    os.environ["PATH"] = libpack.path + "\\bin;" + os.environ["PATH"]
    os.environ["QTDIR"] = libpack.path
    os.environ["CMAKE_PREFIX_PATH"] = libpack.path
    os.environ["PATH"] = "C:\\jom;" + os.environ["PATH"]

    if libpack.toolchain.startswith("vc"):
        #visual studio has mysterious problem running moc on qpytextobject.h
        #use nmake instead
        os.chdir("debug")
        print("\nConfiguring for debug...\n")
        utils.run_cmd("cmake", ["-D", "CMAKE_INSTALL_PREFIX=" + tmp_install,
                                "-D", "SITE_PACKAGE="+tmp_install + "\\bin",
                                "-D", "CMAKE_BUILD_TYPE=Debug",
                                "-D", "BUILD_TESTS=OFF",
                                "-G", "NMake Makefiles", "..\\.."])

        os.chdir("..\\release")
        print("\nConfiguring for release...\n")
        utils.run_cmd("cmake", ["-D", "CMAKE_INSTALL_PREFIX=" + tmp_install,
                                "-D", "SITE_PACKAGE="+tmp_install + "\\bin",
                                "-D", "CMAKE_BUILD_TYPE=Release",
                                "-D", "BUILD_TESTS=OFF",
                                "-G", "NMake Makefiles", "..\\.."])

        os.chdir("..\\debug")
        print("\nBuilding debug...\n")
        utils.run_cmd("jom", ["-j5"])

        os.chdir("..\\release")
        print("\nBuilding release...\n")
        utils.run_cmd("jom", ["-j5"])

        os.chdir("..")

def install(libpack):
    tmp_install = os.path.join(libpack.config.get("Paths", "workspace"),
                               "tmp_install")

    if libpack.toolchain.startswith("vc"):
        os.chdir("debug")
        utils.run_cmd("nmake", ["install"])
        os.chdir("..\\release")
        utils.run_cmd("nmake", ["install"])


    files = utils.move(tmp_install + "\\include\\PySide", libpack.path,
                       "include")
    files.extend(utils.copyfiles([tmp_install + "\\lib\\*.lib"],
                                 libpack.path, "lib"))
    files.extend(utils.move(tmp_install + "\\bin", libpack.path, "bin",
                            root=False))
    files.extend(utils.move(tmp_install + "\\lib\\cmake", libpack.path,
                            "lib\\cmake", root=False))
    #files.extend(utils.move(tmp_install + "\\share", libpack.path,
    #                        "share", root=False))

    libpack.manifest_add(name, version, files)

    os.chdir("..\\..")
    utils.shutil.rmtree(tmp_install)

