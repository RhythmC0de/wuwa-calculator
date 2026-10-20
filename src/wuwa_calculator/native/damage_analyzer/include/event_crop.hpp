#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace damage_analyzer {

// Pedido de recorte: onde (em pixels do vídeo) e quando o número apareceu.
// Os campos espelham DamageEvent.
struct CropRequest {
    double timestamp = 0.0;
    int center_x = 0;
    int center_y = 0;
    int width = 0;
    int height = 0;
};

struct CropOptions {
    // Margem ao redor da caixa, como fração da altura do número.
    double padding = 0.6;

    // Instantes extras (segundos, relativos ao timestamp do evento) a
    // recortar. O número "cresce" e se sobrepõe a outros nos frames
    // seguintes, então dois ou três instantes ajudam a revisar.
    std::vector<double> offsets = {0.0};

    // Recortes menores que isso (altura em px) são ampliados, para que a
    // pessoa consiga ler. 0 desliga.
    int min_height = 96;
};

// Um PNG por instante pedido (vazio se o frame não pôde ser lido).
using CropImages = std::vector<std::vector<std::uint8_t>>;

// Abre o vídeo uma vez e devolve, para cada pedido, os recortes PNG.
// O vetor de saída tem o mesmo tamanho e a mesma ordem de `requests`.
// Lança std::runtime_error se o vídeo não abrir.
std::vector<CropImages> extract_event_crops(
    const std::string& video_path,
    const std::vector<CropRequest>& requests,
    const CropOptions& options = CropOptions{}
);

} // namespace damage_analyzer
