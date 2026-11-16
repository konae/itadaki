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

# Explicitly approved website routes. Do not package unreviewed HTML by directory glob.
PUBLIC_PAGES = ('index.html', 'catering/index.html', 'offers/index.html', 'delivery/index.html')
DIRECTORY_INDEX = re.compile(rb'(?m)^([ \t]*DirectoryIndex[ \t]+)([^\r\n]+)')
INSTAGRAM_TARGET = re.compile(rb'https?://(?:www\.)?instagram\.com/cafeitadaki\.boston/?', re.I)


def planned_directory_settings(before, legacy_php=None):
    """Plan an index.html-first switch, but only from a verified known site mode."""
    matches = list(DIRECTORY_INDEX.finditer(before))
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one DirectoryIndex declaration')
    match = matches[0]
    indexes = match.group(2).decode('ascii').split()
    if not indexes:
        raise RuntimeError('Empty DirectoryIndex')
    if indexes[0] == 'index.html':
        return before
    if indexes[0] != 'index.php' or 'index.html' not in indexes:
        raise RuntimeError('Unsupported server DirectoryIndex configuration')
    source = (legacy_php or b'').decode('utf-8', errors='replace')
    if '<?php' not in source or not re.search(r'header\s*\(.*?Location\s*:', source, re.I | re.S):
        raise RuntimeError('Legacy index.php redirect was not verified')
    if not INSTAGRAM_TARGET.search(legacy_php or b''):
        raise RuntimeError('Legacy index.php is not the approved Instagram redirect')
    reordered = ['index.html'] + [name for name in indexes if name != 'index.html']
    return before[:match.start(2)] + ' '.join(reordered).encode('ascii') + before[match.end(2):]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def asset_path(base, reference):
    url = urlsplit(reference)
    if url.scheme or url.netloc or not url.path:
        return None
    relative = unquote(url.path)
    if relative.startswith('/') or '\\' in relative or any(ord(c) < 32 for c in relative):
        raise ValueError('Unsafe local asset path')
    # Allow ../ only when resolving a link inside an approved subdirectory.
    path_parts = [] if PurePosixPath(base).as_posix() == '.' else list(PurePosixPath(base).parts)
    for part in PurePosixPath(relative).parts:
        if part == '..':
            if not path_parts:
                raise ValueError('Unsafe local asset path')
            path_parts.pop()
        elif part != '.':
            path_parts.append(part)
    if not path_parts:
        raise ValueError('Unsafe empty asset path')
    value = PurePosixPath(*path_parts)
    if value.suffix.lower() not in ALLOWED:
        raise ValueError('Unsupported publication file type')
    return value.as_posix()


class References(HTMLParser):
    def __init__(self, base='.'):
        super().__init__()
        self.paths = set()
        self.base = base

    def handle_starttag(self, tag, attributes):
        for key, value in attributes:
            if key in ('src', 'href') and value:
                name = asset_path(self.base, value)
                if name:
                    self.paths.add(name)


def prepare(root, output):
    root = root.resolve()
    output = output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Publication output must be outside the source tree')
    subprocess.run(['python3', str(root / 'check_site.py')], check=True, cwd=root)
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    pages = [name for name in PUBLIC_PAGES if (root / name).is_file()]
    if 'index.html' not in pages:
        raise ValueError('Missing homepage')
    pending = list(pages)
    files = {}
    while pending:
        name = pending.pop()
        if name in files:
            continue
        path = root / name
        if path.is_symlink() or root not in path.resolve().parents:
            raise ValueError('Asset outside the repository')
        data = path.read_bytes()
        if path.suffix == '.html':
            parser = References(PurePosixPath(name).parent)
            parser.feed(data.decode('utf-8'))
            pending.extend(sorted(parser.paths))
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
    for page in pages:
        source = files[page].decode('utf-8')
        files[page] = re.sub(r'<meta\b[^>]*>', production_meta, source, flags=re.I).encode('utf-8')
        if re.search(r'<meta[^>]*content=["\'][^"\']*noindex', files[page].decode(), re.I):
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


def confirmed_absent(ftp, name):
    """Confirm a 550 means a new file or directory, never an unreadable existing file."""
    current = '.'
    parts = PurePosixPath(name).parts
    for part in parts[:-1]:
        listing = {PurePosixPath(item).name for item in ftp.nlst(current)}
        if part not in listing:
            return True
        current = part if current == '.' else current + '/' + part
    listing = {PurePosixPath(item).name for item in ftp.nlst(current)}
    return parts[-1] not in listing


def backup(output):
    manifest = json.loads((output / 'manifest.json').read_text())
    ftp = connect()
    try:
        settings = get(ftp, '.htaccess')
        declarations = list(DIRECTORY_INDEX.finditer(settings))
        if len(declarations) != 1:
            raise RuntimeError('Unexpected server DirectoryIndex configuration')
        indexes = declarations[0].group(2).split()
        legacy_php = get(ftp, 'index.php') if indexes and indexes[0] == b'index.php' else None
        desired_settings = planned_directory_settings(settings, legacy_php)
        existing = {}
        for name in manifest['files']:
            try:
                data = get(ftp, name)
            except ftplib.error_perm as error:
                if not str(error).startswith('550'):
                    raise
                # Verify absence of a new file or its directory. A listing error stops publication.
                if not confirmed_absent(ftp, name):
                    raise RuntimeError('Existing public file cannot be backed up')
                existing[name] = None
                continue
            path = output / 'backup' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            existing[name] = digest(data)
        (output / 'backup').mkdir(exist_ok=True)
        (output / 'backup' / 'manifest.json').write_text(json.dumps(existing, indent=2) + '\n')
        (output / 'backup' / 'htaccess-before.backup').write_bytes(settings)
        (output / 'planned-htaccess').write_bytes(desired_settings)
        print('Backed up public files and server index setting before publication; legacy PHP was not modified.')
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
    # Check user-facing clean URL routes as well as individual uploaded index.html files.
    for name in PUBLIC_PAGES[1:]:
        if name not in manifest['files']:
            continue
        directory = PurePosixPath(name).parent.as_posix()
        url = 'https://itadakiboston.com/' + directory + '/?release=' + manifest['commit']
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0 Itadaki-Publication',
                                       'Cache-Control': 'no-cache'})
        with urlopen(request, timeout=45) as response:
            if urlsplit(response.url).hostname not in ('itadakiboston.com', 'www.itadakiboston.com'):
                raise RuntimeError('Unexpected public route redirect: ' + directory)
            if digest(response.read()) != manifest['files'][name]:
                raise RuntimeError('Public clean URL mismatch: ' + directory)


def deploy(output):
    manifest = json.loads((output / 'manifest.json').read_text())
    before = json.loads((output / 'backup' / 'manifest.json').read_text())
    before_settings = (output / 'backup' / 'htaccess-before.backup').read_bytes()
    desired_settings = (output / 'planned-htaccess').read_bytes()
    names = sorted(set(manifest['files']) - {'index.html'}) + ['index.html']
    changed = []
    settings_changed = False
    ftp = connect()
    try:
        # Refuse deployment if the server changed after the backup was captured.
        if get(ftp, '.htaccess') != before_settings:
            raise RuntimeError('Server index settings changed after backup')
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
            # The previous Instagram redirect stays active until all files are transferred.
            if desired_settings != before_settings:
                settings_changed = True
                put(ftp, '.htaccess', desired_settings)
                if get(ftp, '.htaccess') != desired_settings:
                    raise RuntimeError('Server index switch was not verified')
                print('Switched homepage from the verified legacy redirect to index.html.')
            verify_public(output, manifest)
        except Exception as publish_error:
            # Restore the former redirect first, then original assets and homepage.
            recovery_errors = []
            if settings_changed:
                try:
                    put(ftp, '.htaccess', before_settings)
                    if get(ftp, '.htaccess') != before_settings:
                        raise RuntimeError('Server index rollback did not verify')
                except Exception as error:
                    recovery_errors.append(f'.htaccess: {error}')
            for name in sorted(set(changed) - {'index.html'}) + (['index.html'] if 'index.html' in changed else []):
                try:
                    if before.get(name) is None:
                        try:
                            ftp.delete(name)
                        except ftplib.error_perm as error:
                            if not str(error).startswith('550'):
                                raise
                    else:
                        put(ftp, name, (output / 'backup' / name).read_bytes())
                except Exception as error:
                    recovery_errors.append(f'{name}: {error}')
            if recovery_errors:
                raise RuntimeError('Publication failed; recovery incomplete: ' + '; '.join(recovery_errors)) from publish_error
            print('Restored prior server settings and public files; removed newly published files.')
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
