from json import loads, dumps
from github import Github, Auth
from wmill import get_variable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import copy
import logging
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRIPTS_FOLDER = 'scripts'
EXTENSIONS = {
    'py': 'python',
    'ps1': 'powershell',
    'bat': 'cmd'
}


def _fetch_blob(repo, file_name: str, sha: str) -> tuple[str, str]:
    """Fetch a single file's content via the blob API. Returns (name, content)."""
    blob = repo.get_git_blob(sha)
    content = base64.b64decode(blob.content).decode('utf-8')
    return file_name, content


def get_script_hashes():
    github_token = get_variable("GITHUB_TOKEN")
    github_repo = get_variable("GITHUB_TRMM_SYNC_REPO")
    github_org = get_variable("GITHUB_TRMM_SYNC_ORG")

    if not github_token:
        return []

    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    repo = g.get_repo(f"{github_org}/{github_repo}")

    # --- Single API call: fetch the entire tree for the scripts folder ---
    # Get the branch's HEAD commit, then the tree for the scripts subtree.
    # recursive=False is fine here since SCRIPTS_FOLDER is flat.
    branch_sha = repo.get_branch(repo.default_branch).commit.sha
    tree = repo.get_git_tree(branch_sha, recursive=True)

    # Filter tree items to only those inside SCRIPTS_FOLDER
    items = [
        item for item in tree.tree
        if item.path.startswith(f"{SCRIPTS_FOLDER}/") and item.type == "blob"
    ]

    default_file = {
        "name": "",
        "shell": "Powershell",
        "default_timeout": 120,
        "args": [],
        "run_as_user": False,
        "env_vars": [],
        "description": "",
        "supported_platforms": ["windows"]
    }
    json_files = {}
    script_files = {}  # name -> content

    # --- Fetch all blobs concurrently ---
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(_fetch_blob, repo, item.path.split("/")[-1], item.sha): item
            for item in items
        }
        for future in as_completed(futures):
            file_name, content = future.result()

            if file_name == 'Default.json':
                default_file = loads(content)
            elif file_name.endswith('.json'):
                json_files[Path(file_name).stem] = loads(content)
            else:
                script_files[file_name] = content

    # --- Build the script list (no more lazy fetches) ---
    scripts = []
    for file_name, content in script_files.items():
        stem = Path(file_name).stem
        ext = Path(file_name).suffix.lstrip('.')

        file_hash = hashlib.sha1(content.encode()).hexdigest()

        if stem in json_files:
            metadata = json_files[stem]
        else:
            metadata = copy.deepcopy(default_file)
            metadata['name'] = stem
            metadata['shell'] = EXTENSIONS.get(ext, 'powershell')

        metadata['script_body'] = content
        scripts.append({
            'script': metadata,
            'hash': file_hash,
            'code': content
        })

    g.close()
    return scripts


def main(payload: dict, event: str) -> dict:
    if event != 'push':
        logger.error("event is not a push")
        return []

    branch = None
    try:
        if "ref_type" in payload:
            if payload["ref_type"] == "branch":
                branch = payload["ref"]
        elif "pull_request" in payload:
            branch = payload["pull_request"]["base"]["ref"]
        elif event == "push":
            branch = payload["ref"].split("/", 2)[2]
    except KeyError:
        pass

    name = payload["repository"]["name"] if "repository" in payload else None
    meta = {"name": name, "branch": branch, "event": event}
    logger.info(f"Metadata:\n{dumps(meta)}")

    if payload.get("deleted"):
        logger.info(f"Skipping push-delete event for {dumps(meta)}")
        return []

    return get_script_hashes()