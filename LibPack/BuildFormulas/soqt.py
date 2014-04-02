import libpack_utils as utils
import os

name = "soqt"
version = "1.5.0"
source = {"type":"archive", "url":
          "https://bitbucket.org/Coin3D/coin/downloads/SoQt-{0}.zip".format(version)}
depends_on = ["qt", "coin"]
patches = ["soqt_vcproj"]

def build(libpack):

    if libpack.toolchain.startswith("vc"):

        os.chdir("build\\msvc9")

        vcproj = "soqt1.vcproj"

        if libpack.toolchain == "vc12":
            vcproj = libpack.upgrade_vcproj("soqt1")

        os.environ["QTDIR"] = libpack.path
        os.environ["COINDIR"] = libpack.path

        print("\nBuilding release...\n")
        libpack.vcbuild(vcproj, "DLL (Release)", "Win32")

        print("\nBuilding debug...\n")
        libpack.vcbuild(vcproj, "DLL (Debug)", "Win32")


def install(libpack):

    if libpack.toolchain.startswith("vc"):
        os.chdir("build\\msvc9")

        os.environ["COINDIR"] = libpack.tmp_install
        utils.run_shell("..\misc\install-sdk.bat dll release msvc9 soqt1",
                        env=os.environ)
        utils.run_shell("..\misc\install-sdk.bat dll debug msvc9 soqt1",
                        env=os.environ)

    files = utils.move(os.path.join(libpack.tmp_install, "include", "Inventor"),
                       libpack.path, "include\\Inventor", root=False)

    files.extend(utils.move(os.path.join(libpack.tmp_install, "lib"),
                            libpack.path, "lib", root=False))
    files.extend(utils.move(os.path.join(libpack.tmp_install, "bin"),
                            libpack.path, "bin", root=False))

    libpack.manifest_add(name, version, files)
