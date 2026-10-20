// damage_analyzer_cli: executa a análise sem precisar de Python.
//
//   damage_analyzer_cli <video> [--start S] [--end S] [--stride N]
//                       [--model PATH] [--dict PATH] [--no-hud-filter]
//                       [--min-damage N] [--json] [--verbose]

#include <cstdio>
#include <exception>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

#include "analyzer.hpp"

#if defined(_WIN32)
    #ifndef NOMINMAX
        #define NOMINMAX
    #endif
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
#endif

namespace {

void print_usage() {
    std::cerr <<
        "Usage: damage_analyzer_cli <video> [options]\n"
        "  --start S         start time in seconds (default 0)\n"
        "  --end S           end time in seconds (default: end of video)\n"
        "  --stride N        analyze 1 of every N frames (default 1)\n"
        "  --model PATH      OCR model (.onnx)\n"
        "  --dict PATH       OCR dictionary (.txt)\n"
        "  --min-damage N    minimum accepted damage (default 100)\n"
        "  --no-hud-filter   disable the HUD exclusion zones\n"
        "  --json            print the result as JSON\n"
        "  --verbose         print pipeline statistics\n";
}

std::string json_number(double value) {
    char buffer[64];
    std::snprintf(buffer, sizeof(buffer), "%.3f", value);
    return buffer;
}

int run(const std::vector<std::string>& args) {
    if (args.size() < 2) {
        print_usage();
        return 2;
    }

    std::string video;
    double start = 0.0;
    double end = -1.0;
    bool json = false;

    damage_analyzer::AnalyzerConfig config;

    for (std::size_t i = 1; i < args.size(); ++i) {
        const std::string& arg = args[i];

        auto next = [&]() -> const std::string& {
            if (i + 1 >= args.size()) {
                throw std::runtime_error("Missing value for " + arg);
            }
            return args[++i];
        };

        if (arg == "--start") start = std::stod(next());
        else if (arg == "--end") end = std::stod(next());
        else if (arg == "--stride") config.frame_stride = std::stoi(next());
        else if (arg == "--model") config.model_path = next();
        else if (arg == "--dict") config.dictionary_path = next();
        else if (arg == "--min-damage") config.min_damage = std::stoi(next());
        else if (arg == "--no-hud-filter") config.exclusion_zones.clear();
        else if (arg == "--json") json = true;
        else if (arg == "--verbose") config.verbose = true;
        else if (arg == "--help" || arg == "-h") {
            print_usage();
            return 0;
        }
        else if (!arg.empty() && arg[0] == '-') {
            throw std::runtime_error("Unknown option: " + arg);
        }
        else video = arg;
    }

    if (video.empty()) {
        print_usage();
        return 2;
    }

    const damage_analyzer::AnalysisResult result =
        damage_analyzer::analyze_video(video, start, end, config);

    if (json) {
        std::cout << "{\n"
                  << "  \"total_damage\": "
                  << json_number(result.total_damage) << ",\n"
                  << "  \"total_hits\": " << result.total_hits << ",\n"
                  << "  \"peak_damage\": " << result.peak_damage << ",\n"
                  << "  \"average_damage\": "
                  << json_number(result.average_damage) << ",\n"
                  << "  \"events\": [\n";

        for (std::size_t i = 0; i < result.events.size(); ++i) {
            const auto& e = result.events[i];

            std::cout << "    {\"timestamp\": " << json_number(e.timestamp)
                      << ", \"damage\": " << e.damage
                      << ", \"x\": " << e.center_x
                      << ", \"y\": " << e.center_y << "}"
                      << (i + 1 < result.events.size() ? "," : "")
                      << "\n";
        }

        std::cout << "  ]\n}\n";
        return 0;
    }

    std::cout << "time(s)   damage\n";

    for (const auto& e : result.events) {
        std::printf("%8.2f  %d\n", e.timestamp, e.damage);
    }

    std::printf(
        "\nhits=%d total=%.0f average=%.1f peak=%d\n",
        result.total_hits,
        result.total_damage,
        result.average_damage,
        result.peak_damage
    );

    return 0;
}

} // namespace

#if defined(_WIN32)

// No Windows, argv em "char" usa a code page ANSI e corrompe caminhos
// com acentos. wmain recebe UTF-16, convertido aqui para UTF-8.
int wmain(int argc, wchar_t** wargv) {
    std::vector<std::string> args;

    for (int i = 0; i < argc; ++i) {
        const int size = WideCharToMultiByte(
            CP_UTF8, 0, wargv[i], -1, nullptr, 0, nullptr, nullptr);

        std::string utf8(size > 0 ? size - 1 : 0, '\0');

        if (size > 1) {
            WideCharToMultiByte(
                CP_UTF8, 0, wargv[i], -1,
                utf8.data(), size, nullptr, nullptr);
        }

        args.push_back(std::move(utf8));
    }

    try {
        return run(args);
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
}

#else

int main(int argc, char** argv) {
    std::vector<std::string> args(argv, argv + argc);

    try {
        return run(args);
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
}

#endif
