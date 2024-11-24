import requests
import base64
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Replace these with your details
GITHUB_TOKEN = "your_github_token"
ORG_NAME = "your_organization_name"  # GitHub organization/team name
TEAM_NAME = "your_team_name"  # GitHub team name

# Path to the local CODOWNERS file
LOCAL_CODOWNERS_PATH = "/path/to/your/CODOWNERS"

# Headers for authentication
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

BASE_URL = f"https://api.github.com/orgs/{ORG_NAME}/teams/{TEAM_NAME}/repos"


def get_repositories():
    """Get all repositories in the specified team."""
    url = f"{BASE_URL}?per_page=100"  # Fetch up to 100 repositories per request
    response = requests.get(url, headers=HEADERS, verify=False)
    response.raise_for_status()
    return [repo['name'] for repo in response.json()]


def branch_exists(repo_name, branch_name):
    """Check if a branch exists in the repository."""
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/git/ref/heads/{branch_name}"
    response = requests.get(url, headers=HEADERS, verify=False)
    return response.status_code == 200


def create_main_branch(repo_name):
    """Create the 'main' branch if it doesn't exist."""
    if branch_exists(repo_name, "main"):
        print(f"Main branch already exists in {repo_name}. Skipping creation.")
        return

    print(f"Main branch does not exist in {repo_name}. Creating 'main' branch.")
    # Initialize the repository with an initial commit
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/git/trees"
    tree_payload = {"tree": []}  # Empty tree for the initial commit
    response = requests.post(url, json=tree_payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    tree_sha = response.json()["sha"]

    # Create the commit
    commit_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/git/commits"
    commit_payload = {
        "message": "Initial commit",
        "tree": tree_sha,
        "parents": []
    }
    response = requests.post(commit_url, json=commit_payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    commit_sha = response.json()["sha"]

    # Create the 'main' branch
    branch_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/git/refs"
    branch_payload = {
        "ref": "refs/heads/main",
        "sha": commit_sha
    }
    response = requests.post(branch_url, json=branch_payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    print(f"Main branch created in {repo_name}.")


def create_branch(repo_name, branch_name, source_branch="main"):
    """Create a new branch from a source branch."""
    if branch_exists(repo_name, branch_name):
        print(f"Branch '{branch_name}' already exists in {repo_name}. Skipping creation.")
        return

    # Get the SHA of the source branch
    source_branch_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/git/ref/heads/{source_branch}"
    response = requests.get(source_branch_url, headers=HEADERS, verify=False)
    if response.status_code == 404:
        print(f"Source branch '{source_branch}' does not exist in {repo_name}. Cannot create '{branch_name}'.")
        return

    response.raise_for_status()
    sha = response.json()["object"]["sha"]

    # Create the new branch
    create_branch_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/git/refs"
    payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    }
    response = requests.post(create_branch_url, json=payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    print(f"Branch '{branch_name}' created in {repo_name}.")


def add_codowners(repo_name):
    """Upload or update the CODOWNERS file in the repository."""
    try:
        with open(LOCAL_CODOWNERS_PATH, "rb") as file:
            codowners_content = file.read()
    except FileNotFoundError:
        print(f"CODOWNERS file not found at {LOCAL_CODOWNERS_PATH}.")
        return

    # Base64 encode the content
    encoded_content = base64.b64encode(codowners_content).decode("utf-8")

    for branch in ["main", "dev", "uat"]:
        # Check if CODOWNERS file exists
        url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/contents/.github/CODOWNERS?ref={branch}"
        response = requests.get(url, headers=HEADERS, verify=False)

        if response.status_code == 200:
            # File exists, get the SHA for updating
            sha = response.json()["sha"]
            print(f"CODOWNERS file exists in {repo_name} ({branch}) branch. Updating with new content.")
            payload = {
                "message": "Update CODOWNERS file",
                "content": encoded_content,
                "sha": sha,
                "branch": branch
            }
        else:
            # File does not exist, create a new one
            print(f"CODOWNERS file not found in {repo_name} ({branch}) branch. Creating a new one.")
            payload = {
                "message": "Add CODOWNERS file",
                "content": encoded_content,
                "branch": branch
            }

        # Create or update the CODOWNERS file
        response = requests.put(url, json=payload, headers=HEADERS, verify=False)
        response.raise_for_status()
        print(f"CODOWNERS file added or updated in '{repo_name}' ({branch}) branch.")


def enforce_branch_protection(repo_name, branch_name):
    """Apply branch protection rules to a branch."""
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/branches/{branch_name}/protection"
    payload = {
        "required_status_checks": None,
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": True,
            "required_approving_review_count": 1
        },
        "restrictions": None
    }
    response = requests.put(url, json=payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    print(f"Branch protection rules set for '{branch_name}' in {repo_name}.")


def bypass_pull_request_for_user(repo_name, branch_name, user_login):
    """Allow a specific user to bypass pull request requirements."""
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/branches/{branch_name}/protection/required_pull_request_reviews"
    payload = {
        "dismiss_stale_reviews": False,
        "require_code_owner_reviews": True,
        "required_approving_review_count": 1,
        "bypass_pull_request_approval": [user_login]  # Bypass PR for the specified user
    }
    response = requests.put(url, json=payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    print(f"Bypass pull request for user '{user_login}' set on '{branch_name}' in {repo_name}.")


def main():
    try:
        # Step 1: Get all repositories in the team
        repositories = get_repositories()

        # Step 2: Ensure the main, dev, uat branches exist in each repo
        for repo_name in repositories:
            # Ensure 'main' branch exists
            create_main_branch(repo_name)

            # Create 'dev' and 'uat' branches
            create_branch(repo_name, "dev")
            create_branch(repo_name, "uat")

            # Step 3: Add or overwrite CODOWNERS file across all branches (main, dev, uat)
            add_codowners(repo_name)

            # Step 4: Enforce branch protection rules for all branches (main, dev, uat)
            for branch in ["main", "dev", "uat"]:
                enforce_branch_protection(repo_name, branch)
                bypass_pull_request_for_user(repo_name, branch, "your_user_login")  # Specify the user to bypass PR

        print("All tasks completed successfully across all repositories.")
    except requests.HTTPError as e:
        print(f"HTTP error occurred: {e.response.json()}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
