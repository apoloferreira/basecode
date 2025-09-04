from __future__ import annotations

import re
import sys
import json
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Iterable, Any, Dict

# Dependências opcionais são importadas defensivamente
try:
    import camelot
except Exception:
    camelot = None  # type: ignore

try:
    import pdfplumber
except Exception:
    pdfplumber = None  # type: ignore

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None  # type: ignore

try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None  # type: ignore

try:
    import pytesseract
except Exception:
    pytesseract = None  # type: ignore

try:
    from pydantic import BaseModel, ValidationError, field_validator
except Exception:
    BaseModel = object  # type: ignore
    ValidationError = Exception  # type: ignore

# OpenAI opcional (LLM assist)
try:
    import os
    from openai import OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
except Exception:
    OpenAI = None  # type: ignore
    OPENAI_API_KEY = None  # type: ignore


# -----------------------------
# Modelos & Utilitários
# -----------------------------

@dataclass
class Coord:
    lat: float
    lon: float

    def as_wkt_pair(self) -> str:
        # WKT usa ordem (lon lat)
        return f"{self.lon:.8f} {self.lat:.8f}"


class RowModel(BaseModel):  # type: ignore[misc]
    ponto: Optional[int] = None
    poligono: Optional[str] = None
    latitude: str
    longitude: str

    @field_validator("latitude", "longitude")
    @classmethod
    def strip_spaces(cls, v: str) -> str:
        return v.strip()


DMS_RE = re.compile(
    r"""
    ^\s*
    (?P<deg>[-+]?\d{1,3})\D+
    (?P<min>\d{1,2})\D+
    (?P<sec>\d{1,2}(?:[\.,]\d+)?)
    \s*(?P<hem>[NSEWnsew])?
    \s*$
    """,
    re.VERBOSE,
)

DECIMAL_RE = re.compile(r"^\s*[-+]?\d{1,3}(?:[\.,]\d+)?\s*$")

HEM_HINT_RE = re.compile(r"([NSEWnsew])")


def dms_to_decimal(deg: float, minutes: float, seconds: float, hemisphere: Optional[str]) -> float:
    dec = abs(deg) + minutes / 60.0 + seconds / 3600.0
    if (hemisphere and hemisphere.upper() in ("S", "W")) or float(deg) < 0:
        dec = -dec
    return dec


def parse_angle(s: str, is_lat: bool) -> float:
    """Aceita decimal com vírgula/ponto e DMS com hemisférios.
    - is_lat=True: valida faixa [-90, 90]
    - is_lat=False: valida faixa [-180, 180]
    """
    s_clean = s.strip()

    # Troca vírgula por ponto
    s_std = s_clean.replace(",", ".")

    # 1) Decimal simples
    if DECIMAL_RE.match(s_clean):
        val = float(s_std)
    else:
        # 2) Procurar hemisfério explícito no fim/início
        hem_match = HEM_HINT_RE.search(s_clean)
        hemisphere = hem_match.group(1).upper() if hem_match else None
        m = DMS_RE.match(s_clean)
        if not m:
            # Tentar formatos como 23 33 01 S
            parts = re.split(r"\s+", s_clean)
            if len(parts) >= 3:
                try:
                    deg = float(parts[0])
                    minutes = float(parts[1])
                    seconds = float(parts[2])
                    if len(parts) > 3 and parts[3].upper() in ("N", "S", "E", "W"):
                        hemisphere = parts[3].upper()
                    return dms_to_decimal(deg, minutes, seconds, hemisphere)
                except Exception as e:
                    raise ValueError(f"Ângulo inválido: {s_clean}") from e
            raise ValueError(f"Ângulo inválido: {s_clean}")
        deg = float(m.group("deg"))
        minutes = float(m.group("min"))
        seconds = float(m.group("sec").replace(",", "."))
        val = dms_to_decimal(deg, minutes, seconds, m.group("hem"))

    # Validação de faixa
    if is_lat and not (-90 <= val <= 90):
        raise ValueError(f"Latitude fora de faixa: {val}")
    if not is_lat and not (-180 <= val <= 180):
        raise ValueError(f"Longitude fora de faixa: {val}")
    return val


# -----------------------------
# Extração de tabelas
# -----------------------------

def extract_with_camelot(pdf_path: str) -> List[Dict[str, Any]]:
    if camelot is None:
        return []
    tables: List[Dict[str, Any]] = []
    try:
        # Tentar lattice (linhas) e stream (texto)
        for flavor in ("lattice", "stream"):
            try:
                t = camelot.read_pdf(pdf_path, pages="all", flavor=flavor)
                for tbl in t:
                    data = [row for row in tbl.df.values.tolist()]
                    tables.append({"headers": data[0], "rows": data[1:]})
                if tables:
                    return tables
            except Exception:
                continue
    except Exception:
        pass
    return tables


def extract_with_pdfplumber(pdf_path: str) -> List[Dict[str, Any]]:
    if pdfplumber is None:
        return []
    out: List[Dict[str, Any]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                try:
                    tables = page.extract_tables()
                    for tb in tables or []:
                        if not tb:
                            continue
                        headers, rows = tb[0], tb[1:]
                        out.append({"headers": headers, "rows": rows})
                except Exception:
                    continue
    except Exception:
        pass
    return out


def ocr_page_images(pdf_path: str) -> List[Any]:
    if convert_from_path is None:
        return []
    try:
        images = convert_from_path(pdf_path, dpi=300)
        return images
    except Exception:
        return []


def extract_with_ocr(pdf_path: str, lang: str = "por+eng") -> List[Dict[str, Any]]:
    if pytesseract is None:
        return []
    images = ocr_page_images(pdf_path)
    out: List[Dict[str, Any]] = []
    for img in images:
        try:
            text = pytesseract.image_to_string(img, lang=lang)
            # Heurística simples: linhas -> células por separadores ; , | ou múltiplos espaços
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            # Detectar cabeçalho por presença de palavras-chave
            header_idx = None
            for i, ln in enumerate(lines[:10]):
                if re.search(r"ponto|pt|latitude|longitude|lat|lon", ln, flags=re.I):
                    header_idx = i
                    break
            if header_idx is None:
                # fallback: assumir primeira linha como cabeçalho
                header_idx = 0
            headers = re.split(r"\s*[;|,\t]|\s{2,}\s*", lines[header_idx])
            rows: List[List[str]] = []
            for ln in lines[header_idx + 1 : ]:
                cells = re.split(r"\s*[;|,\t]|\s{2,}\s*", ln)
                if len(cells) >= 2:
                    rows.append(cells)
            out.append({"headers": headers, "rows": rows})
        except Exception:
            continue
    return out


# -----------------------------
# Parsing tabular para linhas padronizadas
# -----------------------------

HEADER_ALIASES = {
    "ponto": {"ponto", "pt", "id", "indice", "#", "n", "n."},
    "lat": {"latitude", "lat", "y"},
    "lon": {"longitude", "lon", "x"},
    "poligono": {"poligono", "polígono", "area", "área", "grupo"},
}


def normalize_header(h: str) -> str:
    h = (h or "").strip().lower()
    for key, aliases in HEADER_ALIASES.items():
        if h in aliases:
            return key
    return h


def rows_from_table(tbl: Dict[str, Any]) -> List[RowModel]:
    headers = [normalize_header(h or "") for h in (tbl.get("headers") or [])]
    idx_ponto = next((i for i, h in enumerate(headers) if h == "ponto"), None)
    idx_lat = next((i for i, h in enumerate(headers) if h in ("lat", "latitude")), None)
    idx_lon = next((i for i, h in enumerate(headers) if h in ("lon", "longitude")), None)
    idx_pol = next((i for i, h in enumerate(headers) if h == "poligono"), None)

    rows: List[RowModel] = []
    for raw in tbl.get("rows") or []:
        def at(i: Optional[int]) -> Optional[str]:
            if i is None:
                return None
            if i < len(raw):
                return None if raw[i] is None else str(raw[i])
            return None
        lat_s = at(idx_lat)
        lon_s = at(idx_lon)
        if not lat_s or not lon_s:
            # Heurística: procurar strings que pareçam ângulos
            candidates = [str(x) for x in raw if isinstance(x, str)]
            angles = [c for c in candidates if DMS_RE.search(c) or DECIMAL_RE.match(c)]
            if len(angles) >= 2:
                lat_s, lon_s = angles[0], angles[1]
            else:
                continue
        ponto_val = at(idx_ponto)
        try:
            ponto_int = int(re.sub(r"\D", "", ponto_val)) if ponto_val else None
        except Exception:
            ponto_int = None
        pol_val = at(idx_pol)
        try:
            item = RowModel(ponto=ponto_int, poligono=(pol_val or None), latitude=lat_s, longitude=lon_s)
            rows.append(item)
        except ValidationError:
            continue
    return rows


# -----------------------------
# Agrupamento em polígonos e WKT
# -----------------------------

def group_rows_into_polygons(rows: List[RowModel]) -> List[List[Coord]]:
    if not rows:
        return []
    # 1) Se houver coluna poligono, agrupar por ela
    groups: Dict[str, List[RowModel]] = {}
    has_pol = any(r.poligono for r in rows)
    if has_pol:
        for r in rows:
            key = r.poligono or "_"
            groups.setdefault(key, []).append(r)
        ordered_groups = [groups[k] for k in sorted(groups.keys())]
    else:
        # 2) Agrupar por reinício de ponto (ponto == 1 reinicia)
        ordered_groups = []
        cur: List[RowModel] = []
        last_ponto = None
        for r in rows:
            if r.ponto == 1 and cur:
                ordered_groups.append(cur)
                cur = []
            cur.append(r)
            last_ponto = r.ponto
        if cur:
            ordered_groups.append(cur)
        if len(ordered_groups) == 1:
            # 3) Caso não haja pista, tudo em um único polígono
            ordered_groups = [rows]

    polygons: List[List[Coord]] = []
    for grp in ordered_groups:
        coords: List[Coord] = []
        for r in grp:
            lat = parse_angle(r.latitude, is_lat=True)
            lon = parse_angle(r.longitude, is_lat=False)
            coords.append(Coord(lat=lat, lon=lon))
        # Remover duplicados consecutivos
        dedup: List[Coord] = []
        for c in coords:
            if not dedup or (abs(dedup[-1].lat - c.lat) > 1e-9 or abs(dedup[-1].lon - c.lon) > 1e-9):
                dedup.append(c)
        # Fechar anel
        if dedup and (abs(dedup[0].lat - dedup[-1].lat) > 1e-9 or abs(dedup[0].lon - dedup[-1].lon) > 1e-9):
            dedup.append(dedup[0])
        polygons.append(dedup)
    return polygons


def polygons_to_wkt(polys: List[List[Coord]]) -> List[str]:
    wkts: List[str] = []
    for coords in polys:
        pairs = ", ".join(c.as_wkt_pair() for c in coords)
        wkts.append(f"POLYGON(({pairs}))")
    return wkts


# -----------------------------
# Pipeline principal
# -----------------------------

def extract_tables_any(pdf_path: str) -> List[Dict[str, Any]]:
    # Ordem de tentativa
    for extractor in (extract_with_camelot, extract_with_pdfplumber, extract_with_ocr):
        try:
            tables = extractor(pdf_path)
            if tables:
                return tables
        except Exception:
            continue
    return []


def llm_assisted_rows(raw_tables: List[Dict[str, Any]]) -> List[RowModel]:
    """Opcional: usa LLM para normalizar cabeçalhos/células em casos ambíguos.
    Requer OPENAI_API_KEY.
    """
    if not OPENAI_API_KEY or OpenAI is None:
        return []
    client = OpenAI()
    # Monta prompt conciso com amostra das tabelas
    sample = raw_tables[:3]
    prompt = (
        "Você receberá tabelas extraídas de um PDF com colunas relacionadas a ponto, latitude e longitude. "
        "Retorne JSON com uma lista 'rows' onde cada item possui: ponto (int opcional), poligono (str opcional), "
        "latitude (str), longitude (str). Não invente valores. Apenas reorganize e selecione colunas corretas.\n\n"
        f"Tabelas:\n{json.dumps(sample, ensure_ascii=False)}\n\n"
        "Responda APENAS com JSON válido com a chave 'rows'."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        rows: List[RowModel] = []
        for item in data.get("rows", []):
            try:
                rows.append(RowModel(**item))
            except ValidationError:
                continue
        return rows
    except Exception:
        return []


def extract_polygons_wkt(pdf_path: str) -> List[str]:
    raw_tables = extract_tables_any(pdf_path)
    rows: List[RowModel] = []
    for tb in raw_tables:
        rows.extend(rows_from_table(tb))

    if not rows:
        # tentativa final com LLM assistido
        rows = llm_assisted_rows(raw_tables)

    if not rows:
        raise RuntimeError("Não foi possível extrair coordenadas do PDF.\n"
                           "Verifique se a tabela está legível; tente instalar camelot/pdfplumber/tesseract.")

    polygons = group_rows_into_polygons(rows)
    if not polygons:
        raise RuntimeError("Coordenadas não formaram polígonos válidos.")

    return polygons_to_wkt(polygons)


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python pdf_to_wkt.py /caminho/arquivo.pdf", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    wkts = extract_polygons_wkt(path)
    for w in wkts:
        print(w)