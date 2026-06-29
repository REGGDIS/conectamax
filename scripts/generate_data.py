"""Generador de datos sinteticos para ConectaMax (Spec 02, rev. PR #6).

Crea >= 2.000 clientes coherentes con el contrato de config/settings.py y los
expande al modelo relacional. La variable `abandono` surge de varios drivers
ponderados + ruido (Plan v3.2 §29.3).

Por seguridad NO borra datos existentes salvo que se pase --reset (punto 1).
Maneja transacciones con rollback y cierre seguro (punto 6).

Uso:
    python scripts/generate_data.py [--db data/conectamax.db] [--n 2500] [--csv] [--reset]
"""
from __future__ import annotations

import argparse
import math
import os
import sqlite3
from datetime import date, timedelta

import numpy as np

from _paths import default_db, schema_path

SEED = 42
HOY = date(2026, 6, 28)  # fecha de referencia (ventanas de 6 meses)

CIUDADES = [
    ("Santiago", 1, 0.30), ("Valparaiso", 3, 0.10), ("Concepcion", 4, 0.10),
    ("Antofagasta", 2, 0.08), ("Puerto Montt", 5, 0.07), ("La Serena", 3, 0.07),
    ("Temuco", 4, 0.07), ("Rancagua", 1, 0.06), ("Iquique", 2, 0.06),
    ("Valdivia", 5, 0.05), ("Arica", 2, 0.04),
]
SUCURSALES = [
    (1, "Casa Matriz Santiago", "Santiago", "Metropolitana"),
    (2, "Sucursal Norte", "Antofagasta", "Antofagasta"),
    (3, "Sucursal Centro", "Valparaiso", "Valparaiso"),
    (4, "Sucursal Sur", "Concepcion", "Biobio"),
    (5, "Sucursal Austral", "Puerto Montt", "Los Lagos"),
]
SERVICIOS = [
    (1, "SRV-BAS", "Basico", "movil", 17990.0),
    (2, "SRV-MMX", "Movil Max", "movil", 24990.0),
    (3, "SRV-FIB", "Fibra Plus", "internet", 33990.0),
    (4, "SRV-HOG", "Hogar Total", "paquete", 46990.0),
    (5, "SRV-EMP", "Empresas", "empresarial", 68990.0),
]
PRECIO = {s[2]: s[4] for s in SERVICIOS}
IDSRV = {s[2]: s[0] for s in SERVICIOS}
PLANES = [s[2] for s in SERVICIOS]
PLAN_PESO = [0.22, 0.24, 0.26, 0.18, 0.10]
TIPO_CONTRATO = ["Mensual", "Anual", "Bienal"]
TIPO_PESO = [0.55, 0.32, 0.13]
SEGMENTOS = ["Jovenes Digitales", "Familias Conectadas", "Profesionales Urbanos",
             "Adultos Mayores", "Clientes en Riesgo"]
GENEROS = ["F", "M", "otro"]
NOMBRES = ["Ana", "Luis", "Marcela", "Diego", "Camila", "Jorge", "Paula", "Felipe",
           "Daniela", "Roberto", "Isabel", "Matias", "Carolina", "Andres", "Valentina"]
APELLIDOS = ["Rojas", "Paredes", "Soto", "Salinas", "Fuentes", "Molina", "Herrera",
             "Vargas", "Castro", "Nunez", "Medina", "Campos", "Vega", "Torres", "Leon"]

W = dict(b0=-0.95, reclamos=2.4, pagos=1.9, satisf=2.0, desuso=1.5,
         antig=1.6, servicios=1.1, mensual=0.9, sigma=0.40)

TABLAS = ["predicciones", "interacciones", "reclamos", "pagos", "facturas",
          "contratos", "clientes", "servicios", "sucursales", "parametros"]


def sigmoide(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def construir(n: int):
    rng = np.random.default_rng(SEED)
    ciudades = [c[0] for c in CIUDADES]
    cpesos = np.array([c[2] for c in CIUDADES]); cpesos = cpesos / cpesos.sum()
    suc_de_ciudad = {c[0]: c[1] for c in CIUDADES}
    clientes, contratos, facturas, pagos, reclamos, interacciones = [], [], [], [], [], []

    for i in range(1, n + 1):
        cid = f"CXM{i:04d}"
        ciudad = rng.choice(ciudades, p=cpesos)
        id_suc = suc_de_ciudad[ciudad]
        segmento = rng.choice(SEGMENTOS)
        genero = rng.choice(GENEROS, p=[0.48, 0.48, 0.04])
        nombre = f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)}"
        edad = int(np.clip(rng.normal(40, 13), 18, 85))
        antiguedad = int(np.clip(rng.gamma(2.2, 9), 1, 72))
        reclamos_n = int(np.clip(rng.poisson(1.0), 0, 6))
        pagos_atr = int(np.clip(rng.poisson(0.8), 0, 6))
        dias_sin_uso = int(np.clip(rng.gamma(2.0, 4), 0, 30))
        cant_serv = int(rng.choice([1, 2, 3, 4, 5], p=[0.30, 0.28, 0.22, 0.13, 0.07]))
        plan = rng.choice(PLANES, p=PLAN_PESO)
        tipo_contrato = rng.choice(TIPO_CONTRATO, p=TIPO_PESO)
        ingreso = float(np.clip(rng.normal(900000, 450000), 300000, 3000000))
        sat = 5 - 0.55 * reclamos_n - 0.45 * pagos_atr - 0.05 * dias_sin_uso + rng.normal(0, 0.5)
        satisfaccion = int(np.clip(round(sat), 1, 5))

        z = (W["b0"]
             + W["reclamos"] * (reclamos_n / 6.0)
             + W["pagos"] * (pagos_atr / 6.0)
             + W["satisf"] * ((3 - satisfaccion) / 2.0)
             + W["desuso"] * (dias_sin_uso / 30.0)
             - W["antig"] * (antiguedad / 72.0)
             - W["servicios"] * (cant_serv / 5.0)
             + W["mensual"] * (1.0 if tipo_contrato == "Mensual" else 0.0)
             + rng.normal(0, W["sigma"]))
        abandono = int(rng.random() < sigmoide(z))
        estado = "inactivo" if abandono else "activo"
        fecha_alta = (HOY - timedelta(days=int(antiguedad * 30))).isoformat()

        servicios_cli = [plan]
        otros = [s for s in PLANES if s != plan]
        rng.shuffle(otros)
        servicios_cli += otros[: cant_serv - 1]
        for k, sv in enumerate(servicios_cli):
            contratos.append((cid, IDSRV[sv], tipo_contrato if k == 0 else "Mensual",
                              fecha_alta, None, "activo", PRECIO[sv], 1 if k == 0 else 0))

        idx_atrasados = set(rng.choice(6, size=min(pagos_atr, 6), replace=False).tolist()) if pagos_atr else set()
        monto_total = sum(PRECIO[s] for s in servicios_cli)
        for m in range(6):
            fmes = HOY.replace(day=1) - timedelta(days=30 * m)
            emision = fmes.isoformat()
            venc = (fmes + timedelta(days=20)).isoformat()
            atrasado = m in idx_atrasados
            facturas.append((cid, fmes.strftime("%Y-%m"), monto_total, emision, venc,
                             "vencida" if atrasado else "pagada"))
            pagos.append((cid, fmes.strftime("%Y-%m"), monto_total, emision, venc, atrasado))

        tipos_r = ["facturacion", "tecnico", "servicio", "comercial"]
        canales_r = ["telefono", "app", "sucursal", "web"]
        for _ in range(reclamos_n):
            dias = int(rng.integers(0, 180))
            reclamos.append((cid, id_suc, (HOY - timedelta(days=dias)).isoformat(),
                             rng.choice(tipos_r), rng.choice(canales_r),
                             rng.choice(["abierto", "resuelto"], p=[0.3, 0.7])))

        canales_i = ["soporte", "llamada", "app", "sucursal"]
        for _ in range(int(np.clip(reclamos_n + rng.poisson(0.5), 0, 10))):
            dias = int(rng.integers(0, 180))
            interacciones.append((cid, (HOY - timedelta(days=dias)).isoformat(),
                                  rng.choice(canales_i),
                                  rng.choice(["consulta", "soporte", "reclamo", "venta"]),
                                  int(rng.integers(1, 30))))

        clientes.append((cid, nombre, edad, genero, ciudad, id_suc, segmento,
                         "pyme" if plan == "Empresas" else "residencial",
                         antiguedad, ingreso, satisfaccion, dias_sin_uso, estado,
                         fecha_alta, abandono))
    return clientes, contratos, facturas, pagos, reclamos, interacciones


def poblar(db_path: str, n: int, exportar_csv: bool = False, reset: bool = False):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(open(schema_path(), encoding="utf-8").read())

        existe = con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        if existe and not reset:
            raise SystemExit(
                f"La base ya tiene {existe} clientes. Usa --reset para regenerar "
                "(esto borra datos y predicciones).")
        if reset:
            for t in TABLAS:
                con.execute(f"DELETE FROM {t}")

        con.execute("INSERT INTO parametros (id, fecha_referencia) VALUES (1, ?)",
                    (HOY.isoformat(),))
        con.executemany("INSERT INTO sucursales VALUES (?,?,?,?)", SUCURSALES)
        con.executemany("INSERT INTO servicios VALUES (?,?,?,?,?)", SERVICIOS)

        cli, ctr, fac, pag, rec, inter = construir(n)
        con.executemany(
            "INSERT INTO clientes (id_cliente,nombre,edad,genero,ciudad,id_sucursal,segmento,"
            "tipo_cliente,antiguedad_meses,ingreso_mensual,satisfaccion,dias_sin_uso,estado,"
            "fecha_alta,abandono) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", cli)
        con.executemany(
            "INSERT INTO contratos (id_cliente,id_servicio,tipo_contrato,fecha_inicio,fecha_fin,"
            "estado,monto_mensual,es_principal) VALUES (?,?,?,?,?,?,?,?)", ctr)

        cur = con.cursor()
        for (cid, periodo, monto, emision, venc, estadof), (_, _, _, _, _, atrasado) in zip(fac, pag):
            cur.execute("INSERT INTO facturas (id_cliente,periodo,monto_facturado,fecha_emision,"
                        "fecha_vencimiento,estado) VALUES (?,?,?,?,?,?)",
                        (cid, periodo, monto, emision, venc, estadof))
            idf = cur.lastrowid
            if atrasado:
                cur.execute("INSERT INTO pagos (id_factura,fecha_pago,monto_pagado,estado,dias_atraso)"
                            " VALUES (?,?,?,?,?)", (idf, venc, monto, "atrasado", 5 + (idf % 25)))
            else:
                cur.execute("INSERT INTO pagos (id_factura,fecha_pago,monto_pagado,estado,dias_atraso)"
                            " VALUES (?,?,?,?,?)", (idf, emision, monto, "a_tiempo", 0))

        con.executemany("INSERT INTO reclamos (id_cliente,id_sucursal,fecha,tipo,canal,estado)"
                        " VALUES (?,?,?,?,?,?)", rec)
        con.executemany("INSERT INTO interacciones (id_cliente,fecha,canal,motivo,duracion_min)"
                        " VALUES (?,?,?,?,?)", inter)
        con.commit()

        if exportar_csv:
            import csv
            cols = ["id_cliente", "nombre", "ciudad", "antiguedad_meses", "tipo_contrato",
                    "plan", "monto_mensual", "reclamos_ultimos_6_meses", "pagos_atrasados",
                    "dias_sin_uso", "satisfaccion", "abandono", "edad", "cantidad_servicios"]
            rows = con.execute(
                f"SELECT {','.join(cols)} FROM comportamiento_cliente ORDER BY id_cliente").fetchall()
            out = os.path.join(os.path.dirname(db_path) or ".", "clientes_generados.csv")
            with open(out, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh); w.writerow(cols); w.writerows(rows)
            print(f"CSV exportado: {out} ({len(rows)} filas)")

        total = con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        churn = con.execute("SELECT AVG(abandono)*100 FROM clientes").fetchone()[0]
        print(f"Clientes: {total} | Tasa de abandono: {churn:.1f}%")
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=default_db())
    ap.add_argument("--n", type=int, default=2500)
    ap.add_argument("--csv", action="store_true")
    ap.add_argument("--reset", action="store_true",
                    help="borra datos y predicciones existentes antes de generar")
    a = ap.parse_args()
    poblar(a.db, a.n, a.csv, a.reset)


if __name__ == "__main__":
    main()
