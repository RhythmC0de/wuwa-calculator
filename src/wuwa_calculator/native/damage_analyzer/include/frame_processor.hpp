#pragma once

#include <opencv2/core.hpp>

namespace damage_analyzer {

struct ProcessedFrame {
    cv::Mat roi;
    cv::Mat hsv;
    cv::Mat candidate_mask;

    int roi_left = 0;
    int roi_top = 0;
    int width = 0;
    int height = 0;

    double timestamp = 0.0;
};

class FrameProcessor {
public:
    ProcessedFrame process(
        const cv::Mat& frame,
        double timestamp
    ) const;
};

} // namespace damage_analyzer