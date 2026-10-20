#include "damage_ocr.hpp"

#include "ort_utils.hpp"
#include "platform.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <limits>
#include <string>
#include <stdexcept>

#include <opencv2/imgproc.hpp>

namespace damage_analyzer {

namespace {

constexpr int OCR_HEIGHT = 48;
constexpr int OCR_MAX_WIDTH = 320;

constexpr std::size_t OCR_DICTIONARY_SIZE = 436;
constexpr std::size_t OCR_CLASS_COUNT = 438;

// Verdadeiro se o texto lido tem dois ou mais grupos de dígitos separados
// por espaço (ex.: "1436 1574"). Isso acontece quando dois números de dano
// ficam lado a lado e a detecção os junta em um só recorte; concatenar os
// grupos daria um valor falso (14361574), então a leitura é descartada.
bool has_multiple_number_groups(const std::string& text) {
    bool seen_group = false;
    bool pending_space = false;
    bool in_digits = false;

    for (const char character : text) {
        const bool is_digit = character >= '0' && character <= '9';

        if (is_digit) {
            if (seen_group && !in_digits && pending_space) {
                return true;
            }

            seen_group = true;
            in_digits = true;
            pending_space = false;
        } else {
            in_digits = false;

            if (character == ' ') {
                pending_space = true;
            }
        }
    }

    return false;
}

}

DamageOCR::DamageOCR(
    const std::string& model_path,
    const std::string& dictionary_path
)
    : env_(
        ORT_LOGGING_LEVEL_WARNING,
        "WuwaDamageLabOCR"
    )
{
    // --------------------------------------------------------
    // Load dictionary
    // --------------------------------------------------------

    std::ifstream dictionary_file(
        utf8_path(dictionary_path)
    );

    if (!dictionary_file.is_open()) {
        throw std::runtime_error(
            "Could not open OCR dictionary: " +
            dictionary_path
        );
    }

    std::vector<std::string> characters;

    std::string line;

    while (std::getline(dictionary_file, line)) {
        // Remove BOM UTF-8 caso o arquivo tenha sido salvo por um
        // editor do Windows.
        if (characters.empty() &&
            line.size() >= 3 &&
            static_cast<unsigned char>(line[0]) == 0xEF &&
            static_cast<unsigned char>(line[1]) == 0xBB &&
            static_cast<unsigned char>(line[2]) == 0xBF) {
            line.erase(0, 3);
        }

        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        characters.push_back(line);
    }

    if (characters.size() != OCR_DICTIONARY_SIZE) {
        throw std::runtime_error(
            "Unexpected OCR dictionary size: " +
            std::to_string(characters.size()) +
            ", expected " +
            std::to_string(OCR_DICTIONARY_SIZE)
        );
    }

    // --------------------------------------------------------
    // CTC label layout
    //
    // class 0      = blank
    // classes 1-436 = dictionary
    // class 437    = space
    // --------------------------------------------------------

    labels_.reserve(OCR_CLASS_COUNT);

    labels_.emplace_back("<blank>");

    for (const auto& character : characters) {
        labels_.push_back(character);
    }

    labels_.emplace_back(" ");

    if (labels_.size() != OCR_CLASS_COUNT) {
        throw std::runtime_error(
            "OCR label count does not match "
            "the model class count."
        );
    }

    // --------------------------------------------------------
    // ONNX Runtime
    // --------------------------------------------------------

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


// ============================================================
// recognize
// ============================================================

std::vector<OCRResult> DamageOCR::recognize(
    const cv::Mat& image
) const {
    std::vector<OCRResult> results;

    if (image.empty()) {
        return results;
    }

    if (!session_) {
        return results;
    }

    // --------------------------------------------------------
    // Preserve aspect ratio
    // --------------------------------------------------------

    const double ratio =
        static_cast<double>(image.cols) /
        static_cast<double>(image.rows);

    int resized_width =
        static_cast<int>(
            std::ceil(
                OCR_HEIGHT * ratio
            )
        );

    resized_width =
        std::clamp(
            resized_width,
            1,
            OCR_MAX_WIDTH
        );

    cv::Mat resized;

    cv::resize(
        image,
        resized,
        cv::Size(
            resized_width,
            OCR_HEIGHT
        ),
        0.0,
        0.0,
        cv::INTER_LINEAR
    );

    // --------------------------------------------------------
    // Create CHW float32 tensor
    //
    // Layout:
    //
    // [1, 3, 48, width]   (width = resized width, at most 320)
    // --------------------------------------------------------

    constexpr int channels = 3;

    // O modelo aceita largura dinâmica. Usar a largura real do recorte
    // (como o PaddleOCR faz com um único texto) evita processar
    // até 320 colunas de preenchimento a cada chamada.
    const int input_width = resized_width;

    const std::size_t input_size =
        static_cast<std::size_t>(
            channels *
            OCR_HEIGHT *
            input_width
        );

    std::vector<float> input_data(
        input_size,
        0.0f
    );

    for (int y = 0;
         y < OCR_HEIGHT;
         ++y) {

        for (int x = 0;
             x < resized_width;
             ++x) {

            const cv::Vec3b pixel =
                resized.at<cv::Vec3b>(
                    y,
                    x
                );

            for (int c = 0;
                 c < channels;
                 ++c) {

                const std::size_t index =
                    static_cast<std::size_t>(
                        c *
                        OCR_HEIGHT *
                        input_width +
                        y *
                        input_width +
                        x
                    );

                const float normalized =
                    static_cast<float>(
                        pixel[c]
                    ) / 255.0f;

                input_data[index] =
                    (normalized - 0.5f) / 0.5f;
            }
        }
    }

    // --------------------------------------------------------
    // Obtain model names
    // --------------------------------------------------------

    Ort::AllocatorWithDefaultOptions allocator;

    auto input_name =
        session_->GetInputNameAllocated(
            0,
            allocator
        );

    auto output_name =
        session_->GetOutputNameAllocated(
            0,
            allocator
        );

    // --------------------------------------------------------
    // Create tensor
    // --------------------------------------------------------

    const std::array<std::int64_t, 4> input_shape = {
        1,
        channels,
        OCR_HEIGHT,
        input_width
    };

    Ort::MemoryInfo memory_info =
        Ort::MemoryInfo::CreateCpu(
            OrtArenaAllocator,
            OrtMemTypeDefault
        );

    Ort::Value input_tensor =
        Ort::Value::CreateTensor<float>(
            memory_info,
            input_data.data(),
            input_data.size(),
            input_shape.data(),
            input_shape.size()
        );

    const char* input_names[] = {
        input_name.get()
    };

    const char* output_names[] = {
        output_name.get()
    };

    // --------------------------------------------------------
    // Inference
    // --------------------------------------------------------

    auto outputs = session_->Run(
        Ort::RunOptions{nullptr},
        input_names,
        &input_tensor,
        1,
        output_names,
        1
    );

    if (outputs.empty()) {
        return results;
    }

    auto& output = outputs[0];

    const auto tensor_info =
        output.GetTensorTypeAndShapeInfo();

    const auto output_shape =
        tensor_info.GetShape();

    if (output_shape.size() != 3) {
        throw std::runtime_error(
            "Unexpected OCR output rank."
        );
    }

    const std::size_t batch =
        static_cast<std::size_t>(
            output_shape[0]
        );

    const std::size_t timesteps =
        static_cast<std::size_t>(
            output_shape[1]
        );

    const std::size_t classes =
        static_cast<std::size_t>(
            output_shape[2]
        );

    if (batch != 1) {
        throw std::runtime_error(
            "Unexpected OCR batch size."
        );
    }

    if (classes != OCR_CLASS_COUNT) {
        throw std::runtime_error(
            "Unexpected OCR class count: " +
            std::to_string(classes)
        );
    }

    const float* output_data =
        output.GetTensorData<float>();

    // --------------------------------------------------------
    // CTC decoding
    // --------------------------------------------------------

    double confidence = 0.0;

    const std::string text =
        decode_ctc(
            output_data,
            timesteps,
            classes,
            confidence
        );

    // --------------------------------------------------------
    // Extract digits
    // --------------------------------------------------------

    const std::string digits =
        extract_digits(text);

    if (digits.empty()) {
        return results;
    }

    if (has_multiple_number_groups(text)) {
        return results;
    }

    // --------------------------------------------------------
    // Convert to integer
    // --------------------------------------------------------

    int value = 0;

    try {
        value = std::stoi(digits);
    }
    catch (const std::exception&) {
        return results;
    }

    if (!is_valid_numeric_reading(value)) {
        return results;
    }

    // --------------------------------------------------------
    // Result
    //
    // Coordinates are intentionally zero here.
    //
    // The detector owns the candidate coordinates.
    // The analyzer will attach them when integrating OCR.
    // --------------------------------------------------------

    OCRResult result;

    result.value = value;
    result.confidence = confidence;

    result.x = 0;
    result.y = 0;
    result.width = image.cols;
    result.height = image.rows;

    results.push_back(result);

    return results;
}


// ============================================================
// CTC decoder
// ============================================================

std::string DamageOCR::decode_ctc(
    const float* data,
    std::size_t timesteps,
    std::size_t classes,
    double& confidence
) const {
    std::string text;

    double confidence_sum = 0.0;
    std::size_t confidence_count = 0;

    std::size_t previous_class =
        std::numeric_limits<std::size_t>::max();

    for (std::size_t t = 0;
         t < timesteps;
         ++t) {

        const float* timestep =
            data +
            t * classes;

        std::size_t best_class = 0;

        float best_probability =
            timestep[0];

        for (std::size_t c = 1;
             c < classes;
             ++c) {

            if (timestep[c] > best_probability) {
                best_probability =
                    timestep[c];

                best_class = c;
            }
        }

        // ----------------------------------------------------
        // CTC duplicate suppression
        // ----------------------------------------------------

        if (best_class == previous_class) {
            continue;
        }

        previous_class = best_class;

        // ----------------------------------------------------
        // Blank
        // ----------------------------------------------------

        if (best_class == 0) {
            continue;
        }

        if (best_class >= labels_.size()) {
            continue;
        }

        text += labels_[best_class];

        confidence_sum +=
            static_cast<double>(
                best_probability
            );

        ++confidence_count;
    }

    if (confidence_count > 0) {
        confidence =
            confidence_sum /
            static_cast<double>(
                confidence_count
            );
    }
    else {
        confidence = 0.0;
    }

    return text;
}


// ============================================================
// Validation
// ============================================================

bool DamageOCR::is_valid_numeric_reading(
    int value
) {
    // Valores pequenos são mantidos de propósito: o analisador
    // precisa vê-los para que o filtro temporal reconheça contagens
    // regressivas da interface. O dano mínimo é aplicado depois.
    return value >= 1 &&
           value <= 99'999'999;
}


// ============================================================
// Digits extraction
// ============================================================

std::string DamageOCR::extract_digits(
    const std::string& text
) {
    std::string digits;

    for (const char character : text) {
        if (
            character >= '0' &&
            character <= '9'
        ) {
            digits += character;
        }
    }

    return digits;
}

}