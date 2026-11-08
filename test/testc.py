"""test/testc.py"""

from wuwa_calculator.infrastructure.native_engine import load_engine

damage_analyzer = load_engine()

result = damage_analyzer.analyze_video(
    "teste.mp4",
    0.0,
    10.0,
)

print(result.total_damage)
print(result.average_damage)
print(result.total_hits)
print(result.peak_damage)
