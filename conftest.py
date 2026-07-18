"""
Permite ejecutar `pytest` desde la raíz del proyecto resolviendo
los imports de paquetes internos (ia, database, backend, config, utils)
del mismo modo que lo hace backend/main.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
