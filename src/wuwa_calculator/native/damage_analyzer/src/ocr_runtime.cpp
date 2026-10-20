#include "ocr_runtime.hpp"

#include "ort_utils.hpp"

namespace damage_analyzer {

OCRRuntime::OCRRuntime(const std::string& model_path)
    : env_(ORT_LOGGING_LEVEL_WARNING, "WuwaDamageLab")
{
    session_options_.SetIntraOpNumThreads(1);
    session_options_.SetGraphOptimizationLevel(
        GraphOptimizationLevel::ORT_ENABLE_ALL
    );

    session_ = make_ort_session(
        env_,
        session_options_,
        model_path
    );
}

bool OCRRuntime::is_ready() const {
    return session_ != nullptr;
}

} // namespace damage_analyzer