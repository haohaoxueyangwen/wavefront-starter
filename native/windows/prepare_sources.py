"""Apply explicit Windows portability changes to build copies, preserving frozen sources."""
from pathlib import Path
import hashlib, json, shutil

def prepare(root, destination):
    root, destination = Path(root), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    copies = {'cpu': root/'native/speckle/cpu_cpp/source', 'gpu': root/'native/speckle/gpu_common'}
    receipt = []
    for name, source in copies.items():
        shutil.copytree(source, destination/name, dirs_exist_ok=True)
    def edit(relative, replacements):
        path = destination/relative
        before = path.read_bytes()
        value = before.decode('utf-8')
        for old, new in replacements:
            if old not in value: raise ValueError('Patch anchor missing: '+relative+' '+old)
            value = value.replace(old, new)
        path.write_bytes(value.encode('utf-8'))
        receipt.append({'file':relative,'original_sha256':hashlib.sha256(before).hexdigest(),
                        'windows_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    edit('cpu/include/wsvt/aligned_alloc.hpp', [
        ('namespace wsvt {', '''#ifdef _MSC_VER
#include <malloc.h>
#endif
namespace wsvt {
inline void* platform_aligned_alloc(std::size_t alignment, std::size_t bytes) {
#ifdef _MSC_VER
    return _aligned_malloc(bytes, alignment);
#else
    return std::aligned_alloc(alignment, bytes);
#endif
}
inline void platform_aligned_free(void* p) noexcept {
#ifdef _MSC_VER
    _aligned_free(p);
#else
    std::free(p);
#endif
}'''),
        ('std::aligned_alloc(Alignment, bytes)', 'platform_aligned_alloc(Alignment, bytes)'),
        ('std::free(p);\n    }', 'platform_aligned_free(p);\n    }'),
        ('std::free(data_)', 'platform_aligned_free(data_)')])
    edit('cpu/src/io_h5.cpp', [('ssize_t name_len', 'auto name_len')])
    edit('cpu/CMakeLists.txt', [('find_package(OpenMP REQUIRED)', 'set(OpenMP_CXX_FLAGS "/openmp:experimental /openmp:llvm")\nset(OpenMP_CXX_LIB_NAMES "libomp")\nfind_package(OpenMP REQUIRED)')])
    edit('cpu/src/main.cpp', [('int main(int argc, char** argv) {', '''int main(int argc, char** argv) {
    if (argc==2 && std::string(argv[1])=="--probe") {
        std::cout << "{\\\"backend\\\":\\\"cpp\\\",\\\"hdf5\\\":true,\\\"fftw\\\":true,\\\"openmp\\\":true}" << std::endl;
        return 0;
    }''')])
    for path in (destination/'cpu').rglob('*'):
        if path.suffix not in {'.hpp','.cpp'}: continue
        if '__restrict__' in path.read_text(encoding='utf-8'):
            edit(path.relative_to(destination).as_posix(), [('__restrict__','__restrict')])
    edit('gpu/src/main.cpp', [
        ('#include "speckle_native.h"', '#include "speckle_native.h"\n#include <cuda_runtime.h>\n#include <cufft.h>'),
        ('int main(int argc,char** argv){', '''int main(int argc,char** argv){
    if(argc==2 && std::string(argv[1])=="--probe") {
        int count=0;auto status=cudaGetDeviceCount(&count);
        if(status!=cudaSuccess){std::cerr<<cudaGetErrorString(status);return 2;}
        std::cout<<"{\\\"devices\\\":[";
        for(int i=0;i<count;++i){cudaDeviceProp p{};cudaGetDeviceProperties(&p,i);cudaSetDevice(i);
            cufftHandle plan{};auto fft=cufftPlan2d(&plan,8,8,CUFFT_C2C);if(fft==CUFFT_SUCCESS)cufftDestroy(plan);
            int sm=p.major*10+p.minor;bool supported=sm>=60&&fft==CUFFT_SUCCESS;
            if(i)std::cout<<",";
            std::cout<<"{\\\"index\\\":"<<i<<",\\\"name\\\":\\\""<<p.name<<"\\\",\\\"sm\\\":"<<sm<<",\\\"memory_bytes\\\":"<<p.totalGlobalMem<<",\\\"available\\\":"<<(supported?"true":"false")<<",\\\"cufft_status\\\":"<<int(fft)<<"}";
        }
        std::cout<<"]}"<<std::endl;return 0;
    }'''),
        ('#include <sys/resource.h>', '''#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#else
#include <sys/resource.h>
#endif
static uint64_t peak_rss_bytes() {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS m{};
    if(!GetProcessMemoryInfo(GetCurrentProcess(), &m, sizeof(m))) return 0;
    return uint64_t(m.PeakWorkingSetSize);
#else
    struct rusage m{};getrusage(RUSAGE_SELF,&m);return uint64_t(m.ru_maxrss)*1024;
#endif
}'''),
        ('struct rusage usage{};getrusage(RUSAGE_SELF,&usage);', ''),
        ('uint64_t(usage.ru_maxrss)*1024', 'peak_rss_bytes()')])
    (destination/'gpu/CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.21)
project(speckle_windows LANGUAGES CXX CUDA)
find_package(CUDAToolkit REQUIRED)
add_library(speckle_native SHARED native/edge_kernels.cu src/session.cu)
target_include_directories(speckle_native PUBLIC include)
target_compile_options(speckle_native PRIVATE "$<$<COMPILE_LANGUAGE:CUDA>:-O3;--std=c++17;--fmad=false>")
target_link_libraries(speckle_native PRIVATE CUDA::cufft CUDA::cudart)
set_target_properties(speckle_native PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON CUDA_ARCHITECTURES "60-real;61-real;70-real;75-real;80-real;86-real;86-virtual" CUDA_STANDARD 17 CUDA_STANDARD_REQUIRED ON)
add_executable(speckle_gpu src/main.cpp)
target_compile_features(speckle_gpu PRIVATE cxx_std_17)
target_compile_options(speckle_gpu PRIVATE /O2 /utf-8)
target_compile_definitions(speckle_gpu PRIVATE SPECKLE_PLATFORM="desktop")
target_link_libraries(speckle_gpu PRIVATE speckle_native CUDA::cudart CUDA::cufft psapi)
''', encoding='utf-8')
    receipt.append({'file':'gpu/CMakeLists.txt','reason':'Windows MSVC flags, DLL exports, CUDA SM60/61/70/75/80/86 plus compute86 PTX, PSAPI memory receipt'})
    (destination/'portability.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return destination

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    args=p.parse_args();prepare(Path(__file__).resolve().parents[2],args.destination)
