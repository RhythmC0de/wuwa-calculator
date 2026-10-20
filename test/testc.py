from wuwa_calculator.native.damage_analyzer  import damage_analyzer

result = damage_analyzer.analyze_video(
    "teste.mp4",
    0.0,
    10.0,
)

print(result.total_damage)
print(result.average_damage)
print(result.total_hits)
print(result.peak_damage)