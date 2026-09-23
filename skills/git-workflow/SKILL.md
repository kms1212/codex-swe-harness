---
name: git-workflow
description: Preserve user state while operating on Git history or refs. Use for Git mutations or when change provenance affects safe execution; ordinary file work in a repository does not activate this skill by itself.
---

# Git Workflow

## Governing outcome

Preserve the user's working state while producing the authorized conceptual change. A dirty working tree is valid. A clean tree is not a success criterion and does not justify moving or discarding work.

Git history should describe meaningful system evolution. The number or size of commits is not the goal. Use the conceptual boundary established by `software-evolution` and preserve the verification that makes that boundary trustworthy.

## Responsibility

This skill owns safe Git operations and change provenance. `software-evolution` owns the engineering decision being recorded. Repository guidance governs the project's Git workflow and release requirements. Global governance determines authorization and permission boundaries.

Apply this skill when an operation changes Git state or existing Git state affects safe execution. A read-only inspection does not authorize a later mutation.

## Establish authorization and state

### Authorization

A request to implement does not by itself authorize recording a commit or changing a ref. Commit when the user requests it or applicable repository guidance requires it.

Treat working-state operations and history edits as distinct authorization scopes. Remote mutation has its own external effect. Authorization for one scope does not imply authorization for another.

### Relevant state

Before a mutation, establish the repository and worktree that own the target. Inspect the current checkout and the state the operation can affect. Account for an operation already in progress before beginning another.

Inspect the index separately from the working tree. Include untracked files when assessing preservation. For ref operations, establish the affected refs and whether their history is shared. Inspect other worktrees when they may hold an affected branch.

Use executable project guidance to determine required verification and release policy. Repeat state inspection when intervening work can invalidate it, not for every ordinary code read.

## Preserve provenance

Assume an existing change may belong to the user or another agent until its origin is established. Work around it in place when that remains safe. Uncertain provenance is not permission to include the change in a commit or discard it.

Before a state-discarding or history-rewriting action, identify its exact target. Establish what must survive and why the operation is necessary. Confirm its authorization and expected impact. Determine whether recovery is possible and identify the concrete recovery path.

A stash is a move of user state with restoration obligations. It is not a default response to inconvenient working changes. Preservation in place remains the default.

When ownership cannot be established and affects a proposed mutation, stop that mutation and request direction. Report uncertainty without claiming evidence the repository does not provide.

## Diagnose before changing strategy

An operation failure does not broaden authorization. Inspect the actual cause before selecting a response. Establish whether the obstacle comes from Git state or an external execution constraint.

Resolve the evidenced cause while preserving unrelated work. Do not escalate from failure to a destructive operation merely because it is convenient. Request additional filesystem access only for a diagnosed restriction and its exact target.

## Perform the authorized operation

When preparing a commit or revising unpublished local history, read [Commits and history](references/commits-and-history.md). It governs staged-content selection and review. The index must express the intended conceptual unit rather than the accidental order of edits.

When operating on refs or moving working state, read [Operations and remotes](references/operations-and-remotes.md). Also read it for conflicts or nested repository boundaries. Use the operation-specific safeguards and verify the actual destination before external mutation.

Do not treat local unpublished history and shared history as equivalent risk. A tidier graph does not justify rewriting shared history. Reconstructing the current implementation does not grant permission to erase its recorded past.

## Completion judgment

Inspect the result of the operation in the intended repository. Confirm that the recorded or staged content matches the authorized change and that unrelated working state remains intact. Do not substitute a working-tree diff for review of the index or commit.

Required verification must apply to the final relevant state. For remote changes, inspect the actual resulting ref rather than assuming a successful local command proves the intended remote outcome.

Report remaining state and unresolved ownership. An unrestored stash remains user state. Uncommitted changes do not make a successfully completed task incomplete unless the request required recording them.
