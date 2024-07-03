# import settings
from django.conf import settings
import re


def convert_gitea_internal_api_url_to_viewable_url(url: str):
    # url format: $GITEA_INTERNAL_URL/api/v1/repos/miq/adareTEST/raw/experiments/deletefile/action.py?ref=main
    # convert to: $GITEA_URL/miq/adareTEST/src/branch/main/experiments/deletefile/action.py

    # convert the internal API URL to a viewable URL
    gitea_url = settings.GITEA_URL
    gitea_internal_url = settings.GITEA_INTERNAL_URL

    # remove the internal URL
    url = url.replace(gitea_internal_url, "")
    # remove the /api/v1/repos part
    url = url.replace("api/v1/repos/", "")

    # check if ?ref=$BRANCH is present
    branch = re.search(r"\?ref=(.*)", url)
    if branch:
        branch = branch.group(1)
        # remove the ?ref=$BRANCH part
        url = url.replace(f"?ref={branch}", "")
    else:
        branch = "main"

    # replace /raw/ with /src/branch/main/
    url = url.replace("/raw/", f"/src/branch/{branch}/")

    # add the Gitea URL
    url = f"{gitea_url}{url}"
    return url



