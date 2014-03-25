from __future__ import print_function
import shutil
import os
import sys
import fnmatch
import subprocess
import urllib

import patch

_original_env = os.environ.copy()
_commands = {}

class CommandNotFound(Exception):
    pass

def find_command(name):
    if sys.platform == "win32":
        name = name + ".exe"
        
    env_path = os.environ["PATH"].split(os.pathsep)
    env_path.extend(_original_env["PATH"].split(os.pathsep))
    
    for path in env_path:
        full_name = os.path.join(path, name)
        if os.path.isfile(full_name):
            return full_name
    raise CommandNotFound("Cannot find {0} in PATH".format(name))


def run_cmd(name, args=[], env=None, silent=False):
    if not env:
        env=os.environ
        
    if not _commands.has_key(name):
        _commands[name] = find_command(name)

    cmd_line = [_commands[name]]
    cmd_line.extend(args)
    
    if silent:
        with open(os.devnull, 'wb') as devnull:
            subprocess.check_call(cmd_line, stdout=devnull,
                                  stderr=devnull, env=env)
    else:
        subprocess.check_call(cmd_line, env=env)

def run_shell(args, env=None):
    return subprocess.call(args, shell=True, env=env)

def apply_patch(patch_filename, root_dir=None):
    p = patch.fromfile(patch_filename)
    if not p:
        return p
    return p.apply(root=root_dir)

def environ_from_bat(bat_file, args, initial_env=None):
    """
    Get environment modified by .bat file by parsing the output of set
    called in the same shell
    """
    cmd = 'cmd.exe /s /c ""{0}" {1} && echo OutputSeparator && set"'.format(
        bat_file, args)
    output = subprocess.check_output(cmd, shell=True, env=initial_env)
    env_dump = output.split("OutputSeparator")[1]

    new_environ = {}

    for line in env_dump.strip().split("\r\n"):
        pair = line.split("=")
        new_environ[pair[0].upper()] = pair[1]

    return new_environ

def setup_env(toolchain, arch):
    """
    Setup build environment for specified toolchain.
    """
    
    #Minimum PATH for Windows
    #default_path = "C:\\Windows\\system32;C:\\Windows;C:\\Windows\\System32\\Wbem;"
    #os.environ["PATH"] = default_path
    
    if toolchain.startswith("vc"):
        #trimming "vc" gets the version
	vs_ver = toolchain[2:]
        vs_dir = "Microsoft Visual Studio {0}.0".format(vs_ver)
        env_pattern = "C:\\{0}\\{1}\\VC\\vcvarsall.bat"

	env_bat = None

	comntools = os.environ["VS{0}0COMNTOOLS".format(vs_ver)]
	if comntools and os.path.exists("{0}vsvars32.bat".format(comntools)):
	    env_bat = "{0}vsvars32.bat".format(comntools)

	if not env_bat and comntools and os.path.exists("{0}vcvarsall.bat".format(comntools)):
	    env_bat = "{0}vcvarsall.bat".format(comntools)

        if not env_bat and os.path.exists(env_pattern.format("Program Files (x86)", vs_dir)):
            env_bat = env_pattern.format("Program Files (x86)", vs_dir)

        if not env_bat and os.path.exists(env_pattern.format("Program Files", vs_dir)):
            env_bat = env_pattern.format("Program Files", vs_dir)

	if not env_bat:
            raise ValueError("Could not find vcvarsall.bat for " + toolchain)
            
        if arch == "x64":
            #first check if x64 tools are installed
            if subprocess.check_output([env_bat, "amd64"]) == '':
                os.environ = environ_from_bat(env_bat, "amd64")
            elif subprocess.check_output([env_bat, "x86_amd64"]) == '':
                os.environ = environ_from_bat(env_bat, "x86_amd64")
            else:
                raise ValueError(toolchain +
                                 " vcvarsall.bat cannot find a x64 toolchain")
        else:
            #arch == x86
            #vcvarsall.bat should allways be able to find x86 tools
            os.environ = environ_from_bat(env_bat, "x86")
        #print(os.environ["PATH"])
            
    #elif toolchain == "mingw64":


def _download_progress(blocks, block_size, file_size):
    percent = min(blocks*block_size*100.0 / file_size, 100)
    print("{0:3.1f}%".format(percent), end='\r')
    
def get_source(source, dest_dir, name):
    if source["type"] == "archive":

        dest_src_dir = os.path.join(dest_dir, name)
        changed = False
        
        filename = os.path.basename(source["url"])
        dest_file = os.path.join(dest_dir, filename)

        if not os.path.exists(dest_file):
            print("Downloading {0}...".format(filename))
            urllib.urlretrieve(source["url"], dest_file, _download_progress)
            changed = True

        #get directory name by extracting to empty directory
        tmp_dir = os.path.join(dest_dir, "tmp_" + name)
        if changed or not os.path.exists(tmp_dir) or not os.listdir(tmp_dir):
            print("Extracting " + name)
            run_cmd("7z", ["x", "-y", "-o" + tmp_dir, dest_file], silent=True)
            changed = True

        #it might be a tar
        contents = os.listdir(tmp_dir)
        if contents[0].endswith(".tar"):
            dest_file = os.path.join(tmp_dir, contents[0])
            print("Extracting " + contents[0])
            run_cmd("7z", ["x", "-y", "-o" + tmp_dir, dest_file], silent=True)

        src_dir = ""    
        for n in os.listdir(tmp_dir):
            if not n.endswith(".tar"):
                src_dir = n
        
        #if os.path.exists(dest_src_dir):
            #shutil.rmtree(dest_src_dir)
            
        #os.rename(os.path.join(tmp_dir, src_dir), dest_src_dir)

        if not os.path.exists(dest_src_dir):
            os.rename(os.path.join(tmp_dir, src_dir), dest_src_dir)
            
        return dest_src_dir
    
    elif source["type"] == "git":
       run_cmd("git", ["clone", source["url"]])
       
def filter_multi(names, patterns):
    include_names = set()
    for p in patterns:
        matched = fnmatch.filter(names, p)
        for n in matched:
            include_names.add(n)
    return include_names

ignore_names = shutil.ignore_patterns

def ignore_names_inverse(patterns, dir_filter=["*"]):
    """
    Returns a function that can be used as copytree's ignore argument.
    All filenames that don't match a pattern in patterns will be ignored.
    Only include directories that don't match a pattern in dir_filter. 
    """
    def _ignore_function(path, names):
	include_names = filter_multi(names, patterns)
        exclude_dirs = filter_multi(names, dir_filter)
        ignore_names = set()
        for n in names:
            if os.path.isdir(os.path.join(path, n)):
                if n in exclude_dirs:
                    ignore_names.add(n)
            else:    
                if patterns and n not in include_names:
                    ignore_names.add(n)
            
        return ignore_names

    return _ignore_function

def copyfiles(src_patterns, dest_root, dest, ignore_patterns=None):
    """
    """
    copied = []
    abs_dest = os.path.join(dest_root, dest)

    files = set()
    rel_paths = set()
    for p in src_patterns:
        if os.path.isabs(p) and os.path.exists(p):
            files.add(p)
        else:
            rel_path = os.path.dirname(p)
            if not rel_path: rel_path = ".\\"
            rel_paths.add(rel_path)
            
    for p in rel_paths:
        contents = os.listdir(p)
        names = []
        ignore_files = set()
        for n in contents:
            names.append(os.path.join(p, n))
        if ignore_patterns != None:
            ignore_files = filter_multi(names, ignore_patterns)
        files = files.union(filter_multi(names, src_patterns) - ignore_files)
   
    for f in files:
        if not os.path.exists(abs_dest):
            os.mkdir(abs_dest)
        shutil.copy(f, abs_dest)
        copied.append(os.path.join(dest, os.path.basename(f)))

    return copied

def copytree(src, dest_root, dest, symlinks=False, root=True, ignore=None):
    """
    Copy an entire directory tree rooted at src.
    If root is False, only the contents of src is copied.
    """
    copied = []
    abs_dest = os.path.join(dest_root, dest)
    if not root:
        contents = os.listdir(src)
        
        ignore_names = set()
        if ignore != None:
            ignore_names = ignore(src, contents)
        
        for name in contents:
            if name not in ignore_names:
                subsrc = os.path.join(src, name)

                if os.path.isfile(subsrc):
                    if not os.path.exists(abs_dest):
                        os.mkdir(abs_dest)
                    print(os.path.join(abs_dest, name))
                    shutil.copy(subsrc, abs_dest)
                    copied.append(os.path.join(dest, name))
                elif os.path.isdir(subsrc):
                    #delete if already exists
                    dest_src = os.path.join(abs_dest, name)
                    print(dest_src)
                    if os.path.isdir(dest_src):
                        shutil.rmtree(dest_src)
                    
                    shutil.copytree(subsrc, dest_src, symlinks, ignore)
                    copied.append(os.path.join(dest, name))
    else:
        print(abs_dest)  
        if os.path.isdir(abs_dest):
            shutil.rmtree(abs_dest)
            
        shutil.copytree(src, abs_dest, symlinks, ignore)
        copied.append(dest)

    return copied
        
def move(src, dest_root, dest, root=True, ignore=None):
    """"
    Recursively move a file or directory.
    If root is False and src is a directory,
    only the contents of root_src is copied.
    """
    moved = []
    abs_dest = os.path.join(dest_root, dest)

    if not root and os.path.isdir(src):
        contents = os.listdir(src)
        
        ignore_names = []
        if ignore != None:
            ignore_names = ignore(src, contents)
        
        for name in contents:
            if name not in ignore_names:
                subsrc = os.path.join(src, name)
                #delete if already exists
                dest_src = os.path.join(abs_dest, name)
                if os.path.isdir(dest_src):
                    shutil.rmtree(dest_src)
                if os.path.isfile(dest_src):
                    os.remove(dest_src)
                print(os.path.join(abs_dest, name))    
                shutil.move(subsrc, abs_dest)
                moved.append(os.path.join(dest, name))
    else:
        #delete if already exists
        dest_src = os.path.join(abs_dest, os.path.basename(src))
        print(dest_src)
        if os.path.isdir(dest_src):
            shutil.rmtree(dest_src)
        if os.path.isfile(dest_src):
            os.remove(dest_src)
            
        shutil.move(src, abs_dest)
        moved.append(os.path.join(dest, os.path.basename(src)))

    return moved


def check_update(old_path, new_path):

    if not os.path.exists(old_path):
        return False

    if not os.path.exists(new_path):
        return True

    old_time = os.path.getmtime(old_path)
    new_time = os.path.getmtime(new_path)

    return old_time > new_time
    
