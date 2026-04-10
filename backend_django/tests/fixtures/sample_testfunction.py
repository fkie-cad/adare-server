class IsFileParams:
    path: str = ""


class IsFile(BasicTest):
    testname: str = "is_file"
    testdescription: str = "Check if a file exists at the given path"
    params: IsFileParams
