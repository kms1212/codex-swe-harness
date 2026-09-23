# Operations and Remotes

Read this reference for branch and worktree operations, stash, conflicts, merge, rebase, cherry-pick, revert, amend, history rewrite, push, force push, tags, submodules, nested repositories, or other ref mutation.

## Branches and worktrees

Create a branch when it provides a real isolation, review, delivery, parallel-work, or experimentation boundary. Do not create a branch automatically for every edit.

Before switching branches, determine how staged, unstaged, and untracked state will behave:

- whether it follows the switch;
- whether it conflicts;
- whether it can be overwritten;
- whether it prevents the switch.

Do not respond to a blocked switch by automatically stashing, resetting, or deleting the existing state.

Treat each Git worktree as an independent workspace with its own path, branch, and working state. Inspect relevant worktrees before changing or deleting a branch. Do not force a branch away from another worktree.

Do not confuse Codex workspace roots and filesystem permissions with Git worktree identity.

## Stash

Stash only when moving state is necessary and authorized.

Before stashing, establish:

- the exact tracked and untracked changes to move;
- the known or uncertain owner of those changes;
- why preserving them in place prevents safe progress;
- whether ignored or untracked files are included;
- how the stash will be identified;
- when and where it will be restored;
- what happens if restoration conflicts.

Do not describe a stash as harmless cleanup. Report an unrestored stash as remaining user state.

## Conflicts

A conflict is a disagreement between intended states, not only overlapping text.

Before resolving it, understand as applicable:

- the requirement each side implements;
- current architecture and ownership;
- relevant contracts and tests;
- later changes on each side;
- compatibility constraints;
- repository merge policy.

Do not select `ours`, `theirs`, the newer timestamp, or the larger body of code as a default resolution.

Produce the currently intended conceptual state. Verify the resolved contract and inspect the final diff for silently discarded behavior.

## Merge, rebase, cherry-pick, and revert

Do not impose a global merge-only or rebase-only policy. Follow repository workflow and choose based on:

- whether history is shared;
- branch ownership;
- review and delivery boundaries;
- conflict risk;
- repository convention;
- history clarity.

Before rebase or cherry-pick, identify the exact source and target commits, affected worktree, publication state, likely conflicts, and recovery path.

A revert creates a new inverse change; it does not erase history. Confirm that reverting the selected commit produces the intended current system state, especially when later commits depend on it.

Do not use reset as a generic substitute for understanding a failed merge, rebase, cherry-pick, or revert. Inspect the operation state and use the operation-specific continue, skip, abort, or repair path only when its effect is understood and authorized.

## Amend and history rewrite

Distinguish local unpublished history from shared history.

Amend or rewrite may be appropriate when:

- the affected commits are unpublished;
- the change remains one conceptual unit;
- the operation is authorized;
- the recovery path is known.

Treat a commit as potentially shared when it has been pushed, referenced by a review, included in a release or tag, or may be the base of another person's work.

Before rewriting shared history, confirm the exact commits and refs, affected consumers, explicit authorization, expected remote state, and recovery plan.

Do not retain accidental local edit order merely to avoid an authorized cleanup. Do not rewrite shared history merely to produce a tidier graph.

## Push and remote mutation

A push is an external mutation. Before pushing, verify:

- current branch or detached HEAD state;
- exact remote;
- exact destination ref;
- upstream configuration;
- commit range to be sent;
- whether the range contains only intended commits;
- required local verification;
- repository-specific pre-push policy;
- whether tags or additional refs will also be sent.

Do not infer the target from a familiar remote name. Inspect the configured URL and ref mapping when ambiguity matters.

Do not push while required verification is failing or unverified when repository policy requires it. Report the blocked state instead.

A non-fast-forward rejection is evidence of divergent state, not authorization to force push. Fetch or otherwise inspect the relevant remote state before selecting a resolution.

## Force push

Force push is not a default recovery mechanism.

When an authorized history rewrite requires a remote update, prefer a lease-based operation when it can verify the expected remote state. `--force-with-lease` reduces one class of overwrite risk but does not establish that the rewrite itself is correct or authorized.

Before force pushing, confirm:

- exact remote and destination branch;
- expected remote commit;
- new commit range;
- other contributors' possible work;
- branch protection and review state;
- authorization for the shared-history rewrite;
- recovery path.

Do not broaden an authorization for one branch into permission to force-update another ref.

## Tags and release refs

Treat tags as potentially published release identities.

Before creating a tag, inspect repository convention for:

- annotated or lightweight tags;
- signing;
- release automation;
- artifact association;
- naming;
- publication.

Before moving or deleting a tag, determine whether it is already published or tied to a release or artifact. Do not move a published release tag without explicit authorization and an understood recovery and communication plan.

Do not include tags in a push unless the requested scope or repository workflow includes them.

## Nested repositories, submodules, and subtrees

When the target path may cross a repository boundary, inspect the actual Git ownership of the path.

Do not assume an outer repository records the full contents of a nested repository or submodule. Do not stage a submodule pointer change without understanding the referenced commit and the state inside the submodule.

Do not delete or clean nested untracked state from the outer repository.

For subtrees or vendored generated content, follow the repository's actual update and verification procedure instead of inferring it from directory names.

## Unexpected artifacts

Investigate unexpected:

- binary changes;
- large generated diffs;
- lockfile rewrites;
- file-mode changes;
- mass renames or deletions;
- submodule pointer changes.

Size alone is not a reason to exclude a required change. Lack of an established relationship to the requested conceptual change is a reason to stop and investigate.

## Operation completion check

After the operation, verify:

- repository and worktree identity;
- current branch or detached state;
- HEAD and affected refs;
- remaining staged, unstaged, and untracked state;
- ongoing-operation state;
- intended remote result when a remote was mutated;
- preservation of unrelated user state;
- validity of required verification for the final state.

Report unresolved conflicts, remaining stashes, uncertain provenance, unpublished rewritten commits, upstream ambiguity, or remote verification limits explicitly.
