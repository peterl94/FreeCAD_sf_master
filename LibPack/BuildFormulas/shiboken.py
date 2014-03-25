import libpack_utils as utils
import os

name = "shiboken"
version = "1.2.1"
source = {"type":"archive", "url":
          "http://download.qt-project.org/official_releases/pyside"\
          "/shiboken-1.2.1.tar.bz2"}
depends_on = ["python", "qt"]
patches = ["shiboken_d_suffix", "shiboken_rel_path1", "shiboken_rel_path2"]

def build(libpack):
    if not os.path.exists("cmake_build"):
        os.mkdir("cmake_build")

    os.chdir("cmake_build")

    tmp_install = os.path.join(libpack.config.get("Paths", "workspace"),
                               "tmp_install")

    os.environ["PATH"] = libpack.path + "\\bin;" + os.environ["PATH"]
    os.environ["QTDIR"] = libpack.path
    os.environ["CMAKE_PREFIX_PATH"] = libpack.path

    generator = ""

    if libpack.toolchain.startswith("vc"):

        utils.run_cmd("cmake", ["-D", "CMAKE_INSTALL_PREFIX=" + tmp_install,
                                "-D", "PYTHON_SITE_PACKAGES="+tmp_install + "\\bin",
                                "-D", "BUILD_TESTS=OFF"
                                "-D", "CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE=.",
                                "-G", libpack.cmake_generator, ".."])

        print("\nBuilding debug...\n")
        libpack.vcbuild("shiboken.sln", "Debug", "Win32")

        print("\nBuilding release...\n")
        libpack.vcbuild("shiboken.sln", "Release", "Win32")

def install(libpack):
    tmp_install = os.path.join(libpack.config.get("Paths", "workspace"),
                               "tmp_install")

    if libpack.toolchain.startswith("vc"):
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Debug", "Win32")
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Release", "Win32")

    files = utils.move(os.path.join(tmp_install, "include", "shiboken"),
                       libpack.path, "include")

    files.extend(utils.copyfiles([tmp_install + "\\lib\\*.lib"],
                                 libpack.path, "lib"))
    files.extend(utils.copyfiles([tmp_install + "\\bin\\*"],
                                 libpack.path, "bin"))
    files.extend(utils.copytree(os.path.join(tmp_install, "lib", "cmake"),
                                libpack.path, "lib\\cmake", root=False))

    libpack.manifest_add(name, version, files)

    os.chdir("..")
    utils.shutil.rmtree(tmp_install, ignore_errors=True)

