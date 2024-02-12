import re
from pathlib import Path


class Requirement:
    package = ""
    version = ""
    relation = ""

    def __init__(self, package, version, relation):
        self.package = package
        self.version = version
        self.relation = relation

    def __str__(self):
        return self.package

    def __repr__(self):
        if not self.version and not self.relation:
            return self.package
        return f"{self.package} {self.version} {self.relation}"


def parse_requirements_from_file(file: Path) -> list:
    requirements = []
    with open(file, "r") as f:
        for line in f.readlines():
            if line.startswith("#"):
                continue
            if not line.strip():
                continue
            # match package name, version and relation (also allow for only package name)
            match = re.match(r"^(?!#)(\w[\w\.-]*)([<>=]=?[\w\.-]+)?$", line)
            if match:
                package, relation, version = match.groups()
                requirements.append(Requirement(package, version, relation))

    return requirements


def check_if_requirements_file_is_valid(file: Path) -> bool:
    with open(file, "r") as f:
        for line in f.readlines():
            if line.startswith("#"):
                continue
            if not line.strip():
                continue
            # match package name, version and relation (also allow for only package name)
            match = re.match(r"^(?!#)(\w[\w\.-]*)([<>=]=?[\w\.-]+)?$", line)
            if not match:
                return False
    return True
