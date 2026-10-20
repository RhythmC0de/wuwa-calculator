#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <memory>

#include "candidate_filter.hpp"
#include "platform.hpp"

#include "analyzer.hpp"
#include "event_crop.hpp"

// [OPTIONAL DIAGNOSTICS]
// These three headers are only needed by the diagnostic Python exports
// at the bottom of this file. See CLEANUP_GUIDE.md before removing them.
#include "ocr_model_info.hpp"
#include "ocr_inference_test.hpp"
#include "damage_ocr_test.hpp"

namespace py = pybind11;

PYBIND11_MODULE(damage_analyzer, m) {
    m.doc() = "Wuthering Waves damage analyzer";
    // Nível da API Python. O aplicativo exige >= 3 (AnalyzerConfig,
    // CancelToken, estatísticas e extract_event_crops).
    m.attr("API_LEVEL") = 3;

    py::class_<damage_analyzer::DamageEvent>(m, "DamageEvent")
        .def_readonly("timestamp",
                      &damage_analyzer::DamageEvent::timestamp)
        .def_readonly("damage",
                      &damage_analyzer::DamageEvent::damage)
        .def_readonly("center_x",
                      &damage_analyzer::DamageEvent::center_x)
        .def_readonly("center_y",
                      &damage_analyzer::DamageEvent::center_y)
        .def_readonly("width",
                      &damage_analyzer::DamageEvent::width)
        .def_readonly("height",
                      &damage_analyzer::DamageEvent::height)
        .def_readonly("color_score",
                      &damage_analyzer::DamageEvent::color_score)
        .def_readonly("observations",
                      &damage_analyzer::DamageEvent::observations)
        .def_readonly("digit_pitch",
                      &damage_analyzer::DamageEvent::digit_pitch)
        .def_readonly("repeats",
                      &damage_analyzer::DamageEvent::repeats)
        .def_readonly("confirmed",
                      &damage_analyzer::DamageEvent::confirmed)
        .def_readonly("stacked",
                      &damage_analyzer::DamageEvent::stacked)
        .def_readonly("verified",
                      &damage_analyzer::DamageEvent::verified);

    py::class_<damage_analyzer::AnalysisResult>(m, "AnalysisResult")
    .def_readonly(
        "events",
        &damage_analyzer::AnalysisResult::events
    )
    .def_readonly(
        "total_damage",
        &damage_analyzer::AnalysisResult::total_damage
    )
    .def_readonly(
        "average_damage",
        &damage_analyzer::AnalysisResult::average_damage
    )
    .def_readonly(
        "total_hits",
        &damage_analyzer::AnalysisResult::total_hits
    )
    .def_readonly(
        "peak_damage",
        &damage_analyzer::AnalysisResult::peak_damage
    )
    .def_readonly(
        "stacked_hits",
        &damage_analyzer::AnalysisResult::stacked_hits
    )
    .def_readonly(
        "unconfirmed_hits",
        &damage_analyzer::AnalysisResult::unconfirmed_hits
    )
    .def_readonly(
        "unconfirmed_damage",
        &damage_analyzer::AnalysisResult::unconfirmed_damage
    )
    .def_readonly(
        "fps",
        &damage_analyzer::AnalysisResult::fps
    )
    .def_readonly(
        "frame_count",
        &damage_analyzer::AnalysisResult::frame_count
    )
    .def_readonly(
        "duration",
        &damage_analyzer::AnalysisResult::duration
    )
    .def_readonly(
        "frames_read",
        &damage_analyzer::AnalysisResult::frames_read
    )
    .def_readonly(
        "first_timestamp",
        &damage_analyzer::AnalysisResult::first_timestamp
    )
    .def_readonly(
        "last_timestamp",
        &damage_analyzer::AnalysisResult::last_timestamp
    )
    .def_readonly(
        "frame_width",
        &damage_analyzer::AnalysisResult::frame_width
    )
    .def_readonly(
        "frame_height",
        &damage_analyzer::AnalysisResult::frame_height
    )
    .def_readonly("frames_analyzed",
        &damage_analyzer::AnalysisResult::frames_analyzed)
    .def_readonly("candidates_detected",
        &damage_analyzer::AnalysisResult::candidates_detected)
    .def_readonly("candidates_rejected_hud",
        &damage_analyzer::AnalysisResult::candidates_rejected_hud)
    .def_readonly("candidates_rejected_geometry",
        &damage_analyzer::AnalysisResult::candidates_rejected_geometry)
    .def_readonly("candidates_passed_filters",
        &damage_analyzer::AnalysisResult::candidates_passed_filters)
    .def_readonly("ocr_calls",
        &damage_analyzer::AnalysisResult::ocr_calls)
    .def_readonly("ocr_no_numeric_result",
        &damage_analyzer::AnalysisResult::ocr_no_numeric_result)
    .def_readonly("ocr_rejected_confidence",
        &damage_analyzer::AnalysisResult::ocr_rejected_confidence)
    .def_readonly("ocr_ignored_countdown",
        &damage_analyzer::AnalysisResult::ocr_ignored_countdown)
    .def_readonly("ocr_below_min_damage",
        &damage_analyzer::AnalysisResult::ocr_below_min_damage)
    .def_readonly("cancelled",
        &damage_analyzer::AnalysisResult::cancelled);

    py::class_<damage_analyzer::ExclusionZone>(m, "ExclusionZone")
        .def(py::init<>())
        .def(
            py::init([](double left, double top,
                        double right, double bottom) {
                return damage_analyzer::ExclusionZone{
                    left, top, right, bottom};
            }),
            py::arg("left"), py::arg("top"),
            py::arg("right"), py::arg("bottom")
        )
        .def_readwrite("left", &damage_analyzer::ExclusionZone::left)
        .def_readwrite("top", &damage_analyzer::ExclusionZone::top)
        .def_readwrite("right", &damage_analyzer::ExclusionZone::right)
        .def_readwrite("bottom", &damage_analyzer::ExclusionZone::bottom)
        .def("__repr__", [](const damage_analyzer::ExclusionZone& z) {
            return "ExclusionZone(left=" + std::to_string(z.left) +
                   ", top=" + std::to_string(z.top) +
                   ", right=" + std::to_string(z.right) +
                   ", bottom=" + std::to_string(z.bottom) + ")";
        });

    py::class_<damage_analyzer::CandidateLimits>(m, "CandidateLimits")
        .def(py::init<>())
        .def_readwrite("min_height",
            &damage_analyzer::CandidateLimits::min_height)
        .def_readwrite("max_height",
            &damage_analyzer::CandidateLimits::max_height)
        .def_readwrite("min_aspect",
            &damage_analyzer::CandidateLimits::min_aspect)
        .def_readwrite("max_aspect",
            &damage_analyzer::CandidateLimits::max_aspect);

    py::class_<damage_analyzer::CancelToken,
               std::shared_ptr<damage_analyzer::CancelToken>>(m, "CancelToken")
        .def(py::init<>())
        .def("cancel", &damage_analyzer::CancelToken::cancel,
             "Request cancellation (thread-safe)")
        .def("is_cancelled", &damage_analyzer::CancelToken::is_cancelled);

    py::class_<damage_analyzer::AnalyzerConfig>(m, "AnalyzerConfig")
        .def(py::init<>())
        .def_readwrite("model_path",
            &damage_analyzer::AnalyzerConfig::model_path)
        .def_readwrite("dictionary_path",
            &damage_analyzer::AnalyzerConfig::dictionary_path)
        .def_readwrite("exclusion_zones",
            &damage_analyzer::AnalyzerConfig::exclusion_zones)
        .def_readwrite("limits",
            &damage_analyzer::AnalyzerConfig::limits)
        .def_readwrite("frame_stride",
            &damage_analyzer::AnalyzerConfig::frame_stride)
        .def_readwrite("min_confidence",
            &damage_analyzer::AnalyzerConfig::min_confidence)
        .def_readwrite("min_damage",
            &damage_analyzer::AnalyzerConfig::min_damage)
        .def_readwrite("min_observations",
            &damage_analyzer::AnalyzerConfig::min_observations)
        .def_readwrite("track_max_gap",
            &damage_analyzer::AnalyzerConfig::track_max_gap)
        .def_readwrite("crop_padding",
            &damage_analyzer::AnalyzerConfig::crop_padding)
        .def_readwrite("cancel_token",
            &damage_analyzer::AnalyzerConfig::cancel_token)
        .def_readwrite("bloom_fraction",
            &damage_analyzer::AnalyzerConfig::bloom_fraction)
        .def_readwrite("ocr_threads",
            &damage_analyzer::AnalyzerConfig::ocr_threads)
        .def_readwrite("verbose",
            &damage_analyzer::AnalyzerConfig::verbose);

    m.def(
        "default_exclusion_zones",
        &damage_analyzer::default_exclusion_zones,
        "Default HUD exclusion zones (normalized 0..1 coordinates)"
    );

    m.def(
        "find_models_directory",
        []() {
            return damage_analyzer::to_utf8(
                damage_analyzer::find_models_directory());
        },
        "Directory where the OCR model and dictionary were found"
    );

    m.def(
        "analyze_video",
        [](const std::string& video_path,
           double start_time,
           double end_time,
           const damage_analyzer::AnalyzerConfig& config) {
            // Solta o GIL: a análise é longa e não toca em objetos Python.
            py::gil_scoped_release release;

            return damage_analyzer::analyze_video(
                video_path, start_time, end_time, config);
        },
        py::arg("video_path"),
        py::arg("start_time") = 0.0,
        py::arg("end_time") = -1.0,
        py::arg("config") = damage_analyzer::AnalyzerConfig{},
        "Analyze a video and extract damage events. "
        "end_time <= 0 analyzes until the end of the video."
    );

    m.def(
        "extract_event_crops",
        [](const std::string& video_path,
           const std::vector<damage_analyzer::DamageEvent>& events,
           double padding,
           const std::vector<double>& offsets,
           int min_height) {
            std::vector<damage_analyzer::CropRequest> requests;
            requests.reserve(events.size());
            for (const auto& e : events) {
                damage_analyzer::CropRequest r;
                r.timestamp = e.timestamp;
                r.center_x = e.center_x;
                r.center_y = e.center_y;
                r.width = e.width;
                r.height = e.height;
                requests.push_back(r);
            }

            damage_analyzer::CropOptions options;
            options.padding = padding;
            options.offsets = offsets;
            options.min_height = min_height;

            std::vector<damage_analyzer::CropImages> crops;
            {
                py::gil_scoped_release release;
                crops = damage_analyzer::extract_event_crops(
                    video_path, requests, options);
            }

            // list[list[bytes]]: um PNG por evento e por instante
            // (bytes vazio quando o frame não pôde ser lido).
            py::list result;
            for (const auto& per_event : crops) {
                py::list images;
                for (const auto& png : per_event) {
                    images.append(py::bytes(
                        reinterpret_cast<const char*>(png.data()),
                        png.size()));
                }
                result.append(std::move(images));
            }
            return result;
        },
        py::arg("video_path"),
        py::arg("events"),
        py::arg("padding") = 0.6,
        py::arg("offsets") = std::vector<double>{0.0},
        py::arg("min_height") = 96,
        "PNG crops of each event, one per time offset (seconds relative "
        "to the event timestamp). Used by the review screen and to save "
        "training examples."
    );

    // [OPTIONAL DIAGNOSTICS] May be removed together with the matching
    // .cpp/.hpp files and CMake entries; see CLEANUP_GUIDE.md.
    m.def(
        "inspect_ocr_model",
        &damage_analyzer::OCRModelInfo::inspect,
        py::arg("model_path"),
        "Inspect an OCR model and print its input/output information"
    );

    m.def(
        "run_ocr_inference_test",
        &damage_analyzer::OCRInferenceTest::run,
        py::arg("model_path"),
        "Run a simple OCR inference test with a synthetic input"
    );

    m.def(
        "run_ocr_inference_test_with_image",
        &damage_analyzer::OCRInferenceTest::run_image,
        py::arg("model_path"),
        py::arg("image_path"),
        "Run an OCR inference test with a specific image"
    );

    m.def(
    "test_damage_ocr",
    &damage_analyzer::DamageOCRTest::run,
    py::arg("model_path"),
    py::arg("dictionary_path"),
    py::arg("image_path"),
    "Test the DamageOCR pipeline"
    );
}
