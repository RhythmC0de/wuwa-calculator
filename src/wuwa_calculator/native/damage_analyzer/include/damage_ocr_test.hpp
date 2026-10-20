#pragma once

#include <string>

namespace damage_analyzer {

class DamageOCRTest {
public:
    static void run(
        const std::string& model_path,
        const std::string& dictionary_path,
        const std::string& image_path
    );
};

}