
#include "temporal_filter.hpp"

#include <algorithm>
#include <cmath>

namespace damage_analyzer {

bool TemporalFilter::should_ignore(
    const DetectionCandidate& candidate,
    int value,
    double timestamp,
    int frame_width,
    int frame_height
) {
    if (frame_width <= 0 ||
        frame_height <= 0 ||
        candidate.width <= 0 ||
        candidate.height <= 0 ||
        value < 0 ||
        timestamp < 0.0) {
        return false;
    }

    prune(timestamp);

    const double cx =
        normalized_center_x(candidate, frame_width);

    const double cy =
        normalized_center_y(candidate, frame_height);

    Track* matched_track = nullptr;
    double nearest_distance = TRACK_DISTANCE;

    for (Track& track : tracks_) {
        const double d = distance(
            cx,
            cy,
            track.center_x,
            track.center_y
        );

        if (d < nearest_distance) {
            nearest_distance = d;
            matched_track = &track;
        }
    }

    // Ainda não existe histórico nessa posição.
    if (matched_track == nullptr) {
        Track track;
        track.center_x = cx;
        track.center_y = cy;
        track.last_value = value;
        track.last_timestamp = timestamp;

        tracks_.push_back(track);
        return false;
    }

    Track& track = *matched_track;

    const double elapsed =
        timestamp - track.last_timestamp;

    // Uma observação repetida no mesmo instante não conta
    // como uma nova etapa da contagem.
    if (elapsed <= 0.0) {
        return track.countdown_detected;
    }

    if (elapsed > MAX_STEP_INTERVAL) {
        // Interrupção longa: reinicia a sequência.
        track.descending_steps = 0;
        track.countdown_detected = false;
    } else if (
        value >= 1 &&
        track.last_value >= 2 &&
        value == track.last_value - 1
    ) {
        ++track.descending_steps;

        // Exige pelo menos três transições consecutivas, em
        // qualquer magnitude: 6 -> 5 -> 4 -> 3 ou 121 -> 120 -> 119 -> 118.
        if (track.descending_steps >= 3) {
            track.countdown_detected = true;
        }
    } else if (value != track.last_value) {
        // Valor que não continua a sequência decrescente.
        track.descending_steps = 0;
        track.countdown_detected = false;
    }

    // Atualiza a posição suavemente para tolerar pequenas
    // movimentações do texto entre frames.
    track.center_x = cx;
    track.center_y = cy;
    track.last_timestamp = timestamp;
    track.last_value = value;

    return track.countdown_detected;
}

void TemporalFilter::prune(double current_timestamp) {
    tracks_.erase(
        std::remove_if(
            tracks_.begin(),
            tracks_.end(),
            [current_timestamp](const Track& track) {
                return current_timestamp -
                           track.last_timestamp >
                       TRACK_TIMEOUT;
            }
        ),
        tracks_.end()
    );
}

void TemporalFilter::reset() {
    tracks_.clear();
}

double TemporalFilter::normalized_center_x(
    const DetectionCandidate& candidate,
    int frame_width
) {
    return (
        candidate.x + candidate.width / 2.0
    ) / frame_width;
}

double TemporalFilter::normalized_center_y(
    const DetectionCandidate& candidate,
    int frame_height
) {
    return (
        candidate.y + candidate.height / 2.0
    ) / frame_height;
}

double TemporalFilter::distance(
    double ax,
    double ay,
    double bx,
    double by
) {
    return std::hypot(ax - bx, ay - by);
}

} // namespace damage_analyzer
