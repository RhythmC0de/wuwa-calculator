#pragma once

#include <vector>

#include "damage_detector.hpp"
#include "result.hpp"

namespace damage_analyzer {

struct DamageObservation {
    double timestamp = 0.0;
    int value = 0;
    double confidence = 0.0;
    double color_score = 0.0;
    DetectionCandidate box;

    // Verificação por faixas (topo/base) feita no analyzer:
    // stacked  = as duas faixas leram o mesmo valor (cópias empilhadas).
    // verified = uma faixa reproduziu a leitura completa (número único).
    bool stacked = false;
    bool verified = false;
};

// Um número de dano fica vários frames na tela, subindo e desaparecendo.
// O EventTracker agrupa as leituras de OCR de um mesmo número em uma
// trilha e produz UM DamageEvent por número.
//
// Leituras isoladas e inconsistentes (ex.: o OCR leu "48998" em um frame
// e "489982" nos vizinhos) são tratadas como ruído: só viram evento as
// sequências de leituras iguais com pelo menos `min_observations` frames.
class EventTracker {
public:
    struct Params {
        // Tempo sem novas leituras para encerrar uma trilha (segundos).
        double max_gap = 0.35;

        // Quantidade mínima de frames com o mesmo valor.
        int min_observations = 2;

        // Distância máxima de associação, em alturas de texto.
        double match_distance_in_heights = 1.5;

        // Texto de interface (contador de HP do chefe, cronômetro...) fica
        // parado no mesmo lugar por muito tempo, enquanto o dano real sobe e
        // some em menos de ~1 s. Uma trilha que dura pelo menos
        // `static_min_duration` segundos e quase não se move (menos que
        // `static_max_move_in_heights` alturas de texto) é HUD: seus eventos
        // são descartados, assim como os de qualquer outra trilha que apareça
        // no mesmo lugar em outro momento do vídeo (ex.: leituras
        // interrompidas do mesmo contador).
        double static_min_duration = 0.25;
        double static_max_move_in_heights = 0.6;

        // Leitura com dígitos a mais: o OCR às vezes cola um dígito de um
        // ícone ao lado ("24274" vira "2424274"). Se, na mesma janela de
        // tempo, existe outro evento cujo número é um sufixo mais curto
        // (>= `suffix_min_digits` dígitos, pelo menos 2 dígitos a menos), o
        // evento longo é descartado.
        double suffix_window = 0.6;
        int suffix_min_digits = 3;

        // Valores muito altos (ex.: >= 1.000.000) são quase sempre leituras
        // erradas de números sobrepostos; só valem com mais confirmações.
        int large_value = 1000000;
        int large_value_min_observations = 4;

        // A mesma leitura "andando" pela tela (ex.: a ultimate subindo) vira
        // vários eventos com um dígito de diferença. Valores com pelo menos
        // `near_dup_min_digits` dígitos, a no máximo 1 dígito de distância,
        // próximos no tempo e no espaço, são o mesmo número: fica o mais
        // confirmado.
        double near_dup_window = 0.6;
        int near_dup_min_digits = 5;
        double near_dup_distance_in_heights = 6.0;

        // Valores com este número de dígitos ou mais só são "confirmados" se
        // aparecerem em mais de um evento.
        int unconfirmed_min_digits = 5;

        // Espaçamento por dígito (largura/altura/dígitos, mediana da trilha):
        // >= pitch_confident é um número isolado; entre pitch_suspect e
        // pitch_confident só é confirmado se o valor se repetir; abaixo de
        // pitch_suspect é leitura de números sobrepostos.
        double pitch_confident = 0.58;
        double pitch_suspect = 0.50;
    };

    EventTracker() = default;
    explicit EventTracker(Params params);

    // Deve ser chamado uma vez por frame analisado, antes de observe().
    void begin_frame(double timestamp);

    void observe(const DamageObservation& observation);

    // Remove as trilhas próximas de (x, y), usado quando o filtro
    // temporal descobre que aquela posição é um contador da interface.
    void discard_near(const DetectionCandidate& box);

    // Verdadeiro se o candidato está em cima de um texto de interface já
    // descoberto (contador que troca de valor parado no mesmo lugar). Usado
    // para pular o OCR: o resultado final é o mesmo, pois esses eventos já
    // seriam descartados em finish().
    bool is_known_static_hud(const DetectionCandidate& box) const;

    // Encerra todas as trilhas e devolve os eventos em ordem de tempo.
    std::vector<DamageEvent> finish();

private:
    struct Track {
        double center_x = 0.0;
        double center_y = 0.0;
        double height = 0.0;
        double last_timestamp = 0.0;
        bool matched_in_frame = false;
        std::vector<DamageObservation> observations;
    };

    struct StaticSpot {
        double center_x = 0.0;
        double center_y = 0.0;
        double height = 0.0;
        double t_first = 0.0;
        double t_last = 0.0;
        int min_value = 0;
        int max_value = 0;
    };

    Params params_;
    std::vector<StaticSpot> static_spots_;
    std::vector<Track> tracks_;
    std::vector<DamageEvent> finished_;

    void finalize(const Track& track);
};

} // namespace damage_analyzer
