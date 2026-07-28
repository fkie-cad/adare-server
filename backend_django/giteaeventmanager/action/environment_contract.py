"""Ingest-time contract checks for the environment YAML ``recipe:`` block.

Extracted from ``EnvironmentPlugin.check_file_validity`` (see ``plugin.py``) when
the block grew a second ISO form (BYO) and a build-time ``provision`` list; the
plugin module is close to the project's 1000-line ceiling and the recipe rules
are self-contained.

**This is a coarse filter, not a trust boundary.** Everything here is derived
from publisher-supplied YAML, and the server cannot cross-check the two fields
that actually matter for the BYO decision: there is no server-side OS-profile
catalog, ``Recipe.profile`` is a free-form CharField, and profiles are
host-extensible on the client (shipping a snapshot of the client catalog would
false-reject a consumer's custom profile). So a publisher who writes
``os.platform: windows`` over a Linux profile passes every check in this module.
The authoritative gate is consumer-side, in the client's ``backend/vm/recipe.py``,
which resolves the profile for real before honouring a BYO ISO. Do not add
security-relevant decisions here on the assumption that this code is
authoritative -- it is only the fast, friendly rejection of obvious mistakes.
"""
import re

from experiments.models import Recipe
from giteaeventmanager.errorcodes import SubmitErrorCode
from giteaeventmanager.exception import TaskFailure

# A BYO ("bring your own") ISO filename. Anchored, no path separators, no '..',
# no scheme, no drive letter, '.iso' required; first char alphanumeric so a
# leading '-' can never be read as a flag by anything downstream. Length is
# capped at 200 by the pattern itself (1 + 199), matching Recipe.iso_name.
#
# CONTRACT MIRROR -- this regex is duplicated character-for-character in:
#   * the client:    adare/adare/adare/services/recipe_contract.py (ISO_NAME_RE)
#   * the adare-web BYO environment dialog
# Change all three together, the way the sha256 and vm_format contracts are
# already mirrored across client/server (see plugin.SHA256_HEX_RE, VM_FORMATS).
ISO_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._+-]{0,199}\.iso$')

# Lowercase-only 64-hex sha256 for `recipe.iso_sha256`. Deliberately stricter
# than plugin.SHA256_HEX_RE (case-insensitive, and still what governs the baked
# `vm_sha256` path): the client's `verify_iso_hash` compares the digest it
# computes against this string case-SENSITIVELY, so an uppercase digest would
# sail through publish and ingest and then leave the environment permanently
# unbuildable. Reject it here instead of shipping a broken recipe.
RECIPE_SHA256_HEX_RE = re.compile(r'^[0-9a-f]{64}$')

# Allowed values for `provision[*].shell` (mirrors the client's ProvisionCommand).
PROVISION_SHELLS = ('powershell', 'cmd', 'bash', 'auto')

# Keys accepted on a provision entry. CONTRACT MIRROR of the client's
# ProvisionCommand / ProvisionGroup attrs classes: unknown keys are rejected
# rather than ignored, because the client's cattrs structuring silently drops
# them -- a typo'd `timeout_minuts` would otherwise be accepted at publish time
# and then quietly fall back to the 30-minute default during the build.
PROVISION_COMMAND_KEYS = frozenset({
    'name', 'description', 'command', 'cwd', 'shell', 'allow_exit_codes',
    'verify', 'log_files', 'timeout_minutes', 'reboot',
})
# A group's documented shape is name/description/for_each/steps, but the client's
# ProvisionStep *subclasses* ProvisionCommand, so cattrs also accepts every leaf
# key on a top-level group entry. Those inherited keys are inert for a group
# (expand_provision's _step_commands returns `steps`, so a group-level `shell` or
# `timeout_minutes` is simply never read) -- but the client raises no error for
# them, so rejecting them here would false-reject YAML that publishes fine.
# Accept the union; the exactly-one-of command/steps check still runs first.
PROVISION_GROUP_KEYS = PROVISION_COMMAND_KEYS | frozenset({'for_each', 'steps'})

# Bounds on the provision list. `provision` is a JSONField (jsonb, effectively
# unbounded), so nothing in the schema stops a publisher from submitting a
# multi-megabyte list that every consumer then has to build; these caps keep the
# stored document reviewable and the expanded build plan finite. The expanded
# count is what a consumer actually executes: a group runs `steps` once per
# `for_each` item.
PROVISION_MAX_ENTRIES = 50
PROVISION_MAX_STEPS_PER_GROUP = 50
PROVISION_MAX_FOR_EACH_ITEMS = 20
PROVISION_MAX_EXPANDED_COMMANDS = 500

# String bounds inside a provision entry. Chosen to match the equivalent
# PostSetupInstallation columns where one exists (name/description/cwd) and to
# leave room for a realistic installer one-liner or verify snippet otherwise.
PROVISION_NAME_MAX = 500
PROVISION_DESCRIPTION_MAX = 1000
PROVISION_COMMAND_MAX = 4000
PROVISION_CWD_MAX = 2000
PROVISION_LOG_FILE_MAX = 1000
PROVISION_FOR_EACH_ITEM_MAX = 200
PROVISION_MAX_EXIT_CODES = 20
# 24h: a Windows feature install or a large MSI can legitimately run for hours,
# but a timeout beyond a day means the publisher meant something else.
PROVISION_MAX_TIMEOUT_MINUTES = 1440


def _invalid(message: str) -> TaskFailure:
    """Build the INVALID_CONTENT TaskFailure every check in this module raises."""
    return TaskFailure(message, code=SubmitErrorCode.INVALID_CONTENT)


def _check_str(value, label: str, max_length: int) -> str:
    """Type- and length-check an author-controlled scalar.

    Author-controlled YAML scalars must never reach ``re.match()``/``urlparse()``
    or a DB write unguarded: a bare ``12345`` parses as an int (TypeError -> 500,
    not a clean 400), and an over-long string only fails at the Postgres INSERT
    because ``Recipe.objects.create()`` skips ``full_clean()``.
    """
    if not isinstance(value, str):
        raise _invalid(f'{label} must be a string (got {value!r})')
    if len(value) > max_length:
        raise _invalid(f'{label} exceeds the maximum length of {max_length} characters')
    return value


def _check_int(value, label: str, maximum: int) -> int:
    """Type- and range-check a positive integer (rejecting bool, an int subclass)."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise _invalid(f'{label} must be an integer (got {value!r})')
    if value < 1:
        raise _invalid(f'{label} must be a positive integer (got {value!r})')
    if value > maximum:
        raise _invalid(f'{label} must not exceed {maximum} (got {value!r})')
    return value


def check_recipe_block(recipe_block, os_block):
    """Validate an environment file's ``recipe:`` block, raising ``TaskFailure``.

    ``os_block`` is needed because the BYO ISO form is gated on
    ``os.platform == 'windows'``; the caller validates the ``os`` block's own
    mandatory keys first, so ``os_block`` is a mapping by the time we get here.

    See the module docstring: coarse filter, not a trust boundary.
    """
    if not isinstance(recipe_block, dict):
        raise _invalid("environment 'recipe' block must be a mapping")

    # profile/iso/template: type + length must match the Recipe model columns,
    # since Recipe.objects.create() skips full_clean() and an over-long value
    # would otherwise only fail at the Postgres INSERT.
    profile = recipe_block.get('profile')
    if not profile:
        raise _invalid("environment 'recipe' block is missing required key 'profile'")
    _check_str(profile, "recipe 'profile'", Recipe._meta.get_field('profile').max_length)

    _check_iso_source(recipe_block, os_block)

    iso_sha256 = recipe_block.get('iso_sha256')
    if not iso_sha256:
        raise _invalid("environment 'recipe' block is missing required key 'iso_sha256'")
    if not isinstance(iso_sha256, str):
        raise _invalid(f"recipe 'iso_sha256' must be a 64-hex string (got {iso_sha256!r})")
    if not RECIPE_SHA256_HEX_RE.match(iso_sha256):
        raise _invalid(
            f"recipe 'iso_sha256' is not a valid sha256 hex digest: {iso_sha256!r}; "
            'it must be 64 lowercase hex characters (the consumer compares it '
            'case-sensitively, so an uppercase digest would never match)')

    template = recipe_block.get('template')
    if template:
        _check_str(template, "recipe 'template'", Recipe._meta.get_field('template').max_length)

    _check_params(recipe_block.get('params') or {})
    check_provision(recipe_block.get('provision'))


def _check_iso_source(recipe_block, os_block):
    """Enforce exactly one of the two ISO forms: hosted ``iso`` URL or BYO ``iso_name``.

    A hosted ISO must be an http(s) URL -- a bare local path (``/isos/x.iso``) is
    meaningful only on the publisher's machine and is unresolvable for every
    consumer, exactly as for the baked ``vm`` source. BYO is the Windows-only
    escape hatch: a Microsoft Windows ISO cannot legally be rehosted, so the
    consumer supplies the file and ``iso_sha256`` stays the integrity boundary.
    """
    iso = recipe_block.get('iso')
    iso_name = recipe_block.get('iso_name')

    # Both forms must be checked explicitly, including the "neither" case: the
    # client structures this YAML with cattrs, which silently ignores unknown
    # keys, so a typo'd `iso_nmae` must be rejected here rather than sliding
    # through as a recipe that simply has no ISO.
    if iso and iso_name:
        raise _invalid(
            "recipe must declare exactly one ISO source, but both 'iso' and "
            "'iso_name' are set; use 'iso' for a hosted http(s) URL or "
            "'iso_name' for a consumer-supplied (BYO) Windows ISO")
    if not iso and not iso_name:
        raise _invalid(
            "environment 'recipe' block is missing its ISO source: set 'iso' to an "
            "http(s) URL, or (Windows only) 'iso_name' to the bare filename the "
            'consumer must supply locally')

    iso_notes = recipe_block.get('iso_notes')
    if iso_notes is not None:
        # Rendered as PLAIN TEXT only -- publisher-supplied, therefore
        # attacker-controlled (see the Recipe.iso_notes model comment).
        _check_str(iso_notes, "recipe 'iso_notes'", Recipe._meta.get_field('iso_notes').max_length)

    if iso:
        _check_str(iso, "recipe 'iso'", Recipe._meta.get_field('iso').max_length)
        # urlsplit-free scheme check: the same rule the baked `vm` source applies,
        # which the recipe branch was missing entirely until BYO made the two
        # forms distinguishable.
        if not iso.startswith(('http://', 'https://')):
            raise _invalid(
                f"recipe 'iso' must be an http(s) URL (got {iso!r}); host the ISO and "
                "provide its URL, or for a Windows ISO that cannot be rehosted use "
                "'iso_name' + 'iso_sha256' so the consumer supplies it")
        return

    # BYO form.
    _check_str(iso_name, "recipe 'iso_name'", Recipe._meta.get_field('iso_name').max_length)
    platform = (os_block.get('platform') or '') if isinstance(os_block, dict) else ''
    if str(platform).lower() != 'windows':
        raise _invalid(
            f"recipe 'iso_name' (consumer-supplied ISO) is only allowed for Windows "
            f"environments, but os.platform is {platform!r}; host the ISO at an "
            "http(s) URL and declare it as 'iso' instead")
    # Matched on the stripped value because the client's contract check does the
    # same (`ISO_NAME_RE.match(recipe.iso_name.strip())`): a quoted YAML scalar
    # can carry padding, and the client tolerates it. `__db_create_environment`
    # stores the stripped form so the column stays canonical. Note the digest is
    # deliberately NOT stripped -- a padded `iso_sha256` is non-canonical, the
    # client's publish gate rejects it, and the server stores it verbatim.
    if not ISO_NAME_RE.match(iso_name.strip()):
        raise _invalid(
            f"recipe 'iso_name' must be a bare .iso filename (got {iso_name!r}): no "
            'path separators, no "..", no scheme and no drive letter, starting with '
            'a letter or digit and ending in ".iso"')


def _check_params(params):
    """Validate the ``recipe.params`` mapping against the Recipe columns."""
    if not isinstance(params, dict):
        raise _invalid("recipe 'params' must be a mapping")
    for int_key in ('setup_level', 'ram_mb', 'cpus'):
        value = params.get(int_key)
        if value is not None and not (isinstance(value, int) and not isinstance(value, bool)):
            raise _invalid(f'recipe params.{int_key} must be an integer (got {value!r})')

    # disk_size is coerced to str(...) before storage (see __db_create_environment);
    # check the length of that same coercion here.
    disk_size = params.get('disk_size')
    if disk_size is not None:
        disk_size_max = Recipe._meta.get_field('disk_size').max_length
        if len(str(disk_size)) > disk_size_max:
            raise _invalid(f'recipe params.disk_size exceeds the maximum length of '
                           f'{disk_size_max} characters')

    arch = params.get('arch')
    if arch:
        _check_str(arch, 'recipe params.arch', Recipe._meta.get_field('arch').max_length)


def check_provision(provision):
    """Validate the ``recipe.provision`` list (build-time steps), raising ``TaskFailure``.

    Stored verbatim in ``Recipe.provision``; these are the steps a consumer runs
    once, via the QEMU guest agent, while the disk is being built -- not the
    per-run ``postsetupinstallations``. Each entry is either a *command* (has
    ``command``) or a *group* (has ``steps``, optionally repeated over
    ``for_each``); groups do not nest.
    """
    if provision is None:
        return
    if not isinstance(provision, list):
        raise _invalid(f"recipe 'provision' must be a list (got {provision!r})")
    if len(provision) > PROVISION_MAX_ENTRIES:
        raise _invalid(f"recipe 'provision' must not contain more than "
                       f'{PROVISION_MAX_ENTRIES} entries (got {len(provision)})')

    expanded = 0
    for index, entry in enumerate(provision):
        label = f"recipe provision[{index}]"
        if not isinstance(entry, dict):
            raise _invalid(f'{label} must be a mapping (got {entry!r})')

        name = entry.get('name')
        if not name:
            raise _invalid(f"{label} is missing a non-empty 'name'")
        _check_str(name, f"{label} 'name'", PROVISION_NAME_MAX)
        label = f"recipe provision entry {name!r}"

        command = entry.get('command')
        steps = entry.get('steps')
        if command and steps:
            raise _invalid(f"{label} sets both 'command' and 'steps'; an entry is "
                           'either a single command or a group of steps, not both')
        if not command and not steps:
            raise _invalid(f"{label} must set exactly one of 'command' (a single "
                           "command) or 'steps' (a group)")

        if command:
            if 'for_each' in entry:
                raise _invalid(f"{label} sets 'for_each' without 'steps'; only a "
                               'group of steps can be repeated over a list')
            _check_unknown_keys(entry, PROVISION_COMMAND_KEYS, label)
            _check_provision_command(entry, label)
            expanded += 1
            continue

        _check_unknown_keys(entry, PROVISION_GROUP_KEYS, label)
        description = entry.get('description')
        if description is not None:
            _check_str(description, f"{label} 'description'", PROVISION_DESCRIPTION_MAX)
        expanded += _check_provision_group(entry, label)

    if expanded > PROVISION_MAX_EXPANDED_COMMANDS:
        raise _invalid(f"recipe 'provision' expands to {expanded} commands, which "
                       f'exceeds the limit of {PROVISION_MAX_EXPANDED_COMMANDS}')


def _check_unknown_keys(entry, allowed: frozenset, label: str):
    """Reject keys the client would silently drop (see PROVISION_COMMAND_KEYS)."""
    unknown = sorted(set(entry) - allowed)
    if unknown:
        raise _invalid(f'{label} has unknown key(s) {unknown}; allowed keys are '
                       f'{sorted(allowed)}')


def _check_provision_group(entry, label: str) -> int:
    """Validate a group entry's ``for_each``/``steps``; return its expanded command count."""
    for_each = entry.get('for_each')
    repeats = 1
    if for_each is not None:
        if not isinstance(for_each, list):
            raise _invalid(f"{label} 'for_each' must be a list of strings (got {for_each!r})")
        if len(for_each) > PROVISION_MAX_FOR_EACH_ITEMS:
            raise _invalid(f"{label} 'for_each' must not contain more than "
                           f'{PROVISION_MAX_FOR_EACH_ITEMS} items (got {len(for_each)})')
        for item in for_each:
            _check_str(item, f"{label} 'for_each' item", PROVISION_FOR_EACH_ITEM_MAX)
        repeats = len(for_each)

    steps = entry.get('steps')
    if not isinstance(steps, list):
        raise _invalid(f"{label} 'steps' must be a list (got {steps!r})")
    if len(steps) > PROVISION_MAX_STEPS_PER_GROUP:
        raise _invalid(f"{label} 'steps' must not contain more than "
                       f'{PROVISION_MAX_STEPS_PER_GROUP} steps (got {len(steps)})')

    for step_index, step in enumerate(steps):
        step_label = f'{label} step[{step_index}]'
        if not isinstance(step, dict):
            raise _invalid(f'{step_label} must be a mapping (got {step!r})')
        step_name = step.get('name')
        if not step_name:
            raise _invalid(f"{step_label} is missing a non-empty 'name'")
        _check_str(step_name, f"{step_label} 'name'", PROVISION_NAME_MAX)
        step_label = f'{label} step {step_name!r}'
        # Groups do not nest: a step is always a plain command.
        if 'steps' in step or 'for_each' in step:
            raise _invalid(f"{step_label} may not contain 'steps' or 'for_each'; "
                           'provision groups do not nest')
        if not step.get('command'):
            raise _invalid(f"{step_label} is missing a non-empty 'command'")
        _check_unknown_keys(step, PROVISION_COMMAND_KEYS, step_label)
        _check_provision_command(step, step_label)

    return repeats * len(steps)


def _check_provision_command(entry, label: str):
    """Validate the optional fields of a single provision command."""
    _check_str(entry.get('command'), f"{label} 'command'", PROVISION_COMMAND_MAX)

    description = entry.get('description')
    if description is not None:
        _check_str(description, f"{label} 'description'", PROVISION_DESCRIPTION_MAX)

    cwd = entry.get('cwd')
    if cwd is not None:
        _check_str(cwd, f"{label} 'cwd'", PROVISION_CWD_MAX)

    verify = entry.get('verify')
    if verify is not None:
        _check_str(verify, f"{label} 'verify'", PROVISION_COMMAND_MAX)

    shell = entry.get('shell')
    if shell is not None and shell not in PROVISION_SHELLS:
        raise _invalid(f"{label} 'shell' must be one of {PROVISION_SHELLS} (got {shell!r})")

    allow_exit_codes = entry.get('allow_exit_codes')
    if allow_exit_codes is not None:
        if not isinstance(allow_exit_codes, list):
            raise _invalid(f"{label} 'allow_exit_codes' must be a list of integers "
                           f'(got {allow_exit_codes!r})')
        if len(allow_exit_codes) > PROVISION_MAX_EXIT_CODES:
            raise _invalid(f"{label} 'allow_exit_codes' must not contain more than "
                           f'{PROVISION_MAX_EXIT_CODES} codes')
        for code in allow_exit_codes:
            if not isinstance(code, int) or isinstance(code, bool):
                raise _invalid(f"{label} 'allow_exit_codes' must contain only integers "
                               f'(got {code!r})')

    log_files = entry.get('log_files')
    if log_files is not None:
        if not isinstance(log_files, list):
            raise _invalid(f"{label} 'log_files' must be a list of paths (got {log_files!r})")
        for log_file in log_files:
            _check_str(log_file, f"{label} 'log_files' entry", PROVISION_LOG_FILE_MAX)

    timeout_minutes = entry.get('timeout_minutes')
    if timeout_minutes is not None:
        _check_int(timeout_minutes, f"{label} 'timeout_minutes'", PROVISION_MAX_TIMEOUT_MINUTES)

    reboot = entry.get('reboot')
    if reboot is not None and not isinstance(reboot, bool):
        raise _invalid(f"{label} 'reboot' must be a boolean (got {reboot!r})")
