import time
import random

def delay(seconds=None):
    """Pausa aleatoria para evitar bloqueos"""
    if seconds is None:
        seconds = random.uniform(1, 3)
    time.sleep(seconds)
