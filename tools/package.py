"""Create a public archive from an allowlist; never package raw rows or caches."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT.parent / 'global-disaster-analysis-public.zip'
patterns = ['README.md', 'README.en.md', 'requirements.txt', 'requirements-tested.txt', '.gitignore',
            'docs/*.md', 'src/*.py', 'tools/*.py', 'tests/*.py',
            'notebooks/*.ipynb', 'reports/*.md', 'reports/*.json',
            'reports/tables/*.csv', 'reports/figures/*.png',
            'reports/figures/*.html', 'data/raw/.gitkeep']
files = sorted({p for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()})
with zipfile.ZipFile(TARGET, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, Path(ROOT.name) / path.relative_to(ROOT))
print(f'Public archive: {TARGET.name} ({len(files)} files)')
