#include "classic_text_detector.hpp"

#include <algorithm>
#include <cmath>

#include <opencv2/imgproc.hpp>

namespace damage_analyzer {

namespace {

// Divide uma caixa alta (duas linhas de texto coladas) pelo perfil horizontal.
std::vector<cv::Rect> split_tall(
    const cv::Mat& edges, const cv::Rect& box, double median_h
) {
    const cv::Mat roi = edges(box);
    std::vector<double> profile(static_cast<std::size_t>(box.height), 0.0);
    double peak = 0.0;
    for (int y = 0; y < box.height; ++y) {
        profile[y] = cv::countNonZero(roi.row(y));
        peak = std::max(peak, profile[y]);
    }
    const double threshold = std::max(1.0, 0.12 * peak);

    std::vector<std::pair<int, int>> parts;
    int start = -1;
    for (int y = 0; y < box.height; ++y) {
        const bool on = profile[y] > threshold;
        if (on && start < 0) {
            start = y;
        } else if (!on && start >= 0) {
            parts.emplace_back(start, y);
            start = -1;
        }
    }
    if (start >= 0) {
        parts.emplace_back(start, box.height);
    }

    // Junta fatias muito próximas (acentos, i/j).
    std::vector<std::pair<int, int>> merged;
    for (const auto& part : parts) {
        if (!merged.empty() &&
            part.first - merged.back().second < 0.18 * median_h) {
            merged.back().second = part.second;
        } else {
            merged.push_back(part);
        }
    }

    std::vector<cv::Rect> result;
    for (const auto& part : merged) {
        if (part.second - part.first >= 0.5 * median_h) {
            result.emplace_back(
                box.x, box.y + part.first, box.width,
                part.second - part.first);
        }
    }
    return result;
}

} // namespace

std::vector<cv::Rect> detect_text_classic(
    const cv::Mat& image_bgr, const ClassicDetectionParams& params
) {
    std::vector<cv::Rect> boxes;
    if (image_bgr.empty() || image_bgr.channels() != 3) {
        return boxes;
    }

    const double scale =
        (image_bgr.cols < 1400 || image_bgr.cols > 2200)
            ? static_cast<double>(params.target_width) / image_bgr.cols
            : 1.0;
    cv::Mat big;
    if (scale != 1.0) {
        cv::resize(image_bgr, big, cv::Size(), scale, scale,
                   scale > 1.0 ? cv::INTER_CUBIC : cv::INTER_AREA);
    } else {
        big = image_bgr;
    }

    cv::Mat gray;
    cv::cvtColor(big, gray, cv::COLOR_BGR2GRAY);
    cv::GaussianBlur(gray, gray, cv::Size(3, 3), 0);

    cv::Mat gradient;
    cv::morphologyEx(
        gray, gradient, cv::MORPH_GRADIENT,
        cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(3, 3)));

    cv::Mat scratch;
    const double otsu =
        cv::threshold(gradient, scratch, 0, 255,
                      cv::THRESH_BINARY | cv::THRESH_OTSU);
    cv::Mat bw;
    cv::threshold(gradient, bw, std::max(8.0, otsu * params.edge_factor),
                  255, cv::THRESH_BINARY);

    // Linhas longas (colchetes, separadores) colam o texto em caixas enormes.
    cv::Mat vertical, horizontal;
    cv::morphologyEx(
        bw, vertical, cv::MORPH_OPEN,
        cv::getStructuringElement(cv::MORPH_RECT, cv::Size(1, 45)));
    cv::morphologyEx(
        bw, horizontal, cv::MORPH_OPEN,
        cv::getStructuringElement(cv::MORPH_RECT, cv::Size(90, 1)));
    cv::Mat long_lines;
    cv::bitwise_or(vertical, horizontal, long_lines);
    cv::dilate(long_lines, long_lines, cv::Mat::ones(3, 3, CV_8U));
    cv::bitwise_and(bw, ~long_lines, bw);

    const cv::Mat raw = bw.clone();
    cv::morphologyEx(
        bw, bw, cv::MORPH_CLOSE,
        cv::getStructuringElement(cv::MORPH_RECT, cv::Size(21, 3)));
    cv::morphologyEx(
        bw, bw, cv::MORPH_OPEN,
        cv::getStructuringElement(cv::MORPH_RECT, cv::Size(9, 5)));

    cv::Mat labels, stats, centroids;
    const int count =
        cv::connectedComponentsWithStats(bw, labels, stats, centroids, 8);

    std::vector<int> heights;
    for (int i = 1; i < count; ++i) {
        const int w = stats.at<int>(i, cv::CC_STAT_WIDTH);
        const int h = stats.at<int>(i, cv::CC_STAT_HEIGHT);
        if (h >= params.min_height && h <= params.max_height &&
            static_cast<double>(w) / std::max(h, 1) >= params.min_aspect) {
            heights.push_back(h);
        }
    }
    std::sort(heights.begin(), heights.end());
    const double median_h =
        heights.empty() ? 24.0 : heights[heights.size() / 2];

    const cv::Rect big_rect(0, 0, big.cols, big.rows);
    for (int i = 1; i < count; ++i) {
        const cv::Rect box(
            stats.at<int>(i, cv::CC_STAT_LEFT),
            stats.at<int>(i, cv::CC_STAT_TOP),
            stats.at<int>(i, cv::CC_STAT_WIDTH),
            stats.at<int>(i, cv::CC_STAT_HEIGHT));
        const int area = stats.at<int>(i, cv::CC_STAT_AREA);
        if (box.width < params.min_width || box.height < params.min_height) {
            continue;
        }

        std::vector<cv::Rect> candidates{box};
        if (box.height > 1.6 * median_h && box.height <= 3.2 * median_h) {
            auto parts = split_tall(raw, box & big_rect, median_h);
            if (!parts.empty()) {
                candidates = std::move(parts);
            }
        }

        for (const cv::Rect& c : candidates) {
            if (c.height < params.min_height || c.height > params.max_height ||
                c.width < params.min_width ||
                static_cast<double>(c.width) / c.height < params.min_aspect) {
                continue;
            }
            if (candidates.size() == 1 &&
                static_cast<double>(area) / std::max(box.area(), 1) <
                    params.min_fill) {
                continue;
            }
            boxes.emplace_back(
                static_cast<int>(c.x / scale), static_cast<int>(c.y / scale),
                static_cast<int>(c.width / scale),
                static_cast<int>(c.height / scale));
        }
    }

    // Ordem de leitura: de cima para baixo; na mesma linha, da esquerda
    // para a direita.
    std::sort(boxes.begin(), boxes.end(),
              [](const cv::Rect& a, const cv::Rect& b) {
                  return a.y + a.height / 2.0 < b.y + b.height / 2.0;
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

} // namespace damage_analyzer
