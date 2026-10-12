"""Conjunto pequeno de concursos com estatísticas conferidas à mão (T06).

Há uma lacuna na numeração (não existe o concurso 4) e a dezena 25 nunca saiu.
"""

from datetime import date

C1 = list(range(1, 16))  # 1 a 15
C2 = list(range(10, 25))  # 10 a 24
C3 = list(range(1, 16))  # 1 a 15
C5 = [1, 2, 3, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 23, 24]

CONCURSOS = [
    (1, date(2026, 1, 5), C1),
    (2, date(2026, 1, 6), C2),
    (3, date(2026, 1, 7), C3),
    (5, date(2026, 1, 9), C5),
]

# Quantas vezes cada dezena saiu nos 4 concursos (conferido à mão; soma = 60).
FREQUENCIA_TOTAL = {
    1: 3, 2: 3, 3: 3, 4: 2, 5: 3, 6: 3, 7: 2, 8: 3, 9: 2, 10: 4, 11: 3, 12: 4, 13: 3,
    14: 4, 15: 3, 16: 2, 17: 1, 18: 2, 19: 1, 20: 2, 21: 1, 22: 2, 23: 2, 24: 2, 25: 0,
}  # fmt: skip
