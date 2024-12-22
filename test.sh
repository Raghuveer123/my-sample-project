#!/bin/bash

# Inputs
OWNER="$OWNER"  # GitHub owner (e.g., your username or organization)
REPO="$REPO"    # Repository name
BRANCH="main"   # Branch name (could be parameterized)
TAG_NAME="$TAG_NAME"  # Tag name passed from the workflow
TAG_MESSAGE="$TAG_MESSAGE"  # Tag message passed from the workflow
TOKEN="$GH_TOKEN"  # GitHub token passed from the workflow

# 1. Get the latest commit SHA
LATEST_COMMIT_SHA=$(curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$OWNER/$REPO/git/ref/heads/$BRANCH" | jq -r '.object.sha')

if [[ -z "$LATEST_COMMIT_SHA" || "$LATEST_COMMIT_SHA" == "null" ]]; then
  echo "Failed to fetch the latest commit SHA"
  exit 1
fi

echo "Latest commit SHA: $LATEST_COMMIT_SHA"

# 2. Create the tag object
TAG_OBJECT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d @- "https://api.github.com/repos/$OWNER/$REPO/git/tags" <<EOF
{
  "tag": "$TAG_NAME",
  "message": "$TAG_MESSAGE",
  "object": "$LATEST_COMMIT_SHA",
  "type": "commit"
}
EOF
)

TAG_SHA=$(echo "$TAG_OBJECT" | jq -r '.sha')

if [[ -z "$TAG_SHA" || "$TAG_SHA" == "null" ]]; then
  echo "Failed to create the tag object"
  exit 1
fi

echo "Tag object SHA: $TAG_SHA"

# 3. Create the tag reference
CREATE_REF_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d @- "https://api.github.com/repos/$OWNER/$REPO/git/refs" <<EOF
{
  "ref": "refs/tags/$TAG_NAME",
  "sha": "$TAG_SHA"
}
EOF
)

if echo "$CREATE_REF_RESPONSE" | grep -q '"ref":'; then
  echo "Tag $TAG_NAME successfully created and pushed!"
else
  echo "Failed to create the tag reference"
  echo "$CREATE_REF_RESPONSE"
  exit 1
fi
