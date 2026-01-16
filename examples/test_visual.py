import numpy as np
from datetime import datetime, timedelta

# 24h de ciclo diário simples
n = 24
T = 25 + 7 * np.sin(np.linspace(0, 2*np.pi, n))
RH = 0.55 - 0.15 * np.sin(np.linspace(0, 2*np.pi, n))

time = [datetime(2023, 1, 1) + timedelta(hours=i) for i in range(n)]

