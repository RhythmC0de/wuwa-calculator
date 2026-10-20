#include "ocr_model_info.hpp"

#include <iostream>
#include <memory>

#include <onnxruntime_cxx_api.h>

#include "ort_utils.hpp"

namespace damage_analyzer {

void OCRModelInfo::inspect(const std::string& model_path) {
    Ort::Env env(
        ORT_LOGGING_LEVEL_WARNING,
        "WuwaDamageLabModelInspector"
    );

    Ort::SessionOptions options;

    options.SetIntraOpNumThreads(1);
    options.SetGraphOptimizationLevel(
        GraphOptimizationLevel::ORT_ENABLE_ALL
    );

    const auto session_ptr =
        make_ort_session(env, options, model_path);

    Ort::Session& session = *session_ptr;

    Ort::AllocatorWithDefaultOptions allocator;

    const std::size_t input_count =
        session.GetInputCount();

    const std::size_t output_count =
        session.GetOutputCount();

    std::cout << "=== OCR MODEL ===\n";
    std::cout << "Model: " << model_path << '\n';

    std::cout << "\nInputs: "
              << input_count << '\n';

    for (std::size_t i = 0; i < input_count; ++i) {
        auto name = session.GetInputNameAllocated(
            i,
            allocator
        );

        auto type_info =
            session.GetInputTypeInfo(i);

        auto tensor_info =
            type_info.GetTensorTypeAndShapeInfo();

        const auto shape =
            tensor_info.GetShape();

        std::cout << "\nInput #" << i << '\n';
        std::cout << "Name: "
                  << name.get()
                  << '\n';

        std::cout << "Type: "
                  << tensor_info.GetElementType()
                  << '\n';

        std::cout << "Shape: ";

        for (const auto dimension : shape) {
            std::cout << dimension << ' ';
        }

        std::cout << '\n';
    }

    std::cout << "\nOutputs: "
              << output_count << '\n';

    for (std::size_t i = 0; i < output_count; ++i) {
        auto name = session.GetOutputNameAllocated(
            i,
            allocator
        );

        auto type_info =
            session.GetOutputTypeInfo(i);

        auto tensor_info =
            type_info.GetTensorTypeAndShapeInfo();

        const auto shape =
            tensor_info.GetShape();

        std::cout << "\nOutput #" << i << '\n';
        std::cout << "Name: "
                  << name.get()
                  << '\n';

        std::cout << "Type: "
                  << tensor_info.GetElementType()
                  << '\n';

        std::cout << "Shape: ";

        for (const auto dimension : shape) {
            std::cout << dimension << ' ';
        }

        std::cout << '\n';
    }

    std::cout << "\n=== END ===\n";
}

} // namespace damage_analyzer