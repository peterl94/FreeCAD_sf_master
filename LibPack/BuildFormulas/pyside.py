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

    os.environ["PATH"] = libpack.path + "\\bin;" + os.environ["PATH"]
    os.environ["QTDIR"] = libpack.path
    os.environ["CMAKE_PREFIX_PATH"] = libpack.path

    if libpack.toolchain.startswith("vc"):
        #visual studio has mysterious problem running moc on qpytextobject.h
        #use nmake instead
        if libpack.toolchain == "vc9":

            os.environ["PATH"] = "C:\\jom;" + os.environ["PATH"]

            if not os.path.exists("debug"):
                os.mkdir("debug")

            if not os.path.exists("release"):
                os.mkdir("release")

            os.chdir("debug")
            print("\nConfiguring for debug...\n")
            utils.run_cmd("cmake", ["-D", "CMAKE_INSTALL_PREFIX=" + libpack.tmp_install,
                                    "-D", "SITE_PACKAGE="+libpack.tmp_install + "\\bin",
                                    "-D", "CMAKE_BUILD_TYPE=Debug",
                                    "-D", "BUILD_TESTS=OFF",
                                    "-G", "NMake Makefiles", "..\\.."])

            os.chdir("..\\release")
            print("\nConfiguring for release...\n")
            utils.run_cmd("cmake", ["-D", "CMAKE_INSTALL_PREFIX=" + libpack.tmp_install,
                                    "-D", "SITE_PACKAGE="+libpack.tmp_install + "\\bin",
                                    "-D", "CMAKE_BUILD_TYPE=Release",
                                    "-D", "BUILD_TESTS=OFF",
                                    "-G", "NMake Makefiles", "..\\.."])

            os.chdir("..\\debug")
            print("\nBuilding debug...\n")
            utils.run_cmd("nmake")

            os.chdir("..\\release")
            print("\nBuilding release...\n")
            utils.run_cmd("nmake")

        if libpack.toolchain == "vc12":

            utils.run_cmd("cmake", ["-D", "CMAKE_INSTALL_PREFIX=" + libpack.tmp_install,
                                    "-D", "SITE_PACKAGE="+libpack.tmp_install + "\\bin",
                                    "-D", "BUILD_TESTS=OFF",
                                    "-G", libpack.cmake_generator, ".."])

            print("\nBuilding release...\n")
            libpack.vcbuild("ALL_BUILD" + libpack.cmake_projext, "Release", "Win32")

            print("\nBuilding debug...\n")
            libpack.vcbuild("ALL_BUILD" + libpack.cmake_projext, "Debug", "Win32")


def install(libpack):
    os.chdir("cmake_build")

    if libpack.toolchain.startswith("vc"):

        if libpack.toolchain == "vc9":
            os.chdir("debug")
            utils.run_cmd("nmake", ["install"])
            os.chdir("..\\release")
            utils.run_cmd("nmake", ["install"])

        if libpack.toolchain == "vc12":

            libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Release", "Win32")
            libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Debug", "Win32")


    files = utils.move(libpack.tmp_install + "\\include\\PySide", libpack.path, "include")
    files.extend(utils.copyfiles([libpack.tmp_install + "\\lib\\*.lib"], libpack.path, "lib"))
    files.extend(utils.move(libpack.tmp_install + "\\bin", libpack.path, "bin", root=False))
    files.extend(utils.move(libpack.tmp_install + "\\lib\\cmake", libpack.path, "lib\\cmake", root=False))
    #files.extend(utils.move(libpack.tmp_install + "\\share", libpack.path,
    #                        "share", root=False))

    libpack.manifest_add(name, version, files)
