#pragma once

#include <string>

namespace damage_analyzer {

class OCRInferenceTest {
public:
    static void run(const std::string& model_path);

    static void run_image(
        const std::string& model_path,
        const std::string& image_path
    );
};

}