# MDF Extractor – Guía de Uso

Herramienta de extracción y conversión de diccionarios lingüísticos al formato estructurado MDF (Machine-Readable Dictionary Format).

---

## Descripción

`mdf_extractor.py` recibe archivos de diccionario en formato `.txt`, `.docx` o `.pdf` y produce una salida estructurada en **JSON**, **YAML** o **MDF etiquetado**, siguiendo el esquema de etiquetas definido para los diccionarios maya, popoluca, iskonawa, zapoteco y náhuatl.

---

## Requisitos

Python 3.7 o superior. Instalar dependencias:

```bash
pip install pyyaml python-docx PyMuPDF
```

| Paquete | Necesario para |
|---|---|
| `pyyaml` | Salida en formato YAML |
| `python-docx` | Leer archivos `.docx` |
| `PyMuPDF` | Leer archivos `.pdf` |

> Para solo procesar archivos `.txt`, no se requieren paquetes externos.

---

## Uso básico

```bash
python mdf_extractor.py <archivo_entrada> [opciones]
```

### Opciones

| Opción | Descripción | Valores posibles | Por defecto |
|---|---|---|---|
| `--format` / `-f` | Formato de salida | `json`, `yaml`, `mdf` | `json` |
| `--output` / `-o` | Archivo de salida | ruta de archivo | stdout |
| `--indent` | Nivel de indentación JSON | número entero | `2` |

---

## Ejemplos de uso

### Convertir un `.txt` a JSON (stdout)
```bash
python mdf_extractor.py diccionario_iskonawa.txt
```

### Convertir un `.txt` a JSON y guardar archivo
```bash
python mdf_extractor.py diccionario_iskonawa.txt --format json --output salida_iskonawa.json
```

### Convertir un `.pdf` a YAML
```bash
python mdf_extractor.py diccionario_maya.pdf --format yaml --output salida_maya.yaml
```

### Convertir un `.docx` a YAML
```bash
python mdf_extractor.py diccionario_nahuatl.docx --format yaml --output salida_nahuatl.yaml
```

### Producir salida en formato MDF etiquetado (`\tag`)
```bash
python mdf_extractor.py diccionario_zapoteco.txt --format mdf --output salida_zapoteco.mdf
```

---

## Etiquetas MDF soportadas

| Etiqueta | Descripción |
|---|---|
| `\id` | Número de identificador de entrada |
| `\lx` | Lexema / headword (entrada principal) |
| `\ps` | Parte de la oración |
| `\sn` | Número de sentido / acepción |
| `\se` | Subentrada |
| `\ph` | Transcripción fonética |
| `\mr` | Representación morfológica |
| `\de` | Definición en inglés |
| `\dn` | Definición en español |
| `\ge` | Glosa en inglés |
| `\gn` | Glosa en español |
| `\xv` | Ejemplo en lengua vernácula *(repetible)* |
| `\xe` | Traducción del ejemplo al inglés *(repetible)* |
| `\xn` | Traducción del ejemplo al español *(repetible)* |
| `\rf` | Fuente del ejemplo *(repetible)* |
| `\cf` | Referencia cruzada genérica |
| `\lf` | Función léxica |
| `\lv` | Lexema relacionado en red semántica |
| `\wv` | Archivo de audio |
| `\vd` | Archivo de video |
| `\nt` | Notas generales |
| `\et` | Etimología |
| `\sc` | Nombre científico |
| `\lo` | Localidad de registro |
| `\pc` | Archivo de imagen |

---

## Modos de detección

El extractor detecta automáticamente si el archivo ya usa etiquetado MDF (`\tag`) o si es texto plano sin etiquetar:

- **Formato MDF etiquetado**: el programa parsea directamente los marcadores `\tag`.
- **Texto plano (heurístico)**: el programa intenta identificar entradas léxicas, partes del discurso y definiciones mediante patrones lingüísticos.

---

## Estructura de la salida JSON

```json
[
  {
    "id": "1",
    "lx": "áaktun",
    "ps": "s.",
    "sn": "1",
    "se": "",
    "ph": "",
    "mr": "",
    "de": "",
    "dn": "caverna, cueva, gruta",
    "ge": "",
    "gn": "",
    "xv": ["Ka p'áato'ob j kajtal te' áaktuno'"],
    "xe": [],
    "xn": ["Se quedaron a vivir en esa cueva"],
    "rf": ["CY1:146"],
    "cf": "", "lf": "", "lv": "", "wv": "", "vd": "",
    "nt": "", "et": "", "sc": "", "lo": "", "pc": ""
  }
]
```

> Los campos repetibles (`xv`, `xe`, `xn`, `rf`) se representan como listas. Los demás campos son cadenas de texto.

---

## Notas

- El programa procesa correctamente Unicode completo (caracteres diacríticos, IPA, lenguas indígenas).
- Las entradas sin `\id` explícito reciben un identificador secuencial automático.
- Las entradas sin `\sn` reciben el valor `"1"` por defecto.
- Los campos vacíos se representan como cadena vacía `""` o lista vacía `[]`.

# Instalar dependencias
pip install pyyaml python-docx PyMuPDF

# Convertir a JSON
python mdf_extractor.py mi_diccionario.txt --format json --output salida.json

# Convertir a YAML
python mdf_extractor.py mi_diccionario.pdf --format yaml --output salida.yaml

# Producir MDF etiquetado
python mdf_extractor.py mi_diccionario.docx --format mdf --output salida.mdf