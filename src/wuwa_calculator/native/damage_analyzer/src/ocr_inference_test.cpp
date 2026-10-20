#include "ocr_inference_test.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>

#include <onnxruntime_cxx_api.h>

#include "ort_utils.hpp"
#include "platform.hpp"

namespace damage_analyzer
{

    void OCRInferenceTest::run(const std::string &model_path)
    {
        Ort::Env env(
            ORT_LOGGING_LEVEL_WARNING,
            "WuwaDamageLabOCRTest");

        Ort::SessionOptions options;

        options.SetIntraOpNumThreads(1);
        options.SetGraphOptimizationLevel(
            GraphOptimizationLevel::ORT_ENABLE_ALL);

        const auto session_ptr =
            make_ort_session(env, options, model_path);

        Ort::Session &session = *session_ptr;

        Ort::AllocatorWithDefaultOptions allocator;

        // Test image.
        //
        // The model accepts:
        // [batch, channels, height, width]
        //
        // We start with a common recognition height of 48.
        // Width is dynamic.
        constexpr int batch = 1;
        constexpr int channels = 3;
        constexpr int height = 48;
        constexpr int width = 160;

        const std::size_t input_size =
            static_cast<std::size_t>(
                batch *
                channels *
                height *
                width);

        std::vector<float> input_data(input_size, 0.0f);

        // Simple synthetic pattern.
        //
        // This is NOT intended to produce meaningful OCR.
        // It only verifies that inference and output decoding
        // behave as expected.
        for (int c = 0; c < channels; ++c)
        {
            for (int y = 0; y < height; ++y)
            {
                for (int x = 0; x < width; ++x)
                {
                    const std::size_t index =
                        static_cast<std::size_t>(
                            c * height * width +
                            y * width +
                            x);

                    input_data[index] =
                        static_cast<float>(x) /
                        static_cast<float>(width);
                }
            }
        }

        const std::array<std::int64_t, 4> input_shape = {
            batch,
            channels,
            height,
            width};

        Ort::MemoryInfo memory_info =
            Ort::MemoryInfo::CreateCpu(
                OrtArenaAllocator,
                OrtMemTypeDefault);

        Ort::Value input_tensor =
            Ort::Value::CreateTensor<float>(
                memory_info,
                input_data.data(),
                input_data.size(),
                input_shape.data(),
                input_shape.size());

        auto input_name =
            session.GetInputNameAllocated(
                0,
                allocator);

        auto output_name =
            session.GetOutputNameAllocated(
                0,
                allocator);

        const char *input_names[] = {
            input_name.get()};

        const char *output_names[] = {
            output_name.get()};

        std::cout << "=== OCR INFERENCE TEST ===\n";

        std::cout
            << "Input shape: ["
            << batch << ", "
            << channels << ", "
            << height << ", "
            << width << "]\n";

        std::cout
            << "Input elements: "
            << input_size
            << '\n';

        auto outputs = session.Run(
            Ort::RunOptions{nullptr},
            input_names,
            &input_tensor,
            1,
            output_names,
            1);

        if (outputs.empty())
        {
            std::cerr << "No output returned.\n";
            return;
        }

        auto &output = outputs[0];

        auto tensor_info =
            output.GetTensorTypeAndShapeInfo();

        const auto output_shape =
            tensor_info.GetShape();

        std::cout << "Output shape: [";

        for (std::size_t i = 0; i < output_shape.size(); ++i)
        {
            if (i > 0)
            {
                std::cout << ", ";
            }

            std::cout << output_shape[i];
        }

        std::cout << "]\n";

        const float *output_data =
            output.GetTensorData<float>();

        std::size_t output_elements = 1;

        for (const auto dimension : output_shape)
        {
            output_elements *=
                static_cast<std::size_t>(dimension);
        }

        std::cout
            << "Output elements: "
            << output_elements
            << '\n';

        if (output_shape.size() != 3)
        {
            std::cerr
                << "Unexpected output rank. "
                << "Expected 3 dimensions.\n";

            return;
        }

        const std::size_t batch_size =
            static_cast<std::size_t>(output_shape[0]);

        const std::size_t timesteps =
            static_cast<std::size_t>(output_shape[1]);

        const std::size_t classes =
            static_cast<std::size_t>(output_shape[2]);

        std::cout
            << "Batch: "
            << batch_size
            << '\n';

        std::cout
            << "Timesteps: "
            << timesteps
            << '\n';

        std::cout
            << "Classes: "
            << classes
            << '\n';

        if (batch_size != 1)
        {
            std::cerr
                << "Unexpected batch size.\n";

            return;
        }

        std::cout << "\nDominant classes:\n";

        const std::size_t samples =
            std::min<std::size_t>(
                timesteps,
                30);

        for (std::size_t t = 0; t < samples; ++t)
        {
            const float *timestep =
                output_data +
                t * classes;

            std::size_t best_class = 0;
            float best_value =
                -std::numeric_limits<float>::infinity();

            for (std::size_t c = 0; c < classes; ++c)
            {
                if (timestep[c] > best_value)
                {
                    best_value = timestep[c];
                    best_class = c;
                }
            }

            std::cout
                << "t="
                << t
                << " class="
                << best_class
                << " value="
                << best_value
                << '\n';
        }

        std::cout << "\nFirst timestep logits:\n";

        const std::size_t logit_samples =
            std::min<std::size_t>(
                classes,
                20);

        for (std::size_t c = 0; c < logit_samples; ++c)
        {
            std::cout
                << "class "
                << c
                << ": "
                << output_data[c]
                << '\n';
        }
        std::cout << "\nDictionary/model mapping:\n";
        std::cout << "Dictionary entries: 436\n";
        std::cout << "Model classes: " << classes << '\n';
        std::cout << "Extra classes: "
                  << (classes - 436)
                  << '\n';

        if (classes == 438)
        {
            std::cout << "Expected character classes: 0..435\n";
            std::cout << "Extra model classes: 436, 437\n";
        }
        std::cout << "\n=== END ===\n";
    }

    void OCRInferenceTest::run_image(
        const std::string &model_path,
        const std::string &image_path
    ){
        
        constexpr int input_height = 48;
        constexpr int input_width = 320;
        constexpr int channels = 3;

        constexpr std::size_t dictionary_size = 436;
        constexpr std::size_t class_count = 438;

        // ---------------------------------------------------------
        // Load dictionary
        // ---------------------------------------------------------

        const std::filesystem::path models_dir =
            find_models_directory();

        std::ifstream dictionary_file(
            models_dir.empty()
                ? std::filesystem::path(
                      "models/ocr/ppocrv5_en_dict.txt")
                : models_dir / "ppocrv5_en_dict.txt");

        if (!dictionary_file.is_open())
        {
            throw std::runtime_error(
                "Could not open OCR dictionary.");
        }

        std::vector<std::string> characters;

        std::string line;

        while (std::getline(dictionary_file, line))
        {
            if (!line.empty() && line.back() == '\r')
            {
                line.pop_back();
            }

            characters.push_back(line);
        }

        if (characters.size() != dictionary_size)
        {
            throw std::runtime_error(
                "Unexpected OCR dictionary size: " +
                std::to_string(characters.size()));
        }

        // RapidOCR / PP-OCR CTC layout:
        //
        // 0       = blank
        // 1..436  = dictionary characters
        // 437     = space
        //
        std::vector<std::string> labels;

        labels.reserve(class_count);

        labels.emplace_back("<blank>");

        for (const auto &character : characters)
        {
            labels.push_back(character);
        }

        labels.emplace_back(" ");

        if (labels.size() != class_count)
        {
            throw std::runtime_error(
                "OCR label count does not match model.");
        }

        // ---------------------------------------------------------
        // Load image
        // ---------------------------------------------------------

        const cv::Mat image =
            read_image_utf8(image_path);

        if (image.empty())
        {
            throw std::runtime_error(
                "Could not open OCR test image: " +
                image_path);
        }

        if (image.cols <= 0 || image.rows <= 0)
        {
            throw std::runtime_error(
                "Invalid OCR test image dimensions.");
        }

        // ---------------------------------------------------------
        // Resize while preserving aspect ratio
        // ---------------------------------------------------------

        const double ratio =
            static_cast<double>(image.cols) /
            static_cast<double>(image.rows);

        int resized_width =
            static_cast<int>(
                std::ceil(
                    input_height * ratio));

        resized_width =
            std::clamp(
                resized_width,
                1,
                input_width);

        cv::Mat resized;

        cv::resize(
            image,
            resized,
            cv::Size(
                resized_width,
                input_height),
            0.0,
            0.0,
            cv::INTER_LINEAR);

        // ---------------------------------------------------------
        // Build CHW float tensor
        // ---------------------------------------------------------

        const std::size_t input_size =
            static_cast<std::size_t>(
                channels *
                input_height *
                input_width);

        std::vector<float> input_data(
            input_size,
            0.0f);

        for (int y = 0; y < input_height; ++y)
        {
            for (int x = 0; x < resized_width; ++x)
            {
                const cv::Vec3b pixel =
                    resized.at<cv::Vec3b>(y, x);

                for (int c = 0; c < channels; ++c)
                {
                    const std::size_t index =
                        static_cast<std::size_t>(
                            c *
                                input_height *
                                input_width +
                            y *
                                input_width +
                            x);

                    const float normalized =
                        static_cast<float>(
                            pixel[c]) /
                        255.0f;

                    input_data[index] =
                        (normalized - 0.5f) / 0.5f;
                }
            }
        }

        // ---------------------------------------------------------
        // ONNX Runtime
        // ---------------------------------------------------------

        Ort::Env env(
            ORT_LOGGING_LEVEL_WARNING,
            "WuwaDamageLabOCRImageTest");

        Ort::SessionOptions options;

        options.SetIntraOpNumThreads(1);

        options.SetGraphOptimizationLevel(
            GraphOptimizationLevel::ORT_ENABLE_ALL);

        const auto session_ptr =
            make_ort_session(env, options, model_path);

        Ort::Session &session = *session_ptr;

        Ort::AllocatorWithDefaultOptions allocator;

        auto input_name =
            session.GetInputNameAllocated(
                0,
                allocator);

        auto output_name =
            session.GetOutputNameAllocated(
                0,
                allocator);

        const std::array<std::int64_t, 4> input_shape = {
            1,
            channels,
            input_height,
            input_width};

        Ort::MemoryInfo memory_info =
            Ort::MemoryInfo::CreateCpu(
                OrtArenaAllocator,
                OrtMemTypeDefault);

        Ort::Value input_tensor =
            Ort::Value::CreateTensor<float>(
                memory_info,
                input_data.data(),
                input_data.size(),
                input_shape.data(),
                input_shape.size());

        const char *input_names[] = {
            input_name.get()};

        const char *output_names[] = {
            output_name.get()};

        auto outputs = session.Run(
            Ort::RunOptions{nullptr},
            input_names,
            &input_tensor,
            1,
            output_names,
            1);

        if (outputs.empty())
        {
            throw std::runtime_error(
                "OCR model returned no output.");
        }

        auto &output = outputs[0];

        const auto output_info =
            output.GetTensorTypeAndShapeInfo();

        const auto output_shape =
            output_info.GetShape();

        if (output_shape.size() != 3)
        {
            throw std::runtime_error(
                "Unexpected OCR output rank.");
        }

        const std::size_t batch =
            static_cast<std::size_t>(
                output_shape[0]);

        const std::size_t timesteps =
            static_cast<std::size_t>(
                output_shape[1]);

        const std::size_t classes =
            static_cast<std::size_t>(
                output_shape[2]);

        if (batch != 1)
        {
            throw std::runtime_error(
                "Unexpected OCR batch size.");
        }

        if (classes != class_count)
        {
            throw std::runtime_error(
                "Unexpected OCR class count: " +
                std::to_string(classes));
        }

        const float *output_data =
            output.GetTensorData<float>();

        // ---------------------------------------------------------
        // CTC decode
        // ---------------------------------------------------------

        std::string text;

        float confidence_sum = 0.0f;
        int confidence_count = 0;

        std::size_t previous_class =
            std::numeric_limits<std::size_t>::max();

        std::cout << "\nRaw CTC sequence:\n";

        for (std::size_t t = 0; t < timesteps; ++t)
        {
            const float *timestep =
                output_data +
                t * classes;

            std::size_t best_class = 0;
            float best_probability =
                timestep[0];

            for (std::size_t c = 1; c < classes; ++c)
            {
                if (timestep[c] > best_probability)
                {
                    best_probability =
                        timestep[c];

                    best_class = c;
                }
            }

            std::cout
                << "t="
                << t
                << " class="
                << best_class
                << " prob="
                << best_probability;

            if (best_class < labels.size())
            {
                std::cout
                    << " label=\""
                    << labels[best_class]
                    << "\"";
            }

            std::cout << '\n';

            // CTC duplicate suppression.
            if (best_class == previous_class)
            {
                continue;
            }

            previous_class = best_class;

            // CTC blank.
            if (best_class == 0)
            {
                continue;
            }

            if (best_class >= labels.size())
            {
                continue;
            }

            text += labels[best_class];

            confidence_sum += best_probability;
            ++confidence_count;
        }

        const float confidence =
            confidence_count > 0
                ? confidence_sum /
                      static_cast<float>(confidence_count)
                : 0.0f;

        // ---------------------------------------------------------
        // Digits-only extraction
        // ---------------------------------------------------------

        std::string digits;

        for (const char character : text)
        {
            if (
                character >= '0' &&
                character <= '9')
            {
                digits += character;
            }
        }

        std::cout << "\n=== REAL OCR TEST ===\n";

        std::cout
            << "Image: "
            << image_path
            << '\n';

        std::cout
            << "Original size: "
            << image.cols
            << "x"
            << image.rows
            << '\n';

        std::cout
            << "Resized size: "
            << resized_width
            << "x"
            << input_height
            << '\n';

        std::cout
            << "Model input: [1, 3, "
            << input_height
            << ", "
            << input_width
            << "]\n";

        std::cout
            << "Output shape: ["
            << batch
            << ", "
            << timesteps
            << ", "
            << classes
            << "]\n";

        std::cout
            << "Decoded text: \""
            << text
            << "\"\n";

        std::cout
            << "Digits only: \""
            << digits
            << "\"\n";

        std::cout
            << "Confidence: "
            << confidence
            << '\n';

        std::cout << "=== END REAL OCR TEST ===\n";
    }

}