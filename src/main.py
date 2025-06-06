# TODO Make patches great again
# TODO Generate parametrized .sv files from regtool.py
# TODO calculate relative path between module and working_dir/pulp_soc
# NOTE the output is a pulp-platform directory where pulpissimo and pulp-runtime, at least, are git repos
from os import system as sys
import os
import subprocess

# from patch import patch_gen
import monopatch

path = "../pulp-platform.out"  # the path of the pulp-platform directory
branch_name = "develop"
module_path = "../wide_alu.in"


def main():
    branch(f"{path}/pulpissimo", branch_name)
    branch(f"{path}/pulp-runtime", branch_name)
    bender_init()
    patch(f"{path}/pulpissimo/working_dir/pulp_soc", "test", module_path, "pulp_soc")
    patch(f"{path}/pulp-runtime", "test", module_path, "pulp-runtime")

    # print(
    #     subprocess.check_output(["git"])
    # )


def branch(repo_path, branch_name):
    if not branch_exists(repo_path, branch_name):
        sys(f"""git -C {repo_path} branch {branch_name} && 
            git -C {repo_path} checkout {branch_name}""")
    else:
        print(f"branch {branch_name} already exists")


def branch_exists(repo_path, branch_name):
    out = subprocess.check_output(
        f"git -C {repo_path} branch --list {branch_name}".split(" ")
    )
    return True if out != b"" else False


def bender_init():
    print("Initializing bender project")
    # bender_path = f"{path}/pulpissimo/bender"
    command = f""" cd {path}/pulpissimo
make checkout &&
./bender update &&
./bender checkout &&
./bender clone pulp_soc
"""
    if not os.path.exists(f"{path}/pulpissimo/working_dir/pulp_soc"):
        sys(command)


def patch(repo_dir, module_name, module_path, repo):
    with open(f"{repo_dir}/patch.diff", "w") as f:
        f.write(monopatch.patch(module_name, module_path)[repo])
    print("applying patch")
    sys(f"git -C {repo_dir} apply patch.diff")


#     command = f'''
# cd {directory} &&

# '''

if __name__ == "__main__":
    main()
