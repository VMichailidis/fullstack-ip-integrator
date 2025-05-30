from templates import patches
import sys

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print(f"""
    Error: Not enough arguments!
    Run uv run {sys.argv[0]} --help for argument values""")
        exit()
    elif sys.argv[1] == "--help":
        print(f"""
    Usage: $python {sys.argv[0]} [MODULENAME] [REPO]
    Return patch in order to connect MODULENAME to pulp-platform sub-REPO
    via AXI""")
        exit()
    module_name = sys.argv[1]
    repo = sys.argv[2]
    patch_acc = ""
    for patch in patches(module_name):
        if patch["repo"] == repo:
            patch_acc += patch["patch"].rstrip()
    print(patch_acc)


def patch_gen(module_name, repo):
    patch_acc = ""
    for patch in patches(module_name):
        if patch["repo"] == repo:
            patch_acc += patch["patch"].rstrip()
    # print(patch_acc)
    return patch_acc
