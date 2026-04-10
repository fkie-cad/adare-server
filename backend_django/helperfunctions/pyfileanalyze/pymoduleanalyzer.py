# external imports
import ast
from pathlib import Path
from typing import Optional

# internal imports
from helperfunctions.pyfileanalyze.load import load_as_ast_module
from helperfunctions.pyfileanalyze.pyclassanalyzer import PyClassAnalyzer

# configure logging
import logging
log = logging.getLogger(__name__)


class PyDecoratedAttributeAdapter:
    """Adapter that mimics PyClassAttributeAnalyzer for decorator-based testfunction attributes."""

    def __init__(self, value: str = '', attr_type: str = ''):
        self._value = value
        self._type = attr_type

    def get_value(self) -> str:
        return self._value

    def get_type(self) -> str:
        return self._type

    def get_attribute_as_dict(self) -> dict:
        return {'name': '', 'type': self._type, 'value': self._value}


class PyDecoratedParamAnalyzer:
    """Adapter that mimics PyClassAnalyzer for synthetic parameter classes
    extracted from @testfunction-decorated function signatures."""

    def __init__(self, func_node: ast.FunctionDef):
        self._func_node = func_node
        self.name = f'_DecoratorParam_{func_node.name}'

    def get_attributes_as_dict(self) -> dict:
        """Extract parameters from function signature, skipping 'ctx'."""
        attributes = {}
        args = self._func_node.args

        # Build list of (arg, default) pairs. defaults are right-aligned to args.
        num_args = len(args.args)
        num_defaults = len(args.defaults)
        defaults_offset = num_args - num_defaults

        for i, arg in enumerate(args.args):
            if arg.arg == 'ctx':
                continue
            if arg.arg == 'self':
                continue

            param_type = ''
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param_type = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant):
                    param_type = str(arg.annotation.value)
                elif isinstance(arg.annotation, ast.Attribute):
                    param_type = arg.annotation.attr

            param_value = ''
            default_index = i - defaults_offset
            if default_index >= 0 and default_index < num_defaults:
                default_node = args.defaults[default_index]
                if isinstance(default_node, ast.Constant):
                    param_value = str(default_node.value)
                elif isinstance(default_node, ast.Name):
                    param_value = default_node.id

            attributes[arg.arg] = {
                'name': arg.arg,
                'type': param_type,
                'value': param_value,
            }

        return attributes

    def has_attribute(self, attr_name: str) -> bool:
        return attr_name in self.get_attributes_as_dict()

    def get_attribute(self, attr_name: str):
        attrs = self.get_attributes_as_dict()
        if attr_name in attrs:
            attr = attrs[attr_name]
            return PyDecoratedAttributeAdapter(value=attr['value'], attr_type=attr['type'])
        return None


class PyDecoratedFunctionAnalyzer:
    """Adapter that mimics PyClassAnalyzer for @testfunction-decorated functions."""

    def __init__(self, func_node: ast.FunctionDef, decorator_kwargs: dict):
        self._func_node = func_node
        self._decorator_kwargs = decorator_kwargs
        self.name = f'_DecoratorTest_{func_node.name}'
        self._param_analyzer = PyDecoratedParamAnalyzer(func_node)

    def has_attribute(self, attr_name: str) -> bool:
        return attr_name in ('params', 'parameter', 'testname', 'testdescription')

    def get_attribute(self, attr_name: str) -> Optional[PyDecoratedAttributeAdapter]:
        if attr_name == 'testname':
            return PyDecoratedAttributeAdapter(value=self._decorator_kwargs.get('name', ''))
        if attr_name == 'testdescription':
            return PyDecoratedAttributeAdapter(value=self._decorator_kwargs.get('description', ''))
        if attr_name in ('params', 'parameter'):
            return PyDecoratedAttributeAdapter(attr_type=self._param_analyzer.name)
        return None

    def get_attributes_as_dict(self) -> dict:
        return self._param_analyzer.get_attributes_as_dict()


def _extract_decorator_kwargs(decorator: ast.Call) -> dict:
    """Extract keyword arguments from a @testfunction(...) decorator call."""
    kwargs = {}
    for kw in decorator.keywords:
        if kw.arg and isinstance(kw.value, ast.Constant):
            kwargs[kw.arg] = str(kw.value.value)
        elif kw.arg and isinstance(kw.value, ast.Attribute):
            kwargs[kw.arg] = kw.value.attr
        elif kw.arg and isinstance(kw.value, ast.Name):
            kwargs[kw.arg] = kw.value.id
    return kwargs


def _is_testfunction_decorator(decorator) -> bool:
    """Check if a decorator node is @testfunction (with or without attribute access)."""
    if isinstance(decorator, ast.Call):
        func = decorator.func
        # @testfunction(...)
        if isinstance(func, ast.Name) and func.id == 'testfunction':
            return True
        # @something.testfunction(...)
        if isinstance(func, ast.Attribute) and func.attr == 'testfunction':
            return True
    return False


class PyModuleAnalyzer:
    module: ast.Module

    def __init__(self, python_file: Path):
        self.module = load_as_ast_module(python_file)
        self._decorated_functions: Optional[list[PyDecoratedFunctionAnalyzer]] = None
        self._decorated_param_map: Optional[dict[str, PyDecoratedParamAnalyzer]] = None

    def _ensure_decorated_functions_parsed(self):
        """Lazily parse @testfunction-decorated functions from the module."""
        if self._decorated_functions is not None:
            return
        self._decorated_functions = []
        self._decorated_param_map = {}
        for node in self.module.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if _is_testfunction_decorator(decorator):
                    kwargs = _extract_decorator_kwargs(decorator)
                    analyzer = PyDecoratedFunctionAnalyzer(node, kwargs)
                    self._decorated_functions.append(analyzer)
                    self._decorated_param_map[analyzer._param_analyzer.name] = analyzer._param_analyzer
                    break

    def get_decorated_testfunctions(self) -> list[PyDecoratedFunctionAnalyzer]:
        """Return analyzers for all @testfunction-decorated functions in the module."""
        self._ensure_decorated_functions_parsed()
        return list(self._decorated_functions)

    def get_classes(self, parent: str = None) -> list[PyClassAnalyzer]:
        class_list: list = []
        for node in self.module.body:
            if type(node) == ast.ClassDef:
                node: ast.ClassDef
                if parent:
                    is_subclass = False
                    if hasattr(node, 'bases'):
                        for base in node.bases:
                            if hasattr(base, 'id'):
                                if base.id == parent:
                                    is_subclass = True
                            else:
                                log.warning(f'base has no id: {base}')
                        if is_subclass:
                            class_list.append(PyClassAnalyzer(node))
                else:
                    class_list.append(PyClassAnalyzer(node))

        # Include @testfunction-decorated functions when looking for BasicTest subclasses
        if parent == 'BasicTest':
            class_list.extend(self.get_decorated_testfunctions())

        return class_list

    def has_class(self, class_name: str) -> bool:
        classes = self.get_classes()
        found_class = class_name in [cl.name for cl in classes]
        return found_class

    def get_class(self, class_name: str) -> Optional[PyClassAnalyzer]:
        classes = self.get_classes()
        for cl in classes:
            if cl.name == class_name:
                return cl

        # Check synthetic parameter classes from decorated functions
        self._ensure_decorated_functions_parsed()
        if class_name in self._decorated_param_map:
            return self._decorated_param_map[class_name]

        return None
