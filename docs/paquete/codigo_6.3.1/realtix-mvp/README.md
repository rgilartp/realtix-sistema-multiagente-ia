# Sistema Multiagente de IA — Realtix
### Base de datos sintética y adaptador de datos (Fase 3, actividad 6.3.1)

Guía para dejar este proyecto corriendo en Visual Studio Code desde cero.

> **Estado a octubre de 2026.** Este es el código de la actividad 6.3.1 tal
> como quedó, con la corrección de idempotencia de `demo.py`. Sus fallas conocidas
> y las observaciones nuevas están en `ESTADO_DEL_CODIGO.md`; se corrigen en el
> Paso 2 del plan, al migrar el código a la estructura `src/`. En este paquete solo
> se actualizaron comentarios, docstrings y este README; la lógica no cambió.

---

## 1. ¿Qué es esto?

Todavía no tenemos acceso al sistema real de Realtix (RealSit), así que este
módulo simula ese ambiente: genera una base de datos con contribuyentes,
predios y obligaciones tributarias falsas pero realistas, y expone el mismo
contrato de acceso a datos (`RealSitAdapter`) que definimos en la Tabla 7 del
documento de arquitectura (versión 2). Los agentes que construyamos más adelante van a
hablar con este adaptador — el día que Realtix dé acceso real, se reemplaza
la implementación de adentro y los agentes no cambian ni una línea (RF-SYS-05).

**No tiene nada gráfico.** Todo lo que hay hoy corre en la terminal. La
interfaz conversacional (el widget con el que va a hablar el contribuyente)
es una actividad aparte, más adelante en el cronograma.

## 2. Estructura del proyecto

| Archivo | Qué hace |
|---|---|
| `models.py` | Define las 6 entidades del modelo de datos (Contribuyente, Predio, ObligacionTributaria, Pago, Conversacion, CasoEscalado) y los tipos que devuelve el adaptador. Solo estructura, sin lógica. |
| `database.py` | Esquema SQLite (tablas, relaciones) y conexión a la base. |
| `generate_synthetic_data.py` | **Script que se ejecuta una vez** (o cada vez que quieras datos frescos). Genera contribuyentes, predios, obligaciones IPU/ICA e historial de pagos con Faker. |
| `adapter.py` | El único punto por donde se debe tocar la base. Implementa 6 de los 7 métodos de la Tabla 7 (el séptimo, `get_predios_contribuyente`, se agrega en el Paso 2) y valida que un contribuyente no pueda consultar predios ajenos (RF-AUT-02). |
| `demo.py` | Prueba manual: llama al adaptador y muestra los resultados en consola, incluyendo el caso en que el acceso debe rechazarse. |
| `data/realtix_sintetico.db` | La base de datos generada (se crea sola al correr `generate_synthetic_data.py`; no viene en el paquete). |

Orden de dependencia: `models.py` y `database.py` no dependen de nada del
proyecto → `generate_synthetic_data.py` depende de `database.py`, y
`adapter.py` de `database.py` y `models.py` → `demo.py` depende de
`adapter.py`, `database.py` y `models.py`.

## 3. Requisitos

- **Python 3.10 o superior.** Se construyó y se probó con Python 3.12 y 3.14.7;
  cualquier versión 3.10+ funciona porque el código usa sintaxis de tipos
  moderna (`int | None`, `list[dict]`). El desarrollo del sistema multiagente
  de IA continúa en Python 3.12, la misma versión del contenedor. Si no tienes
  Python, instala **Python 3.12 desde [python.org/downloads](https://www.python.org/downloads/)**
  (evita la Microsoft Store — ver la sección de problemas más abajo).
- Visual Studio Code con la extensión **Python** (de Microsoft).
- Opcional: la extensión **SQLite Viewer** (de Florian Klampfer / qwtel) para
  ver la base de datos generada sin salir de VS Code.

## 4. Instalación y ejecución paso a paso

1. **Abre la carpeta completa** `realtix-mvp` en VS Code (Archivo > Abrir
   carpeta). No abras archivos sueltos — los `import` internos necesitan que
   VS Code y la terminal trabajen desde esta carpeta como raíz.

2. **Instala la extensión Python** desde el panel de Extensiones
   (Ctrl+Shift+X), si no la tienes; selecciona la publicada por Microsoft.

3. **Abre una terminal** (Terminal > Nueva Terminal) y crea un entorno
   virtual:
   ```
   python -m venv venv
   ```

4. **Activa el entorno virtual:**
   - Windows (PowerShell): `venv\Scripts\activate`
   - macOS / Linux: `source venv/bin/activate`

   Debe aparecer `(venv)` al inicio de la línea. Si VS Code te pregunta si
   quieres usar ese intérprete, dile que sí (o selecciónalo manualmente con
   Ctrl+Shift+P > "Python: Select Interpreter").

5. **Instala las dependencias:**
   ```
   pip install -r requirements.txt
   ```
   (Solo instala Faker — todo lo demás que usa el proyecto ya viene con Python.)

6. **Genera la base de datos sintética:**
   ```
   python generate_synthetic_data.py --contribuyentes 150 --seed 42
   ```
   Debe imprimir algo así:
   ```
   Contribuyentes: 150
   Predios: 170
   Obligaciones tributarias: 434
   Pagos registrados: 317
   Base de datos: ...\data\realtix_sintetico.db
   ```

7. **Corre la demo:**
   ```
   python demo.py
   ```
   Al final deberías ver una línea que dice `Rechazado correctamente -> ...` —
   esa es la prueba de que la protección de datos (RF-AUT-02) funciona.

## 5. Problemas comunes y solución

### "Python was not found; run without arguments to install from the Microsoft Store"
Windows no encuentra un Python real en el PATH. Antes de instalar nada,
prueba `py --version` en la misma terminal — si te da un número de versión,
ya tienes Python y puedes usar `py` en vez de `python` en todos los comandos
de este documento. Si `py --version` también falla:
1. Descarga el instalador desde python.org (no la Microsoft Store).
2. En la primera pantalla del instalador, marca **"Add python.exe to PATH"**
   antes de darle a Install Now — es el paso que casi todos se saltan.
3. Cierra y vuelve a abrir la terminal de VS Code (los cambios de PATH no
   aplican a terminales ya abiertas).
4. Si sigue sin funcionar, ve a Configuración de Windows > Aplicaciones >
   Configuración avanzada de aplicaciones > Alias de ejecución de
   aplicaciones, y apaga "python.exe" y "python3.exe".

### "No se puede cargar el archivo ...Activate.ps1 porque la ejecución de scripts está deshabilitada"
PowerShell bloquea scripts por defecto. Corre una sola vez (sin ser
administrador):
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Si te pregunta, confirma con `S` (o `Y`). Luego vuelve a intentar
`venv\Scripts\activate`.

### "ModuleNotFoundError: No module named 'faker'"
El entorno virtual no está activado, o no corriste `pip install -r
requirements.txt`. Revisa que la terminal muestre `(venv)` al inicio de la
línea; si no, repite el paso 4.

### "ModuleNotFoundError: No module named 'adapter'" (o 'database', 'models')
Pasa cuando estos módulos se importan desde un script o una consola de Python
ubicados en otra carpeta: Python busca los módulos del proyecto en la carpeta
del script que se ejecuta, o en la carpeta actual si es una consola. Ejecuta
los scripts de esta carpeta (`python demo.py` dentro de `realtix-mvp/`, o el
botón ▷ "Run Python File" de VS Code) y, si los vas a importar desde una
consola, ábrela dentro de `realtix-mvp/`. En la estructura `src/` del Paso 2
esto se resuelve con imports absolutos.

### "sqlite3.OperationalError: no such table: contribuyente"
Te faltó el paso 6 — `demo.py` necesita que la base de datos ya exista y
tenga datos. Corre `generate_synthetic_data.py` primero.

### Quiero ver los datos generados sin escribir SQL
Instala la extensión **SQLite Viewer** (autor: Florian Klampfer / qwtel) desde
el panel de Extensiones. Después, haz clic en `data/realtix_sintetico.db` en
el explorador de archivos de VS Code y se abre solo, con tablas navegables.

## 6. El contrato del adaptador (para cuando escribamos los agentes)

```python
from adapter import MockRealSitAdapter
adapter = MockRealSitAdapter()

adapter.get_estado_cuenta(predio_id, contribuyente_id)      -> EstadoCuenta
adapter.get_historial_pagos(predio_id, contribuyente_id)    -> list[Pago]
adapter.get_avaluo_catastral(predio_id, contribuyente_id)   -> Avaluo
adapter.get_tarifa_ica(actividad_economica)                 -> Tarifa
adapter.get_obligaciones_vigentes(predio_id, contribuyente_id, tributo) -> list[ObligacionTributaria]
adapter.registrar_caso_escalado(resumen)                    -> Ack
adapter.get_predios_contribuyente(contribuyente_id)         -> list[Predio]  # D1: se agrega en el Paso 2
```

**Nota respecto al documento de arquitectura:** el contrato es la Tabla 7, y
en la versión 2 ya muestra el parámetro `contribuyente_id`. La versión 1 no lo
mostraba, aunque su sección 6.1 ya exigía que "el adaptador de datos filtra
toda consulta contra el contexto autorizado"; este código se escribió con una
numeración anterior del documento y por eso llamaba "Tabla 5" al contrato.
Aquí quedó hecho código: si el predio no pertenece al contribuyente
autenticado, el adaptador lanza `PredioNoAutorizadoError` en vez de devolver
datos. El sistema multiagente de IA rechaza esa consulta con un mensaje
explícito, sin revelar datos del predio y sin escalar (decisión D3).

## 7. Qué falta (no es parte de esta actividad)

- Los agentes de LangGraph que van a *consumir* este adaptador (actividades
  6.3.4 y 6.3.5 del cronograma).
- La resolución real de `contribuyente_id` a partir del token de sesión del
  widget (por ahora se pasa directo, como lo haría el backend una vez
  resuelto el token).
- Migrar de SQLite a otra base si el volumen de la Fase 4 lo justifica — para
  el tamaño del MVP no hace falta.
