import libpack_utils as utils
import os

name = "soqt"
version = "1.5.0"
source = {"type":"archive", "url":
          "https://bitbucket.org/Coin3D/coin/downloads/SoQt-1.5.0.zip"}
depends_on = ["qt", "coin"]
patches = []

def build(libpack):

    if libpack.toolchain.startswith("vc"):

        old_dir = os.getcwd()
        os.chdir("build\\msvc9")

        vcproj = "soqt1.vcproj"
        if utils.check_update(vcproj, "soqt1.vcxproj"):
            utils.run_cmd("devenv", ["/upgrade", "soqt1.sln"])
            vcproj = "soqt1.vcxproj"

        os.environ["QTDIR"] = libpack.path
        os.environ["COINDIR"] = libpack.path

        print("\nBuilding release...\n")
        libpack.vcbuild(vcproj, "DLL (Release)", "Win32")

        print("\nBuilding debug...\n")
        libpack.vcbuild(vcproj, "DLL (Debug)", "Win32")

        os.chdir(old_dir)


def install(libpack):
    tmp_install = os.path.join(libpack.config.get("Paths", "workspace"),
                               "tmp_install")
    if not os.path.exists(tmp_install):
        os.mkdir(tmp_install)

    if libpack.toolchain.startswith("vc"):
        os.chdir("build\\msvc9")

        os.environ["COINDIR"] = tmp_install
        utils.run_shell("..\misc\install-sdk.bat dll release msvc9 soqt1",
                        env=os.environ)
        utils.run_shell("..\misc\install-sdk.bat dll debug msvc9 soqt1",
                        env=os.environ)
        os.chdir("..\\..")

    files = utils.move(os.path.join(tmp_install, "include", "Inventor"),
                       libpack.path, "include\\Inventor", root=False)

    files.extend(utils.move(os.path.join(tmp_install, "lib"),
                            libpack.path, "lib", root=False))
    files.extend(utils.move(os.path.join(tmp_install, "bin"),
                            libpack.path, "bin", root=False))

    libpack.manifest_add(name, version, files)

    utils.shutil.rmtree(tmp_install)

