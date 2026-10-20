#include "event_crop.hpp"

#include <algorithm>
#include <cmath>
#include <map>
#include <stdexcept>

#include <opencv2/core.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/videoio.hpp>

namespace damage_analyzer {

namespace {

cv::Rect padded_box(const CropRequest& request,
                    double padding,
                    int frame_width,
                    int frame_height)
{
    const int pad = std::max(
        4, static_cast<int>(std::lround(request.height * padding)));

    const int half_w = request.width / 2 + pad;
    const int half_h = request.height / 2 + pad;

    const int x0 = std::max(0, request.center_x - half_w);
    const int y0 = std::max(0, request.center_y - half_h);
    const int x1 = std::min(frame_width, request.center_x + half_w);
    const int y1 = std::min(frame_height, request.center_y + half_h);

    return cv::Rect(x0, y0, std::max(0, x1 - x0), std::max(0, y1 - y0));
}

std::vector<std::uint8_t> encode_crop(const cv::Mat& frame,
                                      const cv::Rect& box,
                                      int min_height)
{
    if (box.width <= 0 || box.height <= 0) {
        return {};
    }

    cv::Mat crop = frame(box).clone();

    if (min_height > 0 && crop.rows < min_height) {
        const double scale =
            static_cast<double>(min_height) / crop.rows;
        cv::Mat larger;
        cv::resize(crop, larger, cv::Size(), scale, scale,
                   cv::INTER_CUBIC);
        crop = larger;
    }

    std::vector<std::uint8_t> png;
    if (!cv::imencode(".png", crop, png)) {
        return {};
    }
    return png;
}

} // namespace

std::vector<CropImages> extract_event_crops(
    const std::string& video_path,
    const std::vector<CropRequest>& requests,
    const CropOptions& options)
{
    cv::VideoCapture capture;
    capture.open(video_path, cv::CAP_FFMPEG);
    if (!capture.isOpened()) {
        capture.open(video_path, cv::CAP_ANY);
    }
    if (!capture.isOpened()) {
        throw std::runtime_error("Could not open video: " + video_path);
    }

    double fps = capture.get(cv::CAP_PROP_FPS);
    if (fps <= 0.0) {
        fps = 30.0;
    }
    const int total_frames =
        static_cast<int>(capture.get(cv::CAP_PROP_FRAME_COUNT));

    const std::vector<double> offsets =
        options.offsets.empty() ? std::vector<double>{0.0}
                                : options.offsets;

    // Todos os (pedido, instante) agrupados por índice de frame: cada
    // frame é decodificado uma única vez, mesmo quando vários eventos
    // caem nele, e a leitura anda sempre para a frente.
    struct Slot {
        std::size_t request;
        std::size_t offset;
    };
    std::map<int, std::vector<Slot>> by_frame;

    for (std::size_t r = 0; r < requests.size(); ++r) {
        for (std::size_t o = 0; o < offsets.size(); ++o) {
            int index = static_cast<int>(std::lround(
                (requests[r].timestamp + offsets[o]) * fps));
            index = std::max(0, index);
            if (total_frames > 0) {
                index = std::min(index, total_frames - 1);
            }
            by_frame[index].push_back({r, o});
        }
    }

    std::vector<CropImages> output(
        requests.size(), CropImages(offsets.size()));

    int next_index = -1;  // índice do próximo frame que read() devolve
    cv::Mat frame;

    for (const auto& entry : by_frame) {
        const int wanted = entry.first;

        // Para frente por até ~1 s lê sequencialmente; senão, reposiciona.
        const bool near_forward =
            next_index >= 0 && wanted >= next_index &&
            wanted - next_index <= static_cast<int>(fps);

        if (!near_forward) {
            capture.set(cv::CAP_PROP_POS_FRAMES, wanted);
            next_index = wanted;
        }

        bool ok = true;
        while (next_index <= wanted) {
            ok = capture.read(frame);
            ++next_index;
            if (!ok) {
                break;
            }
        }

        if (!ok || frame.empty()) {
            next_index = -1;  // força reposicionamento no próximo
            continue;
        }

        for (const Slot& slot : entry.second) {
            const cv::Rect box = padded_box(
                requests[slot.request],
                options.padding,
                frame.cols,
                frame.rows);

            output[slot.request][slot.offset] =
                encode_crop(frame, box, options.min_height);
        }
    }

    return output;
}

} // namespace damage_analyzer
