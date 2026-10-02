"""Bounded command semantics, not a general shell parser."""
from __future__ import annotations

import re
import shlex
from pathlib import PurePath


def words(command: str) -> list[str]:
    # Do not interpret heredoc text, pipelines, substitutions, or compound commands as one check.
    first = command.split('\n', 1)[0]
    if any(token in first for token in (';', '&&', '||', '|', '<<', '$(', '`')):
        return []
    try:
        argv = shlex.split(first)
    except ValueError:
        return []
    if argv and argv[0] == 'env':
        argv.pop(0)
    while argv and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*', argv[0]):
        argv.pop(0)
    if argv and PurePath(argv[0]).name == 'corepack':
        argv.pop(0)
    return argv


def verification_command(command: str, declaration: dict | None = None) -> dict | None:
    argv = words(command)
    if declaration:
        if declaration.get('command_or_tool') != command or not declaration.get('scope') or not declaration.get('target_identity'):
            raise ValueError('verification declaration must bind command, scope and identity')
        return dict(declaration, expensive=True)
    if not argv:
        return None
    exe = PurePath(argv[0]).name
    args = argv[1:]
    test = (exe in {'pytest', 'jest', 'vitest'}
            or (re.fullmatch(r'python(?:3(?:\.\d+)?)?', exe) and len(args) >= 2 and args[0] == '-m' and args[1] in {'pytest', 'unittest'})
            or (exe == 'node' and '--test' in args)
            or (exe in {'cargo', 'go', 'make'} and args and args[0] == 'test'))
    if exe in {'npm', 'pnpm', 'yarn', 'bun'}:
        scripts = []
        skip = False
        for arg in args:
            if skip:
                skip = False
                continue
            if arg in {'--filter', '-F', '--dir', '-C', '--cwd', '--prefix'}:
                skip = True
            elif not arg.startswith('-'):
                scripts.append(arg)
        if scripts and scripts[0] in {'run', 'exec'}:
            scripts = scripts[1:]
        test = bool(scripts and (scripts[0] in {'test', 'pytest', 'jest', 'vitest'} or scripts[0].startswith('test:')))
    if not test:
        return None
    return dict(command_or_tool=command, scope='test', expensive=True)


def result_status(response) -> str:
    if isinstance(response, dict):
        if response.get('isError') is True or response.get('exit_code') not in (None, 0):
            return 'FAIL'
        if response.get('session_id') or response.get('cell_id'):
            return 'UNKNOWN'  # Started work is not completed verification.
        if response.get('exit_code') == 0:
            return 'PASS'
        response = response.get('output', '')
    if isinstance(response, str):
        if re.search(r'\bFAILED\b|\b[1-9][0-9]* failed\b|(?:#|ℹ) fail [1-9]|\bexit code [1-9]', response):
            return 'FAIL'
        if re.search(r'Ran \d+ tests? in [^\n]+\n\nOK\b|\b\d+ passed\b|(?:#|ℹ) fail 0\b', response):
            return 'PASS'
    return 'UNKNOWN'
