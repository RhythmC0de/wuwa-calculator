#pragma once

#include <vector>

#include <opencv2/core.hpp>

namespace damage_analyzer {

struct ClassicDetectionParams {
    // Imagens fora de 1400-2200 px são reescaladas.
    int target_width = 1920;
    double edge_factor = 0.5;      // limiar = max(8, Otsu * edge_factor)
    int min_height = 14;           // em pixels da imagem reescalada
    int max_height = 70;
    int min_width = 18;
    double min_aspect = 1.2;       // largura / altura
    double min_fill = 0.25;
};

// Detector de linhas de texto sem modelo (gradiente morfológico + componentes
// conexos). É o plano B quando models/ocr/ppocrv5_det.onnx não existe: serve
// para telas de interface (texto claro em fundo liso, como a ficha de status).
// Devolve caixas na escala da imagem original, em ordem de leitura.
std::vector<cv::Rect> detect_text_classic(
    const cv::Mat& image_bgr,
    const ClassicDetectionParams& params = ClassicDetectionParams{}
);

} // namespace damage_analyzer
