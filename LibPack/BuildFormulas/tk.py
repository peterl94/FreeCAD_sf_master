import libpack_utils as utils
import os

name = "tk"
version = "8.6.1"
source = {
    "type":"archive",
    "url": "http://prdownloads.sourceforge.net/tcl/tk{0}-src.tar.gz".format(version)
}
depends_on = ["tcl"]
patches = []

def build(libpack):

    if libpack.toolchain.startswith("vc"):

        os.chdir("win")

        os.environ["TCLDIR"] = libpack.get_formula_dir("tcl")

        utils.run_cmd("nmake", ["/f", "makefile.vc"])


def install(libpack):

    if libpack.toolchain.startswith("vc"):
        old_dir = os.getcwd()
        os.chdir("win")

        utils.run_cmd("nmake", ["/f", "makefile.vc",
                                "_INSTALLDIR={0}".format(libpack.tmp_install),
                                "install" ])

        os.chdir(old_dir)

    # install-private-headers would have been nice...
    files = utils.copyfiles(["generic\\tklInt.h",
                             "generic\\tkIntDecls.h",
                             "generic\\tkIntPlatDecls.h",
                             "generic\\tkPort.h",
                             "win\\tkWinPort.h",
                             "win\\tkWinInt.h",
                             "win\\tkWin.h"],
                            libpack.path, "include");

    os.chdir(libpack.tmp_install)

    files.extend(utils.copytree("bin", libpack.path, "bin", root=False))
    files.extend(utils.copytree("lib", libpack.path, "lib", root=False))
    files.extend(utils.copytree("include", libpack.path, "include", root=False))

    libpack.manifest_add(name, version, files)
