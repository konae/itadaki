"""Safety checks for packaging and failure recovery, without network access."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('publication', Path(__file__).with_name('publish_bluehost.py'))
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


class PublicationTests(unittest.TestCase):
    def test_rejects_paths_escaping_public_files(self):
        for value in ['../password.txt', '%2e%2e/secret.png', '/private/photo.jpg', 'index.php']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                publication.asset_path('.', value)

    def test_only_linked_assets_are_packaged(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / 'source'
            root.mkdir()
            (root / 'index.html').write_text('<meta name="robots" content="noindex, nofollow">\n<img src="hero.jpg"><link href="style.css">')
            (root / 'hero.jpg').write_bytes(b'photo')
            (root / 'style.css').write_text('body {background: url(background.png)}')
            (root / 'background.png').write_bytes(b'background')
            (root / 'secret.txt').write_text('must stay private')
            (root / 'owner-editing-guide.md').write_text('not a public site asset')
            with patch.object(publication.subprocess, 'run'), patch.object(publication.subprocess, 'check_output', return_value='a' * 40):
                publication.prepare(root, parent / 'output')
            manifest = json.loads((parent / 'output/manifest.json').read_text())
            self.assertEqual(set(manifest['files']), {'index.html', 'hero.jpg', 'style.css', 'background.png', 'robots.txt'})
            self.assertNotIn('noindex', (parent / 'output/release/index.html').read_text())

    def test_public_verification_failure_restores_old_homepage_and_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / 'release').mkdir()
            (output / 'backup').mkdir()
            names = ['index.html', 'hero.jpg']
            old = {name: ('old ' + name).encode() for name in names}
            new = {name: ('new ' + name).encode() for name in names}
            for name in names:
                (output / 'release' / name).write_bytes(new[name])
                (output / 'backup' / name).write_bytes(old[name])
            (output / 'manifest.json').write_text(json.dumps({'commit': 'a' * 40, 'files': {n: publication.digest(v) for n, v in new.items()}}))
            (output / 'backup/manifest.json').write_text(json.dumps({n: publication.digest(v) for n, v in old.items()}))
            server = dict(old)
            class Connection:
                def close(self):
                    pass
            with patch.object(publication, 'connect', return_value=Connection()), patch.object(publication, 'get', side_effect=lambda f, n: server[n]), patch.object(publication, 'put', side_effect=lambda f, n, d: server.__setitem__(n, d)), patch.object(publication, 'verify_public', side_effect=RuntimeError('simulated public failure')):
                with self.assertRaises(RuntimeError):
                    publication.deploy(output)
            self.assertEqual(server, old)


    def test_multi_page_package_resolves_parent_links_without_private_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / 'source'
            root.mkdir()
            (root / 'index.html').write_text('<meta name="robots" content="noindex, nofollow"><h1 id="home">Home</h1><img src="hero.jpg"><link href="styles.css">')
            (root / 'hero.jpg').write_bytes(b'hero')
            (root / 'styles.css').write_text('body {}')
            (root / 'landing.css').write_text('body { background: url("texture.png"); }')
            (root / 'texture.png').write_bytes(b'texture')
            (root / 'logo.png').write_bytes(b'logo')
            for route in ('catering', 'offers', 'delivery'):
                folder = root / route
                folder.mkdir()
                (folder / 'index.html').write_text(
                    '<meta name="robots" content="noindex,nofollow">'
                    '<link href="../styles.css"><link href="../landing.css">'
                    '<img src="../logo.png"><a href="../index.html#home">Home</a>'
                )
            (root / 'private').mkdir()
            (root / 'private' / 'index.html').write_text('Private draft should not be published')
            (root / 'secret.txt').write_text('Secret should not be published')
            with patch.object(publication.subprocess, 'run'), patch.object(publication.subprocess, 'check_output', return_value='a' * 40):
                publication.prepare(root, parent / 'output')
            output = parent / 'output'
            manifest = json.loads((output / 'manifest.json').read_text())
            expected = {
                'index.html', 'catering/index.html', 'offers/index.html', 'delivery/index.html',
                'styles.css', 'landing.css', 'texture.png', 'hero.jpg', 'logo.png', 'robots.txt'
            }
            self.assertEqual(set(manifest['files']), expected)
            self.assertNotIn('private/index.html', manifest['files'])
            self.assertNotIn('secret.txt', manifest['files'])
            for name in publication.PUBLIC_PAGES:
                self.assertNotIn('noindex', (output / 'release' / name).read_text().lower())

    def test_missing_remote_directory_is_confirmed_safe_to_backup(self):
        class Remote:
            def nlst(self, dirname):
                self.assert_nlst = dirname
                if dirname == '.':
                    return ['index.html', 'legacy.php', '.htaccess']
                raise AssertionError('Unexpected directory listing ' + dirname)
            def close(self):
                pass
        remote = Remote()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / 'manifest.json').write_text(json.dumps({
                'commit': 'a' * 40,
                'files': {'index.html': 'hash', 'catering/index.html': 'hash'}
            }))
            def get_file(ftp, name):
                if name == '.htaccess':
                    return b'DirectoryIndex index.html index.php\n'
                if name == 'index.html':
                    return b'old homepage'
                raise publication.ftplib.error_perm('550 absent')
            with patch.object(publication, 'connect', return_value=remote), patch.object(publication, 'get', side_effect=get_file):
                publication.backup(output)
            previous = json.loads((output / 'backup/manifest.json').read_text())
            self.assertEqual(previous['index.html'], publication.digest(b'old homepage'))
            self.assertIsNone(previous['catering/index.html'])

    def test_failed_publication_removes_new_route_and_restores_homepage(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / 'release' / 'catering').mkdir(parents=True)
            (output / 'backup').mkdir()
            old = {'index.html': b'old homepage'}
            new = {'index.html': b'new homepage', 'catering/index.html': b'new route'}
            (output / 'release/index.html').write_bytes(new['index.html'])
            (output / 'release/catering/index.html').write_bytes(new['catering/index.html'])
            (output / 'backup/index.html').write_bytes(old['index.html'])
            (output / 'manifest.json').write_text(json.dumps({
                'commit': 'b' * 40, 'files': {n: publication.digest(v) for n, v in new.items()}
            }))
            (output / 'backup/manifest.json').write_text(json.dumps({
                'index.html': publication.digest(old['index.html']), 'catering/index.html': None
            }))
            server = dict(old)
            class Remote:
                def delete(self, name):
                    del server[name]
                def close(self):
                    pass
            with patch.object(publication, 'connect', return_value=Remote()), patch.object(publication, 'get', side_effect=lambda ftp, name: server[name]), patch.object(publication, 'put', side_effect=lambda ftp, name, data: server.__setitem__(name, data)), patch.object(publication, 'verify_public', side_effect=RuntimeError('simulated HTTPS failure')):
                with self.assertRaisesRegex(RuntimeError, 'simulated HTTPS failure'):
                    publication.deploy(output)
            self.assertEqual(server, old)

    def test_missing_password_does_not_connect(self):
        with patch.dict(publication.os.environ, {}, clear=True), patch.object(publication.ftplib, 'FTP_TLS') as ftp:
            with self.assertRaises(RuntimeError):
                publication.connect()
            ftp.assert_not_called()


if __name__ == '__main__':
    unittest.main()
