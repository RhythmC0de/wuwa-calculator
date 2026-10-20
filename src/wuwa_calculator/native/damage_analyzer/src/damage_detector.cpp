#include "damage_detector.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <opencv2/imgproc.hpp>
#include <vector>

namespace damage_analyzer {

namespace {
// cv::contourArea / cv::boundingRect não estão mais em imgproc.hpp no OpenCV 5.
double contour_area(const std::vector<cv::Point>& c) {
    if (c.size() < 3) return 0.0;
    double twice = 0.0;
    for (std::size_t i = 0, j = c.size() - 1; i < c.size(); j = i++)
        twice += double(c[j].x) * c[i].y - double(c[i].x) * c[j].y;
    return std::abs(twice) * 0.5;
}
cv::Rect bounding_rect(const std::vector<cv::Point>& c) {
    if (c.empty()) return {};
    int x0 = c[0].x, x1 = c[0].x, y0 = c[0].y, y1 = c[0].y;
    for (const auto& q : c) {
        x0 = std::min(x0, q.x); x1 = std::max(x1, q.x);
        y0 = std::min(y0, q.y); y1 = std::max(y1, q.y);
    }
    return {x0, y0, x1 - x0 + 1, y1 - y0 + 1};
}
}  // namespace

std::vector<DetectionCandidate> DamageDetector::detect(
    const cv::Mat& candidate_mask
) const {
    std::vector<DetectionCandidate> candidates;

    if (candidate_mask.empty()) {
        return candidates;
    }

    std::vector<std::vector<cv::Point>> contours;

    cv::findContours(
        candidate_mask,
        contours,
        cv::RETR_EXTERNAL,
        cv::CHAIN_APPROX_SIMPLE
    );

    std::vector<DetectionCandidate> components;
    components.reserve(contours.size());

    for (const auto& contour : contours) {
        const double area = contour_area(contour);

        if (area < 12.0) {
            continue;
        }

        const cv::Rect bounds = bounding_rect(contour);

        DetectionCandidate candidate;

        candidate.x = bounds.x;
        candidate.y = bounds.y;
        candidate.width = bounds.width;
        candidate.height = bounds.height;
        components.push_back(candidate);
    }

    if (components.empty()) {
        return candidates;
    }

    /*
     * Build groups using only the original components.
     *
     * A component can connect to another component, but the
     * bounding box produced by the group is never used to create
     * additional connections.
     */
    std::vector<bool> visited(components.size(), false);

    for (std::size_t i = 0; i < components.size(); ++i) {
        if (visited[i]) {
            continue;
        }

        std::vector<std::size_t> group_indices;
        std::vector<std::size_t> pending;

        pending.push_back(i);
        visited[i] = true;

        while (!pending.empty()) {
            const std::size_t current = pending.back();
            pending.pop_back();

            group_indices.push_back(current);

            for (std::size_t j = 0; j < components.size(); ++j) {
                if (visited[j]) {
                    continue;
                }

                if (!should_merge_candidates(
                        components[current],
                        components[j])) {
                    continue;
                }

                visited[j] = true;
                pending.push_back(j);
            }
        }

        /*
         * Build the final bounding box from the original components
         * belonging to this connected group.
         */
        DetectionCandidate group = components[group_indices.front()];

        for (std::size_t k = 1; k < group_indices.size(); ++k) {
            const DetectionCandidate& component =
                components[group_indices[k]];

            const cv::Rect merged_rect =
                merge_candidates(group, component);

            group.x = merged_rect.x;
            group.y = merged_rect.y;
            group.width = merged_rect.width;
            group.height = merged_rect.height;
        }

        candidates.push_back(group);
    }

    return candidates;
}

bool DamageDetector::should_merge_candidates(
    const DetectionCandidate& a,
    const DetectionCandidate& b
) {
    const int a_right = a.x + a.width;
    const int b_right = b.x + b.width;

    const int a_bottom = a.y + a.height;
    const int b_bottom = b.y + b.height;

    const int horizontal_gap = std::max(
        0,
        std::max(
            a.x - b_right,
            b.x - a_right
        )
    );

    const double min_height =
        static_cast<double>(
            std::min(a.height, b.height)
        );

    if (min_height <= 0.0) {
        return false;
    }

    const double vertical_overlap =
        static_cast<double>(
            std::min(a_bottom, b_bottom) -
            std::max(a.y, b.y)
        ) / min_height;

    if (horizontal_gap > min_height * 0.75) {
        return false;
    }

    if (vertical_overlap < 0.30) {
        return false;
    }

    return true;
}

cv::Rect DamageDetector::merge_candidates(
    const DetectionCandidate& a,
    const DetectionCandidate& b
) {
    const cv::Rect rect_a(
        a.x,
        a.y,
        a.width,
        a.height
    );

    const cv::Rect rect_b(
        b.x,
        b.y,
        b.width,
        b.height
    );

    return rect_a | rect_b;
}

} // namespace damage_analyzer