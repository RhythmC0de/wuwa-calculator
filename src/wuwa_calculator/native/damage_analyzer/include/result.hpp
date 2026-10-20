#pragma once

#include <vector>

namespace damage_analyzer {

struct DamageEvent {
    double timestamp = 0.0;

    int damage = 0;

    int center_x = 0;
    int center_y = 0;

    int width = 0;
    int height = 0;

    double color_score = 0.0;

    // Quantas leituras do OCR confirmaram este valor.
    int observations = 0;

    // Quantos OUTROS eventos têm exatamente o mesmo valor.
    int repeats = 0;

    // Mediana de largura/altura/dígitos da caixa (~0,6-0,7 num número
    // limpo; ~0,4-0,5 em números sobrepostos).
    double digit_pitch = 0.0;

    // false = número de 5+ dígitos com forma de números sobrepostos, ou de
    // forma duvidosa e sem repetição. O evento continua na lista: quem usa a
    // engine decide se conta ou não no total.
    bool confirmed = true;

    // As duas metades (topo e base) da caixa leram este mesmo valor: são
    // 2+ cópias do mesmo número empilhadas e levemente deslocadas. O valor é
    // confiável, mas a QUANTIDADE de cópias não é conhecida.
    bool stacked = false;

    // Uma metade da caixa reproduziu a leitura completa: é um número único
    // (ex.: último dígito ainda "crescendo"), não uma mistura.
    bool verified = false;
};

struct AnalysisResult {
    std::vector<DamageEvent> events;

    double total_damage = 0.0;
    double average_damage = 0.0;

    int total_hits = 0;
    int peak_damage = 0;

    // Eventos não confirmados (veja DamageEvent::confirmed) e o dano deles.
    int unconfirmed_hits = 0;
    double unconfirmed_damage = 0.0;
    int stacked_hits = 0;

    // Video properties
    double fps = 0.0;
    int frame_count = 0;
    double duration = 0.0;

    // Analysis properties
    int frames_read = 0;
    double first_timestamp = 0.0;
    double last_timestamp = 0.0;

    // Frame Information
    int frame_width = 0;
    int frame_height = 0;

    // Pipeline statistics (úteis para calibrar zonas e limiares)
    int frames_analyzed = 0;
    int candidates_detected = 0;
    int candidates_rejected_hud = 0;
    int candidates_rejected_geometry = 0;
    int candidates_passed_filters = 0;
    int ocr_calls = 0;
    int ocr_no_numeric_result = 0;
    int ocr_rejected_confidence = 0;
    int ocr_ignored_countdown = 0;
    int ocr_below_min_damage = 0;

    // true se a análise foi interrompida por CancelToken (resultado parcial)
    bool cancelled = false;
};

} // namespace damage_analyzer