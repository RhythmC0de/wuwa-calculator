#pragma once

#include <memory>
#include <string>

#include <onnxruntime_cxx_api.h>

namespace damage_analyzer {

class OCRRuntime {
public:
    explicit OCRRuntime(const std::string& model_path);

    bool is_ready() const;

private:
    Ort::Env env_;
    Ort::SessionOptions session_options_;
    std::unique_ptr<Ort::Session> session_;
};

} // namespace damage_analyzer