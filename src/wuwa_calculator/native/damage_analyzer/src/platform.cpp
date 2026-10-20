#include "platform.hpp"

#include <opencv2/imgcodecs.hpp>

#include <cstdlib>
#include <fstream>
#include <iterator>
#include <system_error>

#if defined(_WIN32)
    #ifndef NOMINMAX
        #define NOMINMAX
    #endif
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
#else
    #include <dlfcn.h>
#endif

#ifndef DAMAGE_ANALYZER_SOURCE_MODELS_DIR
    #define DAMAGE_ANALYZER_SOURCE_MODELS_DIR ""
#endif

namespace fs = std::filesystem;

namespace damage_analyzer {

fs::path utf8_path(const std::string& utf8) {
    const std::u8string u8(
        reinterpret_cast<const char8_t*>(utf8.data()),
        utf8.size()
    );

    return fs::path(u8);
}

std::string to_utf8(const fs::path& path) {
    const std::u8string u8 = path.u8string();

    return std::string(u8.begin(), u8.end());
}

fs::path module_directory() {
#if defined(_WIN32)
    HMODULE module = nullptr;

    const BOOL ok = GetModuleHandleExW(
        GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
            GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&module_directory),
        &module
    );

    if (!ok || module == nullptr) {
        return {};
    }

    std::wstring buffer(32768, L'\0');

    const DWORD length = GetModuleFileNameW(
        module,
        buffer.data(),
        static_cast<DWORD>(buffer.size())
    );

    if (length == 0 || length >= buffer.size()) {
        return {};
    }

    buffer.resize(length);

    return fs::path(buffer).parent_path();
#else
    Dl_info info{};

    if (dladdr(reinterpret_cast<void*>(&module_directory), &info) == 0 ||
        info.dli_fname == nullptr) {
        return {};
    }

    std::error_code ec;

    fs::path library = fs::weakly_canonical(info.dli_fname, ec);

    if (ec) {
        library = info.dli_fname;
    }

    return library.parent_path();
#endif
}

fs::path find_models_directory() {
    std::vector<fs::path> candidates;

    if (const char* env = std::getenv("DAMAGE_ANALYZER_MODELS_DIR")) {
        if (*env != '\0') {
            candidates.push_back(utf8_path(env));
        }
    }

    const fs::path here = module_directory();

    if (!here.empty()) {
        candidates.push_back(here / "models" / "ocr");
        candidates.push_back(here.parent_path() / "models" / "ocr");
    }

    if (*DAMAGE_ANALYZER_SOURCE_MODELS_DIR != '\0') {
        candidates.push_back(
            utf8_path(DAMAGE_ANALYZER_SOURCE_MODELS_DIR)
        );
    }

    for (const fs::path& candidate : candidates) {
        std::error_code ec;

        if (fs::is_directory(candidate, ec)) {
            return candidate;
        }
    }

    return {};
}

cv::Mat read_image_utf8(const std::string& utf8_path_string) {
    std::ifstream file(
        utf8_path(utf8_path_string),
        std::ios::binary
    );

    if (!file.is_open()) {
        return {};
    }

    const std::vector<unsigned char> bytes(
        (std::istreambuf_iterator<char>(file)),
        std::istreambuf_iterator<char>()
    );

    if (bytes.empty()) {
        return {};
    }

    return cv::imdecode(bytes, cv::IMREAD_COLOR);
}

} // namespace damage_analyzer
