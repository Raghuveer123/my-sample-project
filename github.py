import requests
import base64
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Replace these with your details
GITHUB_TOKEN = "your_github_token"
REPO_OWNER = "your_repo_owner"
REPO_NAME = "your_repo_name"

# Headers for authentication
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"


def branch_exists(branch_name):
    """Check if a branch exists in the repository."""
    url = f"{BASE_URL}/git/ref/heads/{branch_name}"
    response = requests.get(url, headers=HEADERS, verify=False)
    return response.status_code == 200


def create_main_branch():
    """Create the 'main' branch if it doesn't exist."""
    if branch_exists("main"):
        print("Main branch already exists. Skipping creation.")
        return

    print("Main branch does not exist. Creating 'main' branch.")
    # Initialize the repository with an initial commit
    url = f"{BASE_URL}/git/trees"
    tree_payload = {"tree": []}  # Empty tree for the initial commit
    response = requests.post(url, json=tree_payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    tree_sha = response.json()["sha"]

    # Create the commit
    commit_url = f"{BASE_URL}/git/commits"
    commit_payload = {
        "message": "Initial commit",
        "tree": tree_sha,
        "parents": []
    }
    response = requests.post(commit_url, json=commit_payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    commit_sha = response.json()["sha"]

    # Create the 'main' branch
    branch_url = f"{BASE_URL}/git/refs"
    branch_payload = {
        "ref": "refs/heads/main",
        "sha": commit_sha
    }
    response = requests.post(branch_url, json=branch_payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    print("Main branch created successfully.")


def add_codeowners():
    """Add or overwrite a CODEOWNERS file in the repository."""
    codeowners_content = "* @your-github-username"  # Replace with your actual username
    encoded_content = base64.b64encode(codeowners_content.encode("utf-8")).decode("utf-8")

    # Check if CODEOWNERS file exists
    url = f"{BASE_URL}/contents/.github/CODEOWNERS"
    response = requests.get(url, headers=HEADERS, verify=False)

    if response.status_code == 200:
        # File exists, get the SHA for updating
        sha = response.json()["sha"]
        print("CODEOWNERS file exists. Updating with new content.")
        payload = {
            "message": "Update CODEOWNERS file",
            "content": encoded_content,
            "sha": sha,  # Include the file's SHA for update
            "branch": "main"
        }
    else:
        # File does not exist, create a new one
        print("CODEOWNERS file not found. Creating a new one.")
        payload = {
            "message": "Add CODEOWNERS file",
            "content": encoded_content,
            "branch": "main"
        }

    # Create or update the CODEOWNERS file
    response = requests.put(url, json=payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    print("CODEOWNERS file added or updated successfully.")


def enforce_branch_protection(branch_name):
    """Apply branch protection rules to a branch."""
    url = f"{BASE_URL}/branches/{branch_name}/protection"
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
    print(f"Branch protection rules set for '{branch_name}'.")


def create_branch(branch_name, source_branch="main"):
    """Create a new branch from a source branch."""
    if branch_exists(branch_name):
        print(f"Branch '{branch_name}' already exists. Skipping creation.")
        return

    # Get the SHA of the source branch
    source_branch_url = f"{BASE_URL}/git/ref/heads/{source_branch}"
    response = requests.get(source_branch_url, headers=HEADERS, verify=False)
    if response.status_code == 404:
        print(f"Source branch '{source_branch}' does not exist. Cannot create '{branch_name}'.")
        return

    response.raise_for_status()
    sha = response.json()["object"]["sha"]

    # Create the new branch
    create_branch_url = f"{BASE_URL}/git/refs"
    payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    }
    response = requests.post(create_branch_url, json=payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    print(f"Branch '{branch_name}' created successfully.")


def main():
    try:
        # Step 1: Ensure the main branch exists
        create_main_branch()

        # Step 2: Create 'dev' and 'uat' branches
        create_branch("dev")
        create_branch("uat")

        # Step 3: Add or overwrite CODEOWNERS file
        add_codeowners()

        # Step 4: Enforce branch protection rules for all branches
        for branch in ["main", "dev", "uat"]:
            enforce_branch_protection(branch)

        print("All tasks completed successfully.")
    except requests.HTTPError as e:
        print(f"HTTP error occurred: {e.response.json()}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
