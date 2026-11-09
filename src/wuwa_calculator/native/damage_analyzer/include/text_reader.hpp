#pragma once

#include <memory>
#include <string>
#include <vector>

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <onnxruntime_cxx_api.h>

#include "classic_text_detector.hpp"
#include "damage_ocr.hpp"

namespace damage_analyzer {

// Uma linha de texto lida de uma imagem. x e y são o centro da caixa.
struct TextLine {
    std::string text;
    double confidence = 0.0;
    double x = 0.0;
    double y = 0.0;
    double width = 0.0;
    double height = 0.0;
};

struct DetectionParams {
    double threshold = 0.3;       // binarização do mapa de probabilidade
    double box_threshold = 0.6;   // nota mínima média da caixa
    double unclip_ratio = 1.5;    // quanto a caixa cresce (DB)
    double min_side = 3.0;        // lado mínimo, em pixels do mapa
    int max_boxes = 1000;
};

// Transforma o mapa de probabilidade do detector (CV_32F, linhas x colunas)
// em caixas alinhadas ao eixo, na escala da imagem original. Ordenadas de
// cima para baixo e da esquerda para a direita. Não depende de ONNX.
std::vector<cv::Rect> boxes_from_probability_map(
    const cv::Mat& probability,
    const cv::Size& image_size,
    const DetectionParams& params = DetectionParams{}
);

// Detector de linhas de texto (DBNet, PP-OCRv5 mobile det em ONNX).
class TextDetector {
public:
    explicit TextDetector(const std::string& model_path);

    std::vector<cv::Rect> detect(
        const cv::Mat& image_bgr,
        const DetectionParams& params = DetectionParams{}
    ) const;

private:
    Ort::Env env_;
    Ort::SessionOptions session_options_;
    std::unique_ptr<Ort::Session> session_;
};

struct ReadTextOptions {
    bool enhance = false;           // cinza + contraste + nitidez antes de ler
    double min_confidence = 0.3;    // descarta linhas abaixo disso
    double pad_ratio = 0.10;        // folga ao redor de cada caixa
};

// Realça uma imagem para o OCR (cinza, CLAHE e nitidez), de volta em BGR.
cv::Mat enhance_for_ocr(const cv::Mat& image_bgr);

// Lê o texto de cada caixa. Se `boxes` estiver vazio e houver `detector`,
// as caixas vêm da detecção; sem detector, do detector clássico (sem modelo).
std::vector<TextLine> read_text_lines(
    const cv::Mat& image_bgr,
    const DamageOCR& ocr,
    const TextDetector* detector,
    const std::vector<cv::Rect>& boxes,
    const ReadTextOptions& options = ReadTextOptions{}
);

} // namespace damage_analyzer
