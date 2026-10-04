"""Render assets/systemmanager.svg into a macOS .iconset folder (then `iconutil -c icns` turns it into an .icns)."""
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

SIZES = [16, 32, 128, 256, 512]  # each also written at 2x

svg, out = Path(sys.argv[1]), Path(sys.argv[2])
QGuiApplication(["make_icns"])
renderer = QSvgRenderer(str(svg))
out.mkdir(parents=True, exist_ok=True)
for size in SIZES:
    for scale in (1, 2):
        px = size * scale
        img = QImage(px, px, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        painter = QPainter(img)
        renderer.render(painter)
        painter.end()
        img.save(str(out / f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"))
