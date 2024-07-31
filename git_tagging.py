import argparse
import os
from os.path import join as pjoin
from git import Repo
import xml.etree.ElementTree as et

dry_run = True


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_project_root():
    """Finding the root directory of the project."""
    current_dir = os.getcwd()
    while True:
        if os.path.exists(pjoin(current_dir, '.repo')):
            return current_dir
        elif os.path.dirname(current_dir) == current_dir:
            print("Project root not found, exiting")
            exit(os.EX_USAGE)
        current_dir = os.path.dirname(current_dir)


def update_release_tag(git_path, tag_name, fallback=False):
    """Update or create a release tag in this repository."""
    if not os.path.exists(git_path) or not os.path.exists(pjoin(git_path, '.git')):
        print(f"{BColors.FAIL}Not a valid Git repository: {git_path}{BColors.ENDC}")
        return
    try:
        repo = Repo(git_path)
        repo.remotes.origin.fetch()
        if tag_name in repo.tags:
            print(f"{git_path.split('/')[-1]} -> tag {tag_name} already exists")
        else:
            if fallback:
                print(f"Creating fallback tag {tag_name} in {git_path}")
            else:
                print(f"Creating tag {tag_name} in {git_path}")
            if not dry_run:
                new_tag = repo.create_tag(tag_name)
                repo.remotes.origin.push(new_tag)
    except Exception as error:
        print(f"{BColors.WARNING} {git_path} is missing or broken{BColors.ENDC},\n{error}")


def update_release_tags(project_root, cur_manifest, name_map):
    """Update release tags for all projects."""
    print(f"{BColors.HEADER}-== UPDATING TAGS ==-{BColors.ENDC}")
    if dry_run:
        print(f"{BColors.WARNING}Dry run, to create tags add --apply argument{BColors.ENDC}")
    for project in cur_manifest.iter('project'):
        name = project.attrib.get('name')
        path = project.attrib.get('path')
        project_path = pjoin(project_root, path)
        if name in name_map:
            if os.path.exists(project_path):
                if os.path.exists(pjoin(project_path, '.git')):
                    print(f"Updating tag for project: {name}")
                    update_release_tag(project_path, name_map[name])
                else:
                    print(f"{BColors.FAIL}Not a valid Git repository: {project_path}{BColors.ENDC}")
            else:
                print(
                    f"{BColors.WARNING}Project path does not exist: {project_path}. Creating tag in current project.{BColors.ENDC}")
                current_project_path = os.getcwd()
                update_release_tag(current_project_path, name_map[name], fallback=True)
        else:
            print(
                f"{BColors.FAIL}No tag mapping found for project: {name}. Creating tag in current project with the missing project's name.{BColors.ENDC}")
            current_project_path = os.getcwd()
            update_release_tag(current_project_path, name, fallback=True)


def get_name_tag_map(project_root, prev_release, new_release):
    """Creating a map of project tag names."""
    name_map = {}
    for project in os.listdir(pjoin(project_root, ".repo", "manifests")):
        if project == "default.xml":
            tree = et.parse(pjoin(project_root, ".repo", "manifests", project))
            for proj in tree.getroot().iter('project'):
                name_map[proj.attrib['name']] = proj.attrib['upstream'].replace(prev_release, new_release)
    return name_map


def update_revision(project, name_map):
    """Update project revision to tag name."""
    name = project.attrib.get('name')
    tag_name = name_map[name]

    if project.attrib.get('revision') != tag_name:
        action = f"{BColors.OKGREEN}Update existing{BColors.ENDC}"
    else:
        action = 'Skip'
    
    print(f"{action} {name} to {tag_name}")
    project.set('revision', tag_name)


def update_revisions(cur_manifest, name_map):
    """Update tags for all projects."""
    print(f"{BColors.HEADER}-== UPDATING MANIFEST ==-{BColors.ENDC}")
    for project in cur_manifest.iter('project'):
        update_revision(project, name_map)


def main(args):
    global dry_run
    dry_run = not args.apply
    if args.p is None:
        args.p = args.r
    os.system("repo sync")
    project_root = get_project_root()
    name_map = get_name_tag_map(project_root, args.p, args.r)
    tree = et.parse(pjoin(project_root, ".repo/manifests/default.xml"))
    cur_manifest = tree.getroot()
    update_release_tags(project_root, cur_manifest, name_map)
    update_revisions(cur_manifest, name_map)
    new_manifest_path = pjoin(project_root, f".repo/manifests/{args.r}_manifest.xml")
    tree.write(new_manifest_path)
    print(f"{BColors.OKGREEN}New manifest is created in {new_manifest_path}\nManual merge step to default.xml is still required{BColors.ENDC}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', metavar="RELEASE", help='Release version, e.g v700')
    parser.add_argument('-p', metavar="PREVIOUS_RELEASE", help='Previous release version, e.g v600, used as a reference for the tag naming')
    parser.add_argument('--apply', help='Set to create release tags in repositories', default=False, action='store_true')
    main(parser.parse_args())
