#!/usr/bin/env bash
set -euo pipefail

print_help() {
  cat <<EOF
Usage: git smart-clone [options] <git-repo-url>

Clone a Git repository into a structured directory layout based on the URL.
Supports HTTPS and SSH URLs with arbitrary subdirectory depth.

Options:
  -o, --origin <name>  Name for the remote origin (default: origin)
  -h, --help           Show this help message

Environment Variables:
  GIT_CLONE_BASE       Base directory for checkouts (default: \$HOME/workspaces)
  GIT_CLONE_ORIGIN     Default origin name (default: origin)

Examples:
  git smart-clone https://github.com/user/repo.git
  git smart-clone -o upstream https://github.com/user/repo.git
  GIT_CLONE_BASE=~/dev git smart-clone git@gitlab.com:org/project/repo.git
  GIT_CLONE_ORIGIN=upstream git smart-clone https://github.com/user/repo.git

If the repo already exists, it will be updated using 'git pull --rebase --autostash'.
EOF
}

# Parse command-line arguments
ORIGIN_NAME="${GIT_CLONE_ORIGIN:-origin}"
GIT_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      print_help
      exit 0
      ;;
    -o|--origin)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --origin requires an argument"
        exit 1
      fi
      ORIGIN_NAME="$2"
      shift 2
      ;;
    -*)
      echo "Error: Unknown option: $1"
      echo "Run with --help for usage."
      exit 1
      ;;
    *)
      if [[ -n "$GIT_URL" ]]; then
        echo "Error: Multiple URLs provided"
        exit 1
      fi
      GIT_URL="$1"
      shift
      ;;
  esac
done

if [[ -z "$GIT_URL" ]]; then
  echo "Error: Missing Git URL."
  echo "Run with --help for usage."
  exit 1
fi

BASE_DIR="${GIT_CLONE_BASE:-${HOME}/workspaces}"

if [[ "$GIT_URL" =~ ^https://([^/]+)/(.*?)(\.git)?$ ]]; then
  HOST="${BASH_REMATCH[1]}"
  PATH_COMPONENTS="${BASH_REMATCH[2]}"
elif [[ "$GIT_URL" =~ ^git@([^:]+):(.*?)(\.git)?$ ]]; then
  HOST="${BASH_REMATCH[1]}"
  PATH_COMPONENTS="${BASH_REMATCH[2]}"
else
  echo "Error: Unsupported git URL format: $GIT_URL"
  exit 2
fi

PATH_COMPONENTS="${PATH_COMPONENTS%.git}"
TARGET_DIR="${BASE_DIR}/${HOST}/${PATH_COMPONENTS}"

mkdir -p "$(dirname "$TARGET_DIR")"

if [[ -d "$TARGET_DIR/.git" ]]; then
  echo "Repository already exists at: $TARGET_DIR"
  echo "Attempting to update repository..."
  git -C "$TARGET_DIR" pull --rebase --autostash
else
  echo "Cloning $GIT_URL into $TARGET_DIR..."
  git clone --origin "$ORIGIN_NAME" "$GIT_URL" "$TARGET_DIR"
fi

