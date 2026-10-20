#pragma once

#include <filesystem>
#include <string>
#include <vector>

#include <opencv2/core.hpp>

namespace damage_analyzer {

// Converte uma string UTF-8 (como o Python entrega) em um
// std::filesystem::path correto em qualquer plataforma.
//
// No Windows, "const char*" seria interpretado na code page ANSI e
// quebraria caminhos com acentos (ex.: "C:\Users\João\vídeo.mp4").
std::filesystem::path utf8_path(const std::string& utf8);

// Inverso de utf8_path(): path -> std::string UTF-8.
std::string to_utf8(const std::filesystem::path& path);

// Diretório do binário (.so / .pyd / .exe) que contém este código.
// Retorna vazio se não for possível determinar.
std::filesystem::path module_directory();

// Procura a pasta models/ocr em locais conhecidos:
//   1. variável de ambiente DAMAGE_ANALYZER_MODELS_DIR
//   2. <diretório do módulo>/models/ocr
//   3. <diretório do módulo>/../models/ocr
//   4. pasta de código-fonte usada na compilação
// Retorna vazio se nada for encontrado.
std::filesystem::path find_models_directory();

// Lê uma imagem a partir de um caminho UTF-8 (cv::imread não aceita
// caminhos Unicode de forma confiável no Windows). Retorna vazio se falhar.
cv::Mat read_image_utf8(const std::string& utf8_path_string);

} // namespace damage_analyzer
