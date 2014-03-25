import libpack_utils as utils
import os

name = "boost"
version = "1.55"
source = {"type":"archive", "url":
          "http://sourceforge.net/projects/boost/files/boost/1.55.0"\
          "/boost_1_55_0.zip"}
depends_on = []
patches = ["boost"]
    
def build(libpack):
    if libpack.toolchain.startswith("vc"):
        print("\nBuilding release and debug...\n")
        utils.run_shell("bootstrap")
        if libpack.toolchain == "vc9":
            utils.run_shell("b2 toolset=msvc-9.0 link=shared "\
                            "variant=debug,release "\
                            "--with-filesystem --with-program_options "\
                            "--with-regex --with-signals --with-system "\
                            "--with-thread", env=os.environ)
        if libpack.toolchain == "vc12":
            utils.run_shell("b2 toolset=msvc-12.0 link=shared "\
                            "variant=debug,release "\
                            "--with-filesystem --with-program_options "\
                            "--with-regex --with-signals --with-system "\
                            "--with-thread", env=os.environ)

    
def install(libpack): 
    files = utils.copytree("boost", libpack.path, "include\\boost")
    
    files.extend(utils.copytree("stage\\lib", libpack.path, "lib", root=False,
                                ignore=utils.ignore_names_inverse(["*.lib"])))
    files.extend(utils.copytree("stage\\lib", libpack.path, "bin", root=False,
                                ignore=utils.ignore_names_inverse(["*.dll"])))
    
    libpack.manifest_add(name, version, files)

