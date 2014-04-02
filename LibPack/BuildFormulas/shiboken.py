import libpack_utils as utils
import os

name = "shiboken"
version = "1.2.1"
source = {"type":"archive", "url":
          "http://download.qt-project.org/official_releases/pyside"\
          "/shiboken-{0}.tar.bz2".format(version)}
depends_on = ["python", "qt"]
patches = ["shiboken_d_suffix", "shiboken_rel_path1", "shiboken_rel_path2",
           "shiboken_vc12fix"]

def build(libpack):
    if not os.path.exists("cmake_build"):
        os.mkdir("cmake_build")

    os.chdir("cmake_build")

    os.environ["PATH"] = libpack.path + "\\bin;" + os.environ["PATH"]
    os.environ["QTDIR"] = libpack.path
    os.environ["CMAKE_PREFIX_PATH"] = libpack.path

    generator = ""

    if libpack.toolchain.startswith("vc"):

        utils.run_cmd("cmake", ["-D", "CMAKE_INSTALL_PREFIX=" + libpack.tmp_install,
                                "-D", "PYTHON_SITE_PACKAGES="+libpack.tmp_install + "\\bin",
                                "-D", "BUILD_TESTS=OFF"
                                "-D", "CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE=.",
                                "-D", "CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG=.",
                                "-G", libpack.cmake_generator, ".."])

        print("\nBuilding debug...\n")
        libpack.vcbuild("shiboken.sln", "Debug", "Win32")

        print("\nBuilding release...\n")
        libpack.vcbuild("shiboken.sln", "Release", "Win32")

def install(libpack):

    os.chdir("cmake_build")

    if libpack.toolchain.startswith("vc"):
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Debug", "Win32")
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Release", "Win32")

    files = utils.move(os.path.join(libpack.tmp_install, "include", "shiboken"),
                       libpack.path, "include")

    files.extend(utils.copyfiles([libpack.tmp_install + "\\lib\\*.lib"],
                                 libpack.path, "lib"))
    files.extend(utils.copyfiles([libpack.tmp_install + "\\bin\\*"],
                                 libpack.path, "bin"))
    files.extend(utils.copytree(os.path.join(libpack.tmp_install, "lib", "cmake"),
                                libpack.path, "lib\\cmake", root=False))

    libpack.manifest_add(name, version, files)
