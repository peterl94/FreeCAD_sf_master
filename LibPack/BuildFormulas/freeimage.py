import libpack_utils as utils
import os

name = "freeimage"
version = "3.15.4"
source = {"type":"archive", "url":
          "http://downloads.sourceforge.net/freeimage/FreeImage3154.zip"}
depends_on = []
patches = ["freeimage_algorithm"]

def build(libpack):
    utils.shutil.copy(os.path.join(os.path.dirname(__file__),
                                   "..\\patches\\freeimage_CMakeLists.txt"),
                      "CMakeLists.txt")

    if not os.path.exists("cmake_build"):
        os.mkdir("cmake_build")

    os.chdir("cmake_build")

    if libpack.toolchain.startswith("vc"):
        utils.run_cmd("cmake", ["-D","CMAKE_INSTALL_PREFIX=" + libpack.tmp_install,
                                "-G", libpack.cmake_generator, ".."])

        print("\nBuilding release...\n")
        libpack.vcbuild("FreeImage.sln", "Release", "Win32")

        print("\nBuilding debug...\n")
        libpack.vcbuild("FreeImage.sln", "Debug", "Win32")


def install(libpack):

    os.chdir("cmake_build")

    if libpack.toolchain.startswith("vc"):
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Release", "Win32")
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Debug", "Win32")

    files = utils.move(os.path.join(libpack.tmp_install, "include"),
                       libpack.path, "include", root=False)

    files.extend(utils.move(os.path.join(libpack.tmp_install, "lib"),
                            libpack.path, "lib", root=False))
    files.extend(utils.move(os.path.join(libpack.tmp_install, "bin"),
                            libpack.path, "bin", root=False))

    libpack.manifest_add(name, version, files)

