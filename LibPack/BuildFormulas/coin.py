import libpack_utils as utils
import os

name = "coin"
version = "3.1.3"
source = {"type":"archive", "url":
          "https://bitbucket.org/Coin3D/coin/downloads/Coin-3.1.3.zip"}
depends_on = []
patches = ["coin_macro_error", "coin_config"]

def build(libpack):

    if libpack.toolchain.startswith("vc"):

        old_dir = os.getcwd()
        os.chdir("build\\msvc9")

        vcproj = "coin3.vcproj"

        if libpack.toolchain == "vc12":

            if utils.check_update(vcproj, "coin3.vcxproj"):
                utils.run_cmd("devenv", ["/upgrade", "coin3.sln"])

            vcproj = "coin3.vcxproj"


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
        if libpack.toolchain == "vc9" or libpack.toolchain == "vc12":
            os.chdir("build\\msvc9")

            os.environ["COINDIR"] = tmp_install
            utils.run_shell("..\misc\install-sdk.bat dll release msvc9 coin3",
                            env=os.environ)
            utils.run_shell("..\misc\install-sdk.bat dll debug msvc9 coin3",
                            env=os.environ)
            os.chdir("..\\..")

    files = utils.move(os.path.join(tmp_install, "include"),
                       libpack.path, "include", root=False)

    files.extend(utils.move(os.path.join(tmp_install, "lib"),
                            libpack.path, "lib", root=False))
    files.extend(utils.move(os.path.join(tmp_install, "bin"),
                            libpack.path, "bin", root=False))

    libpack.manifest_add(name, version, files)

    utils.shutil.rmtree(tmp_install)

