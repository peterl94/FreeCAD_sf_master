import libpack_utils as utils
import os

name = "f2c"
version = "2014"
source = {"type":"archive", "url":"http://www.netlib.org/cgi-bin"\
          "/netlibfiles.pl?format=zip&filename=/f2c/libf2c.zip"}
depends_on = []
patches = []

def download_f2csrc_http(outdir):
    url = "http://www.netlib.org/f2c/src/"
    utils.urllib.urlretrieve(url, "index.html")

    filenames = []

    with open("index.html", "rb") as f:
        for line in f:
            if line.startswith('file\t<a href="'):
                name = line.split('file\t<a href="')[1].split('"')[0]
                filenames.append(name)

    print("Downloading f2c source...")		    
    for n in filenames:
        #print(n)
        utils.urllib.urlretrieve("http://www.netlib.org/f2c/src/" + n,
                                 os.path.join(outdir, n))

def build(libpack):
    if not os.path.exists("libf2c"):
        os.mkdir("libf2c")
        utils.run_cmd("7z", ["x", "-y", "-olibf2c", "libf2c.zip"], silent=True)

    if not os.path.exists("src"):
        os.mkdir("src")
        download_f2csrc_http("src")

    if libpack.toolchain.startswith("vc"):
        utils.apply_patch(os.path.join(os.path.dirname(__file__),
                                       "..\\patches\\f2c_ssize_t.diff"))
        utils.apply_patch(os.path.join(os.path.dirname(__file__),
                                       "..\\patches\\f2c_makefile.diff"))

        os.chdir("src")
        print("\nBuilding f2c.exe...\n")
        utils.run_cmd("nmake", ["/f", "makefile.vc", "f2c.exe"])
        os.chdir("..")

        os.chdir("libf2c")
        print("\nBuilding f2c.lib...\n")
        utils.run_cmd("nmake", ["/f", "makefile.vc"])
        os.chdir("..")


def install(libpack):
    files = utils.copyfiles(["src\\f2c.exe"], libpack.path, "bin")
    files.extend(utils.copyfiles(["libf2c\\f2c.h"], libpack.path, "include"))
    files.extend(utils.copyfiles(["libf2c\\vcf2c.lib"], libpack.path, "lib"))

    libpack.manifest_add(name, version, files)

