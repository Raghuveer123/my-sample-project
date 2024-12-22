#!/bin/bash

# Inputs
OWNER="your-github-username"
REPO="your-repo-name"
BRANCH="main"
TAG_NAME="v1.0.0"
TAG_MESSAGE="Release $TAG_NAME"
TOKEN="your-personal-access-token"

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
