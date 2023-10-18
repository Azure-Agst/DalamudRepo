#!/usr/bin/env python3

import os
import json
import requests

GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS")
GITHUB_OUTPUT = os.environ.get("GITHUB_OUTPUT")

DEFAULTS = {
    'IsHide': False,
    'IsTestingExclusive': False,
    'ApplicableVersion': 'any',
}

DUPLICATES = {
    'DownloadLinkInstall': ['DownloadLinkTesting', 'DownloadLinkUpdate'],
}

def main():
    """Generates a repo manifest for Dalamud"""

    # Init our main list
    repo_manifest = []

    # Read in source file
    with open("sources.json", "r") as f:
        source_file = json.load(f)

    # For each repo, get the manifest
    for repotag in source_file["repos"]:
        [owner, repo] = repotag.split("/")

        # Get info from API
        repo_api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        res = requests.get(repo_api, allow_redirects=True)
        if res.status_code != 200:
            print("Failed to get repo info from GitHub API:", repotag)
            break
        release_data = res.json()

        # Attempt to identify assets
        # The API should really return a dict, this sucks
        icon_url = None; manifest_url = None; release_url = None
        for item in release_data["assets"]:
            if item["name"] == "icon.png":
                icon_url = item["browser_download_url"]
            elif item["name"] == "latest.zip":
                release_url = item["browser_download_url"]
            elif item["content_type"] == "application/json":
                manifest_url = item["browser_download_url"]

        # Ensure we got the essentials
        if not manifest_url or not manifest_url:
            print("Failed to parse assets:", repotag)
            break

        # Get Manifest
        res = requests.get(manifest_url, allow_redirects=True)
        if res.status_code != 200:
            print("Failed to retrieve manifest from GitHub API:", repotag)
            break
        manifest = res.json()

        # Add dynamic info
        manifest["DownloadCount"] = 7106412  # :)
        manifest['DownloadLinkInstall'] = release_url
        if icon_url: manifest["IconUrl"] = icon_url

        # Add default values if missing
        for k, v in DEFAULTS.items():
            if k not in manifest:
                manifest[k] = v

        # Duplicate keys as specified in DUPLICATES
        for source, keys in DUPLICATES.items():
            for k in keys:
                if k not in manifest:
                    manifest[k] = manifest[source]

        # Append to list
        repo_manifest.append(manifest)

    # Print successful generation
    print("Successfully generated new repo file!")

    # If it exists, read in existing repo file
    old_manifest = None
    if os.path.exists("repo.json"):
        with open("repo.json", "r") as f:
            old_manifest = json.load(f)

    # Diff check
    isUpdated = repo_manifest != old_manifest
    
    # Print respectively & save to disk
    if isUpdated:
        print("Changes detected! Writing to disk...")
        with open("repo.json", "w") as f:
            json.dump(repo_manifest, f, indent=2)
    else:
        print("No changes detected! Exiting...")
    
    # If an action, output value
    if GITHUB_ACTIONS:
        print("Writing GitHub output values...")
        with open(GITHUB_OUTPUT, "a") as f:
            f.write(f"PUSH_CHANGES={isUpdated}\n")
    
    return 0

if __name__ == "__main__":
    exit(main())