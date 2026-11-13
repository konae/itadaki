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

    def test_missing_password_does_not_connect(self):
        with patch.dict(publication.os.environ, {}, clear=True), patch.object(publication.ftplib, 'FTP_TLS') as ftp:
            with self.assertRaises(RuntimeError):
                publication.connect()
            ftp.assert_not_called()


if __name__ == '__main__':
    unittest.main()
