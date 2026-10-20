cmake_minimum_required(VERSION 3.21)

project(damage_analyzer
    VERSION 0.2.0
    LANGUAGES CXX
)

# ---------------------------------------------------------------------------
# Opções
# ---------------------------------------------------------------------------

option(DAMAGE_ANALYZER_BUILD_PYTHON "Compila o módulo Python (pybind11)" ON)
option(DAMAGE_ANALYZER_BUILD_CLI "Compila o executável de linha de comando" ON)
option(DAMAGE_ANALYZER_FETCH_ORT
    "Baixa o ONNX Runtime oficial se ele não for encontrado localmente" ON)

set(DAMAGE_ANALYZER_ORT_VERSION "1.30.0" CACHE STRING
    "Versão do ONNX Runtime baixada automaticamente")

set(ONNXRUNTIME_ROOT "" CACHE PATH
    "Pasta do ONNX Runtime (com include/ e lib/). Vazio = autodetectar")

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# ---------------------------------------------------------------------------
# OpenCV
# ---------------------------------------------------------------------------
#
# Linux:   sudo apt install libopencv-dev
# Windows: baixe o OpenCV em opencv.org e defina OpenCV_DIR, por exemplo
#          -DOpenCV_DIR=C:/opencv/build   (ou use vcpkg: opencv4[ffmpeg])

find_package(OpenCV REQUIRED COMPONENTS
    core
    imgproc
    imgcodecs
    videoio
)

# ---------------------------------------------------------------------------
# ONNX Runtime
# ---------------------------------------------------------------------------
#
# Ordem de busca:
#   1. -DONNXRUNTIME_ROOT=...
#   2. third_party/onnxruntime
#   3. download do pacote oficial (DAMAGE_ANALYZER_FETCH_ORT=ON)

function(_ort_is_valid root out_var)
    set(${out_var} FALSE PARENT_SCOPE)

    if(NOT EXISTS "${root}/include/onnxruntime_cxx_api.h")
        return()
    endif()

    if(WIN32)
        if(EXISTS "${root}/lib/onnxruntime.lib" AND
           EXISTS "${root}/lib/onnxruntime.dll")
            set(${out_var} TRUE PARENT_SCOPE)
        endif()
    else()
        file(GLOB _so "${root}/lib/libonnxruntime.so*")
        if(_so)
            set(${out_var} TRUE PARENT_SCOPE)
        endif()
    endif()
endfunction()

set(_ort_root "")

foreach(_candidate
        "${ONNXRUNTIME_ROOT}"
        "${CMAKE_CURRENT_SOURCE_DIR}/third_party/onnxruntime")
    if(_candidate)
        _ort_is_valid("${_candidate}" _ok)
        if(_ok)
            set(_ort_root "${_candidate}")
            break()
        endif()
    endif()
endforeach()

if(NOT _ort_root)
    if(NOT DAMAGE_ANALYZER_FETCH_ORT)
        message(FATAL_ERROR
            "ONNX Runtime não encontrado. Defina -DONNXRUNTIME_ROOT=<pasta> "
            "ou habilite -DDAMAGE_ANALYZER_FETCH_ORT=ON.")
    endif()

    if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(AMD64|x86_64|X86_64)$")
        set(_ort_arch_win "x64")
        set(_ort_arch_linux "x64")
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(ARM64|arm64|aarch64)$")
        set(_ort_arch_win "arm64")
        set(_ort_arch_linux "aarch64")
    else()
        message(FATAL_ERROR
            "Arquitetura ${CMAKE_SYSTEM_PROCESSOR} sem pacote ONNX Runtime "
            "automático. Defina -DONNXRUNTIME_ROOT=<pasta>.")
    endif()

    set(_ort_base
        "https://github.com/microsoft/onnxruntime/releases/download/v${DAMAGE_ANALYZER_ORT_VERSION}")

    if(WIN32)
        set(_ort_url
            "${_ort_base}/onnxruntime-win-${_ort_arch_win}-${DAMAGE_ANALYZER_ORT_VERSION}.zip")
    elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
        set(_ort_url
            "${_ort_base}/onnxruntime-linux-${_ort_arch_linux}-${DAMAGE_ANALYZER_ORT_VERSION}.tgz")
    else()
        message(FATAL_ERROR
            "Sistema ${CMAKE_SYSTEM_NAME} não suportado. Use Windows ou Linux.")
    endif()

    message(STATUS "Baixando ONNX Runtime: ${_ort_url}")

    include(FetchContent)

    FetchContent_Declare(onnxruntime_package
        URL "${_ort_url}"
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    FetchContent_MakeAvailable(onnxruntime_package)

    set(_ort_root "${onnxruntime_package_SOURCE_DIR}")

    _ort_is_valid("${_ort_root}" _ok)
    if(NOT _ok)
        message(FATAL_ERROR
            "O pacote baixado do ONNX Runtime tem layout inesperado: "
            "${_ort_root}")
    endif()
endif()

message(STATUS "ONNX Runtime: ${_ort_root}")

add_library(onnxruntime SHARED IMPORTED)

# Arquivos que precisam acompanhar o módulo/executável em tempo de execução.
set(DA_RUNTIME_SRC "")
set(DA_RUNTIME_DST "")
set(DA_SONAME_LINK "")
set(DA_SONAME_TARGET "")

if(WIN32)
    set_target_properties(onnxruntime PROPERTIES
        IMPORTED_IMPLIB   "${_ort_root}/lib/onnxruntime.lib"
        IMPORTED_LOCATION "${_ort_root}/lib/onnxruntime.dll"
        INTERFACE_INCLUDE_DIRECTORIES "${_ort_root}/include"
    )

    list(APPEND DA_RUNTIME_SRC "${_ort_root}/lib/onnxruntime.dll")
    list(APPEND DA_RUNTIME_DST "onnxruntime.dll")

    if(EXISTS "${_ort_root}/lib/onnxruntime_providers_shared.dll")
        list(APPEND DA_RUNTIME_SRC
            "${_ort_root}/lib/onnxruntime_providers_shared.dll")
        list(APPEND DA_RUNTIME_DST "onnxruntime_providers_shared.dll")
    endif()
else()
    # Prefere libonnxruntime.so; se o zip perdeu os symlinks, usa a
    # versão numerada.
    file(GLOB _so_candidates "${_ort_root}/lib/libonnxruntime.so*")
    list(SORT _so_candidates)
    list(GET _so_candidates 0 _so_first)
    file(REAL_PATH "${_so_first}" _so_real)

    get_filename_component(_so_real_name "${_so_real}" NAME)

    # SONAME esperado pelo loader: libonnxruntime.so.<major>
    set(_ort_soname "")
    file(READ_ELF "${_so_real}" SONAME _ort_soname)

    if(NOT _ort_soname)
        if(_so_real_name MATCHES "^libonnxruntime\\.so\\.([0-9]+)\\.")
            set(_ort_soname "libonnxruntime.so.${CMAKE_MATCH_1}")
        else()
            set(_ort_soname "${_so_real_name}")
        endif()
    endif()

    set_target_properties(onnxruntime PROPERTIES
        IMPORTED_LOCATION "${_so_real}"
        IMPORTED_SONAME   "${_ort_soname}"
        INTERFACE_INCLUDE_DIRECTORIES "${_ort_root}/include"
    )

    list(APPEND DA_RUNTIME_SRC "${_so_real}")
    list(APPEND DA_RUNTIME_DST "${_so_real_name}")

    # O loader procura pelo SONAME, então cria o link ao lado da cópia.
    if(NOT _ort_soname STREQUAL _so_real_name)
        set(DA_SONAME_LINK "${_ort_soname}")
        set(DA_SONAME_TARGET "${_so_real_name}")
    endif()

    if(EXISTS "${_ort_root}/lib/libonnxruntime_providers_shared.so")
        list(APPEND DA_RUNTIME_SRC
            "${_ort_root}/lib/libonnxruntime_providers_shared.so")
        list(APPEND DA_RUNTIME_DST "libonnxruntime_providers_shared.so")
    endif()
endif()

# ---------------------------------------------------------------------------
# Biblioteca principal (sem Python)
# ---------------------------------------------------------------------------

add_library(damage_core STATIC
    src/analyzer.cpp
    src/video_reader.cpp
    src/frame_processor.cpp
    src/damage_detector.cpp
    src/damage_ocr.cpp
    src/ocr_runtime.cpp
    # [OPTIONAL DIAGNOSTICS]
    # Remova estes três .cpp apenas se também remover seus headers e
    # exports correspondentes em src/bindings.cpp. Veja CLEANUP_GUIDE.md.
    src/ocr_model_info.cpp
    src/ocr_inference_test.cpp
    src/damage_ocr_test.cpp
    src/candidate_filter.cpp
    src/temporal_filter.cpp
    src/event_tracker.cpp
    src/event_crop.cpp
    src/platform.cpp
)

target_include_directories(damage_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(damage_core
    PUBLIC
        ${OpenCV_LIBS}
        onnxruntime
        ${CMAKE_DL_LIBS}
)

set_target_properties(damage_core PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

target_compile_definitions(damage_core
    PRIVATE
        "DAMAGE_ANALYZER_SOURCE_MODELS_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}/models/ocr\""
    PUBLIC
        $<$<PLATFORM_ID:Windows>:NOMINMAX>
        $<$<PLATFORM_ID:Windows>:WIN32_LEAN_AND_MEAN>
)

if(MSVC)
    # /utf-8: os comentários em português usam acentos.
    target_compile_options(damage_core PUBLIC
        /utf-8 /permissive- /EHsc /W3 /Zc:__cplusplus)
else()
    target_compile_options(damage_core PRIVATE -Wall)
endif()

# ---------------------------------------------------------------------------
# Cópia dos arquivos de execução ao lado do binário
# ---------------------------------------------------------------------------

function(damage_analyzer_stage_runtime target)
    # ONNX Runtime
    list(LENGTH DA_RUNTIME_SRC _count)
    math(EXPR _last "${_count} - 1")

    foreach(_i RANGE ${_last})
        list(GET DA_RUNTIME_SRC ${_i} _src)
        list(GET DA_RUNTIME_DST ${_i} _dst)

        add_custom_command(TARGET ${target} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${_src}" "$<TARGET_FILE_DIR:${target}>/${_dst}"
            VERBATIM
        )
    endforeach()

    if(DA_SONAME_LINK)
        add_custom_command(TARGET ${target} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E create_symlink
                "${DA_SONAME_TARGET}"
                "$<TARGET_FILE_DIR:${target}>/${DA_SONAME_LINK}"
            VERBATIM
        )
    endif()

    # Modelo OCR e dicionário
    add_custom_command(TARGET ${target} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory
            "$<TARGET_FILE_DIR:${target}>/models/ocr"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${CMAKE_CURRENT_SOURCE_DIR}/models/ocr/en_PP-OCRv5_rec_mobile.onnx"
            "${CMAKE_CURRENT_SOURCE_DIR}/models/ocr/ppocrv5_en_dict.txt"
            "$<TARGET_FILE_DIR:${target}>/models/ocr"
        VERBATIM
    )

    if(WIN32)
        # DLLs do OpenCV (e demais dependências importadas).
        add_custom_command(TARGET ${target} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                $<TARGET_RUNTIME_DLLS:${target}>
                "$<TARGET_FILE_DIR:${target}>"
            COMMAND_EXPAND_LISTS
            VERBATIM
        )

        # Plugin FFmpeg do OpenCV: é carregado dinamicamente e por isso
        # não aparece nas dependências do CMake.
        file(GLOB _ffmpeg_plugins
            "${OpenCV_DIR}/../bin/opencv_videoio_ffmpeg*.dll"
            "${OpenCV_DIR}/../../bin/opencv_videoio_ffmpeg*.dll"
            "${OpenCV_DIR}/bin/opencv_videoio_ffmpeg*.dll"
            "${OpenCV_DIR}/x64/vc*/bin/opencv_videoio_ffmpeg*.dll"
        )

        foreach(_plugin IN LISTS _ffmpeg_plugins)
            add_custom_command(TARGET ${target} POST_BUILD
                COMMAND ${CMAKE_COMMAND} -E copy_if_different
                    "${_plugin}" "$<TARGET_FILE_DIR:${target}>"
                VERBATIM
            )
        endforeach()
    endif()

    if(UNIX)
        set_target_properties(${target} PROPERTIES
            BUILD_RPATH   "$ORIGIN"
            INSTALL_RPATH "$ORIGIN"
        )
    endif()
endfunction()

# ---------------------------------------------------------------------------
# Módulo Python
# ---------------------------------------------------------------------------

if(DAMAGE_ANALYZER_BUILD_PYTHON)
    find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module)

    set(PYBIND11_FINDPYTHON ON)

    if(NOT pybind11_DIR)
        execute_process(
            COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
            OUTPUT_VARIABLE _pybind11_cmakedir
            OUTPUT_STRIP_TRAILING_WHITESPACE
            RESULT_VARIABLE _pybind11_rc
            ERROR_QUIET
        )

        if(_pybind11_rc EQUAL 0)
            set(pybind11_DIR "${_pybind11_cmakedir}" CACHE PATH
                "pybind11 CMake config directory")
        endif()
    endif()

    find_package(pybind11 CONFIG REQUIRED)

    pybind11_add_module(damage_analyzer MODULE
        src/bindings.cpp
    )

    target_link_libraries(damage_analyzer PRIVATE damage_core)

    damage_analyzer_stage_runtime(damage_analyzer)

    install(TARGETS damage_analyzer
        LIBRARY DESTINATION .
        RUNTIME DESTINATION .
    )
    install(FILES ${DA_RUNTIME_SRC} DESTINATION .)
    if(DA_SONAME_LINK)
        install(CODE "
            file(CREATE_LINK
                \"${DA_SONAME_TARGET}\"
                \"\$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}/${DA_SONAME_LINK}\"
                SYMBOLIC)
        ")
    endif()
endif()

# ---------------------------------------------------------------------------
# Executável de linha de comando
# ---------------------------------------------------------------------------

if(DAMAGE_ANALYZER_BUILD_CLI)
    add_executable(damage_analyzer_cli src/cli_main.cpp)

    target_link_libraries(damage_analyzer_cli PRIVATE damage_core)

    if(MINGW)
        target_link_options(damage_analyzer_cli PRIVATE -municode)
    endif()

    damage_analyzer_stage_runtime(damage_analyzer_cli)

    install(TARGETS damage_analyzer_cli RUNTIME DESTINATION .)
endif()

install(DIRECTORY models/ocr
    DESTINATION models
    FILES_MATCHING
        PATTERN "*.onnx"
        PATTERN "*.txt"
)
