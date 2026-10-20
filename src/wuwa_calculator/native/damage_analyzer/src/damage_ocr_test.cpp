#include "damage_ocr_test.hpp"

#include "damage_ocr.hpp"
#include "platform.hpp"

#include <iostream>

#include <opencv2/imgcodecs.hpp>

namespace damage_analyzer {

void DamageOCRTest::run(
    const std::string& model_path,
    const std::string& dictionary_path,
    const std::string& image_path
) {
    std::cout
        << "=== DAMAGE OCR TEST ===\n";

    DamageOCR ocr(
        model_path,
        dictionary_path
    );

    const cv::Mat image =
        read_image_utf8(image_path);

    if (image.empty()) {
        std::cerr
            << "Could not open image: "
            << image_path
            << '\n';

        return;
    }

    const auto results =
        ocr.recognize(image);

    std::cout
        << "Image: "
        << image_path
        << '\n';

    std::cout
        << "Results: "
        << results.size()
        << '\n';

    for (const auto& result : results) {
        std::cout
            << "Damage: "
            << result.value
            << '\n';

        std::cout
            << "Confidence: "
            << result.confidence
            << '\n';

        std::cout
            << "Size: "
            << result.width
            << "x"
            << result.height
            << '\n';
    }

    std::cout
        << "=== END DAMAGE OCR TEST ===\n";
}

}