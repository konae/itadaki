"""Publish reviewed static files using verified FTPS; no external dependencies."""

import argparse
import ftplib
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import ssl
import subprocess
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit, quote
from urllib.request import Request, urlopen


ALLOWED = {'.html', '.css', '.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif',
           '.svg', '.ico', '.woff', '.woff2', '.ttf', '.otf', '.pdf'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def asset_path(base, reference):
    url = urlsplit(reference)
    if url.scheme or url.netloc or not url.path:
        return None
    value = PurePosixPath(base) / unquote(url.path)
    if value.is_absolute() or '..' in value.parts or '\\' in str(value) or any(ord(c) < 32 for c in str(value)):
        raise ValueError('Unsafe local asset path')
    if value.suffix.lower() not in ALLOWED:
        raise ValueError('Unsupported publication file type')
    return value.as_posix()


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attributes):
        for key, value in attributes:
            if key in ('src', 'href') and value:
                name = asset_path('.', value)
                if name:
                    self.paths.add(name)


def prepare(root, output):
    root = root.resolve()
    output = output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Publication output must be outside the source tree')
    subprocess.run(['python3', str(root / 'check_site.py')], check=True, cwd=root)
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    source = (root / 'index.html').read_text()
    parser = References()
    parser.feed(source)
    pending = ['index.html', *sorted(parser.paths)]
    files = {}
    while pending:
        name = pending.pop()
        if name in files:
            continue
        path = root / name
        if path.is_symlink() or root not in path.resolve().parents:
            raise ValueError('Asset outside the repository')
        data = path.read_bytes()
        if path.suffix == '.css':
            for ref in re.findall(r'url\([\'\"]?([^\)\'\"]+)', data.decode()):
                child = asset_path(PurePosixPath(name).parent, ref)
                if child:
                    pending.append(child)
        files[name] = data
    def production_meta(match):
        tag = match.group()
        if re.search(r'\bname\s*=\s*["\']robots["\']', tag, re.I) and 'noindex' in tag.lower():
            return ''
        return tag
    files['index.html'] = re.sub(r'<meta\b[^>]*>', production_meta, source, flags=re.I).encode()
    if re.search(r'<meta[^>]*content=["\'][^"\']*noindex', files['index.html'].decode(), re.I):
        raise ValueError('Unrecognized preview noindex setting')
    files['robots.txt'] = b'User-agent: *\nAllow: /\n'
    manifest = {'commit': sha, 'files': {name: digest(data) for name, data in sorted(files.items())}}
    for name, data in files.items():
        path = output / 'release' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Prepared reviewed commit', sha, 'with', len(files), 'public files.')


def connect():
    password = os.environ.get('BLUEHOST_FTP_PASSWORD')
    if not password:
        raise RuntimeError('BLUEHOST_FTP_PASSWORD is not configured')
    ftp = ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=60)
    try:
        ftp.connect('box5570.bluehost.com', 21)
        ftp.login('wpuser@itadakiboston.com', password)
        ftp.prot_p()
        ftp.cwd('/')
        return ftp
    except Exception:
        ftp.close()
        raise


def get(ftp, name):
    data = io.BytesIO()
    ftp.retrbinary('RETR ' + name, data.write)
    return data.getvalue()


def backup(output):
    manifest = json.loads((output / 'manifest.json').read_text())
    ftp = connect()
    try:
        settings = get(ftp, '.htaccess').decode()
        if not re.search(r'^DirectoryIndex\s+index\.html(?:\s|$)', settings, re.M):
            raise RuntimeError('Server must prefer index.html before automated publication')
        existing = {}
        for name in manifest['files']:
            try:
                data = get(ftp, name)
            except ftplib.error_perm as error:
                if not str(error).startswith('550'):
                    raise
                # Verify this is absence rather than a read-permission failure.
                directory = str(PurePosixPath(name).parent)
                try:
                    listing = ftp.nlst(directory)
                except ftplib.error_perm:
                    raise RuntimeError('Cannot verify publication directory')
                if PurePosixPath(name).name in {PurePosixPath(item).name for item in listing}:
                    raise RuntimeError('Existing public file cannot be backed up')
                existing[name] = None
                continue
            path = output / 'backup' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            existing[name] = digest(data)
        (output / 'backup').mkdir(exist_ok=True)
        (output / 'backup' / 'manifest.json').write_text(json.dumps(existing, indent=2) + '\n')
        print('Backed up existing public files. Legacy PHP and private settings are excluded.')
    finally:
        ftp.close()


def put(ftp, name, data):
    directory = PurePosixPath(name).parent
    if str(directory) != '.':
        partial = ''
        for part in directory.parts:
            partial = partial + '/' + part
            try:
                ftp.mkd(partial)
            except ftplib.error_perm:
                current = ftp.pwd()
                ftp.cwd(partial)
                ftp.cwd(current)
    temporary = name + '.itadaki-pending'
    ftp.storbinary('STOR ' + temporary, io.BytesIO(data))
    if get(ftp, temporary) != data:
        raise RuntimeError('FTPS checksum mismatch')
    ftp.rename(temporary, name)


def verify_public(output, manifest):
    for name in manifest['files']:
        target = '' if name == 'index.html' else quote(name, safe='/')
        url = 'https://itadakiboston.com/' + target + '?release=' + manifest['commit']
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0 Itadaki-Publication',
                                       'Cache-Control': 'no-cache'})
        with urlopen(request, timeout=45) as response:
            if urlsplit(response.url).hostname not in ('itadakiboston.com', 'www.itadakiboston.com'):
                raise RuntimeError('Unexpected public redirect')
            if digest(response.read()) != manifest['files'][name]:
                raise RuntimeError('Public content verification failed')


def deploy(output):
    manifest = json.loads((output / 'manifest.json').read_text())
    before = json.loads((output / 'backup' / 'manifest.json').read_text())
    names = sorted(set(manifest['files']) - {'index.html'}) + ['index.html']
    changed = []
    ftp = connect()
    try:
        # Refuse deployment if the server changed after the backup was captured.
        for name, previous in before.items():
            if previous is not None and digest(get(ftp, name)) != previous:
                raise RuntimeError('Production changed since backup; review again')
        try:
            for name in names:
                data = (output / 'release' / name).read_bytes()
                if digest(data) != manifest['files'][name]:
                    raise RuntimeError('Release files changed after review')
                if before.get(name) == manifest['files'][name]:
                    continue
                changed.append(name)
                put(ftp, name, data)
                print('Published and verified:', name)
            verify_public(output, manifest)
        except Exception:
            # Restore assets first, then the old homepage, preserving consistent references.
            for name in sorted(set(changed) - {'index.html'}) + (['index.html'] if 'index.html' in changed else []):
                if before.get(name) is not None:
                    put(ftp, name, (output / 'backup' / name).read_bytes())
            print('Restored overwritten public files from the verified backup.')
            raise
        print('Publication successful:', manifest['commit'])
    finally:
        ftp.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['prepare', 'backup', 'deploy'])
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.operation == 'prepare':
        prepare(args.root, args.output)
    else:
        {'backup': backup, 'deploy': deploy}[args.operation](args.output)


if __name__ == '__main__':
    main()
