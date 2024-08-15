import os
from pathlib import Path
import giteaapi as gitea
import base64
import time

# get token from environment variable
API_KEY = os.getenv("GITEA_API_KEY")
API_KEY = '160ed2654847b01ba2d3b2b538b84f31721c5ff4'
conf = gitea.Configuration()
conf.api_key['token'] = API_KEY
conf.host = "https://adare.seclab-bonn.de/git/api/v1"
API = gitea.ApiClient(conf)
OWNER = "miq"
REPO = "adareTEST"
repo_api = gitea.RepositoryApi(API)


def create_branch(owner: str, repo: str, new_branch_name: str, old_branch: str = 'main'):
    # create a new branch
    branch = repo_api.repo_create_branch(
        owner=owner, repo=repo, body={"base": old_branch, "new_branch_name": new_branch_name}
    )
    return branch


def delete_branch(owner: str, repo: str, branch_name: str):
    # delete a branch
    branch = repo_api.repo_delete_branch(
        owner=owner, repo=repo, branch=branch_name
    )
    return branch


def upload_file(owner: str, repo: str, branch: str, file: Path, file_git_path: str, commit_msg: str = None):
    with open(file, "rb") as file:
        content = file.read()
    base64_content = base64.b64encode(content).decode("utf-8")

    if not commit_msg:
        commit_msg = f"upload {file_git_path}"

    data = {
        "content": base64_content,
        "branch": branch,
        "message": commit_msg,
    }
    print(file_git_path)
    repo_api.repo_create_file(owner=owner, repo=repo, filepath=file_git_path, body=data)


def create_pr(owner: str, repo: str, title: str, body: str, head_branch: str, base_branch: str = "main"):
    # create a new pull request
    pr = repo_api.repo_create_pull_request(
        owner=owner, repo=repo, body={"title": title, "body": body, "head": head_branch, "base": base_branch}
    )
    return pr


def close_pr(owner: str, repo: str, pr_id: int):
    # close a pull request
    pr = repo_api.repo_edit_pull_request(
        owner=owner, repo=repo, index=pr_id, body={"state": "closed"}
    )
    return pr


def merge_pr(owner: str, repo: str, pr_id: int):
    # merge a pull request
    pr = repo_api.repo_merge_pull_request(
        owner=owner, repo=repo, index=pr_id, body={"do": "merge"}
    )
    return pr


def merge_pr_and_delete_branch(owner: str, repo: str, pr_id: int):
    # merge a pull request
    pr = repo_api.repo_merge_pull_request(
        owner=owner, repo=repo, index=pr_id, body={"do": "merge"}
    )
    delete_branch(owner, repo, pr['head']['ref'])
    return pr




def delete_all_branches_except_main():
    branches = repo_api.repo_list_branches(owner=OWNER, repo=REPO)
    for branch in branches:
        if branch.name != 'main':
            delete_branch(OWNER, REPO, branch.name)


def close_all_prs():
    prs = repo_api.repo_list_pull_requests(owner=OWNER, repo=REPO)
    for pr in prs:
        if pr.state != 'open':
            continue
        close_pr(OWNER, REPO, pr.id)


def __delete_files_recursive(owner: str, repo: str, branch: str, path: str, exclude: list = None):
    if exclude is None:
        exclude = ['.gitignore', 'README.md', '.gitea']
    if path == '':
        files = repo_api.repo_get_contents_list(owner=owner, repo=repo, ref=branch)
    else:
        files = repo_api.repo_get_contents(owner=owner, repo=repo, filepath=path, ref=branch)
    for file in files:
        if file.name in exclude:
            continue
        if file.type == 'file':
            repo_api.repo_delete_file(owner=owner, repo=repo, filepath=file.path, body={"branch": branch, "message": "clear branch", "sha": file.sha})
        elif file.type == 'dir':
            __delete_files_recursive(owner, repo, branch, file.path)


def clear_branch(owner: str, repo: str,branch: str = 'main'):
    # clear branch by deleting all files
    __delete_files_recursive(owner, repo, branch, '')


def create_pr_testfunction_create(owner: str, repo: str, new_branch_name: str, testfunction_dir: Path, testfunction_name: str, base_branch: str = "main"):
    # create a new branch
    create_branch(owner, repo, new_branch_name)

    # iterate over all files in the testfunction directory and get relative path (even multiple levels deep)
    for file in testfunction_dir.rglob("*"):
        if file.is_file():
            git_file = f'testfunctions/{testfunction_name}/{file.relative_to(testfunction_dir)}'
            # upload file to new branch
            upload_file(owner, repo, new_branch_name, file, git_file)

    # now create a pull request
    title = f'[testfunction create] {testfunction_name}'
    pr = create_pr(
        owner=owner, repo=repo, title=title, body=title, head_branch=new_branch_name, base_branch=base_branch
    )
    return pr.id


def create_pr_environment(owner: str, repo: str, new_branch_name: str, environment_file: Path, environment_name: str, base_branch: str = "main"):
    # create a new branch
    create_branch(owner, repo, new_branch_name)

    # iterate over all files in the testfunction directory and get relative path (even multiple levels deep)
    git_file = f'environments/{environment_file.name}'
    # upload file to new branch
    upload_file(owner, repo, new_branch_name, environment_file, git_file)

    # now create a pull request
    title = f'[environment create] {environment_name}'
    pr = create_pr(
        owner=owner, repo=repo, title=title, body=title, head_branch=new_branch_name, base_branch=base_branch
    )
    return pr.id


def create_pr_experiment(owner: str, repo: str, new_branch_name: str, experiment_dir: Path, experiment_name: str, base_branch: str = "main"):
    # create a new branch
    create_branch(owner, repo, new_branch_name)

    # iterate over all files in the testfunction directory and get relative path (even multiple levels deep)
    for file in experiment_dir.rglob("*"):
        if file.is_file():
            git_file = f'experiments/{experiment_name}/{file.relative_to(experiment_dir)}'
            # upload file to new branch
            upload_file(owner, repo, new_branch_name, file, git_file)
    import time
    time.sleep(1)
    # now create a pull request
    title = f'[experiment create] {experiment_name}'
    pr = create_pr(
        owner=owner, repo=repo, title=title, body=title, head_branch=new_branch_name, base_branch=base_branch
    )
    return pr.id


if __name__ == '__main__':
    #import time
    #clear_branch(OWNER, REPO, 'main')
    #close_all_prs()
    #delete_all_branches_except_main()

    #create_pr_environment(OWNER, REPO, 'env2', Path('/home/miq/Documents/adare/examples2/environments/tenv2.yml'), 'tenv2')
    #create_pr_testfunction_create(OWNER, REPO, 'tfx1', Path('/home/miq/Documents/adare/examples/testfunctions/standard'), 'standard')
    #create_pr_environment(OWNER, REPO, 'envx1', Path('/home/miq/Documents/adare/examples/environments/testenv.yml'), 'testenv')
    #create_pr_experiment(OWNER, REPO, 'exp2', Path('/home/miq/Documents/adare/examples/experiments/deletefile'), 'deletefile')
    #
    merge_pr(OWNER, REPO, 111)
