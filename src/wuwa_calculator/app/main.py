"""Application entry point (run through ``python run_tethys.py``)."""

from __future__ import annotations

import logging
import os
import sys


def main() -> int:
    os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.ffmpeg=false")
    logging.basicConfig(
        level=logging.DEBUG if os.environ.get("TETHYS_DEBUG") == "1" else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    # A engine precisa ser carregada ANTES do Qt Multimedia: o PySide6 traz uma
    # libavutil.so.61 própria (reduzida) e, se ela entrar primeiro no processo,
    # o FFmpeg do sistema usado pelo OpenCV da engine falha com
    # "undefined symbol: av_amf_extract_hdr_metadata". Ordem inversa funciona.
    try:
        from wuwa_calculator.infrastructure.native_engine import load_engine

        load_engine()
    except ImportError as error:  # sem engine o app abre; a análise avisa depois
        logging.getLogger(__name__).warning("engine nativa indisponível: %s", error)

    from PySide6.QtWidgets import QApplication  # lazy: keeps `import main` cheap

    from wuwa_calculator.ui.panels.window import WuwaQtWindow
    from wuwa_calculator.ui.windows.appearance import apply_saved_stylesheet

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_saved_stylesheet(app)
    window = WuwaQtWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())