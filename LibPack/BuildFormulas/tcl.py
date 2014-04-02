import libpack_utils as utils
import os

name = "tcl"
version = "8.6.1"
source = {
    "type":"archive",
    "url": "http://prdownloads.sourceforge.net/tcl/tcl{0}-src.tar.gz".format(version)
}
depends_on = []
patches = []

def build(libpack):

    if libpack.toolchain.startswith("vc"):

        os.chdir("win")

        utils.run_cmd("nmake", ["/f", "makefile.vc"])


def install(libpack):

    if libpack.toolchain.startswith("vc"):
        old_dir = os.getcwd()
        os.chdir("win")

        utils.run_cmd("nmake", ["/f", "makefile.vc",
                                "INSTALLDIR={0}".format(libpack.tmp_install),
                                "install" ])

        os.chdir(old_dir)

    # install-private-headers would have been nice...
    files = utils.copyfiles(["generic\\tclInt.h",
                             "generic\\tclIntDecls.h",
                             "generic\\tclIntPlatDecls.h",
                             "generic\\tclPort.h",
                             "generic\\tclOOInt.h",
                             "generic\\tclOOIntDecls.h",
                             "win\\tclWinPort.h"],
                            libpack.path, "include");

    os.chdir(libpack.tmp_install)

    files.extend(utils.copytree("bin", libpack.path, "bin", root=False))
    files.extend(utils.copytree("lib", libpack.path, "lib", root=False))
    files.extend(utils.copytree("include", libpack.path, "include", root=False))

    libpack.manifest_add(name, version, files)
