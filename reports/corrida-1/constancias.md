**Modo de evaluación (A9): encendido solo durante la corrida.**

1. Antes de lanzar la corrida, `./deploy/desplegar.sh --version v0.9.0 --evaluacion` lo encendió:
   «Desplegado: v0.9.0 (modo de evaluación: true)».
2. La corrida (sistema, juez, componentes y RAGAS) corrió sin interrupciones. Las respuestas
   trajeron `tokens_por_modelo`, que solo existe en ese modo.
3. Apenas terminaron los ensayos, `./deploy/desplegar.sh --version v0.9.0` lo apagó: «Desplegado:
   v0.9.0 (modo de evaluación: false)».
4. Se comprobó desde fuera. Una consulta con `X-Reloj-Simulado` de un jueves a las 10:00 recibió
   el aviso de fuera de horario con el reloj real (madrugada), y sin `tokens_por_modelo`: el
   servidor ya ignora el reloj simulado. No hubo llamada a ningún modelo.

**Versión evaluada.** El commit `805f2efb9600b1262a25ecd3e2a1e481eee3a057` (etiqueta `v0.9.0`), el
mismo de `git rev-parse HEAD` en el servidor antes y después de la corrida.

**Solo lectura de RealSit (RF-SYS-02).** La huella de la base sintética fue
`4479d0369ba967a2d8ed40fb6e7d12bff1ed497ad86ce230093f0c857312d0a2` antes y después de la corrida:
idéntica, e igual a `src/data/huella_realsit.sha256`.

**Trazas (adenda 15, RNF-05).** Este equipo no tiene la llave de LangSmith, así que la revisión se
hizo en el servidor. Se usó la misma función `revisar_ejecuciones` de `src/evaluacion/trazas_eval.py`,
dentro del contenedor del backend y con su `.env`, sin imprimir ningún secreto. Se revisaron las
ejecuciones de las 6 horas anteriores que pertenecen a conversaciones `corrida-1-*`: 71 trazas, 63
conversaciones y 1.279 ejecuciones, ninguna con identificadores de los usuarios de prueba. Faltan 2
de las 65 conversaciones: las de horario, que la API responde antes del grafo. Los componentes
corren en este equipo, sin trazas. El resultado está en `trazas.json`.

**Latencia del cliente.** En 45 de 68 turnos, la del cliente salió menor que la del servidor (mediana
de −69 ms; mínimo de −714 ms), lo que no es posible físicamente. El cronómetro del cliente corre en
WSL 2, y lo más probable es una deriva de su reloj. La meta de RNF-01 usa la del servidor
(`meta.tiempos_ms.total`; A9). La del cliente se reporta con esa limitación, y para la corrida 3
conviene medirla fuera de WSL 2. El desglose está en `latencia.md`.
