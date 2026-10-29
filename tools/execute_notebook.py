"""Execute without installing a user kernel or retaining local identity metadata."""
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'notebooks/disaster_analysis.ipynb'
nb = nbformat.read(path, as_version=4)
km = KernelManager(kernel_name='python3')
# Use the invoking interpreter rather than a machine-specific registered kernel.
km.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
client = NotebookClient(nb, km=km, timeout=180, resources={'metadata': {'path': str(ROOT)}})
try:
    client.execute()
finally:
    if km.has_kernel:
        km.shutdown_kernel(now=True)
for cell in nb.cells:
    cell.metadata = {}
nb.metadata = {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
               'language_info': {'name': 'python', 'version': '.'.join(map(str, sys.version_info[:3]))}}
nbformat.validate(nb)
nbformat.write(nb, path)
print('Notebook executed and validated; local execution metadata removed.')
