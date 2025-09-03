#!/bin/bash

# === CONFIGURATION ===
NEXUS_URL="https://nexus.example.com"
USERNAME="your-username"
PASSWORD="your-password"

# === FUNCTIONS ===

get_repos() {
  curl -s -u "$USERNAME:$PASSWORD" "$NEXUS_URL/service/rest/v1/repositories" | jq -r '.[].name'
}

get_max_file_size() {
  local repo=$1
  local continuationToken=""
  local maxSize=0

  echo "Checking repository: $repo"

  while : ; do
    # Build URL with continuation token if present
    if [ -z "$continuationToken" ]; then
      URL="$NEXUS_URL/service/rest/v1/assets?repository=$repo"
    else
      URL="$NEXUS_URL/service/rest/v1/assets?repository=$repo&continuationToken=$continuationToken"
    fi

    # Fetch assets
    RESPONSE=$(curl -s -u "$USERNAME:$PASSWORD" "$URL")
    SIZES=$(echo "$RESPONSE" | jq '.items[].size // 0')

    for size in $SIZES; do
      # Ensure size is a valid integer
      if [[ "$size" =~ ^[0-9]+$ ]]; then
        if [ "$size" -gt "$maxSize" ]; then
          maxSize=$size
        fi
      fi
    done

    # Check for continuation token
    continuationToken=$(echo "$RESPONSE" | jq -r '.continuationToken // empty')
    [ -z "$continuationToken" ] && break
  done

  echo "Max file size in $repo: $maxSize bytes"
}

# === MAIN ===

repos=$(get_repos)

for repo in $repos; do
  get_max_file_size "$repo"
done
