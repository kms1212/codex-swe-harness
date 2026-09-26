#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

MODE="install"
DRY_RUN=0
ASSUME_YES=0
RESTORE_FROM=""
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DIR="$HOME/.agents/skills"

usage() {
  cat <<'EOF'
Usage: scripts/install.sh [options]

Install or update the Codex SWE harness by linking this checkout into the
user-global Codex locations. Existing files not owned by this installer are
never overwritten.

Options:
  --dry-run             Show the planned operation without changing files.
  --yes                 Run without an interactive confirmation.
  --check               Verify the managed installation and exit.
  --uninstall           Remove links owned by this installer.
  --restore PATH        Restore links from a backup directory or manifest.
  --codex-home PATH     Codex home (default: $CODEX_HOME or ~/.codex).
  --skills-dir PATH     User skill directory (default: ~/.agents/skills).
  -h, --help            Show this help.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

info() {
  printf '%s\n' "$*"
}

require_absolute_path() {
  local label="$1"
  local value="$2"
  case "$value" in
    /*) ;;
    *) die "$label must be an absolute path: $value" ;;
  esac
  case "$value" in
    *$'\n'*|*$'\t'*) die "$label must not contain tabs or newlines" ;;
  esac
}

while (($#)); do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --yes)
      ASSUME_YES=1
      ;;
    --check)
      [[ "$MODE" == "install" ]] || die "choose only one operation"
      MODE="check"
      ;;
    --uninstall)
      [[ "$MODE" == "install" ]] || die "choose only one operation"
      MODE="uninstall"
      ;;
    --restore)
      [[ "$MODE" == "install" ]] || die "choose only one operation"
      (($# >= 2)) || die "--restore requires a path"
      MODE="restore"
      RESTORE_FROM="$2"
      shift
      ;;
    --codex-home)
      (($# >= 2)) || die "--codex-home requires a path"
      CODEX_HOME_DIR="$2"
      shift
      ;;
    --skills-dir)
      (($# >= 2)) || die "--skills-dir requires a path"
      SKILLS_DIR="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
  shift
done

require_absolute_path "repository root" "$REPOSITORY_ROOT"
require_absolute_path "Codex home" "$CODEX_HOME_DIR"
require_absolute_path "skills directory" "$SKILLS_DIR"

STATE_DIR="$CODEX_HOME_DIR/.codex-swe-harness"
MANIFEST_PATH="$STATE_DIR/manifest.tsv"
BACKUPS_DIR="$STATE_DIR/backups"

declare -a EXPECTED_TARGETS=(
  "$CODEX_HOME_DIR/AGENTS.md"
  "$SKILLS_DIR/software-evolution"
  "$SKILLS_DIR/product-ui"
  "$SKILLS_DIR/technical-documentation"
  "$SKILLS_DIR/git-workflow"
  "$SKILLS_DIR/thread-coordination"
)
declare -a EXPECTED_SOURCES=(
  "$REPOSITORY_ROOT/global/AGENTS.md"
  "$REPOSITORY_ROOT/skills/software-evolution"
  "$REPOSITORY_ROOT/skills/product-ui"
  "$REPOSITORY_ROOT/skills/technical-documentation"
  "$REPOSITORY_ROOT/skills/git-workflow"
  "$REPOSITORY_ROOT/skills/thread-coordination"
)

declare -a MANIFEST_TARGETS=()
declare -a MANIFEST_SOURCES=()
MANIFEST_REPOSITORY=""

read_manifest() {
  local path="$1"
  local kind=""
  local first=""
  local second=""
  local extra=""
  local header_seen=0

  [[ -f "$path" && ! -L "$path" ]] || die "manifest is missing or is not a regular file: $path"
  MANIFEST_TARGETS=()
  MANIFEST_SOURCES=()
  MANIFEST_REPOSITORY=""

  while IFS=$'\t' read -r kind first second extra || [[ -n "$kind$first$second$extra" ]]; do
    [[ -z "$extra" ]] || die "invalid manifest record in $path"
    if ((header_seen == 0)); then
      [[ "$kind" == "codex-swe-harness-manifest" && "$first" == "1" && -z "$second" ]] || die "unsupported manifest format: $path"
      header_seen=1
      continue
    fi
    case "$kind" in
      repository)
        [[ -z "$MANIFEST_REPOSITORY" && -n "$first" && -z "$second" ]] || die "invalid repository record in $path"
        MANIFEST_REPOSITORY="$first"
        ;;
      link)
        [[ -n "$first" && -n "$second" ]] || die "invalid link record in $path"
        MANIFEST_TARGETS+=("$first")
        MANIFEST_SOURCES+=("$second")
        ;;
      *)
        die "unknown manifest record '$kind' in $path"
        ;;
    esac
  done < "$path"

  ((header_seen == 1)) || die "empty manifest: $path"
  [[ -n "$MANIFEST_REPOSITORY" ]] || die "manifest has no repository record: $path"
  local link_count="${#MANIFEST_TARGETS[@]}"
  ((link_count == 4 || link_count == 5 || link_count == ${#EXPECTED_TARGETS[@]})) || {
    die "manifest must contain four or five legacy links or ${#EXPECTED_TARGETS[@]} current links: $path"
  }
}

validate_expected_sources() {
  local source
  for source in "${EXPECTED_SOURCES[@]}"; do
    [[ -e "$source" ]] || die "source is missing: $source"
    require_absolute_path "source" "$source"
  done
}

validate_manifest_targets() {
  local index
  for index in "${!MANIFEST_TARGETS[@]}"; do
    [[ "${MANIFEST_TARGETS[$index]}" == "${EXPECTED_TARGETS[$index]}" ]] || {
      die "managed target layout differs from the requested paths; uninstall with the original paths before relocating"
    }
  done
}

validate_manifest_sources() {
  require_absolute_path "manifest repository" "$MANIFEST_REPOSITORY"
  local expected_manifest_sources=(
    "$MANIFEST_REPOSITORY/global/AGENTS.md"
    "$MANIFEST_REPOSITORY/skills/software-evolution"
    "$MANIFEST_REPOSITORY/skills/product-ui"
    "$MANIFEST_REPOSITORY/skills/technical-documentation"
    "$MANIFEST_REPOSITORY/skills/git-workflow"
    "$MANIFEST_REPOSITORY/skills/thread-coordination"
  )
  local index
  for index in "${!MANIFEST_SOURCES[@]}"; do
    [[ "${MANIFEST_SOURCES[$index]}" == "${expected_manifest_sources[$index]}" ]] || die "manifest source layout is invalid"
  done
}

preflight_new_managed_targets() {
  local index target
  for ((index=${#MANIFEST_TARGETS[@]}; index < ${#EXPECTED_TARGETS[@]}; index++)); do
    target="${EXPECTED_TARGETS[$index]}"
    if path_exists_or_link "$target"; then
      die "new managed target already exists and is not owned by this installer: $target"
    fi
  done
}

link_value() {
  readlink "$1"
}

is_exact_link() {
  local target="$1"
  local source="$2"
  [[ -L "$target" ]] && [[ "$(link_value "$target")" == "$source" ]]
}

path_exists_or_link() {
  [[ -e "$1" || -L "$1" ]]
}

preflight_owned_targets() {
  local index target old_source
  for index in "${!MANIFEST_TARGETS[@]}"; do
    target="${MANIFEST_TARGETS[$index]}"
    old_source="${MANIFEST_SOURCES[$index]}"
    if path_exists_or_link "$target" && ! is_exact_link "$target" "$old_source"; then
      die "managed target was changed outside the installer: $target"
    fi
  done
}

confirm_or_exit() {
  local prompt="$1"
  if ((DRY_RUN == 1 || ASSUME_YES == 1)); then
    return
  fi
  [[ -t 0 ]] || die "interactive confirmation is unavailable; rerun with --yes or --dry-run"
  printf '%s [y/N] ' "$prompt" >&2
  local answer=""
  IFS= read -r answer
  case "$answer" in
    y|Y|yes|YES) ;;
    *) die "cancelled" ;;
  esac
}

write_manifest() {
  local output="$1"
  local repository="$2"
  local index
  {
    printf 'codex-swe-harness-manifest\t1\n'
    printf 'repository\t%s\n' "$repository"
    for index in "${!EXPECTED_TARGETS[@]}"; do
      printf 'link\t%s\t%s\n' "${EXPECTED_TARGETS[$index]}" "${EXPECTED_SOURCES[$index]}"
    done
  } > "$output"
}

create_backup() {
  local source_manifest="$1"
  local stamp backup_dir
  stamp="$(date -u +%Y%m%dT%H%M%SZ)-$$"
  backup_dir="$BACKUPS_DIR/$stamp"
  mkdir -p "$backup_dir"
  cp "$source_manifest" "$backup_dir/manifest.tsv"
  printf '%s' "$backup_dir"
}

declare -a CHANGED_TARGETS=()
declare -a PREVIOUS_SOURCES=()
declare -a PREVIOUS_PRESENT=()
declare -a CREATED_DIRS=()
ROLLBACK_ACTIVE=0
TEMP_PATH=""

remember_directory() {
  local directory="$1"
  if [[ ! -d "$directory" ]]; then
    mkdir -p "$directory"
    CREATED_DIRS+=("$directory")
  fi
}

remember_target() {
  local target="$1"
  local previous_source="$2"
  local previous_present="$3"
  CHANGED_TARGETS+=("$target")
  PREVIOUS_SOURCES+=("$previous_source")
  PREVIOUS_PRESENT+=("$previous_present")
}

rollback_changes() {
  local status=$?
  local index target
  if ((ROLLBACK_ACTIVE == 1)); then
    set +e
    if [[ -n "$TEMP_PATH" ]]; then
      rm -f "$TEMP_PATH"
    fi
    for ((index=${#CHANGED_TARGETS[@]} - 1; index >= 0; index--)); do
      target="${CHANGED_TARGETS[$index]}"
      if [[ -L "$target" ]]; then
        rm -f "$target"
      fi
      if [[ "${PREVIOUS_PRESENT[$index]}" == "1" ]]; then
        ln -s "${PREVIOUS_SOURCES[$index]}" "$target"
      fi
    done
    for ((index=${#CREATED_DIRS[@]} - 1; index >= 0; index--)); do
      rmdir "${CREATED_DIRS[$index]}" 2>/dev/null
    done
    printf 'error: operation failed; managed links were rolled back\n' >&2
  fi
  exit "$status"
}
trap rollback_changes EXIT

install_or_update() {
  validate_expected_sources

  local operation="new installation"
  local existing_manifest=0
  local index target source old_source previous_present changes=0

  if path_exists_or_link "$MANIFEST_PATH"; then
    read_manifest "$MANIFEST_PATH"
    validate_manifest_targets
    validate_manifest_sources
    preflight_owned_targets
    preflight_new_managed_targets
    existing_manifest=1
    operation="managed installation update"
  else
    for target in "${EXPECTED_TARGETS[@]}"; do
      if path_exists_or_link "$target"; then
        die "target already exists and is not owned by this installer: $target"
      fi
    done
  fi

  for index in "${!EXPECTED_TARGETS[@]}"; do
    target="${EXPECTED_TARGETS[$index]}"
    source="${EXPECTED_SOURCES[$index]}"
    if ! is_exact_link "$target" "$source"; then
      changes=$((changes + 1))
    fi
  done

  info "Operation: $operation"
  info "Repository: $REPOSITORY_ROOT"
  info "Codex home: $CODEX_HOME_DIR"
  info "Skills directory: $SKILLS_DIR"
  if ((changes == 0 && existing_manifest == 1)); then
    info "Result: already current; all managed links point to this checkout."
    return
  fi
  for index in "${!EXPECTED_TARGETS[@]}"; do
    target="${EXPECTED_TARGETS[$index]}"
    source="${EXPECTED_SOURCES[$index]}"
    if ! is_exact_link "$target" "$source"; then
      info "  link $target -> $source"
    fi
  done

  if ((DRY_RUN == 1)); then
    info "Dry run: no files were changed."
    return
  fi
  confirm_or_exit "Proceed with $operation?"

  local backup_dir=""
  if ((existing_manifest == 1)); then
    backup_dir="$(create_backup "$MANIFEST_PATH")"
    info "Recovery backup: $backup_dir"
  fi

  ROLLBACK_ACTIVE=1
  remember_directory "$CODEX_HOME_DIR"
  remember_directory "$SKILLS_DIR"
  remember_directory "$STATE_DIR"

  for index in "${!EXPECTED_TARGETS[@]}"; do
    target="${EXPECTED_TARGETS[$index]}"
    source="${EXPECTED_SOURCES[$index]}"
    if is_exact_link "$target" "$source"; then
      continue
    fi
    previous_present=0
    old_source=""
    if ((existing_manifest == 1 && index < ${#MANIFEST_SOURCES[@]})) && is_exact_link "$target" "${MANIFEST_SOURCES[$index]}"; then
      previous_present=1
      old_source="${MANIFEST_SOURCES[$index]}"
      rm -f "$target"
    fi
    remember_target "$target" "$old_source" "$previous_present"
    ln -s "$source" "$target"
  done

  TEMP_PATH="$STATE_DIR/manifest.tsv.tmp.$$"
  write_manifest "$TEMP_PATH" "$REPOSITORY_ROOT"
  mv -f "$TEMP_PATH" "$MANIFEST_PATH"
  TEMP_PATH=""
  ROLLBACK_ACTIVE=0
  info "Installed and verified managed links."
}

check_installation() {
  read_manifest "$MANIFEST_PATH"
  validate_manifest_targets
  validate_manifest_sources
  ((${#MANIFEST_TARGETS[@]} == ${#EXPECTED_TARGETS[@]})) || {
    die "managed installation is outdated; run the installer to add the missing managed links"
  }
  local index target source failures=0
  for index in "${!MANIFEST_TARGETS[@]}"; do
    target="${MANIFEST_TARGETS[$index]}"
    source="${MANIFEST_SOURCES[$index]}"
    if [[ ! -e "$source" ]]; then
      printf 'missing source: %s\n' "$source" >&2
      failures=$((failures + 1))
    elif ! is_exact_link "$target" "$source"; then
      printf 'mismatch: %s (expected link to %s)\n' "$target" "$source" >&2
      failures=$((failures + 1))
    elif [[ ! "$target" -ef "$source" ]]; then
      printf 'identity check failed: %s\n' "$target" >&2
      failures=$((failures + 1))
    else
      info "ok: $target -> $source"
    fi
  done
  ((failures == 0)) || die "$failures managed link(s) failed verification"
  info "Verification passed: installed paths resolve to their recorded source-of-truth files."
}

uninstall_managed() {
  read_manifest "$MANIFEST_PATH"
  validate_manifest_targets
  validate_manifest_sources
  preflight_owned_targets
  info "Operation: uninstall managed links"
  local target
  for target in "${MANIFEST_TARGETS[@]}"; do
    if path_exists_or_link "$target"; then
      info "  remove $target"
    fi
  done
  if ((DRY_RUN == 1)); then
    info "Dry run: no files were changed."
    return
  fi
  confirm_or_exit "Remove the managed links?"

  local backup_dir
  backup_dir="$(create_backup "$MANIFEST_PATH")"
  info "Recovery backup: $backup_dir"
  ROLLBACK_ACTIVE=1
  local index
  for index in "${!MANIFEST_TARGETS[@]}"; do
    target="${MANIFEST_TARGETS[$index]}"
    if is_exact_link "$target" "${MANIFEST_SOURCES[$index]}"; then
      remember_target "$target" "${MANIFEST_SOURCES[$index]}" 1
      rm -f "$target"
    fi
  done
  rm -f "$MANIFEST_PATH"
  ROLLBACK_ACTIVE=0
  info "Uninstalled managed links. The source checkout and backup were kept."
}

restore_backup() {
  local backup_manifest="$RESTORE_FROM"
  if [[ -d "$backup_manifest" ]]; then
    backup_manifest="$backup_manifest/manifest.tsv"
  fi
  require_absolute_path "backup path" "$backup_manifest"
  path_exists_or_link "$MANIFEST_PATH" && die "a managed installation already exists: $MANIFEST_PATH"
  read_manifest "$backup_manifest"
  validate_manifest_targets
  validate_manifest_sources

  local index target source
  for index in "${!MANIFEST_TARGETS[@]}"; do
    target="${MANIFEST_TARGETS[$index]}"
    source="${MANIFEST_SOURCES[$index]}"
    [[ -e "$source" ]] || die "backup source is no longer available: $source"
    if path_exists_or_link "$target" && ! is_exact_link "$target" "$source"; then
      die "restore target is occupied: $target"
    fi
  done

  info "Operation: restore managed links"
  info "Backup manifest: $backup_manifest"
  for index in "${!MANIFEST_TARGETS[@]}"; do
    info "  link ${MANIFEST_TARGETS[$index]} -> ${MANIFEST_SOURCES[$index]}"
  done
  if ((DRY_RUN == 1)); then
    info "Dry run: no files were changed."
    return
  fi
  confirm_or_exit "Restore this managed installation?"

  ROLLBACK_ACTIVE=1
  remember_directory "$CODEX_HOME_DIR"
  remember_directory "$STATE_DIR"
  for index in "${!MANIFEST_TARGETS[@]}"; do
    target="${MANIFEST_TARGETS[$index]}"
    source="${MANIFEST_SOURCES[$index]}"
    remember_directory "$(dirname "$target")"
    if ! is_exact_link "$target" "$source"; then
      remember_target "$target" "" 0
      ln -s "$source" "$target"
    fi
  done
  TEMP_PATH="$MANIFEST_PATH.tmp.$$"
  cp "$backup_manifest" "$TEMP_PATH"
  mv -f "$TEMP_PATH" "$MANIFEST_PATH"
  TEMP_PATH=""
  ROLLBACK_ACTIVE=0
  info "Restored and verified managed links."
}

case "$MODE" in
  install) install_or_update ;;
  check) check_installation ;;
  uninstall) uninstall_managed ;;
  restore) restore_backup ;;
  *) die "unsupported operation: $MODE" ;;
esac
