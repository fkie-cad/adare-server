# external imports
from pathlib import Path
import cattrs

# internal imports
from customyaml.customloader import create_yaml_loader_dumper_inputfiles
from helperfunctions.yaml import yaml_to_dict
from testsetfile.fileformat import FTestsetFile, FTest

# logging configuration
import logging
log = logging.getLogger(__name__)


def parse_testsetfile(testset_file: Path) -> FTestsetFile or None:
    """
    parses a testsetfile and returns a TestsetFile object
    :param testset_file: path to the testsetfile
    :return: TestsetFile object
    """
    log.debug(f'start to read input yaml file ({testset_file})')
    loader, dumper = create_yaml_loader_dumper_inputfiles()
    parsed_input = yaml_to_dict(testset_file, loader=loader)
    if not parsed_input:
        log.info(f'parsing input yaml file ({testset_file}) was NOT successful')
        return None
    log.debug(f'read input yaml file ({testset_file}) was successful')
    try:
        testsetfile: FTestsetFile = cattrs.structure(parsed_input, FTestsetFile)
    except cattrs.BaseValidationError as e:
        log.error(f'parsing errors while parsing testsetfile {testset_file}:')
        exec_msgs = cattrs.transform_error(e)
        for msg in exec_msgs:
            log.error(msg)
        return None
    log.debug(f'testsetfile {testset_file} got successfully parsed')
    return testsetfile


def parse_playbook_tests(playbook_file: Path, experiment_name: str) -> FTestsetFile:
    """
    Parse the `tests:` block of a playbook.yml into an FTestsetFile.

    Playbook tests use `function`/`parameter`; map them to FTest's `type`/`params`.
    Params are kept as authored (unresolved {{ }} tokens) — runtime substitution is
    the client's responsibility. Playbook `actions:` are NOT part of the abstract-test
    catalog and are ignored. Only flat `function` tests are supported (no tool-grouped
    tests — the playbook schema has none).
    """
    log.debug(f'start to read playbook yaml file ({playbook_file})')
    loader, dumper = create_yaml_loader_dumper_inputfiles()
    parsed_input = yaml_to_dict(playbook_file, loader=loader)
    if not parsed_input:
        log.info(f'parsing playbook yaml file ({playbook_file}) was NOT successful')
        return FTestsetFile(name=experiment_name, tests=[], description='')

    raw_tests = parsed_input.get('tests') or []
    tests: list[FTest] = []
    for entry in raw_tests:
        function = entry.get('function')
        if not function:
            raise ValueError(f'playbook test entry missing "function": {entry!r}')
        tests.append(FTest(
            name=entry.get('name', ''),
            description=entry.get('description', ''),
            type=function,
            params=entry.get('parameter') or {},
        ))
    log.debug(f'parsed {len(tests)} tests from playbook {playbook_file}')
    return FTestsetFile(name=experiment_name, tests=tests, description='')


