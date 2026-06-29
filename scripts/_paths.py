"""Resolucion de rutas: usa config.settings.DATABASE_PATH si existe (punto 6)."""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_db():
    try:
        from config.settings import DATABASE_PATH  # repo de Roberto
        return str(DATABASE_PATH)
    except Exception:
        return os.path.join(RAIZ, "data", "conectamax.db")


def default_modelo():
    return os.path.join(RAIZ, "models", "modelo_churn.pkl")


def schema_path():
    return os.path.join(RAIZ, "database", "schema.sql")
