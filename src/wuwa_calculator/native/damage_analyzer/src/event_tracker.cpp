#include "event_tracker.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <string>
#include <vector>

namespace damage_analyzer {

namespace {

struct Run {
    int value = 0;
    int count = 0;
    double first_timestamp = 0.0;
    double color_sum = 0.0;
    DetectionCandidate first_box;
    std::vector<double> aspects;  // largura/altura da caixa em cada leitura
    int stacked = 0;
    int verified = 0;
};

double median_of(std::vector<double> values) {
    if (values.empty()) {
        return 0.0;
    }
    std::sort(values.begin(), values.end());
    return values[values.size() / 2];
}

double center_x_of(const DetectionCandidate& box) {
    return box.x + box.width / 2.0;
}

double center_y_of(const DetectionCandidate& box) {
    return box.y + box.height / 2.0;
}

} // namespace

EventTracker::EventTracker(Params params)
    : params_(params) {
}

void EventTracker::begin_frame(double timestamp) {
    for (Track& track : tracks_) {
        track.matched_in_frame = false;
    }

    auto expired = [&](const Track& track) {
        return timestamp - track.last_timestamp > params_.max_gap;
    };

    for (const Track& track : tracks_) {
        if (expired(track)) {
            finalize(track);
        }
    }

    tracks_.erase(
        std::remove_if(tracks_.begin(), tracks_.end(), expired),
        tracks_.end()
    );
}

void EventTracker::observe(const DamageObservation& observation) {
    const double cx = center_x_of(observation.box);
    const double cy = center_y_of(observation.box);

    Track* best = nullptr;
    double best_score = std::numeric_limits<double>::max();

    for (Track& track : tracks_) {
        if (track.matched_in_frame) {
            continue;
        }

        const double limit =
            std::max(track.height, double(observation.box.height)) *
            params_.match_distance_in_heights;

        const double distance =
            std::hypot(cx - track.center_x, cy - track.center_y);

        if (distance > limit) {
            continue;
        }

        // Prefere a trilha que já estava lendo o mesmo valor.
        const double bonus =
            track.observations.back().value == observation.value
                ? 0.5
                : 1.0;

        const double score = distance * bonus;

        if (score < best_score) {
            best_score = score;
            best = &track;
        }
    }

    if (best == nullptr) {
        Track track;
        track.center_x = cx;
        track.center_y = cy;
        track.height = observation.box.height;
        track.last_timestamp = observation.timestamp;
        track.matched_in_frame = true;
        track.observations.push_back(observation);

        tracks_.push_back(std::move(track));
        return;
    }

    // O texto sobe e muda de escala; acompanha a posição atual.
    best->center_x = cx;
    best->center_y = cy;
    best->height = observation.box.height;
    best->last_timestamp = observation.timestamp;
    best->matched_in_frame = true;
    best->observations.push_back(observation);
}

void EventTracker::discard_near(const DetectionCandidate& box) {
    const double cx = center_x_of(box);
    const double cy = center_y_of(box);

    tracks_.erase(
        std::remove_if(
            tracks_.begin(),
            tracks_.end(),
            [&](const Track& track) {
                const double limit =
                    std::max(track.height, double(box.height)) *
                    params_.match_distance_in_heights;

                return std::hypot(
                           cx - track.center_x,
                           cy - track.center_y
                       ) <= limit;
            }
        ),
        tracks_.end()
    );
}

std::vector<DamageEvent> EventTracker::finish() {
    for (const Track& track : tracks_) {
        finalize(track);
    }

    tracks_.clear();

    std::vector<DamageEvent> events = std::move(finished_);
    finished_.clear();

    // Remove eventos de trilhas curtas que caíram em cima de um texto de
    // interface descoberto depois (ou antes) no vídeo.
    events.erase(
        std::remove_if(
            events.begin(),
            events.end(),
            [&](const DamageEvent& event) {
                for (const StaticSpot& spot : static_spots_) {
                    const double limit =
                        std::max(spot.height, double(event.height));

                    if (std::hypot(
                            event.center_x - spot.center_x,
                            event.center_y - spot.center_y
                        ) <= limit) {
                        return true;
                    }

                    // Leitura do mesmo contador em outro lugar (a câmera
                    // balança e o texto muda de posição): o valor cai dentro
                    // da faixa que o contador tinha naquele momento.
                    const double margin = 0.01 * spot.max_value + 5.0;
                    if (event.timestamp >= spot.t_first - 1.5 &&
                        event.timestamp <= spot.t_last + 1.5 &&
                        event.damage >= spot.min_value - margin &&
                        event.damage <= spot.max_value + margin) {
                        return true;
                    }
                }
                return false;
            }
        ),
        events.end()
    );

    std::stable_sort(
        events.begin(),
        events.end(),
        [](const DamageEvent& a, const DamageEvent& b) {
            return a.timestamp < b.timestamp;
        }
    );

    // Remove leituras com dígitos a mais (veja Params::suffix_window).
    std::vector<bool> drop(events.size(), false);
    for (std::size_t i = 0; i < events.size(); ++i) {
        const std::string longer = std::to_string(events[i].damage);

        for (std::size_t j = 0; j < events.size(); ++j) {
            if (i == j) {
                continue;
            }
            if (std::abs(events[i].timestamp - events[j].timestamp) >
                params_.suffix_window) {
                continue;
            }

            const std::string shorter = std::to_string(events[j].damage);
            if (static_cast<int>(shorter.size()) < params_.suffix_min_digits ||
                longer.size() < shorter.size() + 2) {
                continue;
            }
            if (longer.compare(
                    longer.size() - shorter.size(), shorter.size(), shorter
                ) == 0) {
                drop[i] = true;
                break;
            }
        }
    }

    // Mesmo número "andando" pela tela, lido com um dígito errado.
    for (std::size_t i = 0; i < events.size(); ++i) {
        if (drop[i]) {
            continue;
        }

        const std::string a = std::to_string(events[i].damage);

        for (std::size_t j = i + 1; j < events.size(); ++j) {
            if (drop[j]) {
                continue;
            }
            if (events[j].timestamp - events[i].timestamp >
                params_.near_dup_window) {
                break;  // eventos ordenados por tempo
            }

            const std::string b = std::to_string(events[j].damage);
            if (a.size() != b.size() ||
                static_cast<int>(a.size()) < params_.near_dup_min_digits) {
                continue;
            }

            int differences = 0;
            for (std::size_t k = 0; k < a.size(); ++k) {
                differences += a[k] != b[k] ? 1 : 0;
            }
            if (differences != 1) {
                continue;
            }

            const double limit =
                params_.near_dup_distance_in_heights *
                std::max(events[i].height, events[j].height);
            if (std::hypot(
                    double(events[i].center_x - events[j].center_x),
                    double(events[i].center_y - events[j].center_y)
                ) > limit) {
                continue;
            }

            // Fica o mais confirmado; em empate, o mais antigo.
            if (events[j].observations > events[i].observations) {
                drop[i] = true;
                break;
            }
            drop[j] = true;
        }
    }

    std::vector<DamageEvent> kept;
    kept.reserve(events.size());
    for (std::size_t i = 0; i < events.size(); ++i) {
        if (!drop[i]) {
            kept.push_back(events[i]);
        }
    }
    events = std::move(kept);

    // Confirmação. Números de 5+ dígitos só são aceitos sem dúvida se a
    // forma bate com um número isolado (digit_pitch alto). Forma duvidosa
    // exige repetição do mesmo valor em outro evento; forma de número
    // sobreposto nunca é confirmada. O evento fica na lista de qualquer
    // forma: quem usa a engine decide o que contar no total.
    for (std::size_t i = 0; i < events.size(); ++i) {
        int repeats = 0;
        for (std::size_t j = 0; j < events.size(); ++j) {
            if (i != j && events[j].damage == events[i].damage) {
                ++repeats;
            }
        }
        events[i].repeats = repeats;

        const int digits =
            static_cast<int>(std::to_string(events[i].damage).size());
        const double pitch = events[i].digit_pitch;

        if (events[i].stacked || events[i].verified ||
            digits < params_.unconfirmed_min_digits ||
            pitch >= params_.pitch_confident) {
            events[i].confirmed = true;
        } else if (pitch >= params_.pitch_suspect) {
            events[i].confirmed = repeats > 0;
        } else {
            events[i].confirmed = false;
        }
    }

    return events;
}

bool EventTracker::is_known_static_hud(const DetectionCandidate& box) const {
    const double cx = center_x_of(box);
    const double cy = center_y_of(box);

    for (const StaticSpot& spot : static_spots_) {
        const double limit = std::max(spot.height, double(box.height));

        if (std::hypot(cx - spot.center_x, cy - spot.center_y) <= limit) {
            return true;
        }
    }

    return false;
}

void EventTracker::finalize(const Track& track) {
    // Texto parado por muito tempo = interface, não dano (veja Params).
    // O teste é robusto a leituras isoladas fora do lugar: usa a mediana da
    // posição e exige que a maior parte das leituras esteja perto dela.
    if (track.observations.size() >= 3) {
        std::vector<double> xs;
        std::vector<double> ys;
        std::vector<int> values;
        double height_sum = 0.0;

        for (const DamageObservation& observation : track.observations) {
            xs.push_back(center_x_of(observation.box));
            ys.push_back(center_y_of(observation.box));
            values.push_back(observation.value);
            height_sum += observation.box.height;
        }

        const double height =
            height_sum / static_cast<double>(track.observations.size());
        const double duration =
            track.observations.back().timestamp -
            track.observations.front().timestamp;

        std::vector<double> sx = xs;
        std::vector<double> sy = ys;
        std::sort(sx.begin(), sx.end());
        std::sort(sy.begin(), sy.end());
        const double median_x = sx[sx.size() / 2];
        const double median_y = sy[sy.size() / 2];

        const double radius = params_.static_max_move_in_heights * height;
        std::size_t near_count = 0;
        for (std::size_t i = 0; i < xs.size(); ++i) {
            if (std::hypot(xs[i] - median_x, ys[i] - median_y) <= radius) {
                ++near_count;
            }
        }

        // Um contador de interface muda de valor o tempo todo (HP, cronômetro,
        // combo); um número de dano parado tem um único valor, com no máximo
        // algumas leituras erradas do OCR. Sem isso, dano real que fica
        // parado na tela seria confundido com HUD.
        std::sort(values.begin(), values.end());
        const std::size_t distinct = static_cast<std::size_t>(
            std::unique(values.begin(), values.end()) - values.begin()
        );
        values.resize(distinct);
        const bool changes_constantly =
            distinct >= 5 && distinct * 4 >= xs.size();

        if (duration >= params_.static_min_duration &&
            near_count * 10 >= xs.size() * 8 && changes_constantly) {
            // Faixa de valores típica (10%..90%): ignora leituras erradas.
            const int low = values[values.size() / 10];
            const int high = values[(values.size() * 9) / 10];

            static_spots_.push_back({
                median_x,
                median_y,
                height,
                track.observations.front().timestamp,
                track.observations.back().timestamp,
                low,
                high
            });
            return;
        }
    }

    // Votação por valor. O mesmo número de dano costuma ser lido várias vezes
    // na trilha, mas o OCR "pisca" (ex.: A A B A A). Exigir leituras
    // CONSECUTIVAS iguais descartava hits reais sempre que uma leitura ruim
    // quebrava a sequência, e piorava muito com frame_stride > 1.
    // Agora cada valor precisa apenas de `min_observations` leituras na trilha,
    // consecutivas ou não.
    std::vector<Run> votes;  // ordem de primeira aparição

    for (const DamageObservation& observation : track.observations) {
        auto it = std::find_if(
            votes.begin(), votes.end(),
            [&](const Run& run) { return run.value == observation.value; }
        );

        if (it == votes.end()) {
            Run run;
            run.value = observation.value;
            run.first_timestamp = observation.timestamp;
            run.first_box = observation.box;
            votes.push_back(run);
            it = votes.end() - 1;
        }

        it->count += 1;
        it->color_sum += observation.color_score;
        it->stacked += observation.stacked ? 1 : 0;
        it->verified += observation.verified ? 1 : 0;
        it->aspects.push_back(
            double(observation.box.width) /
            std::max(1, observation.box.height)
        );
    }

    // Leituras truncadas/estendidas do mesmo número (48998 x 489982) são
    // ruído: descarta o valor que está contido em outro com mais votos.
    auto is_substring_noise = [&](const Run& run) {
        const std::string text = std::to_string(run.value);

        for (const Run& other : votes) {
            if (other.value == run.value || other.count <= run.count) {
                continue;
            }

            if (std::to_string(other.value).find(text) != std::string::npos) {
                return true;
            }
        }

        return false;
    };

    for (const Run& run : votes) {
        const int required =
            run.value >= params_.large_value
                ? std::max(params_.min_observations,
                           params_.large_value_min_observations)
                : params_.min_observations;

        if (run.count < required || is_substring_noise(run)) {
            continue;
        }

        DamageEvent event;

        event.timestamp = run.first_timestamp;
        event.damage = run.value;
        event.center_x = static_cast<int>(center_x_of(run.first_box));
        event.center_y = static_cast<int>(center_y_of(run.first_box));
        event.width = run.first_box.width;
        event.height = run.first_box.height;
        event.color_score = run.color_sum / run.count;
        event.observations = run.count;
        event.stacked = run.stacked * 2 >= run.count;
        event.verified = run.verified > 0;

        // Espaçamento por dígito: um número limpo ocupa ~0,6-0,7 da altura
        // por dígito. Números sobrepostos dividem a mesma largura e ficam
        // bem mais estreitos (0,4-0,5).
        const int digits = static_cast<int>(std::to_string(run.value).size());
        event.digit_pitch = median_of(run.aspects) / std::max(1, digits);

        finished_.push_back(event);
    }
}

} // namespace damage_analyzer
