#pragma once

#include <atomic>
#include <memory>
#include <string>
#include <vector>

#include "candidate_filter.hpp"
#include "result.hpp"

namespace damage_analyzer {

// Token de cancelamento, seguro entre threads. Cada análise recebe o seu,
// então cancelar uma não interfere em outra em andamento.
struct CancelToken {
    std::atomic<bool> flag{false};

    void cancel() { flag.store(true); }
    bool is_cancelled() const { return flag.load(); }
};

struct AnalyzerConfig {
    // Caminhos do modelo OCR e do dicionário. Se vazios, são procurados
    // automaticamente (veja find_models_directory()).
    std::string model_path;
    std::string dictionary_path;

    // Regiões do HUD ignoradas (coordenadas normalizadas 0..1).
    std::vector<ExclusionZone> exclusion_zones = default_exclusion_zones();

    // Limites de tamanho/proporção de um número de dano plausível.
    CandidateLimits limits;

    // Analisa 1 a cada N frames (1 = todos). Útil para vídeos de 60 fps+.
    int frame_stride = 1;

    // Confiança mínima da leitura do OCR (0..1).
    double min_confidence = 0.80;

    // Dano mínimo aceito. Valores menores são tratados como ruído
    // (níveis, cooldowns, contagens, etc.).
    int min_damage = 100;

    // Frames consecutivos com o mesmo valor para aceitar um número.
    int min_observations = 2;

    // Segundos sem leitura para considerar que o número sumiu.
    double track_max_gap = 0.35;

    // Margem adicionada ao recorte enviado ao OCR (fração da altura).
    double crop_padding = 0.15;

    // Opcional. Se definido e cancelado, a análise termina no próximo frame
    // e devolve o resultado parcial com result.cancelled = true.
    std::shared_ptr<CancelToken> cancel_token;

    // Fração da tela coberta pela máscara a partir da qual o frame é tratado
    // como "explosão" e a detecção extra (cor quente / contorno) é ligada.
    // 0 desliga a detecção extra (mais rápido, perde números em explosões).
    double bloom_fraction = 0.12;

    // Threads para rodar OCRs do mesmo frame em paralelo (0 = automático,
    // até 4 conforme os núcleos da máquina).
    int ocr_threads = 0;

    // Imprime um resumo da análise em stdout.
    bool verbose = false;
};

// end_time <= 0 (ou menor que start_time) significa "até o fim do vídeo".
AnalysisResult analyze_video(
    const std::string& video_path,
    double start_time,
    double end_time,
    const AnalyzerConfig& config = AnalyzerConfig{}
);

} // namespace damage_analyzer
