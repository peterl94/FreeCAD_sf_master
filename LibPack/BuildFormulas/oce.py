import libpack_utils as utils
import os

name = "oce"
version = "0.15"
source = {"type":"archive", "url":
          "https://github.com/tpaviot/oce/archive/OCE-0.15.zip"}
depends_on = ["freetype", "freeimage"]
patches = []

def build(libpack):
    if not os.path.exists("cmake_build"):
        os.mkdir("cmake_build")

    os.chdir("cmake_build")

    tmp_install = os.path.join(libpack.config.get("Paths", "workspace"),
                               "tmp_install")

    os.environ["CMAKE_PREFIX_PATH"] = libpack.path
    #os.environ["FREETYPE_DIR"] = libpack.path

    generator = ""

    if libpack.toolchain.startswith("vc"):

        ft_include = "FREETYPE_INCLUDE_DIRS="\
                "{0}/include/freetype2".format(libpack.path)

        utils.run_cmd("cmake", ["-D", "OCE_INSTALL_PREFIX=" + tmp_install,
                                "-D", "OCE_INSTALL_BIN_DIR=bin",
                                "-D", "OCE_INSTALL_LIB_DIR=lib",
                                "-D", "OCE_INSTALL_CMAKE_DATA_DIR=lib/cmake",
                                #"-D", "OCE_INSTALL_PDB_FILES=OFF",
                                #"-D", "OCE_MULTITHREADED_BUILD=OFF",
                                "-D", ft_include,
                                "-D", "OCE_USE_MSVC_EXPRESS=ON",
                                "-D", "OCE_DRAW=ON",
                                "-D", "OCE_WITH_FREEIMAGE=ON",
                                "-D", "CMAKE_USE_RELATIVE_PATHS=ON",
                                "-G", libpack.cmake_generator, ".."])

        print("\nBuilding release...\n")
        libpack.vcbuild("OCE.sln", "Release", "Win32")

        print("\nBuilding debug...\n")
        libpack.vcbuild("OCE.sln", "Debug", "Win32")

def install(libpack):
    tmp_install = os.path.join(libpack.config.get("Paths", "workspace"),
                               "tmp_install")

    if libpack.toolchain.startswith("vc"):
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Release", "Win32")
        libpack.vcbuild("INSTALL" + libpack.cmake_projext, "Debug", "Win32")

    files = utils.move(os.path.join(tmp_install, "include"),
                       libpack.path, "include", root=False)

    #copy cmake directory separately because it might already exist
    files.extend(utils.move(os.path.join(tmp_install, "lib"), libpack.path,
                            "lib", ignore=utils.ignore_names("cmake"),
                            root=False))
    files.extend(utils.move(os.path.join(tmp_install, "bin"),
                            libpack.path, "bin", root=False))
    files.extend(utils.move(os.path.join(tmp_install, "lib", "cmake"),
                            libpack.path, "lib\\cmake", root=False))

    libpack.manifest_add(name, version, files)

    os.chdir("..")
    utils.shutil.rmtree(tmp_install)

