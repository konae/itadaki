"""Safely restore the legacy Instagram redirect without changing website files."""
import argparse
import ftplib
import hashlib
import json
import re
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from publish_bluehost import connect, get, put

TARGET = re.compile(r'https?://(?:www\.)?instagram\.com/cafeitadaki\.boston/?', re.I)
DIRECTORY_INDEX = re.compile(rb'(?m)^([ \t]*DirectoryIndex[ \t]+)([^\r\n]+)')


def patch_settings(data):
    matches = list(DIRECTORY_INDEX.finditer(data))
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one DirectoryIndex declaration')
    match = matches[0]
    indexes = match.group(2).decode('ascii').split()
    if not indexes or indexes[0] != 'index.html':
        raise RuntimeError('Unexpected DirectoryIndex; refuse to change')
    # Keep every existing fallback index, but make the legacy PHP redirect first.
    reordered = ['index.php'] + [x for x in indexes if x != 'index.php']
    return data[:match.start(2)] + ' '.join(reordered).encode() + data[match.end(2):]


def confirm_legacy_php(data):
    source = data.decode('utf-8', errors='replace')
    if '<?php' not in source or not re.search(r'header\s*\(.*?Location\s*:', source, re.I | re.S):
        raise RuntimeError('Legacy index.php does not contain a PHP Location header')
    if not TARGET.search(source):
        raise RuntimeError('Legacy index.php does not target the expected Instagram page')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def verify_redirect():
    req = Request('https://itadakiboston.com/?itadaki_redirect_check=20261114',
                  headers={'Cache-Control': 'no-cache', 'User-Agent': 'Itadaki-Redirect-Check'})
    try:
        response = build_opener(NoRedirect).open(req, timeout=45)
    except HTTPError as error:
        response = error
    with response:
        status = response.code
        location = response.headers.get('Location', '')
    if status not in (301, 302, 303, 307, 308) or not TARGET.match(location):
        raise RuntimeError(f'HTTPS redirect check failed: status={status}, destination={location!r}')
    print(f'HTTPS redirect verified: HTTP {status} to approved Instagram destination')


def prepare(out):
    out.mkdir(parents=True, exist_ok=True)
    ftp = connect()
    try:
        before = get(ftp, '.htaccess')
        php = get(ftp, 'index.php')
        confirm_legacy_php(php)
        after = patch_settings(before)
        if before == after:
            raise RuntimeError('No configuration change required')
        backup = out / 'backup'
        backup.mkdir(parents=True, exist_ok=True)
        (backup / '.htaccess').write_bytes(before)
        (backup / 'metadata.json').write_text(json.dumps({
            'previous_sha256': hashlib.sha256(before).hexdigest(),
            'replacement_sha256': hashlib.sha256(after).hexdigest(),
            'operation': 'restore_legacy_instagram_redirect'
        }, indent=2) + '\n')
        (out / 'new-htaccess').write_bytes(after)
        print('Validated legacy redirect and backed up existing .htaccess; no server writes yet.')
    finally:
        ftp.close()


def apply(out):
    before = (out / 'backup' / '.htaccess').read_bytes()
    after = (out / 'new-htaccess').read_bytes()
    ftp = connect()
    changed = False
    try:
        confirm_legacy_php(get(ftp, 'index.php'))
        if get(ftp, '.htaccess') != before:
            raise RuntimeError('Live .htaccess changed after backup; refusing to overwrite')
        try:
            changed = True
            put(ftp, '.htaccess', after)
            if get(ftp, '.htaccess') != after:
                raise RuntimeError('FTPS readback mismatch')
            verify_redirect()
        except Exception:
            if changed:
                put(ftp, '.htaccess', before)
                if get(ftp, '.htaccess') != before:
                    raise RuntimeError('Rollback .htaccess verification failed')
                print('Restored original .htaccess after failed verification.')
            raise
        print('Legacy Instagram redirect restored. Original website files unchanged.')
    finally:
        ftp.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['prepare', 'apply'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    {'prepare': prepare, 'apply': apply}[args.operation](args.output)
