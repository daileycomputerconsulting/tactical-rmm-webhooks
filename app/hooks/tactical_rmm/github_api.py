from github import Github, Auth

from github import Auth

from os import environ as env
from pathlib import Path
import hashlib
import json
import copy

GH_TOKEN = env.get('GH_TOKEN', None)
GH_REPO = env.get('GH_REPO', None)
GH_ORG = env.get('GH_ORG', None)

SCRIPTS_FOLDER = 'scripts'

def get_script_hashes():
    auth = Auth.Token(GH_TOKEN)
    g = Github(auth=auth)

    repo = g.get_repo(GH_ORG + '/' + GH_REPO)
    repo_contents = repo.get_contents(SCRIPTS_FOLDER)

    scripts = []
    script_files = []
    json_files = {}

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

    EXTENSIONS = {
        'py': 'python',
        'ps1': 'powershell',
        'bat': 'cmd'
    }

    for s in repo_contents:
        if s.name == 'Default.json':
            default_file = json.loads(str(s.decoded_content, 'utf-8'))
        elif str(s.name).endswith('.json'):
            json_files[str(Path(s.name).stem)] = json.loads(str(s.decoded_content, 'utf-8'))
        else:
            script_files.append((s.name, str(s.decoded_content, 'utf-8')))

    for s in script_files:
        file_hash = (hashlib.sha1(s[1].encode())).hexdigest()
        if str(Path(s[0]).stem) in json_files:
            metadata = json_files[str(Path(s[0]).stem)]
        else:
            metadata = copy.deepcopy(default_file)
            metadata['name'] = (s[0].split('.'))[0]
            metadata['shell'] = EXTENSIONS[(s[0].split('.'))[1]]

        metadata['script_body'] = s[1]
        new_script = {
            'script': metadata,
            'hash': file_hash
        }
        scripts.append(new_script)
    g.close()
    return scripts

if __name__ == "__main__":
    scripts = get_script_hashes()
    for s in scripts:
        print('file: [%s] hash: [%s]' % (s['script']['name'], s['hash']))