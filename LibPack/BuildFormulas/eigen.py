import libpack_utils as utils
import os

name = "eigen"
version = "3.2.1"
source = {"type":"archive", "url":
          "http://bitbucket.org/eigen/eigen/get/3.2.1.zip"}
depends_on = []
patches = []

def build(libpack):
    if not os.path.exists("cmake_build"):
        os.mkdir("cmake_build")

    os.chdir("cmake_build")

    generator = ""

    if libpack.toolchain.startswith("vc"):

        utils.run_cmd("cmake", ["-D", "CMAKE_INSTALL_PREFIX=" + libpack.path,
                                "-G", libpack.cmake_generator, ".."])

def install(libpack):
    if libpack.toolchain.startswith("vc"):
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Release", "Win32")

    files = ["include\\eigen3"]

    libpack.manifest_add(name, version, files)

    os.chdir("..")


