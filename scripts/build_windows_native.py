"""Developer build only. End users download the ready Windows release instead."""
from pathlib import Path
import argparse, os, subprocess, sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hdf5-prefix',required=True,type=Path)
    p.add_argument('--fftw-root',required=True,type=Path)
    p.add_argument('--openmp-lib',required=True,type=Path,help='Redistributable LLVM OpenMP import library, naming libomp.dll')
    p.add_argument('--cuda-root',required=True,type=Path)
    p.add_argument('--cmake',default='cmake');p.add_argument('--jobs',default=4,type=int)
    a=p.parse_args();root=Path(__file__).resolve().parents[1];build=root/'build/windows'
    sys.path.insert(0,str(root/'native/windows'))
    from prepare_sources import prepare
    prepare(root,build/'source')
    def run(args):subprocess.run(list(map(str,args)),check=True)
    common=[a.cmake,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_TRY_COMPILE_CONFIGURATION=Release']
    run(common+['-S',build/'source/cpu','-B',build/'cpu','-DWSVT_WITH_OPENCV=OFF',
        '-DHDF5_INCLUDE_DIR='+str(a.hdf5_prefix/'include'),'-DHDF5_C_LIBRARY_hdf5='+str(a.hdf5_prefix/'lib/hdf5.lib'),
        '-DFFTW3F_LIB='+str(a.fftw_root/'fftw3f.lib'),'-DFFTW3F_INC='+str(a.fftw_root),
        '-DFFTW3F_THREADS_LIB='+str(a.fftw_root/'fftw3f.lib'),'-DOpenMP_libomp_LIBRARY='+a.openmp_lib.as_posix()])
    run([a.cmake,'--build',build/'cpu','--target','wsvt_cli','-j',a.jobs])
    run(common+['-S',build/'source/gpu','-B',build/'gpu','-DCMAKE_CUDA_FLAGS=--use-local-env',
        '-DCMAKE_CUDA_COMPILER='+(a.cuda_root/'bin/nvcc.exe').as_posix()])
    run([a.cmake,'--build',build/'gpu','-j',min(a.jobs,2)])

if __name__=='__main__':main()
