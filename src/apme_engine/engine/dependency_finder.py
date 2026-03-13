"""Find and load Ansible collection and role dependencies."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import cast

import yaml

from . import logger
from .models import (
    LoadType,
    YAMLDict,
    YAMLValue,
)
from .safe_glob import safe_glob

collection_manifest_json = "MANIFEST.json"
role_meta_main_yml = "meta/main.yml"
role_meta_main_yaml = "meta/main.yaml"
requirements_yml = "requirements.yml"
galaxy_yml = "galaxy.yml"
GALAXY_yml = "GALAXY.yml"
github_workflows_dir = ".github/workflows"
ansible_home = os.getenv("ANSIBLE_HOME", "~/.ansible")


def find_dependency(
    type: str,
    target: str,
    dependency_dir: str,
    use_ansible_path: bool = False,
) -> YAMLDict:
    """Find dependencies for a project, role, or collection.

    Args:
        type: LoadType (PROJECT, ROLE, or COLLECTION).
        target: Path to the project, role, or collection directory.
        dependency_dir: Optional pre-downloaded dependency dir to use.
        use_ansible_path: Whether to search ANSIBLE_HOME for installed deps.

    Returns:
        Dict with dependencies, paths, metadata, type, and file keys.
    """
    dependencies: YAMLDict = {"dependencies": {}, "type": "", "file": ""}
    logger.debug("search dependency")
    if dependency_dir:
        dir_reqs, paths, metadata = load_existing_dependency_dir(dependency_dir)
        dependencies["dependencies"] = cast(YAMLValue, dir_reqs)
        dependencies["paths"] = cast(YAMLValue, paths)
        dependencies["metadata"] = cast(YAMLValue, metadata)
        dependencies["type"] = type
        dependencies["file"] = None
    else:
        if type == LoadType.PROJECT:
            logger.debug("search project dependency")
            proj_reqs, reqyml = find_project_dependency(target)
            dependencies["dependencies"] = cast(YAMLValue, proj_reqs)
            dependencies["type"] = LoadType.PROJECT
            dependencies["file"] = reqyml
        elif type == LoadType.ROLE:
            logger.debug("search role dependency")
            role_reqs, mainyml = find_role_dependency(target)
            dependencies["dependencies"] = cast(YAMLValue, role_reqs)
            dependencies["type"] = LoadType.ROLE
            dependencies["file"] = mainyml
        elif type == LoadType.COLLECTION:
            logger.debug("search collection dependency")
            coll_reqs, manifestjson = find_collection_dependency(target)
            dependencies["dependencies"] = cast(YAMLValue, coll_reqs)
            dependencies["type"] = LoadType.COLLECTION
            dependencies["file"] = manifestjson

    if use_ansible_path and dependencies["dependencies"]:
        ansible_dir = Path(ansible_home).expanduser()
        deps = dependencies["dependencies"]
        if isinstance(deps, dict):
            paths, metadata = search_ansible_dir(deps, str(ansible_dir))
            if paths:
                dependencies["paths"] = cast(YAMLValue, paths)
            if metadata:
                dependencies["metadata"] = cast(YAMLValue, metadata)

    return dependencies


def search_ansible_dir(
    dependencies: YAMLDict, ansible_dir: str
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, YAMLValue]]]:
    """Search ANSIBLE_HOME for installed roles and collections.

    Args:
        dependencies: Dict with 'roles' and 'collections' keys.
        ansible_dir: Path to ~/.ansible or ANSIBLE_HOME.

    Returns:
        Tuple of (paths dict, metadata dict) for roles and collections.
    """
    if not dependencies:
        return {}, {}
    if not isinstance(dependencies, dict):
        return {}, {}

    paths: dict[str, dict[str, str]] = {
        "roles": {},
        "collections": {},
    }

    metadata: dict[str, dict[str, YAMLValue]] = {
        "roles": {},
        "collections": {},
    }

    collections = dependencies.get("collections", [])
    if isinstance(collections, list):
        for coll_info in collections:
            if not isinstance(coll_info, dict):
                continue
            coll_name = coll_info.get("name", "")
            if not coll_name or not isinstance(coll_name, str):
                continue

            parts = coll_name.split(":")[0].split(".")
            if len(parts) != 2:
                continue
            collection_dir = os.path.join(ansible_dir, "collections", "ansible_collections")
            search_path = os.path.join(collection_dir, parts[0], parts[1])
            if os.path.exists(search_path):
                paths["collections"][coll_name] = search_path

            _dirs = os.listdir(collection_dir)
            for d_name in _dirs:
                galaxy_data = None
                if d_name.startswith(f"{coll_name}-") and d_name.endswith(".info"):
                    galaxy_yml_path = os.path.join(collection_dir, d_name, GALAXY_yml)
                    try:
                        with open(galaxy_yml_path) as galaxy_yml_file:
                            galaxy_data = yaml.safe_load(galaxy_yml_file)
                    except Exception:
                        pass
                if not isinstance(galaxy_data, dict):
                    continue
                metadata["collections"][coll_name] = cast(YAMLDict, galaxy_data)

    roles = dependencies.get("roles", [])
    if isinstance(roles, list):
        for role_info in roles:
            if not isinstance(role_info, dict):
                continue
            role_name = role_info.get("name", "")
            if not role_name or not isinstance(role_name, str):
                continue

            role_name = role_name.split(":")[0]
            search_path = os.path.join(ansible_dir, "roles", role_name)
            if os.path.exists(search_path):
                paths["roles"][role_name] = search_path

            # set empty metadata because no download_url / version are available in an installed role dir
            metadata["roles"][role_name] = {}
    return paths, metadata


def find_role_dependency(target: str) -> tuple[YAMLDict, str]:
    """Find role and collection dependencies from meta/main.yml.

    Args:
        target: Path to the role directory.

    Returns:
        Tuple of (requirements dict with roles/collections, path to main.yml).

    Raises:
        ValueError: If target directory does not exist.
    """
    requirements = {}
    if not os.path.exists(target):
        raise ValueError(f"Invalid target dir: {target}")
    role_meta_files = safe_glob(
        [
            os.path.join(target, "**", role_meta_main_yml),
            os.path.join(target, "**", role_meta_main_yaml),
        ],
        recursive=True,
    )
    role_meta_files = [fpath for fpath in role_meta_files if github_workflows_dir not in fpath]
    main_yaml = ""
    if len(role_meta_files) > 0:
        for rf in role_meta_files:
            if os.path.exists(rf):
                main_yaml = rf
                with open(rf) as file:
                    try:
                        metadata = yaml.safe_load(file)
                    except Exception as e:
                        logger.debug(f"failed to load this yaml file to read metadata; {e.args[0]}")

                    if metadata is not None and isinstance(metadata, dict):
                        requirements["roles"] = metadata.get("dependencies", [])
                        requirements["collections"] = metadata.get("collections", [])

    # remove local dependencies
    role_reqs = requirements.get("roles", [])
    if role_reqs:
        updated_role_reqs = []
        _target = target[:-1] if target[-1] == "/" else target
        base_dir = os.path.dirname(_target)
        for r_req in role_reqs:
            r_req_name = ""
            if isinstance(r_req, str):
                r_req_name = r_req
            elif isinstance(r_req, dict):
                r_req_name = str(r_req.get("role", "") or "")
            if not r_req_name and "name" in r_req:
                r_req_name = str(r_req.get("name", "") or "")
            # if role dependency name does not have ".", it should be a local dependency
            is_local_dir = False
            if "." not in r_req_name:
                r_req_dir = os.path.join(base_dir, r_req_name)
                if os.path.exists(r_req_dir):
                    is_local_dir = True
            # or, it can be written as `<collection_name>.<role_name>`
            if "." in r_req_name:
                r_short_name = r_req_name.split(".")[-1]
                r_req_dir = os.path.join(base_dir, r_short_name)
                if os.path.exists(r_req_dir):
                    r_req_name = r_short_name
                    is_local_dir = True
            updated_role_reqs.append({"name": r_req_name, "is_local_dir": is_local_dir})
        requirements["roles"] = updated_role_reqs
    return requirements, main_yaml


def find_collection_dependency(target: str) -> tuple[YAMLDict, str]:
    """Find collection dependencies from MANIFEST.json or galaxy.yml.

    Args:
        target: Path to the collection directory.

    Returns:
        Tuple of (requirements dict with collections, path to manifest/galaxy file).
    """
    requirements: YAMLDict = {}
    # collection dir installed by ansible-galaxy command
    manifest_json_files = safe_glob(os.path.join(target, "**", collection_manifest_json), recursive=True)
    manifest_json_files = [fpath for fpath in manifest_json_files if github_workflows_dir not in fpath]
    logger.debug(f"found meta files {manifest_json_files}")
    manifest_json = ""
    if len(manifest_json_files) > 0:
        for cmf in manifest_json_files:
            if os.path.exists(cmf):
                manifest_json = cmf
                metadata = {}
                with open(cmf) as file:
                    metadata = json.load(file)
                    collection_info = metadata.get("collection_info", {})
                    dependencies = collection_info.get("dependencies", {}) if isinstance(collection_info, dict) else {}
                    requirements["collections"] = cast(YAMLValue, format_dependency_info(cast(YAMLDict, dependencies)))
    else:
        requirements, manifest_json = load_dependency_from_galaxy(target)
    return requirements, manifest_json


def find_project_dependency(target: str) -> tuple[YAMLDict, str]:
    """Find dependencies for a project (collection, role, or requirements.yml).

    Args:
        target: Path to the project directory.

    Returns:
        Tuple of (requirements dict, path to requirements file).

    Raises:
        ValueError: If target directory does not exist.
    """
    if os.path.exists(target):
        coll_req = os.path.join(target, collection_manifest_json)
        role_req1 = os.path.join(target, role_meta_main_yaml)
        role_req2 = os.path.join(target, role_meta_main_yml)
        # collection project
        if os.path.exists(coll_req):
            return find_collection_dependency(target)
        # role project
        elif os.path.exists(role_req1) or os.path.exists(role_req2):
            return find_role_dependency(target)
        # local dir
        logger.debug(f"load requirements from dir {target}")
        return load_requirements(target)
    else:
        raise ValueError(f"Invalid target dir: {target}")


def load_requirements(path: str) -> tuple[YAMLDict, str]:
    """Load requirements from requirements.yml or galaxy.yml.

    Args:
        path: Path to the project directory.

    Returns:
        Tuple of (requirements dict, path to the yaml file).
    """
    requirements = {}
    yaml_path = ""
    # project dir
    requirements_yml_path = os.path.join(path, requirements_yml)
    if os.path.exists(requirements_yml_path):
        yaml_path = requirements_yml_path
        with open(requirements_yml_path) as file:
            try:
                requirements = yaml.safe_load(file)
            except Exception as e:
                logger.debug(f"failed to load requirements.yml; {e.args[0]}")
    else:
        requirements, yaml_path = load_dependency_from_galaxy(path)

    # convert old style requirements yml (a list of role info) to new one (a dict)
    if requirements and isinstance(requirements, list):
        new_req = {"roles": []}
        for item in requirements:
            role_name = ""
            if isinstance(item, str):
                role_name = item
            elif isinstance(item, dict):
                role_name = str(item.get("name", "") or "")
            # if no `name` field is given in the requirements yml, we skip this item
            if not role_name:
                continue
            new_req["roles"].append(role_name)
        requirements = new_req

    # sometimes there is empty requirements.yml
    # if so, we set empty dict as requirements instead of `None`
    if not requirements:
        requirements = {}
    return requirements, yaml_path


def is_galaxy_yml(path: str) -> bool:
    """Check if a file is a valid galaxy.yml (has name and namespace).

    Args:
        path: Path to the YAML file.

    Returns:
        True if file exists and has name and namespace keys.
    """
    if not os.path.exists(path):
        return False

    metadata = None
    try:
        with open(path) as file:
            metadata = yaml.safe_load(file)
    except Exception:
        pass

    if not isinstance(metadata, dict):
        return False

    return bool("name" in metadata and "namespace" in metadata)


def load_dependency_from_galaxy(path: str) -> tuple[YAMLDict, str]:
    """Load collection dependencies from galaxy.yml or GALAXY.yml.

    Args:
        path: Path to search for galaxy.yml files.

    Returns:
        Tuple of (requirements dict with collections, path to galaxy file).
    """
    requirements = {}
    yaml_path = ""
    galaxy_yml_files = safe_glob(os.path.join(path, "**", galaxy_yml), recursive=True)
    galaxy_yml_files.extend(safe_glob(os.path.join(path, "**", GALAXY_yml), recursive=True))
    galaxy_yml_files = [fpath for fpath in galaxy_yml_files if github_workflows_dir not in fpath]
    logger.debug(f"found meta files {galaxy_yml_files}")
    if len(galaxy_yml_files) > 0:
        for g in galaxy_yml_files:
            if is_galaxy_yml(g):
                yaml_path = g
                metadata = {}
                with open(g) as file:
                    metadata = yaml.safe_load(file)
                    dependencies = metadata.get("dependencies", {})
                    if dependencies:
                        requirements["collections"] = format_dependency_info(dependencies)
    return cast(tuple[YAMLDict, str], (requirements, yaml_path))


def load_existing_dependency_dir(
    dependency_dir: str,
) -> tuple[
    dict[str, list[str]],
    dict[str, dict[str, str]],
    dict[str, dict[str, YAMLValue]],
]:
    """Load dependencies from an existing installed dependency directory.

    Args:
        dependency_dir: Path to directory with installed collections/roles.

    Returns:
        Tuple of (requirements, paths, metadata) for roles and collections.
    """
    # role_meta_files = safe_glob(
    #     [
    #         os.path.join(dependency_dir, "**", role_meta_main_yml),
    #         os.path.join(dependency_dir, "**", role_meta_main_yaml),
    #     ],
    #     recursive=True,
    # )
    collection_meta_files = safe_glob(os.path.join(dependency_dir, "**", collection_manifest_json), recursive=True)
    collection_meta_files = [fpath for fpath in collection_meta_files if github_workflows_dir not in fpath]
    requirements: dict[str, list[str]] = {
        "roles": [],
        "collections": [],
    }
    paths: dict[str, dict[str, str]] = {
        "roles": {},
        "collections": {},
    }
    metadata: dict[str, dict[str, YAMLValue]] = {
        "roles": {},
        "collections": {},
    }
    # for r_meta_file in role_meta_files:
    #     role_name = r_meta_file.split("/")[-3]
    #     role_path = "/".join(r_meta_file.split("/")[:-2])
    #     requirements["roles"].append(role_name)
    #     paths["roles"][role_name] = role_path
    for c_meta_file in collection_meta_files:
        if "/tests/" in c_meta_file:
            continue
        parts = c_meta_file.split("/")
        collection_name = f"{parts[-3]}.{parts[-2]}"
        collection_path = "/".join(c_meta_file.split("/")[:-1])
        collection_base_path = "/".join(c_meta_file.split("/")[:-3])
        for dir_name in os.listdir(collection_base_path):
            galaxy_data = None
            if dir_name.startswith(collection_name) and dir_name.endswith(".info"):
                galaxy_yml_path = os.path.join(collection_base_path, dir_name, galaxy_yml)
                try:
                    with open(galaxy_yml_path) as galaxy_yml_file:
                        galaxy_data = yaml.safe_load(galaxy_yml_file)
                except Exception:
                    pass
            if not isinstance(galaxy_data, dict):
                continue
            coll_meta = metadata.get("collections", {})
            if isinstance(coll_meta, dict):
                coll_meta[collection_name] = cast(YAMLValue, galaxy_data)
        requirements["collections"].append(collection_name)
        paths["collections"][collection_name] = collection_path
    return requirements, paths, metadata


def install_github_target(target: str, output_dir: str) -> str:
    """Clone a GitHub repo to output_dir via git clone.

    Args:
        target: Git URL or repo identifier.
        output_dir: Directory to clone into.

    Returns:
        stdout from the git clone command.
    """
    proc = subprocess.run(
        f"git clone {target} {output_dir}",
        shell=True,
        stdin=subprocess.PIPE,
        capture_output=True,
        text=True,
    )
    install_msg = proc.stdout
    logger.debug(f"STDOUT: {install_msg}")
    return proc.stdout


def format_dependency_info(dependencies: YAMLDict | list[YAMLValue]) -> list[YAMLDict]:
    """Convert dependency dict (name: version) to list of {name, version} dicts.

    Args:
        dependencies: Dict mapping name to version, or list.

    Returns:
        List of dicts with name and version keys.
    """
    results: list[YAMLDict] = []
    if not isinstance(dependencies, dict):
        return results
    for k, v in dependencies.items():
        results.append({"name": k, "version": v})
    return results
