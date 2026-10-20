#include "video_reader.hpp"

#include <algorithm>
#include <stdexcept>

namespace damage_analyzer {

VideoReader::VideoReader(const std::string& path)
{
    // FFmpeg primeiro (presente nas builds oficiais do OpenCV para
    // Windows e Linux); se não estiver disponível, deixa o OpenCV
    // escolher outro backend (MSMF no Windows, GStreamer no Linux...).
    capture_.open(path, cv::CAP_FFMPEG);

    if (!capture_.isOpened()) {
        capture_.open(path, cv::CAP_ANY);
    }

    if (!capture_.isOpened()) {
        throw std::runtime_error(
            "Could not open video: " + path
        );
    }
}

bool VideoReader::is_open() const {
    return capture_.isOpened();
}

double VideoReader::fps() const {
    return capture_.get(cv::CAP_PROP_FPS);
}

int VideoReader::frame_count() const {
    return static_cast<int>(
        capture_.get(cv::CAP_PROP_FRAME_COUNT)
    );
}

double VideoReader::duration() const {
    const double video_fps = fps();

    if (video_fps <= 0.0) {
        return 0.0;
    }

    return static_cast<double>(frame_count()) / video_fps;
}

double VideoReader::position() const {
    const double msec = capture_.get(cv::CAP_PROP_POS_MSEC);

    if (msec > 0.0) {
        return msec / 1000.0;
    }

    // Alguns backends não informam POS_MSEC; usa o índice do frame.
    const double video_fps = fps();

    if (video_fps > 0.0) {
        const double index =
            capture_.get(cv::CAP_PROP_POS_FRAMES) - 1.0;

        return std::max(0.0, index) / video_fps;
    }

    return 0.0;
}

bool VideoReader::seek(double timestamp) {
    if (timestamp <= 0.0) {
        return true;
    }

    return capture_.set(
        cv::CAP_PROP_POS_MSEC,
        timestamp * 1000.0
    );
}

bool VideoReader::read(cv::Mat& frame) {
    return capture_.read(frame);
}

bool VideoReader::grab() {
    return capture_.grab();
}

bool VideoReader::retrieve(cv::Mat& frame) {
    return capture_.retrieve(frame);
}

} // namespace damage_analyzer