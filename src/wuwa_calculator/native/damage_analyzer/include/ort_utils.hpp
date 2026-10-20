#pragma once

#include <filesystem>
#include <memory>
#include <stdexcept>
#include <string>

#include <onnxruntime_cxx_api.h>

#include "platform.hpp"

namespace damage_analyzer {

// Cria uma sessão ONNX Runtime a partir de um caminho UTF-8.
//
// O ONNX Runtime espera ORTCHAR_T, que é wchar_t no Windows e char no
// Linux. std::filesystem::path::c_str() devolve exatamente o tipo
// nativo de cada plataforma, então o mesmo código funciona nos dois.
inline std::unique_ptr<Ort::Session> make_ort_session(
    Ort::Env& env,
    const Ort::SessionOptions& options,
    const std::string& model_path_utf8
) {
    const std::filesystem::path path = utf8_path(model_path_utf8);

    std::error_code ec;

    if (!std::filesystem::is_regular_file(path, ec)) {
        throw std::runtime_error(
            "OCR model not found: " + model_path_utf8
        );
    }

    return std::make_unique<Ort::Session>(
        env,
        path.c_str(),
        options
    );
}

} // namespace damage_analyzer
