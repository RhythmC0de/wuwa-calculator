#include "text_reader.hpp"

#include "ort_utils.hpp"
#include "platform.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>

#include <opencv2/imgproc.hpp>

#if CV_VERSION_MAJOR >= 5
#include <opencv2/geometry/2d.hpp>
#endif

namespace damage_analyzer {

namespace {

constexpr int DETECTION_MIN_LONG_SIDE = 1280;
constexpr int DETECTION_MAX_LONG_SIDE = 1920;
constexpr int DETECTION_ALIGN = 32;

int round_to_multiple(double value) {
    const int rounded = static_cast<int>(
        std::round(value / DETECTION_ALIGN)) * DETECTION_ALIGN;
    return std::max(DETECTION_ALIGN, rounded);
}

} // namespace

// ============================================================
// Pós-processamento do DBNet
// ============================================================

std::vector<cv::Rect> boxes_from_probability_map(
    const cv::Mat& probability,
    const cv::Size& image_size,
    const DetectionParams& params
) {
    std::vector<cv::Rect> boxes;

    if (probability.empty() || probability.type() != CV_32F ||
        image_size.width <= 0 || image_size.height <= 0) {
        return boxes;
    }

    const double scale_x =
        static_cast<double>(image_size.width) / probability.cols;
    const double scale_y =
        static_cast<double>(image_size.height) / probability.rows;

    cv::Mat binary;
    cv::compare(probability, params.threshold, binary, cv::CMP_GT);

    std::vector<std::vector<cv::Point>> contours;
    cv::findContours(
        binary, contours, cv::RETR_LIST, cv::CHAIN_APPROX_SIMPLE);

    const cv::Rect image_rect(0, 0, image_size.width, image_size.height);

    for (const auto& contour : contours) {
        if (static_cast<int>(boxes.size()) >= params.max_boxes) {
            break;
        }
        if (contour.size() < 4) {
            continue;
        }

        const cv::RotatedRect rotated = cv::minAreaRect(contour);
        const double w = rotated.size.width;
        const double h = rotated.size.height;
        if (std::min(w, h) < params.min_side) {
            continue;
        }

        // Nota média do mapa dentro do contorno.
        const cv::Rect bounds = cv::boundingRect(contour) &
            cv::Rect(0, 0, probability.cols, probability.rows);
        if (bounds.area() <= 0) {
            continue;
        }
        cv::Mat mask = cv::Mat::zeros(bounds.size(), CV_8U);
        std::vector<std::vector<cv::Point>> shifted(1);
        for (const auto& point : contour) {
            shifted[0].push_back(point - bounds.tl());
        }
        cv::drawContours(mask, shifted, 0, cv::Scalar(255), cv::FILLED);
        const double score = cv::mean(probability(bounds), mask)[0];
        if (score < params.box_threshold) {
            continue;
        }

        // "Unclip" do DB: a região prevista é menor que o texto; cresce
        // por d = área * razão / perímetro.
        const double distance =
            (w * h) * params.unclip_ratio / (2.0 * (w + h));
        cv::RotatedRect grown = rotated;
        grown.size = cv::Size2f(
            static_cast<float>(w + 2.0 * distance),
            static_cast<float>(h + 2.0 * distance));
        const cv::Rect2f box = grown.boundingRect2f();

        const int x0 = static_cast<int>(std::floor(box.x * scale_x));
        const int y0 = static_cast<int>(std::floor(box.y * scale_y));
        const int x1 = static_cast<int>(
            std::ceil((box.x + box.width) * scale_x));
        const int y1 = static_cast<int>(
            std::ceil((box.y + box.height) * scale_y));

        const cv::Rect scaled =
            cv::Rect(cv::Point(x0, y0), cv::Point(x1, y1)) & image_rect;
        if (scaled.width < 3 || scaled.height < 3) {
            continue;
        }
        boxes.push_back(scaled);
    }

    // Ordem de leitura: de cima para baixo; na mesma linha, da esquerda
    // para a direita.
    std::sort(boxes.begin(), boxes.end(),
              [](const cv::Rect& a, const cv::Rect& b) {
                  return a.y + a.height / 2 < b.y + b.height / 2;
              });
    for (std::size_t i = 0; i < boxes.size(); ++i) {
        std::size_t j = i + 1;
        while (j < boxes.size() &&
               std::abs((boxes[j].y + boxes[j].height / 2.0) -
                        (boxes[i].y + boxes[i].height / 2.0)) <
                   0.5 * std::min(boxes[i].height, boxes[j].height)) {
            ++j;
        }
        std::sort(boxes.begin() + i, boxes.begin() + j,
                  [](const cv::Rect& a, const cv::Rect& b) {
                      return a.x < b.x;
                  });
        i = j - 1;
    }

    return boxes;
}

// ============================================================
// TextDetector
// ============================================================

TextDetector::TextDetector(const std::string& model_path)
    : env_(ORT_LOGGING_LEVEL_WARNING, "text_detector") {
    session_options_.SetIntraOpNumThreads(2);
    session_options_.SetGraphOptimizationLevel(
        GraphOptimizationLevel::ORT_ENABLE_ALL);
    session_ = make_ort_session(env_, session_options_, model_path);
}

std::vector<cv::Rect> TextDetector::detect(
    const cv::Mat& image_bgr,
    const DetectionParams& params
) const {
    if (image_bgr.empty() || image_bgr.channels() != 3 || !session_) {
        return {};
    }

    // Escala: imagens pequenas sobem (texto de 9 px não é detectado),
    // imagens enormes descem. Os lados viram múltiplos de 32.
    const double long_side = std::max(image_bgr.cols, image_bgr.rows);
    double scale = 1.0;
    if (long_side < DETECTION_MIN_LONG_SIDE) {
        scale = DETECTION_MIN_LONG_SIDE / long_side;
    } else if (long_side > DETECTION_MAX_LONG_SIDE) {
        scale = DETECTION_MAX_LONG_SIDE / long_side;
    }
    const int width = round_to_multiple(image_bgr.cols * scale);
    const int height = round_to_multiple(image_bgr.rows * scale);

    cv::Mat resized;
    cv::resize(image_bgr, resized, cv::Size(width, height), 0.0, 0.0,
               scale > 1.0 ? cv::INTER_CUBIC : cv::INTER_AREA);

    // CHW, RGB, média e desvio do ImageNet.
    constexpr std::array<float, 3> mean = {0.485f, 0.456f, 0.406f};
    constexpr std::array<float, 3> stddev = {0.229f, 0.224f, 0.225f};
    std::vector<float> input(static_cast<std::size_t>(3) * height * width);
    for (int y = 0; y < height; ++y) {
        const cv::Vec3b* row = resized.ptr<cv::Vec3b>(y);
        for (int x = 0; x < width; ++x) {
            for (int c = 0; c < 3; ++c) {
                const float value = row[x][2 - c] / 255.0f;  // BGR -> RGB
                input[(static_cast<std::size_t>(c) * height + y) * width + x] =
                    (value - mean[c]) / stddev[c];
            }
        }
    }

    Ort::AllocatorWithDefaultOptions allocator;
    auto input_name = session_->GetInputNameAllocated(0, allocator);
    auto output_name = session_->GetOutputNameAllocated(0, allocator);

    const std::array<std::int64_t, 4> shape = {1, 3, height, width};
    Ort::MemoryInfo memory_info = Ort::MemoryInfo::CreateCpu(
        OrtArenaAllocator, OrtMemTypeDefault);
    Ort::Value tensor = Ort::Value::CreateTensor<float>(
        memory_info, input.data(), input.size(), shape.data(), shape.size());

    const char* input_names[] = {input_name.get()};
    const char* output_names[] = {output_name.get()};
    auto outputs = session_->Run(
        Ort::RunOptions{nullptr}, input_names, &tensor, 1, output_names, 1);
    if (outputs.empty()) {
        return {};
    }

    const auto out_shape = outputs[0].GetTensorTypeAndShapeInfo().GetShape();
    if (out_shape.size() < 2) {
        throw std::runtime_error("Unexpected detector output rank.");
    }
    const int out_h = static_cast<int>(out_shape[out_shape.size() - 2]);
    const int out_w = static_cast<int>(out_shape[out_shape.size() - 1]);
    if (out_h <= 0 || out_w <= 0) {
        throw std::runtime_error("Unexpected detector output size.");
    }

    cv::Mat probability(out_h, out_w, CV_32F,
        const_cast<float*>(outputs[0].GetTensorData<float>()));
    return boxes_from_probability_map(
        probability.clone(), image_bgr.size(), params);
}

// ============================================================
// Leitura
// ============================================================

cv::Mat enhance_for_ocr(const cv::Mat& image_bgr) {
    if (image_bgr.empty()) {
        return image_bgr;
    }
    cv::Mat gray;
    cv::cvtColor(image_bgr, gray, cv::COLOR_BGR2GRAY);

    cv::Ptr<cv::CLAHE> clahe = cv::createCLAHE(2.0, cv::Size(8, 8));
    cv::Mat contrast;
    clahe->apply(gray, contrast);

    cv::Mat blurred;
    cv::GaussianBlur(contrast, blurred, cv::Size(0, 0), 1.2);
    cv::Mat sharp;
    cv::addWeighted(contrast, 1.5, blurred, -0.5, 0.0, sharp);

    cv::Mat result;
    cv::cvtColor(sharp, result, cv::COLOR_GRAY2BGR);
    return result;
}

std::vector<TextLine> read_text_lines(
    const cv::Mat& image_bgr,
    const DamageOCR& ocr,
    const TextDetector* detector,
    const std::vector<cv::Rect>& boxes,
    const ReadTextOptions& options
) {
    std::vector<TextLine> lines;
    if (image_bgr.empty()) {
        return lines;
    }

    const cv::Mat image =
        options.enhance ? enhance_for_ocr(image_bgr) : image_bgr;

    std::vector<cv::Rect> regions = boxes;
    if (regions.empty()) {
        regions = detector != nullptr ? detector->detect(image)
                                      : detect_text_classic(image);
    }

    const cv::Rect image_rect(0, 0, image.cols, image.rows);
    for (const cv::Rect& box : regions) {
        // O reconhecedor espera texto na horizontal.
        if (box.width <= 0 || box.height <= 0 ||
            box.height > 2 * box.width) {
            continue;
        }

        const int pad_x = static_cast<int>(
            std::round(options.pad_ratio * box.height));
        const int pad_y = static_cast<int>(
            std::round(options.pad_ratio * box.height));
        const cv::Rect padded =
            cv::Rect(box.x - pad_x, box.y - pad_y,
                     box.width + 2 * pad_x, box.height + 2 * pad_y) &
            image_rect;
        if (padded.empty()) {
            continue;
        }

        double confidence = 0.0;
        std::string text = ocr.read_text(image(padded), confidence);

        const auto first = text.find_first_not_of(" \t");
        if (first == std::string::npos) {
            continue;
        }
        text = text.substr(first, text.find_last_not_of(" \t") - first + 1);
        if (confidence < options.min_confidence) {
            continue;
        }

        TextLine line;
        line.text = text;
        line.confidence = confidence;
        line.x = box.x + box.width / 2.0;
        line.y = box.y + box.height / 2.0;
        line.width = box.width;
        line.height = box.height;
        lines.push_back(std::move(line));
    }
    return lines;
}

} // namespace damage_analyzer
