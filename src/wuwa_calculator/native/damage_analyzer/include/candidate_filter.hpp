#pragma once

#include "damage_detector.hpp"

#include <vector>

namespace damage_analyzer {

struct ExclusionZone {
    // Coordenadas normalizadas entre 0.0 e 1.0.
    // left/top: canto superior esquerdo.
    // right/bottom: canto inferior direito.
    double left = 0.0;
    double top = 0.0;
    double right = 0.0;
    double bottom = 0.0;
};

// Limites geométricos de um candidato plausível a número de dano.
// Alturas são frações da altura do frame, então valem para qualquer
// resolução (720p, 1080p, 1440p, 4K...).
struct CandidateLimits {
    double min_height = 0.015;   // fração da altura do frame
    double max_height = 0.12;
    double min_aspect = 1.2;     // largura / altura
    double max_aspect = 14.0;
};

// Zonas de HUD padrão para o layout 16:9 do jogo (coordenadas
// normalizadas). São um ponto de partida e podem ser substituídas.
std::vector<ExclusionZone> default_exclusion_zones();

class CandidateFilter {
public:
    CandidateFilter() = default;

    explicit CandidateFilter(
        std::vector<ExclusionZone> exclusion_zones,
        CandidateLimits limits = {}
    );

    // O candidato está majoritariamente dentro de uma zona de HUD?
    bool is_excluded(
        const DetectionCandidate& candidate,
        int frame_width,
        int frame_height
    ) const;

    // O formato/tamanho do candidato é compatível com um número de dano?
    bool has_plausible_geometry(
        const DetectionCandidate& candidate,
        int frame_width,
        int frame_height
    ) const;

private:
    std::vector<ExclusionZone> exclusion_zones_;
    CandidateLimits limits_;

    // Fração (0..1) da área do candidato coberta pela zona.
    static double overlap_fraction(
        const DetectionCandidate& candidate,
        const ExclusionZone& zone,
        int frame_width,
        int frame_height
    );
};

} // namespace damage_analyzer
