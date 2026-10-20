#include "analyzer.hpp"

#include "candidate_filter.hpp"
#include "damage_detector.hpp"
#include "damage_ocr.hpp"
#include "event_tracker.hpp"
#include "frame_processor.hpp"
#include "platform.hpp"
#include "temporal_filter.hpp"
#include "video_reader.hpp"

#include <algorithm>
#include <atomic>
#include <exception>
#include <mutex>
#include <thread>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>

namespace damage_analyzer {

namespace {

constexpr const char* MODEL_FILE = "en_PP-OCRv5_rec_mobile.onnx";
constexpr const char* DICTIONARY_FILE = "ppocrv5_en_dict.txt";

struct ResolvedPaths {
    std::string model;
    std::string dictionary;
};

ResolvedPaths resolve_paths(const AnalyzerConfig& config) {
    ResolvedPaths paths{config.model_path, config.dictionary_path};

    if (!paths.model.empty() && !paths.dictionary.empty()) {
        return paths;
    }

    const std::filesystem::path models_dir = find_models_directory();

    if (models_dir.empty()) {
        throw std::runtime_error(
            "OCR models not found. Pass model_path/dictionary_path in "
            "the config or set DAMAGE_ANALYZER_MODELS_DIR."
        );
    }

    if (paths.model.empty()) {
        paths.model = to_utf8(models_dir / MODEL_FILE);
    }

    if (paths.dictionary.empty()) {
        paths.dictionary = to_utf8(models_dir / DICTIONARY_FILE);
    }

    return paths;
}

cv::Rect padded_crop(
    const DetectionCandidate& candidate,
    double padding,
    int frame_width,
    int frame_height
) {
    const int pad = static_cast<int>(candidate.height * padding);

    const cv::Rect wanted(
        candidate.x - pad,
        candidate.y - pad,
        candidate.width + 2 * pad,
        candidate.height + 2 * pad
    );

    return wanted & cv::Rect(0, 0, frame_width, frame_height);
}

double mask_fill_ratio(
    const cv::Mat& mask,
    const DetectionCandidate& candidate
) {
    const cv::Rect rect =
        cv::Rect(
            candidate.x,
            candidate.y,
            candidate.width,
            candidate.height
        ) & cv::Rect(0, 0, mask.cols, mask.rows);

    if (rect.area() <= 0) {
        return 0.0;
    }

    return static_cast<double>(cv::countNonZero(mask(rect))) /
           static_cast<double>(rect.area());
}

// Memória curta do resultado do OCR por posição. Um número de dano fica na
// tela por dezenas de frames sempre com o mesmo valor, e efeitos visuais que
// "parecem" texto também persistem. Depois de DUAS leituras iguais seguidas
// no mesmo lugar e com o mesmo tamanho, as próximas `kMaxReuse` leituras
// reaproveitam o resultado em vez de chamar o OCR de novo; depois disso o
// OCR é feito de novo para confirmar. Contadores que mudam de valor a cada
// frame nunca ficam "estáveis" e continuam sendo lidos todos os frames.
struct OcrMemo {
    double cx = 0.0;
    double cy = 0.0;
    double w = 0.0;
    double h = 0.0;
    bool accepted = false;
    int value = 0;
    double confidence = 0.0;
    int streak = 0;
    int skips = 0;
    long last_frame = 0;
    bool used = false;
};

// Fração da área do frame coberta pela máscara a partir da qual o frame é
// tratado como "explosão" (bloom): o fundo claro vira uma mancha enorme na
// máscara e engole os números. Nesses frames, a detecção também é feita com
// uma máscara só de cor quente e com uma máscara de contorno escuro.

// Candidatos extras de contorno: só formas com cara de linha de dígitos.
constexpr double kOutlineMinHeight = 0.03;  // fração da altura do frame
constexpr double kOutlineMinAspect = 2.0;
constexpr double kOutlineMaxAspect = 12.0;
constexpr std::size_t kOutlineMaxCandidates = 8;
constexpr long kOutlineEveryNthFrame = 2;
// O contorno escuro só é usado em explosões extremas (máscara cobrindo mais
// de 40% da tela, como na ultimate): em frames normais ele só acha ruído.
constexpr double kOutlineMinFill = 0.40;

// Verdadeiro se `box` já está (em pelo menos metade da sua área) coberto
// por algum dos candidatos existentes.
bool mostly_covered(
    const DetectionCandidate& box,
    const std::vector<DetectionCandidate>& existing
) {
    const double area = double(box.width) * box.height;

    if (area <= 0.0) {
        return true;
    }

    const cv::Rect rect(box.x, box.y, box.width, box.height);

    for (const DetectionCandidate& other : existing) {
        const cv::Rect overlap =
            rect & cv::Rect(other.x, other.y, other.width, other.height);

        if (double(overlap.width) * overlap.height >= 0.5 * area) {
            return true;
        }
    }

    return false;
}

// Texto escuro de contorno sobre fundo claro (ex.: dano da ultimate em
// vermelho sobre uma explosão laranja): realça traços finos e escuros em
// uma versão reduzida do frame, bem mais barato que no tamanho original.
std::vector<DetectionCandidate> outline_candidates(
    const cv::Mat& frame,
    const DamageDetector& detector
) {
    std::vector<DetectionCandidate> boxes;

    if (frame.empty() || frame.rows <= 0) {
        return boxes;
    }

    constexpr int kTargetHeight = 360;
    const double scale = double(kTargetHeight) / frame.rows;

    cv::Mat gray;
    cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);

    cv::Mat small;
    cv::resize(
        gray,
        small,
        cv::Size(std::max(1, int(frame.cols * scale)), kTargetHeight),
        0.0,
        0.0,
        cv::INTER_AREA
    );

    int kernel_size = std::max(3, int(std::lround(0.03 * kTargetHeight)));
    kernel_size |= 1;

    cv::Mat blackhat;
    cv::morphologyEx(
        small,
        blackhat,
        cv::MORPH_BLACKHAT,
        cv::getStructuringElement(
            cv::MORPH_RECT, cv::Size(kernel_size, kernel_size))
    );

    cv::Mat mask;
    cv::threshold(blackhat, mask, 18, 255, cv::THRESH_BINARY);

    for (const DetectionCandidate& found : detector.detect(mask)) {
        DetectionCandidate box;
        box.x = int(found.x / scale);
        box.y = int(found.y / scale);
        box.width = int(found.width / scale);
        box.height = int(found.height / scale);

        const double aspect = double(box.width) / std::max(1, box.height);
        const double relative_height = double(box.height) / frame.rows;

        if (relative_height < kOutlineMinHeight ||
            aspect < kOutlineMinAspect ||
            aspect > kOutlineMaxAspect) {
            continue;
        }

        boxes.push_back(box);
    }

    std::sort(
        boxes.begin(),
        boxes.end(),
        [](const DetectionCandidate& a, const DetectionCandidate& b) {
            return long(a.width) * a.height > long(b.width) * b.height;
        }
    );

    if (boxes.size() > kOutlineMaxCandidates) {
        boxes.resize(kOutlineMaxCandidates);
    }

    return boxes;
}

// Candidato que passou pelos filtros e espera o OCR do frame atual.
struct PendingOcr {
    DetectionCandidate candidate;
    cv::Rect crop;
    int memo_index = -1;
};

// Verificação por faixas: leituras de 3+ dígitos com caixa estreita demais
// (largura/altura/dígitos abaixo disto) podem ser números sobrepostos. A
// caixa é dividida em topo e base; se as duas metades leem o mesmo valor são
// cópias empilhadas, e se uma metade reproduz a leitura completa é um número
// único com o último dígito ainda "crescendo".
constexpr double kBandSuspectPitch = 0.56;
constexpr double kBandHeightFraction = 0.55;
constexpr double kBandMinConfidence = 0.90;
constexpr int kBandPadding = 4;

constexpr int kMaxReuse = 2;
constexpr long kMemoLifetimeFrames = 3;

} // namespace

AnalysisResult analyze_video(
    const std::string& video_path,
    double start_time,
    double end_time,
    const AnalyzerConfig& config
) {
    const ResolvedPaths paths = resolve_paths(config);

    VideoReader video(video_path);

    AnalysisResult result;

    result.fps = video.fps();
    result.frame_count = video.frame_count();
    result.duration = video.duration();

    const bool has_end = end_time > 0.0 && end_time > start_time;
    const int stride = std::max(1, config.frame_stride);

    FrameProcessor frame_processor;
    DamageDetector damage_detector;
    CandidateFilter candidate_filter(
        config.exclusion_zones,
        config.limits
    );
    TemporalFilter temporal_filter;
    DamageOCR ocr(paths.model, paths.dictionary);

    EventTracker::Params tracker_params;
    tracker_params.min_observations =
        std::max(1, config.min_observations);

    // Ao pular frames, o intervalo entre leituras cresce.
    const double frame_interval =
        result.fps > 0.0 ? 1.0 / result.fps : 1.0 / 30.0;

    tracker_params.max_gap = std::max(
        config.track_max_gap,
        2.5 * stride * frame_interval
    );

    EventTracker tracker(tracker_params);

    // O seek nem sempre é exato (ou é ignorado por alguns backends), então
    // os frames anteriores ao início são descartados pelo timestamp.
    video.seek(start_time);

    const double start_tolerance = 0.5 * frame_interval;

    cv::Mat frame;
    bool first_frame = true;
    long frame_index = 0;

    // Tempo gasto em cada etapa (só é impresso com verbose).
    using Clock = std::chrono::steady_clock;
    Clock::time_point mark = Clock::now();
    double t_grab = 0.0, t_retrieve = 0.0, t_process = 0.0, t_detect = 0.0;
    double t_filter = 0.0, t_ocr = 0.0, t_track = 0.0;
    long skipped_static_hud = 0;
    long reused_ocr = 0;
    long bloom_frames = 0;
    long extra_warm = 0;
    long extra_outline = 0;
    long fill_bins[5] = {0, 0, 0, 0, 0};

    double bloom_fraction = config.bloom_fraction;
    if (const char* env = std::getenv("DAMAGE_ANALYZER_BLOOM_FRACTION")) {
        bloom_fraction = std::atof(env);
    }

    // Threads usadas para rodar vários OCRs de um mesmo frame ao mesmo tempo.
    unsigned ocr_workers = config.ocr_threads > 0
        ? static_cast<unsigned>(config.ocr_threads)
        : std::min(4u, std::max(1u, std::thread::hardware_concurrency()));
    if (const char* env = std::getenv("DAMAGE_ANALYZER_OCR_THREADS")) {
        ocr_workers = static_cast<unsigned>(std::max(1, std::atoi(env)));
    }

    long rejected_digit_width = 0;
    long band_checks = 0;
    long band_stacked = 0;
    long band_verified = 0;

    const bool reuse_enabled =
        std::getenv("DAMAGE_ANALYZER_NO_OCR_REUSE") == nullptr;
    std::vector<OcrMemo> memos;
    long analyzed_index = 0;

    // Diagnóstico opcional: DAMAGE_ANALYZER_DUMP_OCR=<arquivo.csv> grava uma
    // linha por chamada de OCR (posição, forma e resultado).
    std::ofstream dump;
    if (const char* dump_path = std::getenv("DAMAGE_ANALYZER_DUMP_OCR")) {
        dump.open(dump_path);
        dump << "t,x,y,w,h,aspect,fill,outcome,value,conf\n";
    }
    const auto lap = [&](double& accumulator) {
        const Clock::time_point now = Clock::now();
        accumulator += std::chrono::duration<double>(now - mark).count();
        mark = now;
    };

    for (;;) {
        mark = Clock::now();

        if (!video.grab()) {
            break;
        }

        lap(t_grab);

        if (config.cancel_token && config.cancel_token->is_cancelled()) {
            result.cancelled = true;
            break;
        }

        const double current_time = video.position();

        if (has_end && current_time >= end_time) {
            break;
        }

        if (current_time < start_time - start_tolerance) {
            continue;
        }

        const bool analyze = (frame_index % stride) == 0;
        ++frame_index;

        if (first_frame) {
            result.first_timestamp = current_time;
            first_frame = false;
        }

        result.last_timestamp = current_time;
        ++result.frames_read;

        if (!analyze || !video.retrieve(frame) || frame.empty()) {
            continue;
        }

        lap(t_retrieve);

        result.frame_width = frame.cols;
        result.frame_height = frame.rows;
        ++result.frames_analyzed;

        tracker.begin_frame(current_time);

        ++analyzed_index;
        memos.erase(
            std::remove_if(
                memos.begin(),
                memos.end(),
                [&](const OcrMemo& m) {
                    return analyzed_index - m.last_frame > kMemoLifetimeFrames;
                }
            ),
            memos.end()
        );
        for (OcrMemo& m : memos) {
            m.used = false;
        }

        const ProcessedFrame processed =
            frame_processor.process(frame, current_time);

        lap(t_process);

        std::vector<DetectionCandidate> candidates =
            damage_detector.detect(processed.candidate_mask);

        // Frames de explosão: a máscara principal vira uma mancha só.
        const double mask_fill =
            processed.candidate_mask.empty()
                ? 0.0
                : double(cv::countNonZero(processed.candidate_mask)) /
                      double(processed.candidate_mask.total());

        ++fill_bins[
            mask_fill < 0.05 ? 0 :
            mask_fill < 0.12 ? 1 :
            mask_fill < 0.20 ? 2 :
            mask_fill < 0.40 ? 3 : 4
        ];

        if (bloom_fraction > 0.0 && mask_fill >= bloom_fraction) {
            ++bloom_frames;

            // Só candidatos com formato plausível contam como "já cobertos":
            // a mancha gigante da máscara principal não pode esconder os
            // números que a máscara de cor quente separa.
            std::vector<DetectionCandidate> existing;
            for (const DetectionCandidate& c : candidates) {
                if (candidate_filter.has_plausible_geometry(
                        c, frame.cols, frame.rows)) {
                    existing.push_back(c);
                }
            }

            // 1. Só cor quente (amarelo/laranja): separa os números do fundo
            //    branco/rosa que a máscara principal junta a eles.
            cv::Mat warm;
            cv::inRange(
                processed.hsv,
                cv::Scalar(5, 55, 120),
                cv::Scalar(45, 255, 255),
                warm
            );
            cv::morphologyEx(
                warm,
                warm,
                cv::MORPH_OPEN,
                cv::getStructuringElement(cv::MORPH_RECT, cv::Size(2, 2))
            );

            for (const DetectionCandidate& extra :
                 damage_detector.detect(warm)) {
                if (candidate_filter.has_plausible_geometry(
                        extra, frame.cols, frame.rows) &&
                    !mostly_covered(extra, existing)) {
                    candidates.push_back(extra);
                    existing.push_back(extra);
                    ++extra_warm;
                }
            }

            // 2. Contorno escuro (a cada N frames: o número dura bem mais).
            if (mask_fill >= kOutlineMinFill &&
                analyzed_index % kOutlineEveryNthFrame == 0) {
                for (const DetectionCandidate& extra :
                     outline_candidates(frame, damage_detector)) {
                    if (candidate_filter.has_plausible_geometry(
                            extra, frame.cols, frame.rows) &&
                        !mostly_covered(extra, existing)) {
                        candidates.push_back(extra);
                        existing.push_back(extra);
                        ++extra_outline;
                    }
                }
            }
        }

        lap(t_detect);

        std::vector<PendingOcr> pending;

        for (const DetectionCandidate& candidate : candidates) {
            ++result.candidates_detected;

            // 1. Ignora elementos fixos do HUD.
            if (candidate_filter.is_excluded(
                    candidate, frame.cols, frame.rows)) {
                ++result.candidates_rejected_hud;
                lap(t_filter);
                continue;
            }

            // 2. Ignora formas que não parecem número de dano.
            if (!candidate_filter.has_plausible_geometry(
                    candidate, frame.cols, frame.rows)) {
                ++result.candidates_rejected_geometry;
                lap(t_filter);
                continue;
            }

            ++result.candidates_passed_filters;

            // 3. OCR no recorte colorido original.
            const cv::Rect crop = padded_crop(
                candidate,
                config.crop_padding,
                frame.cols,
                frame.rows
            );

            if (crop.area() <= 0) {
                lap(t_filter);
                continue;
            }

            // Contador da interface já conhecido: não precisa de OCR.
            if (tracker.is_known_static_hud(candidate)) {
                ++skipped_static_hud;
                lap(t_filter);
                continue;
            }

            // Procura uma leitura recente no mesmo lugar e com o mesmo tamanho.
            const double cand_cx = candidate.x + candidate.width / 2.0;
            const double cand_cy = candidate.y + candidate.height / 2.0;
            int memo_index = -1;

            if (reuse_enabled) {
                for (std::size_t i = 0; i < memos.size(); ++i) {
                    const OcrMemo& m = memos[i];

                    if (m.used) {
                        continue;
                    }
                    if (std::hypot(cand_cx - m.cx, cand_cy - m.cy) >
                        0.35 * std::max(m.h, double(candidate.height))) {
                        continue;
                    }
                    if (std::abs(candidate.width - m.w) > 0.12 * m.w + 2.0 ||
                        std::abs(candidate.height - m.h) > 0.12 * m.h + 2.0) {
                        continue;
                    }

                    memo_index = static_cast<int>(i);
                    break;
                }
            }

            if (memo_index >= 0) {
                OcrMemo& m = memos[memo_index];

                if (m.streak >= 2 && m.skips < kMaxReuse) {
                    m.used = true;
                    ++m.skips;
                    m.last_frame = analyzed_index;
                    m.cx = cand_cx;
                    m.cy = cand_cy;
                    m.w = candidate.width;
                    m.h = candidate.height;
                    ++reused_ocr;

                    if (m.accepted) {
                        DamageObservation reused;
                        reused.timestamp = current_time;
                        reused.value = m.value;
                        reused.confidence = m.confidence;
                        reused.color_score = mask_fill_ratio(
                            processed.candidate_mask, candidate);
                        reused.box = candidate;

                        tracker.observe(reused);
                    }

                    lap(t_track);
                    continue;
                }
            }

            lap(t_filter);

            ++result.ocr_calls;

            if (memo_index >= 0) {
                memos[memo_index].used = true;
            }

            pending.push_back({candidate, crop, memo_index});
        }

        // Fase B: OCR de todos os candidatos pendentes do frame, em paralelo
        // quando há mais de um (a sessão do ONNX Runtime é thread-safe).
        std::vector<std::vector<OCRResult>> outputs(pending.size());

        if (!pending.empty()) {
            std::exception_ptr failure;
            std::mutex failure_mutex;

            const auto run_one = [&](std::size_t index) {
                try {
                    outputs[index] =
                        ocr.recognize(frame(pending[index].crop));
                } catch (...) {
                    std::lock_guard<std::mutex> lock(failure_mutex);
                    if (!failure) {
                        failure = std::current_exception();
                    }
                }
            };

            const std::size_t count = pending.size();
            const std::size_t workers =
                std::min<std::size_t>(ocr_workers, count);

            if (workers <= 1) {
                for (std::size_t index = 0; index < count; ++index) {
                    run_one(index);
                }
            } else {
                std::atomic<std::size_t> next{0};
                const auto work = [&]() {
                    for (;;) {
                        const std::size_t index = next.fetch_add(1);
                        if (index >= count) {
                            break;
                        }
                        run_one(index);
                    }
                };

                std::vector<std::thread> threads;
                threads.reserve(workers - 1);
                for (std::size_t w = 1; w < workers; ++w) {
                    threads.emplace_back(work);
                }
                work();
                for (std::thread& thread : threads) {
                    thread.join();
                }
            }

            if (failure) {
                std::rethrow_exception(failure);
            }
        }

        lap(t_ocr);

        // Fase C: aplica os resultados na ordem original dos candidatos.
        for (std::size_t p = 0; p < pending.size(); ++p) {
            const DetectionCandidate& candidate = pending[p].candidate;
            int memo_index = pending[p].memo_index;
            const double cand_cx = candidate.x + candidate.width / 2.0;
            const double cand_cy = candidate.y + candidate.height / 2.0;
            const std::vector<OCRResult>& readings = outputs[p];

            // Guarda o resultado desta leitura (aceita ou rejeitada).
            const auto remember = [&](bool accepted, int value, double conf) {
                if (!reuse_enabled) {
                    return;
                }

                if (memo_index < 0) {
                    OcrMemo created;
                    created.streak = 1;
                    memos.push_back(created);
                    memo_index = static_cast<int>(memos.size()) - 1;
                } else {
                    const OcrMemo& previous = memos[memo_index];
                    const bool same =
                        previous.accepted == accepted &&
                        (!accepted || previous.value == value);
                    memos[memo_index].streak = same ? previous.streak + 1 : 1;
                }

                OcrMemo& m = memos[memo_index];
                m.accepted = accepted;
                m.value = value;
                m.confidence = conf;
                m.skips = 0;
                m.used = true;
                m.last_frame = analyzed_index;
                m.cx = cand_cx;
                m.cy = cand_cy;
                m.w = candidate.width;
                m.h = candidate.height;
            };

            // outcome: 0 sem número, 1 confiança baixa, 2 abaixo do mínimo,
            // 3 contagem regressiva, 4 aceita.
            const auto log_ocr = [&](int outcome, int value, double conf) {
                if (!dump.is_open()) {
                    return;
                }
                dump << current_time << ',' << candidate.x << ','
                     << candidate.y << ',' << candidate.width << ','
                     << candidate.height << ','
                     << double(candidate.width) / candidate.height << ','
                     << mask_fill_ratio(processed.candidate_mask, candidate)
                     << ',' << outcome << ',' << value << ',' << conf << '\n';
            };

            if (readings.empty()) {
                ++result.ocr_no_numeric_result;
                log_ocr(0, 0, 0.0);
                remember(false, 0, 0.0);
                continue;
            }

            const OCRResult& reading = readings.front();

            if (reading.confidence < config.min_confidence) {
                ++result.ocr_rejected_confidence;
                log_ocr(1, reading.value, reading.confidence);
                remember(false, 0, 0.0);
                continue;
            }

            // Número de 7+ dígitos muito estreito: são números sobrepostos
            // lidos como um só (cada dígito ocupa ~0,6 da altura).
            const int digit_count =
                static_cast<int>(std::to_string(reading.value).size());
            if (digit_count >= 7 &&
                double(candidate.width) / std::max(1, candidate.height) /
                        digit_count < 0.55) {
                ++rejected_digit_width;
                log_ocr(1, reading.value, reading.confidence);
                remember(false, 0, 0.0);
                continue;
            }

            // 4. Contagens regressivas da interface (6, 5, 4...).
            if (temporal_filter.should_ignore(
                    candidate,
                    reading.value,
                    current_time,
                    frame.cols,
                    frame.rows)) {
                ++result.ocr_ignored_countdown;
                tracker.discard_near(candidate);
                log_ocr(3, reading.value, reading.confidence);
                remember(false, 0, 0.0);
                continue;
            }

            if (reading.value < config.min_damage) {
                ++result.ocr_below_min_damage;
                log_ocr(2, reading.value, reading.confidence);
                remember(false, 0, 0.0);
                continue;
            }

            int final_value = reading.value;
            double final_confidence = reading.confidence;
            bool stacked = false;
            bool verified = false;

            const int accepted_digits =
                static_cast<int>(std::to_string(reading.value).size());
            if (accepted_digits >= 3 &&
                double(candidate.width) / std::max(1, candidate.height) /
                        accepted_digits < kBandSuspectPitch) {
                ++band_checks;

                const int band_height = std::max(
                    1, static_cast<int>(candidate.height * kBandHeightFraction)
                );
                const cv::Rect bounds(0, 0, frame.cols, frame.rows);
                const cv::Rect top_rect = bounds & cv::Rect(
                    candidate.x - kBandPadding,
                    candidate.y - kBandPadding,
                    candidate.width + 2 * kBandPadding,
                    band_height + kBandPadding + 2
                );
                const cv::Rect bottom_rect = bounds & cv::Rect(
                    candidate.x - kBandPadding,
                    candidate.y + candidate.height - band_height - 2,
                    candidate.width + 2 * kBandPadding,
                    band_height + kBandPadding + 2
                );

                const auto read_band = [&](const cv::Rect& rect,
                                           OCRResult& out) {
                    if (rect.width < 8 || rect.height < 8) {
                        return false;
                    }
                    const std::vector<OCRResult> band =
                        ocr.recognize(frame(rect));
                    if (band.empty() ||
                        band.front().confidence < kBandMinConfidence ||
                        band.front().value < config.min_damage) {
                        return false;
                    }
                    out = band.front();
                    return true;
                };

                OCRResult top;
                OCRResult bottom;
                const bool has_top = read_band(top_rect, top);
                const bool has_bottom = read_band(bottom_rect, bottom);

                if ((has_top && top.value == reading.value) ||
                    (has_bottom && bottom.value == reading.value)) {
                    verified = true;
                    ++band_verified;
                } else if (has_top && has_bottom &&
                           top.value == bottom.value &&
                           std::to_string(top.value).size() >= 3) {
                    stacked = true;
                    final_value = top.value;
                    final_confidence = std::min(top.confidence,
                                                bottom.confidence);
                    ++band_stacked;
                }
            }

            log_ocr(4, final_value, final_confidence);
            remember(true, final_value, final_confidence);

            DamageObservation observation;
            observation.timestamp = current_time;
            observation.value = final_value;
            observation.confidence = final_confidence;
            observation.stacked = stacked;
            observation.verified = verified;
            observation.color_score =
                mask_fill_ratio(processed.candidate_mask, candidate);
            observation.box = candidate;

            tracker.observe(observation);
        }

        lap(t_track);
    }

    result.events = tracker.finish();

    for (const DamageEvent& event : result.events) {
        result.total_damage += event.damage;
        result.peak_damage = std::max(result.peak_damage, event.damage);
        if (event.stacked) {
            ++result.stacked_hits;
        }
        if (!event.confirmed) {
            ++result.unconfirmed_hits;
            result.unconfirmed_damage += event.damage;
        }
    }

    result.total_hits = static_cast<int>(result.events.size());

    result.average_damage =
        result.total_hits > 0
            ? result.total_damage / result.total_hits
            : 0.0;

    if (config.verbose) {
        std::cout
            << "Frames read/analyzed: " << result.frames_read
            << "/" << result.frames_analyzed << '\n'
            << "Candidates: " << result.candidates_detected
            << " (HUD: " << result.candidates_rejected_hud
            << ", geometry: " << result.candidates_rejected_geometry
            << ", passed filters: " << result.candidates_passed_filters
            << ")\n"
            << "OCR calls: " << result.ocr_calls
            << " (no numeric result: " << result.ocr_no_numeric_result
            << ", low confidence: " << result.ocr_rejected_confidence
            << ", countdown: " << result.ocr_ignored_countdown
            << ", below min damage: " << result.ocr_below_min_damage
            << ")\n"
            << "Mask fill bins (<5%, 5-12%, 12-20%, 20-40%, >40%): "
            << fill_bins[0] << ", " << fill_bins[1] << ", " << fill_bins[2]
            << ", " << fill_bins[3] << ", " << fill_bins[4]
            << "  bloom frames: " << bloom_frames
            << " (extra warm: " << extra_warm
            << ", extra outline: " << extra_outline << ")\n"
            << "Rejected 7+ digit readings too narrow: "
            << rejected_digit_width << '\n'
            << "OCR skipped (known static HUD): " << skipped_static_hud
            << ", reused from memory: " << reused_ocr << '\n'
            << "Time (s): grab " << t_grab
            << ", retrieve " << t_retrieve
            << ", preprocess " << t_process
            << ", detect " << t_detect
            << ", filters " << t_filter
            << ", OCR " << t_ocr
            << ", tracker " << t_track << '\n'
            << "Hits: " << result.total_hits
            << "  Total: " << result.total_damage
            << "  Peak: " << result.peak_damage << '\n'
            << "Band checks: " << band_checks << " (stacked "
            << band_stacked << ", verified " << band_verified << ")\n"
            << "Stacked events: " << result.stacked_hits << '\n'
            << "Unconfirmed (overlap-like or doubtful): " << result.unconfirmed_hits
            << "  damage: " << result.unconfirmed_damage
            << std::endl;
    }

    return result;
}

} // namespace damage_analyzer
