"""Collect PE dependencies beside the two CLIs; system/driver DLLs stay on Windows."""
from pathlib import Path
import argparse, hashlib, json, shutil
import pefile

def assemble(cpu, gpu, destination, search_dirs):
    destination=Path(destination);records={}
    sources={p.name.lower():p for folder in reversed(search_dirs) for p in Path(folder).rglob('*.dll')}
    for kind, program in [('cpu',Path(cpu)),('gpu',Path(gpu))]:
        folder=destination/kind;folder.mkdir(parents=True,exist_ok=True)
        queue=[program];seen=set()
        while queue:
            source=queue.pop()
            if source.name.lower() in seen:continue
            seen.add(source.name.lower());target=folder/source.name
            shutil.copy2(source,target)
            records[target.relative_to(destination).as_posix()]={'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
            pe=pefile.PE(str(source),fast_load=False)
            imports=[e.dll.decode('ascii').lower() for e in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[])]
            imports += [e.dll.decode('ascii').lower() for e in getattr(pe,'DIRECTORY_ENTRY_DELAY_IMPORT',[])]
            pe.close()
            for name in imports:
                if name.startswith(('api-ms-','ext-ms-')) or name in {'nvcuda.dll','nvml.dll'}:continue
                if name in sources: queue.append(sources[name])
                elif not (Path('C:/Windows/System32')/name).is_file():raise FileNotFoundError('Missing runtime DLL: '+name)
                elif name.startswith(('msvcp','vcruntime','libomp','concrt','cudart','cufft','hdf5','zlib','fftw')):
                    raise FileNotFoundError('Redistributable must be bundled rather than relying on System32: '+name)
    (destination/'manifest.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cpu',required=True);p.add_argument('--gpu',required=True)
    p.add_argument('--out',required=True);p.add_argument('--dll-dir',action='append',default=[])
    a=p.parse_args();print(json.dumps(assemble(a.cpu,a.gpu,a.out,a.dll_dir),indent=2))
