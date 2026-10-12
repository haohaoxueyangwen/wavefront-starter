"""Check local document navigation and release entry points without network I/O."""
from pathlib import Path
import json
import re
import sys
import urllib.parse


ROOT = Path(__file__).resolve().parents[1]


def slug(text):
    text = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', text)
    return re.sub(r'[^\w\-\s]', '', text.casefold()).strip().replace(' ', '-')


def main():
    documents = [ROOT / 'README.md', ROOT / 'CHANGELOG.md', ROOT / 'CONTRIBUTING.md']
    for folder in ('docs', 'examples', 'literature'):
        documents.extend(sorted((ROOT / folder).rglob('*.md')))
    documents.extend([ROOT / 'provenance/NOTICE.md', ROOT / 'provenance/windows-licenses/README.md'])
    errors, links = [], []
    for source in documents:
        content = source.read_text(encoding='utf-8')
        for match in re.finditer(r'\]\(([^)]+)\)', content):
            target = match.group(1).strip().strip('<>')
            if urllib.parse.urlsplit(target).scheme:
                continue
            file, _, anchor = target.partition('#')
            path = (source.parent / urllib.parse.unquote(file)).resolve() if file else source
            item = {'source': str(source.relative_to(ROOT)).replace('\\', '/'), 'target': target}
            links.append(item)
            if not path.exists():
                errors.append(item | {'error': 'missing target'})
            elif anchor and path.suffix == '.md':
                headings = [slug(m.group(1)) for m in re.finditer(r'^#{1,6}\s+(.+)$', path.read_text(encoding='utf-8'), re.M)]
                if urllib.parse.unquote(anchor) not in headings:
                    errors.append(item | {'error': 'missing heading'})
    version = re.search(r'^version = "([^"]+)"', (ROOT / 'pyproject.toml').read_text(), re.M).group(1)
    for name in ('README.md', '先看这里.txt', 'docs/12_windows_quickstart.md', 'docs/14_crl_example.md',
                 'launch_frontend.py', 'src/wfs_starter/ui.py'):
        if version not in (ROOT / name).read_text(encoding='utf-8'):
            errors.append({'source': name, 'error': 'current version absent'})
    templates = sorted((ROOT / 'src/wfs_starter/configs').glob('*.json'))
    if len(templates) != 8:
        errors.append({'error': 'expected eight configuration templates'})
    for path in templates:
        if json.loads(path.read_text(encoding='utf-8'))['mode'] != path.stem:
            errors.append({'source': str(path.relative_to(ROOT)), 'error': 'mode/template mismatch'})
    index = (ROOT / 'docs/README.md').read_text(encoding='utf-8')
    for path in (ROOT / 'docs').glob('[0-9][0-9]_*.md'):
        if path.name not in index:
            errors.append({'source': 'docs/README.md', 'error': 'unindexed guide: ' + path.name})
    references = json.loads((ROOT / 'literature/references.json').read_text(encoding='utf-8'))
    if len(references) != 34 or len({x['doi'] for x in references}) != 34:
        errors.append({'error': 'reference count or DOI uniqueness differs'})
    for name in ('start_speckle.cmd', 'start_grating.cmd', 'start_hartmann.cmd', 'start_wavefront.cmd',
                 'stop_frontends.cmd', 'check_windows.cmd', '先看这里.txt'):
        if not (ROOT / name).is_file():
            errors.append({'error': 'missing entry point: ' + name})
    result = {'version': version, 'documents': len(documents), 'local_links_checked': len(links),
              'templates': len(templates), 'references': len(references), 'errors': errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
