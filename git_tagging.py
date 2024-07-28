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
        print(current_dir)


# def update_release_tag(git_path, tag_name):
#     """Update or create a release tag in this repository."""
#     try:
#         repo = Repo(git_path)
#         repo.remotes.origin.fetch()
#         if tag_name in repo.tags:
#             print(f"{git_path.split('/')[-1]} -> tag {tag_name} already exists")
#         else:
#             print(f"Creating tag {tag_name} in {git_path}")
#             if not dry_run:
#                 new_tag = repo.create_tag(tag_name)
#                 repo.remotes.origin.push(new_tag)
#     except Exception as error:
#         print(f"{BColors.WARNING} {git_path} is missing or broken{BColors.ENDC},\n{error}")


# def update_release_tags(project_root, cur_manifest, name_map):
#     """Update release tags for all projects."""
#     print(f"{BColors.HEADER}-== UPDATING TAGS ==-{BColors.ENDC}")
#     if dry_run:
#         print(f"{BColors.WARNING}Dry run, to create tags add --apply argument{BColors.ENDC}")
#     for project in cur_manifest.iter('project'):
#         name = project.attrib.get('name')
#         update_release_tag(pjoin(project_root, name), name_map[name])


# def get_name_tag_map(project_root, prev_release, new_release):
#     """Creating a map of project tag names."""
#     name_map = {}
#     for project in os.listdir(pjoin(project_root, ".repo", "manifests")):
#         if project.endswith(".xml") and prev_release in project:
#             tree = et.parse(pjoin(project_root, ".repo", "manifests", project))
#             for proj in tree.getroot().iter('project'):
#                 name_map[proj.attrib['name']] = proj.attrib['upstream'].replace(prev_release, new_release)
#     return name_map


# def update_release_tags(project_root, cur_manifest, name_map):
#     """Функція для оновлення тегів релізу для всіх проектів."""
#     print(f"{BColors.HEADER}-== UPDATING TAGS ==-{BColors.ENDC}")
#     if dry_run:
#         print(f"{BColors.WARNING}Dry run, to create tags add --apply argument{BColors.ENDC}")
#     for project in cur_manifest.iter('project'):
#         name = project.attrib.get('name')
#         if name in name_map:
#             print(f"Updating tag for project: {name}")
#             update_release_tag(pjoin(project_root, name), name_map[name])
#         else:
#             print(f"{BColors.FAIL}No tag mapping found for project: {name}{BColors.ENDC}")


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
        project_path = pjoin(project_root, name)
        if name in name_map:
            if os.path.exists(project_path):
                if os.path.exists(pjoin(project_path, '.git')):
                    print(f"Updating tag for project: {name}")
                    update_release_tag(project_path, name_map[name])
                else:
                    print(f"{BColors.FAIL}Not a valid Git repository: {project_path}{BColors.ENDC}")
            else:
                # Якщо проект не існує, створити тег для поточного проекту з назвою неіснуючого проекту
                print(
                    f"{BColors.WARNING}Project path does not exist: {project_path}. Creating tag in current project.{BColors.ENDC}")
                current_project_path = os.getcwd()  # або вкажіть поточний проект вручну
                update_release_tag(current_project_path, name_map[name], fallback=True)
        else:
            print(f"{BColors.FAIL}No tag mapping found for project: {name}{BColors.ENDC}")


def get_name_tag_map(project_root, prev_release, new_release):
    """Creating a map of project tag names."""
    name_map = {}
    manifest_path = pjoin(project_root, ".repo", "manifests")

    # Обробка попереднього релізу
    prev_release_file = next((f for f in os.listdir(manifest_path) if f.endswith(".xml") and prev_release in f), None)
    if prev_release_file:
        tree = et.parse(pjoin(manifest_path, prev_release_file))
        for proj in tree.getroot().iter('project'):
            name_map[proj.attrib['name']] = proj.attrib['upstream'].replace(prev_release, new_release)

    # Обробка поточного маніфесту для відсутніх проектів
    current_manifest_file = "default.xml"
    tree = et.parse(pjoin(manifest_path, current_manifest_file))
    for proj in tree.getroot().iter('project'):
        if proj.attrib['name'] not in name_map:
            name_map[proj.attrib['name']] = proj.attrib['revision'].replace(prev_release, new_release)

    return name_map


def update_hash(project, project_root, name_map):
    """Update project revision hash."""
    name = project.attrib['name']
    tag_name = name_map.get(name)
    if tag_name:
        repo = Repo(pjoin(project_root, name))
        repo.git.checkout(tag_name)
        hash_val = repo.head.commit.hexsha
        if project.attrib.get('revision') != hash_val:
            print(f"{BColors.OKGREEN}Updating {name} to {hash_val[:12]}{BColors.ENDC}")
            project.set('revision', hash_val)


def update_hashes(cur_manifest, project_root, name_map):
    """Update hashes for all projects."""
    print(f"{BColors.HEADER}-== UPDATING MANIFEST ==-{BColors.ENDC}")
    for project in cur_manifest.iter('project'):
        update_hash(project, project_root, name_map)


def main(args):
    global dry_run
    dry_run = not args.apply
    if args.p is None:
        args.p = args.r
    # os.system("repo sync")
    project_root = get_project_root()
    name_map = get_name_tag_map(project_root, args.p, args.r)
    tree = et.parse(pjoin(project_root, ".repo/manifests/default.xml"))
    cur_manifest = tree.getroot()
    # for project in cur_manifest.iter('project'):
    #     project_path = pjoin(project_root, project.attrib.get('path'))
    #     repo = Repo(project_path)
    #     repo.remotes.origin.pull()
    update_release_tags(project_root, cur_manifest, name_map)
    update_hashes(cur_manifest, project_root, name_map)
    new_manifest_path = pjoin(project_root, f".repo/manifests/{args.r}_manifest.xml")
    tree.write(new_manifest_path)
    print(f"{BColors.OKGREEN}New manifest is created in {new_manifest_path}\nManual merge step to default.xml is still required{BColors.ENDC}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', metavar="RELEASE", help='Release version, e.g v700')
    parser.add_argument('-p', metavar="PREVIOUS_RELEASE", help='Previous release version, e.g v600, used as a reference for the tag naming')
    parser.add_argument('--apply', help='Set to create release tags in repositories', default=False, action='store_true')
    main(parser.parse_args())
