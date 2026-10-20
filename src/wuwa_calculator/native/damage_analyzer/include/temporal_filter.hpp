
#pragma once

#include "damage_detector.hpp"

#include <vector>

namespace damage_analyzer {

class TemporalFilter {
public:
    // Registra uma observação e informa se ela parece
    // pertencer a uma contagem regressiva de interface.
    bool should_ignore(
        const DetectionCandidate& candidate,
        int value,
        double timestamp,
        int frame_width,
        int frame_height
    );

    // Remove históricos antigos.
    void prune(double current_timestamp);

    // Limpa o histórico entre análises de vídeos.
    void reset();

private:
    struct Track {
        double center_x = 0.0;
        double center_y = 0.0;

        int last_value = 0;
        int descending_steps = 0;

        double last_timestamp = 0.0;

        bool countdown_detected = false;
    };

    std::vector<Track> tracks_;

    static constexpr double TRACK_DISTANCE = 0.025;
    static constexpr double MAX_STEP_INTERVAL = 1.5;
    static constexpr double TRACK_TIMEOUT = 2.0;

    static double normalized_center_x(
        const DetectionCandidate& candidate,
        int frame_width
    );

    static double normalized_center_y(
        const DetectionCandidate& candidate,
        int frame_height
    );

    static double distance(
        double ax,
        double ay,
        double bx,
        double by
    );
};

} // namespace damage_analyzer
