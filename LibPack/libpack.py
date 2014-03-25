from __future__ import print_function
import logging
import sys
import os
import shutil
import optparse
import pkgutil
import sqlite3
import textwrap
from ConfigParser import SafeConfigParser
from subprocess import CalledProcessError

import libpack_utils as utils

LIBPACK = None

class LibPackError(Exception):
    pass

class LibPack:
    """
    Create and maintain a set of compiled libraries
    """
    def __init__(self, config_path=None):
        self.config = SafeConfigParser()
        self.exists = False
        self.path = None
        self.toolchain = None
        self.arch = None
        
        self._build_formulas = {}
        self._config_file_path = None
        self._manifest_path = None

        self.cmake_generator = None
        self.cmake_projext = ".vcproj"
        
        self._load_config(config_path)

        if not os.path.exists(self.config.get("Paths", "root_dir")):
            os.mkdir(self.config.get("Paths", "root_dir"))
        if not os.path.exists(self.config.get("Paths", "workspace")):
            os.mkdir(self.config.get("Paths", "workspace"))
        self.write_config_file()
        
    def _load_config(self, path):
        default_dir = os.path.join(os.path.expanduser('~'), "FClib_pkg")
        if path == None:
            path = os.path.join(default_dir, "FCLib_pkg.cfg")
        if os.path.exists(path):
            with open(path, "r") as config_file:
                self.config.readfp(config_file)
        self.config_file_path = path
        
        #setup default options if they don't exist   
        path_opts = [("root_dir",default_dir),
                     ("libpack_dir","%(root_dir)s"),
                     ("workspace","%(root_dir)s" + os.path.sep + "workspace")]
        self._set_config_defaults("Paths", path_opts)
        self._set_config_defaults("LibPack", [("name_template",
                                              "FCLibs_{arch}_{toolchain}")])
        
        if self.config.has_option("LibPack", "path"):
            #use an existing LibPack
            self._setup_from_existing()
            
    def _set_config_defaults(self, section, options):
        if not self.config.has_section(section):
            self.config.add_section(section)
        for item in options:
            if not self.config.has_option(section, item[0]):
                self.config.set(section, item[0], item[1])
                
    def _setup_from_existing(self):
        libpack_path = self.config.get("LibPack", "path")
        if os.path.exists(libpack_path):
            manifest_path = os.path.join(libpack_path, "MANIFEST.db")
            if os.path.exists(manifest_path):
                self._manifest_path = manifest_path
                self._setup_from_manifest()
                self.exists = True
                self.path = libpack_path
                return
        print("Config [LibPack] 'path' not set to valid LibPack:", libpack_path,
              file=sys.stderr)
            
    def _setup_from_manifest(self):
        if self._manifest_path != None:
            conn = sqlite3.connect(self._manifest_path)
            cursor = conn.cursor()
            r = cursor.execute("SELECT toolchain, arch FROM info").fetchone()
            self.toolchain = r[0]
            self.arch = r[1]
            conn.commit()
            conn.close()
        
    def _setup_manifest(self):
        #must be called after self.path is set
        self._manifest_path = os.path.join(self.path, "MANIFEST.db")
        conn = sqlite3.connect(self._manifest_path)
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE installed"
                       "(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                       "name TEXT UNIQUE, version TEXT)")
        cursor.execute("CREATE TABLE files (id INT, name TEXT)")

        cursor.execute("CREATE TABLE info (toolchain TEXT, arch TEXT)")
        cursor.execute("INSERT INTO info VALUES (?,?)", (self.toolchain, self.arch))

        conn.commit()
        conn.close()

    def _load_build_formulas(self, formula_pkg):
        for importer, name, ispkg in pkgutil.iter_modules(formula_pkg.__path__):
            full_name = "BuildFormulas." + name
            module = importer.find_module(name).load_module(full_name)
            
            valid = True
            attributes = ["name", "version", "source", "depends_on", "patches",
                          "build", "install"]
            
            if not hasattr(module, "meta"):
                setattr(module, "meta", False)
                
            if module.meta:
                #required attrs for meta formulas
                attributes = ["name", "depends_on"]

            for attr in attributes:
                if not hasattr(module, attr):
                    valid = False
                    print(module.__name__ + " has no attribute " + attr,
                          file=sys.stderr)
                    bad = module.__name__

            if not valid:
                raise ValueError("Invalid build formula: " + bad)
            
            self._build_formulas[module.name] = module

    def write_config_file(self):
        """
        Write in-memory configuration to disk
        """
        with open(self.config_file_path, "wb") as config_file:
            self.config.write(config_file)

    def manifest_add(self, lib_name, lib_version, filenames):
        """
        Add file or directory to manifest database
        """
        if self._manifest_path != None:
            conn = sqlite3.connect(self._manifest_path)
            cursor = conn.cursor()
            id_query = "SELECT id FROM installed WHERE name = ?"
            #make sure lib is not already inserted into installed table
            if cursor.execute(id_query, (lib_name,)).fetchone() == None:
                
                query = "INSERT INTO installed (name, version) VALUES (?,?)"
                cursor.execute(query, (lib_name, lib_version))

            lib_id = cursor.execute(id_query, (lib_name,)).fetchone()[0]
            
            for name in filenames:
                cursor.execute("INSERT INTO files VALUES (?,?)", (lib_id, name))

            conn.commit()
            conn.close()

    def manifest_remove(self, lib_name):
        """
        Remove all entries associated with lib_name
        """
        if self._manifest_path != None:
            conn = sqlite3.connect(self._manifest_path)
            cursor = conn.cursor()
            files_delete = None
            
            id_query = "SELECT id FROM installed WHERE name = ?"
            row = cursor.execute(id_query, (lib_name,)).fetchone()
            if row != None:
                lib_id = row[0]

                query = "SELECT name FROM files WHERE id = ?"
                files_delete = cursor.execute(query, (lib_id,)).fetchall()
                cursor.execute("DELETE FROM files WHERE id = ?", (lib_id,))

                cursor.execute("DELETE FROM installed WHERE id = ?", (lib_id,))

            conn.commit()
            conn.close()

            return files_delete

    def new(self, toolchain, arch):
        """
        Setup a new LibPack
        """

        name = self.config.get("LibPack", "name_template").format(
            toolchain=toolchain, arch=arch)
        libpack_path = os.path.join(self.config.get("Paths","libpack_dir"), name)

        if os.path.exists(libpack_path):
            raise ValueError("Directory already exsits: " + libpack_path)

        os.mkdir(libpack_path)
        os.mkdir(os.path.join(libpack_path, "include"))
        os.mkdir(os.path.join(libpack_path, "lib"))
        os.mkdir(os.path.join(libpack_path, "bin"))
        #os.mkdir(os.path.join(libpack_path, "share"))

        self.exists = True
        self.path = libpack_path
        self.toolchain = toolchain
        self.arch = arch
        
        self._setup_manifest()
        self.config.set("LibPack", "path", libpack_path)
        self.write_config_file()

        print("Successfully created empty LibPack:", self.path)

    def is_installed(self, name):
        conn = sqlite3.connect(self._manifest_path)
        cursor = conn.cursor()

        row = cursor.execute("SELECT * FROM installed WHERE name = ?",
                             (name,)).fetchone()
        conn.commit()
        conn.close()

        return row != None
    
    def install(self, name, force=False):
        if not self.exists:
            raise LibPackError("Config [LibPack] 'path' not set (have you run 'new'?)")

        if not force and self.is_installed(name):
            print(name + " is already installed")
            return

        if self._build_formulas == {}:
            import BuildFormulas
            self._load_build_formulas(BuildFormulas)
            
        try:
            formula = self._build_formulas[name]
        except KeyError:
            raise LibPackError("No build formula found for " + name)

        utils.setup_env(self.toolchain, self.arch)


        if self.toolchain.startswith("vc"):
            if self.toolchain == "vc9":
                self.cmake_generator = "Visual Studio 9 2008"
                self.cmake_projext = ".vcproj"
            elif self.toolchain == "vc12":
                self.cmake_generator = "Visual Studio 12"
                self.cmake_projext = ".vcxproj"
                        
        
        #install dependencies
        print("Dependencies: {0}\n".format(formula.depends_on)) 
        for n in formula.depends_on:
            self.install(n)

        if not formula.meta:
            src_dir = utils.get_source(formula.source, 
                                       self.config.get("Paths", "workspace"),
                                       formula.name + "-" + formula.version)

            if formula.patches:
                print("Patching:")
                patch_dir = os.path.join(os.path.dirname(__file__), "patches")
                for n in formula.patches:
                    print("\t{0}".format(n))
                    patch_file = os.path.join(patch_dir, "{0}\\{1}.diff".format(self.toolchain, n))
                    if not os.path.exists (patch_file):
                        patch_file = os.path.join(patch_dir, "{0}.diff".format(n))
                    if not os.path.exists (patch_file):
                        print("patch not found: {0}".format(n))
                    else:
                        path_result = utils.apply_patch(patch_file, src_dir)
                        #if not path_result:
                        #    print("\t FAILED!")
                        #    exit(1)
            
            old_cwd = os.getcwd()
            os.chdir(src_dir)

            try:
                print("Building {0}...\n".format(name))
                formula.build(self)
                print("Installing {0}...\n".format(name))
                formula.install(self)
                print("Successfully installed {0}\n".format(name))
            except CalledProcessError as e:
                print(e)
                #start shell for debugging
                utils.run_cmd("cmd")
            
            os.chdir(old_cwd)
        

    def uninstall(self, name):
        if not self.is_installed(name):
            raise LibPackError(name + " is not installed")
        
        files_delete = self.manifest_remove(name)
        for item in files_delete:
            path = os.path.join(self.path, item[0])
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
        print("Successfully uninstalled " + name)

    def vcbuild(self, proj, config, platform, extras=[]):
        if self.toolchain.startswith("vc"):
            if self.toolchain == "vc9":
        	utils.run_cmd("vcbuild", [proj, "{0}|{1}".format(config, platform)] + extras)
            elif self.toolchain == "vc12":
        	utils.run_cmd("msbuild", [proj, "/p:Configuration=" + config, "/p:Platform=" + platform] + extras)
        else:
            self.error("unsupported toolchain " + toolchain)


class CustomHelpFormatter(optparse.IndentedHelpFormatter):
    def __init__(self,
                 indent_increment=0,
                 max_help_position=24,
                 width=None,
                 short_first=0):
        optparse.IndentedHelpFormatter.__init__(
            self, indent_increment, max_help_position, width, short_first)
        
    def format_description(self, description):
        paragraphs = description.split("\n\n")
        result = []
        
        for p in paragraphs:
            s = optparse.IndentedHelpFormatter.format_description(self, p)
            if s:
                result.append(s)
                result.append('\n')
        if result:
            #drop last \n
            return "".join(result[:-1])
        return ""
        
class Subcommand:
    def __init__(self, name, options=[], args=None, callback=None,
                 usage="", short_help="", detailed_help=""):
        self.name = name
        self.options = options
        self.args = args
        self.callback = callback
        self.usage = usage
        self.short_help = short_help
        self.detailed_help = detailed_help
        
    def parse_args(self, arg_list):
        help = self.short_help + "\n\n" + self.detailed_help
        
        parser = optparse.OptionParser(usage=self.usage, description=help,
                                       formatter=CustomHelpFormatter())
        parser.add_options(self.options)
        opts, args = parser.parse_args(arg_list)
        
        if self.callback != None:
            self.callback(parser, opts, args)
            
        parser.destroy()
        
class CommandParser(optparse.OptionParser):
    def __init__(self, usage=None, description=None):
        optparse.OptionParser.__init__(self, usage=usage, description=description)

        self.subcommands = {}

    def add_subcommand(self, name, options=[], args=None, callback=None,
                       usage="", short_help="", detailed_help=""):
        self.subcommands[name] = Subcommand(name, options, args, callback,
                                            usage, short_help, detailed_help)

    def add_option(self, *args, **kwargs):
        if "subcmd" in kwargs.keys():
            name = kwargs.pop("subcmd")
            self.subcommands[name].options.append(optparse.Option(*args, **kwargs))
        else:
            optparse.OptionParser.add_option(self, *args, **kwargs)

    def parse_args(self, args=None, values=None):
        if args == None:
            args = sys.argv[1:]
        
        if args[0] in self.subcommands.keys():
            self.subcommands[args[0]].parse_args(args[1:])
        elif not args[0].startswith("-"):
            self.error("unknown subcommand " + args[0])
        else:
            optparse.OptionParser.parse_args(self, args, values)
    
    def _compute_help_indentation(self, formatter):
        formatter.indent()
        max_len = 0
        #find the longest command name
        for k in self.subcommands.keys():
            max_len = max(max_len, len(self.subcommands[k].name) + formatter.current_indent)
        formatter.dedent()
        
        formatter.help_position = min(max_len + 2, formatter.max_help_position)
        formatter.help_width = max(formatter.width - formatter.help_position, 11)
        
    def format_command_help(self, formatter):
        self._compute_help_indentation(formatter)
        command_help = []
        command_help.append(formatter.format_heading("Commands"))

        formatter.indent()
        
        help_list = []
        for k in self.subcommands.keys():
            cmd = self.subcommands[k]
            width = formatter.help_position - formatter.current_indent - 2
            cmd_str = "%*s%-*s  " % (formatter.current_indent, "", width, cmd.name)
            indent_first = 0
            help_list.append(cmd_str)
            
            if cmd.short_help:
                help_lines = textwrap.wrap(cmd.short_help, formatter.help_width)
                help_list.append("%*s%s\n" % (indent_first, "", help_lines[0]))
                help_list.extend(["%*s%s\n" % (formatter.help_position, "", line)
                               for line in help_lines[1:]])
        
            else:
                help_list.append("\n")
                
        command_help.append("".join(help_list))
        command_help.append("\n")
        
        formatter.dedent()
        
        return "".join(command_help)
        
    def format_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        result = []
        if self.usage:
            result.append(self.get_usage() + "\n")
        if self.description:
            result.append(self.format_description(formatter) + "\n")
        result.append(self.format_command_help(formatter))
        result.append(self.format_option_help(formatter))
        result.append(self.format_epilog(formatter))
        return "".join(result)

def on_new(parser, options, args):
    if not args:
        parser.error("toolchain argument is required")
    if args[0] != "vc9" and args[0] != "vc12":
        parser.error("only vc9, vc12 are supported at the moment")
    if options.arch != "x86":
        parser.error("only x86 is supported at the moment")
    LIBPACK.new(args[0], options.arch)

def on_install(parser, options, args):

    if options.install_all:
        import BuildFormulas
        LIBPACK._load_build_formulas(BuildFormulas)
        args = LIBPACK._build_formulas
    
    if not args:
        parser.error("no formula specified")
    for n in args:
        LIBPACK.install(n, force=options.force_install)

def on_uninstall(parser, options, args):
    if not args:
        parser.error("no formula specified")
    for n in args:
        LIBPACK.uninstall(n)

def setup_parser(parser):
    parser.usage = "%prog <command> [options]" 
    parser.description = "Type '%prog <command> --help' for more information "\
                         "on a specific command"
    
    usage = "{0} {1} [options]"
    help = "Sets up a new LibPack"
    parser.add_subcommand("new", callback=on_new,
                          usage=usage.format("new","TOOLCHAIN"), 
                          short_help=help,
                          detailed_help="Currently, only vc9 is the only supported TOOLCHAIN, and only x86")
    parser.add_option("-a", subcmd="new", dest="arch",
                      choices=["x86","x64"], default="x86",
                      help="Set build architecure {x86, x64} [default: %default]")

    help = "Install a library into the LibPack"
    parser.add_subcommand("install", callback=on_install,
                          usage=usage.format("install","FORMULA"),short_help=help)

    parser.add_option("-A", subcmd="install", dest="install_all", action="store_true",
                      help="Build all formulae")

    parser.add_option("-f", "--force", subcmd="install", dest="force_install", action="store_true",
                      help="Force building formulae")
    

    help = "Remove a library from the LibPack"
    parser.add_subcommand("uninstall", callback=on_uninstall,
                          usage=usage.format("uninstall","FORMULA"),short_help=help)

def main():
    global LIBPACK

    root = logging.getLogger()

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)
    
    try:
        LIBPACK = LibPack()
        parser = CommandParser()
        setup_parser(parser)
        parser.parse_args()
    except (ValueError, LibPackError) as e:
        print(e, file=sys.stderr)
        
if __name__ == "__main__":
    main()
