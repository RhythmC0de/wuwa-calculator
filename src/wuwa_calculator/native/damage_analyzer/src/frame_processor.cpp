#include "frame_processor.hpp"

#include <opencv2/imgproc.hpp>

namespace damage_analyzer {

ProcessedFrame FrameProcessor::process(
    const cv::Mat& frame,
    double timestamp
) const {
    ProcessedFrame result;

    if (frame.empty()) {
        return result;
    }
    /*
    const int height = frame.rows;
    const int width = frame.cols;

    const int roi_top = static_cast<int>(height * 0.16);
    const int roi_bottom = static_cast<int>(height * 0.62);
    const int roi_left = static_cast<int>(width * 0.24);
    const int roi_right = static_cast<int>(width * 0.76);

    result.roi_left = roi_left;
    result.roi_top = roi_top;
    */
    result.roi = frame;

    result.width = result.roi.cols;
    result.height = result.roi.rows;
    result.timestamp = timestamp;

    cv::cvtColor(
        result.roi,
        result.hsv,
        cv::COLOR_BGR2HSV
    );

    cv::Mat bright_mask;
    cv::Mat warm_mask;

    cv::inRange(
        result.hsv,
        cv::Scalar(0, 0, 175),
        cv::Scalar(180, 145, 255),
        bright_mask
    );

    cv::inRange(
        result.hsv,
        cv::Scalar(5, 55, 120),
        cv::Scalar(45, 255, 255),
        warm_mask
    );

    cv::bitwise_or(
        bright_mask,
        warm_mask,
        result.candidate_mask
    );

    const cv::Mat kernel = cv::getStructuringElement(
        cv::MORPH_RECT,
        cv::Size(2, 2)
    );

    cv::morphologyEx(
        result.candidate_mask,
        result.candidate_mask,
        cv::MORPH_OPEN,
        kernel
    );

    return result;
}

} // namespace damage_analyzer