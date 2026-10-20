#pragma once

#include <vector>

#include <opencv2/core.hpp>

namespace damage_analyzer {

struct DetectionCandidate {
    int x = 0;
    int y = 0;
    int width = 0;
    int height = 0;
    double area = 0.0;

    int component_count = 0;
};

class DamageDetector {
public:
    std::vector<DetectionCandidate> detect(
        const cv::Mat& candidate_mask
    ) const;

private:
    static bool should_merge_candidates(
        const DetectionCandidate& a,
        const DetectionCandidate& b
    );

private:
    static cv::Rect merge_candidates(
        const DetectionCandidate& a,
        const DetectionCandidate& b
    );
};

} // namespace damage_analyzer