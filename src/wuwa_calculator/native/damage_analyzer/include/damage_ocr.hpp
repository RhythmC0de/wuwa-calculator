#pragma once

#include <string>
#include <vector>
#include <memory>
#include <cstddef>

#include <opencv2/core.hpp>
#include <onnxruntime_cxx_api.h>

namespace damage_analyzer {

struct OCRResult {
    int value = 0;
    double confidence = 0.0;

    int x = 0;
    int y = 0;
    int width = 0;
    int height = 0;
};

class DamageOCR {
public:
    DamageOCR(
        const std::string& model_path,
        const std::string& dicionary_path
    );

    std::vector<OCRResult> recognize(
        const cv::Mat& image
    ) const;

private:
    static bool is_valid_numeric_reading(int value);
    static std::string extract_digits(
        const std::string& text
    );

    std::string decode_ctc(
        const float* data,
        std::size_t timesteps,
        std::size_t classes,
        double& confidence
    ) const;

private:
    Ort::Env env_;
    Ort::SessionOptions session_options_;
    std::unique_ptr<Ort::Session> session_;

    std::vector<std::string> labels_;
};

} // namespace damage_analyzer