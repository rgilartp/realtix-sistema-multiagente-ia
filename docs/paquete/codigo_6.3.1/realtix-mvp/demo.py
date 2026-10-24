"""
Demostración del adaptador de datos sobre la base sintética.

No es un test formal de la Fase 4 (eso corresponde al plan de pruebas);
es una verificación rápida de que los 6 métodos del contrato (Tabla 7 de
arquitectura v2) funcionan de punta a punta, incluida la restricción de
acceso (RF-AUT-02).
"""

import uuid
from datetime import datetime

from adapter import MockRealSitAdapter, PredioNoAutorizadoError
from database import get_connection
from models import CasoEscalado


def cop(valor: int) -> str:
    return f"${valor:,.0f}".replace(",", ".")


def main():
    adapter = MockRealSitAdapter()
    conn = get_connection()

    # Tomamos un contribuyente con al menos un predio y una obligación ICA,
    # para ejercitar ambos tributos en la misma corrida.
    fila = conn.execute("""
        SELECT c.id_contribuyente, c.nombre, p.matricula_catastral
        FROM contribuyente c
        JOIN predio p ON p.id_contribuyente = c.id_contribuyente
        WHERE c.actividad_economica IS NOT NULL
        LIMIT 1
    """).fetchone()
    contribuyente_id, nombre, predio_id = fila["id_contribuyente"], fila["nombre"], fila["matricula_catastral"]

    print(f"Contribuyente de prueba: {nombre} ({contribuyente_id})")
    print(f"Predio de prueba: {predio_id}\n")

    print("== get_estado_cuenta ==")
    estado = adapter.get_estado_cuenta(predio_id, contribuyente_id)
    print(f"Obligaciones pendientes: {estado.obligaciones_pendientes}")
    print(f"Saldo total pendiente: {cop(estado.saldo_total_pendiente)}")
    for o in estado.obligaciones:
        print(f"  - {o.tipo_tributo} {o.vigencia_fiscal}: {cop(o.valor_liquidado)} [{o.estado_pago}]")

    print("\n== get_historial_pagos ==")
    pagos = adapter.get_historial_pagos(predio_id, contribuyente_id)
    for p in pagos:
        print(f"  - {p.fecha_pago}: {cop(p.valor_pagado)} vía {p.medio_pago}")
    if not pagos:
        print("  (sin pagos registrados)")

    print("\n== get_avaluo_catastral ==")
    avaluo = adapter.get_avaluo_catastral(predio_id, contribuyente_id)
    print(f"  Avalúo catastral {avaluo.vigencia_fiscal}: {cop(avaluo.avaluo_catastral)}")

    print("\n== get_obligaciones_vigentes (solo IPU) ==")
    ipu = adapter.get_obligaciones_vigentes(predio_id, contribuyente_id, "IPU")
    print(f"  {len(ipu)} obligación(es) IPU encontradas")

    print("\n== get_tarifa_ica ==")
    tarifa = adapter.get_tarifa_ica("tecnologia_software")
    print(f"  {tarifa.descripcion}: {tarifa.tarifa_por_mil} por mil")

    print("\n== registrar_caso_escalado ==")
    # En esta versión, registrar_caso_escalado exige que la conversación ya
    # exista (falla H-02; desde el Paso 2, el adaptador la registra si no
    # existe). Aquí se inserta para que la demo sea autocontenida.
    # Los identificadores se generan por corrida para que la demo pueda
    # ejecutarse varias veces sin regenerar la base de datos.
    sufijo = uuid.uuid4().hex[:8].upper()
    id_conversacion = f"CONV-DEMO-{sufijo}"
    id_caso = f"CASO-DEMO-{sufijo}"
    conn.execute(
        "INSERT INTO conversacion VALUES (?, ?, ?, ?)",
        (id_conversacion, contribuyente_id, datetime.now().isoformat(), "ipu"),
    )
    conn.commit()
    caso = CasoEscalado(
        id_caso=id_caso, id_conversacion=id_conversacion,
        resumen="El contribuyente pregunta por un descuento no contemplado en la base de conocimiento.",
        nivel_confianza=0.42,
    )
    ack = adapter.registrar_caso_escalado(caso)
    print(f"  {ack.mensaje}")

    print("\n== RF-AUT-02: intento de acceso a un predio ajeno ==")
    otro = conn.execute(
        "SELECT matricula_catastral FROM predio WHERE id_contribuyente != ? LIMIT 1", (contribuyente_id,)
    ).fetchone()
    try:
        adapter.get_estado_cuenta(otro["matricula_catastral"], contribuyente_id)
        print("  ERROR: la consulta no debió haberse permitido.")
    except PredioNoAutorizadoError as e:
        print(f"  Rechazado correctamente -> {e}")


if __name__ == "__main__":
    main()
