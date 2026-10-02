"""Cleanup only resources created in the harness's explicit scratch namespace."""
from __future__ import annotations

import shutil
from pathlib import Path
from .core import Ledger, canonical_bytes


def scratch(ledger: Ledger, name: str) -> str:
    if not name or Path(name).name != name or name in {'.', '..'}:
        raise ValueError('scratch name must be one path component')
    state = ledger.read()
    path = ledger.directory / 'scratch' / name
    path.mkdir(parents=True, exist_ok=False)
    marker = {'task_id': state['task_id'], 'name': name, 'owner': 'harness', 'lifetime': 'ephemeral'}
    (path / '.harness-owned.json').write_bytes(canonical_bytes(marker))
    state['resources'].append(dict(marker, path=str(path), status='active'))
    ledger._write_state(state)
    ledger.append_event('scratch_created', marker)
    return str(path)


def cleanup(ledger: Ledger) -> list[str]:
    state = ledger.read()
    removed = []
    for resource in state['resources']:
        path = Path(resource['path'])
        expected = {key: resource[key] for key in ('task_id', 'name', 'owner', 'lifetime')}
        if resource['status'] != 'active' or expected['owner'] != 'harness' or expected['lifetime'] != 'ephemeral' or expected['task_id'] != state['task_id']:
            continue
        marker = path / '.harness-owned.json'
        if path.parent != ledger.directory / 'scratch' or path.is_symlink() or not marker.is_file() or marker.is_symlink() or marker.read_bytes() != canonical_bytes(expected):
            continue
        shutil.rmtree(path)
        resource['status'] = 'cleaned'
        removed.append(str(path))
    ledger._write_state(state)
    ledger.append_event('scratch_cleaned', {'paths': removed})
    return removed


def tracking_reasons(state: dict, paths: list[str]) -> list[str]:
    """New tracking crosses a persistence boundary, independently of file creation."""
    missing = []
    for path in paths:
        artifact = next((x for x in reversed(state['artifacts']) if path in x.get('repository_paths', [])), None)
        decision = artifact.get('persistence', {}) if artifact else {}
        if (not artifact or not artifact.get('semantic_owner') or artifact.get('expected_lifetime') in {'ephemeral', 'unknown'}
                or not all(decision.get(key) is True for key in ('separate_file', 'repository_placement', 'git_tracking', 'durable'))
                or not all(decision.get(key) for key in ('future_consumer', 'maintainer', 'convention', 'contract', 'alternatives', 'reason'))):
            missing.append(path)
    return missing
