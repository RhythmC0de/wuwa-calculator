#include "candidate_filter.hpp"

#include <algorithm>
#include <utility>

namespace damage_analyzer {

namespace {

// Um candidato é considerado parte do HUD quando pelo menos esta
// fração da sua área cai dentro de uma zona de exclusão. Assim, um
// número de dano que apenas encosta na borda de uma zona não é perdido.
constexpr double HUD_OVERLAP_THRESHOLD = 0.5;

}

std::vector<ExclusionZone> default_exclusion_zones() {
    return {
        // Minimapa, missões e indicadores no canto superior esquerdo.
        {0.00, 0.00, 0.26, 0.40}, // lista de missões (inclui "150s left" etc.)

        // Barra de vida do chefe, cronômetros e avisos no topo central.
        {0.28, 0.00, 0.72, 0.11},

        // Menus, relógio e botões no canto superior direito.
        {0.78, 0.00, 1.00, 0.18},

        // Painel da equipe (retratos, vida, energia) na lateral direita.
        {0.86, 0.18, 1.00, 0.78},

        // Botões de habilidade, eco e ultimate no canto inferior direito.
        {0.66, 0.78, 1.00, 1.00},

        // Chat e notificações no canto inferior esquerdo.
        {0.00, 0.68, 0.22, 1.00},
    };
}

CandidateFilter::CandidateFilter(
    std::vector<ExclusionZone> exclusion_zones,
    CandidateLimits limits
)
    : exclusion_zones_(std::move(exclusion_zones)),
      limits_(limits) {
}

bool CandidateFilter::is_excluded(
    const DetectionCandidate& candidate,
    int frame_width,
    int frame_height
) const {
    if (frame_width <= 0 || frame_height <= 0) {
        return true;
    }

    if (candidate.width <= 0 || candidate.height <= 0) {
        return true;
    }

    for (const ExclusionZone& zone : exclusion_zones_) {
        if (overlap_fraction(
                candidate,
                zone,
                frame_width,
                frame_height) >= HUD_OVERLAP_THRESHOLD) {
            return true;
        }
    }

    return false;
}

bool CandidateFilter::has_plausible_geometry(
    const DetectionCandidate& candidate,
    int frame_width,
    int frame_height
) const {
    if (frame_width <= 0 ||
        frame_height <= 0 ||
        candidate.width <= 0 ||
        candidate.height <= 0) {
        return false;
    }

    const double relative_height =
        static_cast<double>(candidate.height) / frame_height;

    if (relative_height < limits_.min_height ||
        relative_height > limits_.max_height) {
        return false;
    }

    const double aspect =
        static_cast<double>(candidate.width) / candidate.height;

    return aspect >= limits_.min_aspect &&
           aspect <= limits_.max_aspect;
}


double CandidateFilter::overlap_fraction(
    const DetectionCandidate& candidate,
    const ExclusionZone& zone,
    int frame_width,
    int frame_height
) {
    // Ignora zonas com coordenadas inválidas.
    if (zone.left < 0.0 ||
        zone.top < 0.0 ||
        zone.right > 1.0 ||
        zone.bottom > 1.0 ||
        zone.left >= zone.right ||
        zone.top >= zone.bottom) {
        return 0.0;
    }

    // Converte coordenadas normalizadas para pixels.
    const double zone_left = zone.left * frame_width;
    const double zone_top = zone.top * frame_height;
    const double zone_right = zone.right * frame_width;
    const double zone_bottom = zone.bottom * frame_height;

    const double candidate_left = candidate.x;
    const double candidate_top = candidate.y;
    const double candidate_right = candidate.x + candidate.width;
    const double candidate_bottom = candidate.y + candidate.height;

    const double overlap_width =
        std::min(candidate_right, zone_right) -
        std::max(candidate_left, zone_left);

    const double overlap_height =
        std::min(candidate_bottom, zone_bottom) -
        std::max(candidate_top, zone_top);

    if (overlap_width <= 0.0 || overlap_height <= 0.0) {
        return 0.0;
    }

    const double candidate_area =
        static_cast<double>(candidate.width) * candidate.height;

    return (overlap_width * overlap_height) / candidate_area;
}

} // namespace damage_analyzer
