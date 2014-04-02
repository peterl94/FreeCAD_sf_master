import libpack_utils as utils
import os

name = "coin"
version = "3.1.3"
source = {"type":"archive", "url":
          "https://bitbucket.org/Coin3D/coin/downloads/Coin-{0}.zip".format(version)}
depends_on = []
patches = ["coin_macro_error", "coin_config"]

def build(libpack):

    if libpack.toolchain.startswith("vc"):

        os.chdir("build\\msvc9")

        vcproj = "coin3.vcproj"

        if libpack.toolchain == "vc12":
            vcproj = libpack.upgrade_vcproj("coin3")

        print("\nBuilding release...\n")
        libpack.vcbuild(vcproj, "DLL (Release)", "Win32")

        print("\nBuilding debug...\n")
        libpack.vcbuild(vcproj, "DLL (Debug)", "Win32")


def install(libpack):

    if libpack.toolchain.startswith("vc"):
        if libpack.toolchain == "vc9" or libpack.toolchain == "vc12":
            os.chdir("build\\msvc9")

            os.environ["COINDIR"] = libpack.tmp_install
            utils.run_shell("..\misc\install-sdk.bat dll release msvc9 coin3",
                            env=os.environ)
            utils.run_shell("..\misc\install-sdk.bat dll debug msvc9 coin3",
                            env=os.environ)

    files = utils.move(os.path.join(libpack.tmp_install, "include"),
                       libpack.path, "include", root=False)

    files.extend(utils.move(os.path.join(libpack.tmp_install, "lib"),
                            libpack.path, "lib", root=False))
    files.extend(utils.move(os.path.join(libpack.tmp_install, "bin"),
                            libpack.path, "bin", root=False))

    libpack.manifest_add(name, version, files)

