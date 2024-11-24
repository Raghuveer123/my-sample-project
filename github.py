import requests

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


def create_branch(branch_name, source_branch="main"):
    # Get the SHA of the source branch
    source_branch_url = f"{BASE_URL}/git/ref/heads/{source_branch}"
    response = requests.get(source_branch_url, headers=HEADERS)
    response.raise_for_status()
    sha = response.json()["object"]["sha"]

    # Create the new branch
    create_branch_url = f"{BASE_URL}/git/refs"
    payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    }
    response = requests.post(create_branch_url, json=payload, headers=HEADERS)
    response.raise_for_status()
    print(f"Branch '{branch_name}' created successfully.")


def add_codeowners():
    # Create the CODEOWNERS file
    codeowners_content = """
    * @your-github-username
    """
    url = f"{BASE_URL}/contents/.github/CODEOWNERS"
    payload = {
        "message": "Add CODEOWNERS file",
        "content": codeowners_content.encode("utf-8").hex(),  # Base64 encode content
        "branch": "main"
    }
    response = requests.put(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    print("CODEOWNERS file added successfully.")


def enforce_branch_protection(branch_name):
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
    response = requests.put(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    print(f"Branch protection rules set for '{branch_name}'.")


def main():
    try:
        # Step 1: Create 'dev' and 'uat' branches
        create_branch("dev")
        create_branch("uat")

        # Step 2: Add CODEOWNERS file
        add_codeowners()

        # Step 3: Enforce branch protection rules for all branches
        for branch in ["main", "dev", "uat"]:
            enforce_branch_protection(branch)

        print("All tasks completed successfully.")
    except requests.HTTPError as e:
        print(f"HTTP error occurred: {e.response.json()}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
