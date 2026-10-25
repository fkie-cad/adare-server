# external imports
import yaml
import attr
from typing import Optional

# configure logging
import logging

log = logging.getLogger(__name__)


@attr.define
class ComparisonResult:
    success: bool
    details: Optional[str] = attr.Factory(str)
    additional_information: dict = attr.Factory(dict)
    exception: Optional[Exception] = None


class YamlCustomTag(yaml.YAMLObject):
    string: str

    def set_variables(self, variables: dict):
        pass


class YamlString(YamlCustomTag):
    yaml_tag = u'!s'

    def __init__(self, string: str):
        self.string = string

    def __repr__(self):
        return f'{self.string}'

    @classmethod
    def from_yaml(cls, loader: yaml.SafeLoader, node: yaml.nodes.MappingNode):
        return YamlString(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.string)


class YamlPath(YamlCustomTag):
    yaml_tag = u'!path'

    def __init__(self, string: str):
        self.string = string

    def __repr__(self):
        return f'{self.string}'

    @classmethod
    def from_yaml(cls, loader: yaml.SafeLoader, node: yaml.nodes.MappingNode):
        return YamlPath(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.string)


# Options of the client's `!timestamp` tag (adarelib/testset/yaml/customtags.py). The server
# only stores and displays them; the client and the guest do the comparison.
TIMESTAMP_OPTIONS = (
    'tolerance',
    'timezone',
    'format',
    'after',
    'before',
    'precision',
    'localtime',
    'timestamp_format_comparison',
    'timestamp_format_in_entry',
)


class YamlTimestamp(YamlCustomTag):
    """`!timestamp {timestamp, tolerance, timezone, format}` or the interval form `{after, before, precision}`."""

    yaml_tag = u'!timestamp'

    def __init__(self, timestamp=None, **options):
        unknown = sorted(set(options) - set(TIMESTAMP_OPTIONS))
        if unknown:
            raise ValueError(f'!timestamp has unknown option(s) {", ".join(unknown)}; '
                             f'allowed: timestamp, {", ".join(TIMESTAMP_OPTIONS)}')
        has_after, has_before = options.get('after') is not None, options.get('before') is not None
        if has_after != has_before:
            raise ValueError('!timestamp interval needs both after and before')
        if timestamp is None and not has_after:
            raise ValueError('!timestamp needs a timestamp, or an interval with after and before')
        self.string = timestamp if timestamp is not None else options['after']
        self.timestamp = timestamp
        self.options = {key: options[key] for key in TIMESTAMP_OPTIONS if options.get(key) is not None}

    def __repr__(self):
        # Shown in the test catalog: keep how the value is compared, not just the value.
        fields = ({'timestamp': self.timestamp} if self.timestamp is not None else {}) | self.options
        return f'{self.yaml_tag} {{{", ".join(f"{key}: {value}" for key, value in fields.items())}}}'

    @classmethod
    def from_yaml(cls, loader: yaml.SafeLoader, node: yaml.nodes.MappingNode):
        mapping = loader.construct_mapping(node)
        # Like the client: `!timestamp {'{{ t }}': null, tolerance: 5}` names the timestamp by its key.
        if 'timestamp' not in mapping and mapping:
            first_key = next(iter(mapping))
            if isinstance(first_key, str) and first_key not in TIMESTAMP_OPTIONS:
                mapping.pop(first_key)
                mapping['timestamp'] = first_key
        try:
            return YamlTimestamp(**mapping)
        except ValueError as e:
            raise yaml.constructor.ConstructorError(None, None, str(e), node.start_mark) from e

    @classmethod
    def to_yaml(cls, dumper, data):
        mapping = ({'timestamp': data.timestamp} if data.timestamp is not None else {}) | data.options
        return dumper.represent_mapping(cls.yaml_tag, mapping)


class YamlRegexString(YamlCustomTag):
    yaml_tag = u'!re'

    def __init__(self, string: str):
        self.string = string

    def __repr__(self):
        return f'{self.string}'

    @classmethod
    def from_yaml(cls, loader: yaml.SafeLoader, node: yaml.nodes.MappingNode):
        return YamlRegexString(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.string)


class YamlRegexStringAll(YamlRegexString):
    yaml_tag = u'!reALL'

    def __init__(self):
        super().__init__('.*')

    def __repr__(self):
        return f'{self.string}'

    @classmethod
    def from_yaml(cls, loader: yaml.SafeLoader, node: yaml.nodes.MappingNode):
        return YamlRegexStringAll()

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.string)
