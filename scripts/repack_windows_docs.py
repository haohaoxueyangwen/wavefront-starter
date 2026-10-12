"""Repack a docs-only release; do not rebuild or substitute native binaries.

Downloads the immutable v0.6.1 Windows archive, checks its full SHA256, adds
reviewed source from the selected Git tag, verifies preserved algorithm bytes,
and keeps runtime/example-data bytes unchanged. Upload/publication is separate.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import urllib.request
import zipfile

BASE = 'https://github.com/haohaoxueyangwen/wavefront-starter/releases/download/v0.6.1/'
BASE_SHA = 'def5c3ee6abed78e625af68dc8e80a66f245694e63d61417c25b64eaf174a5eb'
DATA_SHA = '1eab44c5f689a2a25230746ff1d38ab180b01d987fffb981b56444ea3fa5f62f'
DATA_NAME = 'crl-bb11-20231102-roi512-v1.zip'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(8 * 1024 * 1024):
            result.update(block)
    return result.hexdigest()


def download(name, path, expected):
    with urllib.request.urlopen(BASE + name, timeout=120) as response, path.open('wb') as stream:
        while block := response.read(8 * 1024 * 1024):
            stream.write(block)
    if digest(path) != expected:
        raise ValueError('Baseline archive SHA256 mismatch: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if args.tag != 'v0.6.2':
        raise ValueError('This audited repack supports only the reviewed v0.6.2 tag.')
    root = Path(__file__).resolve().parents[1]
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    version = args.tag[1:]
    prefix = 'wavefront-starter-' + version + '/'
    source = out / ('wavefront-starter-' + version + '-source.zip')
    windows = out / ('wavefront-starter-' + version + '-windows-x64.zip')
    commit = subprocess.check_output(['git', 'rev-parse', args.tag], cwd=root).decode().strip()
    subprocess.run(['git', 'archive', '--format=zip', '--prefix=' + prefix,
                    '-o', str(source), args.tag], cwd=root, check=True)
    baseline = out.parent / 'baseline-windows-061.zip'
    download('wavefront-starter-0.6.1-windows-x64.zip', baseline, BASE_SHA)
    download(DATA_NAME, out / DATA_NAME, DATA_SHA)
    runtime_count = 0
    with zipfile.ZipFile(baseline) as old, zipfile.ZipFile(source) as src:
        if old.testzip() is not None or src.testzip() is not None:
            raise ValueError('Invalid baseline/source ZIP.')
        old_prefix = 'wavefront-starter-0.6.1/'
        # All executable source remains identical except the service version.
        for item in src.infolist():
            relative = item.filename[len(prefix):]
            if relative.startswith(('src/', 'native/')) and not item.is_dir():
                actual = src.read(item.filename)
                if relative == 'src/wfs_starter/ui.py':
                    actual = actual.replace(b'0.6.2', b'0.6.1')
                if actual != old.read(old_prefix + relative):
                    raise ValueError('Non-documentation algorithm change: ' + relative)
        with zipfile.ZipFile(windows, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as dst:
            for item in src.infolist():
                dst.writestr(item.filename, src.read(item.filename))
            for item in old.infolist():
                relative = item.filename[len(old_prefix):]
                if relative.startswith(('runtime/', 'example-data/')) and not item.is_dir():
                    dst.writestr(prefix + relative, old.read(item.filename))
                    runtime_count += relative.startswith('runtime/')
    with zipfile.ZipFile(windows) as z:
        if z.testzip() is not None:
            raise ValueError('Invalid output ZIP.')
        frozen = json.loads(z.read(prefix + 'provenance/native_speckle_050.json'))['files']
        for item in frozen:
            if hashlib.sha256(z.read(prefix + item['path'])).hexdigest() != item['sha256']:
                raise ValueError('Frozen algorithm source hash changed.')
        data = json.loads(z.read(prefix + 'example-data/crl-bb11-v1/manifest.json'))
        if len(data['files']) != 200:
            raise ValueError('CRL data pair count changed.')
        for item in data['files']:
            if hashlib.sha256(z.read(prefix + 'example-data/crl-bb11-v1/' + item['file'])).hexdigest() != item['sha256']:
                raise ValueError('CRL crop hash changed.')
        if any('/local-runs/' in x or '/.local_runtime.json' in x or '/work/' in x for x in z.namelist()):
            raise ValueError('Host data unexpectedly packaged.')
    assets = [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)}
              for p in (windows, source, out / DATA_NAME)]
    (out / 'SHA256SUMS.txt').write_text(''.join(x['sha256'] + '  ' + x['name'] + '\n' for x in assets), encoding='utf-8')
    receipt = {'commit': commit, 'version': version, 'assets': assets,
               'baseline_windows_sha256': BASE_SHA, 'runtime_files': runtime_count,
               'frozen_sources_verified': len(frozen), 'crl_files_verified': 200,
               'zip_integrity': 'passed', 'method': 'Reuse immutable hash-verified release runtime and data.'}
    (out / 'release_receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
