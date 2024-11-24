def add_codeowners():
    """Upload a CODOWNERS file to the repository."""
    try:
        with open(LOCAL_CODEOWNERS_PATH, "rb") as file:
            codowners_content = file.read()
    except FileNotFoundError:
        print(f"CODEOWNERS file not found at {LOCAL_CODEOWNERS_PATH}.")
        return

    # Base64 encode the content
    encoded_content = base64.b64encode(codeowners_content).decode("utf-8")

    for branch in ["main", "dev", "uat"]:
        # Check if CODOWNERS file exists
        url = f"{BASE_URL}/contents/.github/CODEOWNERS?ref={branch}"
        response = requests.get(url, headers=HEADERS, verify=False)

        if response.status_code == 200:
            # File exists, get the SHA for updating
            sha = response.json()["sha"]
            print(f"CODOWNERS file exists in {branch} branch. Updating with new content.")
            payload = {
                "message": "Update CODOWNERS file",
                "content": encoded_content,
                "sha": sha,
                "branch": branch
            }
        else:
            # File does not exist, create a new one
            print(f"CODOWNERS file not found in {branch} branch. Creating a new one.")
            payload = {
                "message": "Add CODEOWNERS file",
                "content": encoded_content,
                "branch": branch
            }

        # Create or update the CODOWNERS file
        response = requests.put(url, json=payload, headers=HEADERS, verify=False)
        response.raise_for_status()
        print(f"CODEOWNERS file added or updated in '{branch}' branch.")
