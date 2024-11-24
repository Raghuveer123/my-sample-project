def add_codowners():
    """Upload a CODOWNERS file to the repository."""
    # Read the content of the CODOWNERS file from the local path
    try:
        with open(LOCAL_CODOWNERS_PATH, "rb") as file:
            codowners_content = file.read()
    except FileNotFoundError:
        print(f"CODOWNERS file not found at {LOCAL_CODOWNERS_PATH}.")
        return

    # Base64 encode the content
    encoded_content = base64.b64encode(codowners_content).decode("utf-8")

    # Check if CODOWNERS file exists
    url = f"{BASE_URL}/contents/.github/CODOWNERS"
    response = requests.get(url, headers=HEADERS, verify=False)

    if response.status_code == 200:
        # File exists, get the SHA for updating
        sha = response.json()["sha"]
        print("CODOWNERS file exists. Updating with new content.")
        payload = {
            "message": "Update CODOWNERS file",
            "content": encoded_content,
            "sha": sha,  # Include the file's SHA for update
            "branch": "main"
        }
    else:
        # File does not exist, create a new one
        print("CODOWNERS file not found in repository. Creating a new one.")
        payload = {
            "message": "Add CODOWNERS file",
            "content": encoded_content,
            "branch": "main"
        }

    # Create or update the CODOWNERS file
    response = requests.put(url, json=payload, headers=HEADERS, verify=False)
    response.raise_for_status()
    print("CODOWNERS file added or updated successfully.")
