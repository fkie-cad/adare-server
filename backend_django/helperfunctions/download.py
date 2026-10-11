# external imports
import requests
from helperfunctions.http import HTTP_TIMEOUT
from pathlib import Path
from tqdm import tqdm


# configure logging
import logging
log = logging.getLogger(__name__)


def download(url: str, path: Path, headers: dict = None, quiet: bool = False, response_codes_error=None, token: str = None) -> bool:
    """
        download a file from an url

        :param url: url
        :param path: place where the downloaded file will be saved to
        :param headers: headers for the request
        :param quiet: determines whether additional information about the download process should be printed
        :param response_codes_error: list of response codes that should be considered as error
    """
    if not headers:
        headers = dict()
    if token:
        headers['Authorization'] = f'token {token}'

    resp = requests.get(url, stream=True, headers=headers, timeout=HTTP_TIMEOUT)
    if response_codes_error and resp.status_code in response_codes_error:
        log.error(f'error while downloading {url}: {resp.text} ({resp.status_code})')
        return False
    total = int(resp.headers.get('content-length', 0))
    if quiet:
        log.debug(f'download of {path.as_posix()} in silent mode start')
        with open(path.as_posix(), 'wb') as file:
            for data in resp.iter_content(chunk_size=1024):
                file.write(data)
        log.debug(f'download of {path.as_posix()} in silent mode done')
    else:
        log.debug(f'download of {path.as_posix()} start')
        print(f'\nDownload {url} -> {path.as_posix()}')
        with open(path.as_posix(), 'wb') as file, tqdm(
            desc=f'',
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in resp.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)
        log.debug(f'download of {path.as_posix()} done')

    return True

