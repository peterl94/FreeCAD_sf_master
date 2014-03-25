import libpack_utils as utils
import os

name = "zlib"
version = "1.2.8"
source = {"type":"archive", "url":"http://zlib.net/zlib128.zip"}
depends_on = []
patches = []

def build(libpack):
    if not os.path.exists("cmake_build"):
        os.mkdir("cmake_build")

    os.chdir("cmake_build")

    tmp_install = os.path.join(libpack.config.get("Paths", "workspace"),
                               "tmp_install")

    generator = ""

    if libpack.toolchain.startswith("vc"):

        utils.run_cmd("cmake", ["-D", "CMAKE_INSTALL_PREFIX=" + tmp_install,
                                "-G", libpack.cmake_generator, ".."])

        print("\nBuilding debug...\n")
        libpack.vcbuild("zlib.sln", "Debug", "Win32")

        print("\nBuilding release...\n")
        libpack.vcbuild("zlib.sln", "Release", "Win32")

def install(libpack):
    tmp_install = os.path.join(libpack.config.get("Paths", "workspace"),
                               "tmp_install")

    if libpack.toolchain.startswith("vc"):
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Debug", "Win32")
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Release", "Win32")

    files = utils.move(tmp_install + "\\include", libpack.path, "include",
                       root=False)

    files.extend(utils.move(tmp_install + "\\lib", libpack.path, "lib",
                            root=False))
    files.extend(utils.move(tmp_install + "\\bin", libpack.path, "bin",
                            root=False))

    libpack.manifest_add(name, version, files)

    os.chdir("..")
    utils.shutil.rmtree(tmp_install)

