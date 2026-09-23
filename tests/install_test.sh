#!/usr/bin/env bash

set -Eeuo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPOSITORY_ROOT="$(cd "$TEST_DIR/.." && pwd -P)"
INSTALLER="$REPOSITORY_ROOT/scripts/install.sh"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/codex-swe-harness-test.XXXXXX")"
TEST_ROOT="$(cd "$TEST_ROOT" && pwd -P)"
trap 'rm -rf "$TEST_ROOT"' EXIT

pass_count=0

fail() {
  printf 'not ok - %s\n' "$*" >&2
  exit 1
}

pass() {
  pass_count=$((pass_count + 1))
  printf 'ok %d - %s\n' "$pass_count" "$1"
}

assert_link() {
  local target="$1"
  local source="$2"
  [[ -L "$target" ]] || fail "expected symlink: $target"
  [[ "$(readlink "$target")" == "$source" ]] || fail "wrong link target: $target"
  [[ "$target" -ef "$source" ]] || fail "link does not resolve to source: $target"
}

new_environment() {
  local name="$1"
  mkdir -p "$TEST_ROOT/$name/home"
  printf '%s' "$TEST_ROOT/$name/home"
}

run_installer() {
  local home_dir="$1"
  shift
  HOME="$home_dir" CODEX_HOME= "$INSTALLER" \
    --codex-home "$home_dir/.codex" \
    --skills-dir "$home_dir/.agents/skills" "$@"
}

run_checkout_installer() {
  local checkout="$1"
  local home_dir="$2"
  shift 2
  HOME="$home_dir" CODEX_HOME= "$checkout/scripts/install.sh" \
    --codex-home "$home_dir/.codex" \
    --skills-dir "$home_dir/.agents/skills" "$@"
}

seed_legacy_install() {
  local home_dir="$1"
  local repository="$2"
  local state_dir="$home_dir/.codex/.codex-swe-harness"
  mkdir -p "$home_dir/.agents/skills" "$state_dir"
  ln -s "$repository/global/AGENTS.md" "$home_dir/.codex/AGENTS.md"
  ln -s "$repository/skills/software-evolution" "$home_dir/.agents/skills/software-evolution"
  ln -s "$repository/skills/product-ui" "$home_dir/.agents/skills/product-ui"
  ln -s "$repository/skills/technical-documentation" "$home_dir/.agents/skills/technical-documentation"
  {
    printf 'codex-swe-harness-manifest\t1\n'
    printf 'repository\t%s\n' "$repository"
    printf 'link\t%s\t%s\n' "$home_dir/.codex/AGENTS.md" "$repository/global/AGENTS.md"
    printf 'link\t%s\t%s\n' "$home_dir/.agents/skills/software-evolution" "$repository/skills/software-evolution"
    printf 'link\t%s\t%s\n' "$home_dir/.agents/skills/product-ui" "$repository/skills/product-ui"
    printf 'link\t%s\t%s\n' "$home_dir/.agents/skills/technical-documentation" "$repository/skills/technical-documentation"
  } > "$state_dir/manifest.tsv"
}

home_dir="$(new_environment dry-run)"
run_installer "$home_dir" --dry-run >/dev/null
[[ ! -e "$home_dir/.codex" ]] || fail "dry-run created Codex home"
[[ ! -e "$home_dir/.agents" ]] || fail "dry-run created skill directory"
pass "dry-run does not mutate the filesystem"

home_dir="$(new_environment non-interactive)"
if run_installer "$home_dir" </dev/null >/dev/null 2>&1; then
  fail "non-interactive install without --yes unexpectedly succeeded"
fi
[[ ! -e "$home_dir/.codex" ]] || fail "refused non-interactive install changed files"
pass "non-interactive mutation requires explicit --yes"

home_dir="$(new_environment fresh)"
run_installer "$home_dir" --yes >/dev/null
assert_link "$home_dir/.codex/AGENTS.md" "$REPOSITORY_ROOT/global/AGENTS.md"
assert_link "$home_dir/.agents/skills/software-evolution" "$REPOSITORY_ROOT/skills/software-evolution"
assert_link "$home_dir/.agents/skills/git-workflow" "$REPOSITORY_ROOT/skills/git-workflow"
assert_link "$home_dir/.agents/skills/product-ui" "$REPOSITORY_ROOT/skills/product-ui"
assert_link "$home_dir/.agents/skills/technical-documentation" "$REPOSITORY_ROOT/skills/technical-documentation"
run_installer "$home_dir" --check >/dev/null
run_installer "$home_dir" --yes | grep -q 'already current' || fail "repeat install was not idempotent"
pass "fresh install links every source and repeat install is idempotent"

home_dir="$(new_environment legacy-upgrade)"
seed_legacy_install "$home_dir" "$REPOSITORY_ROOT"
if run_installer "$home_dir" --check >/dev/null 2>&1; then
  fail "legacy installation unexpectedly passed current-layout verification"
fi
run_installer "$home_dir" --yes >/dev/null
assert_link "$home_dir/.agents/skills/git-workflow" "$REPOSITORY_ROOT/skills/git-workflow"
run_installer "$home_dir" --check >/dev/null
link_count="$(grep -c $'^link\t' "$home_dir/.codex/.codex-swe-harness/manifest.tsv")"
[[ "$link_count" == "5" ]] || fail "legacy update did not write the five-link manifest"
backup_count="$(find "$home_dir/.codex/.codex-swe-harness/backups" -name manifest.tsv -type f | wc -l | tr -d ' ')"
[[ "$backup_count" == "1" ]] || fail "legacy update did not preserve one recovery manifest"
pass "legacy four-link installation upgrades to the current layout"

home_dir="$(new_environment legacy-collision)"
seed_legacy_install "$home_dir" "$REPOSITORY_ROOT"
mkdir -p "$home_dir/.agents/skills/git-workflow"
printf 'user owned\n' > "$home_dir/.agents/skills/git-workflow/keep.txt"
if run_installer "$home_dir" --yes >/dev/null 2>&1; then
  fail "legacy update overwrote an unmanaged git-workflow target"
fi
[[ -f "$home_dir/.agents/skills/git-workflow/keep.txt" ]] || fail "legacy collision changed user content"
link_count="$(grep -c $'^link\t' "$home_dir/.codex/.codex-swe-harness/manifest.tsv")"
[[ "$link_count" == "4" ]] || fail "legacy collision rewrote the manifest"
pass "legacy update refuses an occupied new target before mutation"

home_dir="$(new_environment moved-checkout)"
checkout_a="$TEST_ROOT/moved-checkout/checkout-a"
checkout_b="$TEST_ROOT/moved-checkout/checkout-b"
for checkout in "$checkout_a" "$checkout_b"; do
  mkdir -p "$checkout/scripts"
  cp "$INSTALLER" "$checkout/scripts/install.sh"
  cp -R "$REPOSITORY_ROOT/global" "$checkout/global"
  cp -R "$REPOSITORY_ROOT/skills" "$checkout/skills"
done
run_checkout_installer "$checkout_a" "$home_dir" --yes >/dev/null
run_checkout_installer "$checkout_b" "$home_dir" --yes >/dev/null
assert_link "$home_dir/.codex/AGENTS.md" "$checkout_b/global/AGENTS.md"
assert_link "$home_dir/.agents/skills/git-workflow" "$checkout_b/skills/git-workflow"
assert_link "$home_dir/.agents/skills/product-ui" "$checkout_b/skills/product-ui"
backup_count="$(find "$home_dir/.codex/.codex-swe-harness/backups" -name manifest.tsv -type f | wc -l | tr -d ' ')"
[[ "$backup_count" == "1" ]] || fail "checkout move did not create one recovery backup"
pass "managed update repoints a moved checkout and records recovery state"

home_dir="$(new_environment collision)"
mkdir -p "$home_dir/.agents/skills/product-ui"
printf 'user owned\n' > "$home_dir/.agents/skills/product-ui/keep.txt"
if run_installer "$home_dir" --yes >/dev/null 2>&1; then
  fail "collision install unexpectedly succeeded"
fi
[[ ! -e "$home_dir/.codex/AGENTS.md" ]] || fail "preflight collision left a partial install"
[[ -f "$home_dir/.agents/skills/product-ui/keep.txt" ]] || fail "collision changed user content"
pass "unmanaged collisions abort before any target changes"

home_dir="$(new_environment rollback)"
wrapper_dir="$TEST_ROOT/rollback/bin"
mkdir -p "$wrapper_dir"
real_ln="$(command -v ln)"
counter_file="$TEST_ROOT/rollback/ln-count"
cat > "$wrapper_dir/ln" <<EOF
#!/usr/bin/env bash
count=0
[[ ! -f "$counter_file" ]] || count=\$(cat "$counter_file")
count=\$((count + 1))
printf '%s' "\$count" > "$counter_file"
if [[ "\$count" == "2" ]]; then
  exit 73
fi
exec "$real_ln" "\$@"
EOF
chmod +x "$wrapper_dir/ln"
if PATH="$wrapper_dir:$PATH" run_installer "$home_dir" --yes >/dev/null 2>&1; then
  fail "injected partial failure unexpectedly succeeded"
fi
[[ ! -e "$home_dir/.codex/AGENTS.md" && ! -L "$home_dir/.codex/AGENTS.md" ]] || fail "rollback left AGENTS link"
[[ ! -e "$home_dir/.agents/skills/software-evolution" && ! -L "$home_dir/.agents/skills/software-evolution" ]] || fail "rollback left skill link"
[[ ! -e "$home_dir/.codex/.codex-swe-harness/manifest.tsv" ]] || fail "rollback left manifest"
pass "partial link failure rolls back managed targets"

home_dir="$(new_environment recovery)"
run_installer "$home_dir" --yes >/dev/null
run_installer "$home_dir" --uninstall --yes >/dev/null
[[ ! -e "$home_dir/.codex/AGENTS.md" && ! -L "$home_dir/.codex/AGENTS.md" ]] || fail "uninstall left AGENTS link"
backup_manifest="$(find "$home_dir/.codex/.codex-swe-harness/backups" -name manifest.tsv -type f | head -1)"
[[ -n "$backup_manifest" ]] || fail "uninstall did not create a recovery backup"
run_installer "$home_dir" --restore "$(dirname "$backup_manifest")" --yes >/dev/null
run_installer "$home_dir" --check >/dev/null
pass "uninstall backup restores the exact managed links"

home_dir="$(new_environment tamper)"
run_installer "$home_dir" --yes >/dev/null
rm "$home_dir/.agents/skills/product-ui"
mkdir -p "$home_dir/.agents/skills/product-ui"
printf 'user replacement\n' > "$home_dir/.agents/skills/product-ui/keep.txt"
if run_installer "$home_dir" --yes >/dev/null 2>&1; then
  fail "tampered managed target unexpectedly updated"
fi
[[ -f "$home_dir/.agents/skills/product-ui/keep.txt" ]] || fail "tamper check changed replacement content"
pass "updates refuse externally changed managed targets"

printf '1..%d\n' "$pass_count"
