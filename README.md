# danielgalea7.github.io · Portfolio

Portfolio de **Daniel Galea Romero**, Data Analyst junior con el Google Cloud Data Analytics Certificate. Bilingüe (ES/EN), claro/oscuro, sin frameworks.

**Web:** https://danielgalea7.github.io · **Caso estrella:** [TheLook Fintech](https://danielgalea7.github.io/caso/thelook-fintech/)

## Qué hay dentro
- `/` y `/en/`: sobre mí, *data journey* interactivo, proyecto estrella, 4 proyectos prácticos con su SQL, stack, certificado y contacto.
- `/caso/thelook-fintech/` y `/en/case-study/thelook-fintech/`: problema → datos → SQL en BigQuery → dashboard en Looker → insights → recomendaciones → qué aprendí.
- Todos los gráficos usan **datos reales** consultados en el BigQuery sandbox el 12/10/2026 (`data/`): `cloud-training-demos.fintech` (capstone) y `bigquery-public-data.thelook_ecommerce` (sintético; foto a esa fecha).

## Cómo se construye
```bash
python3 tools/build.py              # genera el HTML de las 4 páginas desde data/*.json
node tools/shots.mjs og             # imágenes Open Graph (Playwright)
node tools/shots.mjs shots http://localhost:8765   # capturas de verificación
```
HTML, CSS y JS propios; fuentes autoalojadas (Inter, Instrument Serif, JetBrains Mono, licencia OFL); gráficos en HTML/SVG generados en el build, con tabla de datos accesible. Lighthouse local: 97–100 en todas las categorías.

## Publicación
GitHub Pages desde la rama `main` (repo `Danielgalea7.github.io`). `vercel.json` permite desplegarlo también en Vercel sin cambios.
