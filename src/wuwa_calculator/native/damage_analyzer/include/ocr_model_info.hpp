#pragma once

#include <string>

namespace damage_analyzer {

class OCRModelInfo {
public:
    static void inspect(const std::string& model_path);
};

} // namespace damage_analyzer