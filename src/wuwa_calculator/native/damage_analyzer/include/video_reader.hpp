#pragma once

#include <string>

#include <opencv2/videoio.hpp>

namespace damage_analyzer {

class VideoReader {
public:
    explicit VideoReader(const std::string& path);

    bool is_open() const;

    double fps() const;
    int frame_count() const;
    double duration() const;
    double position() const;
    
    bool seek(double timestamp);
    bool read(cv::Mat& frame);
    bool grab();
    bool retrieve(cv::Mat& frame);

private:
    cv::VideoCapture capture_;
};

} // namespace damage_analyzer