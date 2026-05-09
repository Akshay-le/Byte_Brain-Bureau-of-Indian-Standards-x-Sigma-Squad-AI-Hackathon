
import os
import json
import time
import re
import math
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).parent.parent
_CHUNKS_PATH = _ROOT / "data" / "chunks.json"

_FALLBACK_DB = [
    # ── CEMENT ──────────────────────────────────────────────────────────────
    {"id":"IS_269","standard":"IS 269","title":"Ordinary Portland Cement – Specification","category":"Cement","keywords":["cement","ordinary portland cement","opc","binding","concrete","mortar","construction"],"summary":"Specifies OPC used in general civil construction. Covers chemical composition, physical requirements, strength grades 33/43/53, and test methods.","year":"2015"},
    {"id":"IS_455","standard":"IS 455","title":"Portland Slag Cement – Specification","category":"Cement","keywords":["slag cement","portland slag","psc","blast furnace","cement","concrete"],"summary":"Covers Portland Slag Cement (PSC) made by intergrinding Portland cement clinker with granulated blast furnace slag. Suitable for marine and hydraulic structures.","year":"2015"},
    {"id":"IS_1489_1","standard":"IS 1489 (Part 1)","title":"Portland Pozzolana Cement – Fly Ash Based – Specification","category":"Cement","keywords":["pozzolana cement","ppc","fly ash","cement","concrete","mortar"],"summary":"Fly-ash based Portland Pozzolana Cement (PPC). Fly ash content 15–35%. Reduced heat of hydration.","year":"2015"},
    {"id":"IS_8112","standard":"IS 8112","title":"43 Grade Ordinary Portland Cement – Specification","category":"Cement","keywords":["43 grade cement","opc 43","ordinary portland cement","cement"],"summary":"43 Grade OPC with 28-day compressive strength not less than 43 MPa.","year":"2013"},
    {"id":"IS_12269","standard":"IS 12269","title":"53 Grade Ordinary Portland Cement – Specification","category":"Cement","keywords":["53 grade cement","opc 53","high strength cement","structural cement"],"summary":"53 Grade OPC with 28-day compressive strength not less than 53 MPa. Used in high-strength concrete mixes.","year":"2013"},
    # ── STEEL ────────────────────────────────────────────────────────────────
    {"id":"IS_1786","standard":"IS 1786","title":"High Strength Deformed Steel Bars and Wires for Concrete Reinforcement – Specification","category":"Steel","keywords":["tmt bars","steel bars","reinforcement","rebar","deformed bars","fe415","fe500","fe550","fe600","steel reinforcement","concrete reinforcement"],"summary":"Covers HSD steel bars (TMT bars) grades Fe 415/500/550/600 for RCC and prestressed concrete.","year":"2008"},
    {"id":"IS_2062","standard":"IS 2062","title":"Hot Rolled Medium and High Tensile Structural Steel – Specification","category":"Steel","keywords":["structural steel","mild steel","ms plate","steel plate","angle","channel","beam","ismb","hot rolled steel"],"summary":"Hot-rolled structural steel plates, sections, bars. Grades E250–E650. Used in steel structures and bridges.","year":"2011"},
    {"id":"IS_432_1","standard":"IS 432 (Part 1)","title":"Mild Steel and Medium Tensile Steel Bars for Concrete Reinforcement","category":"Steel","keywords":["mild steel bars","plain bars","reinforcement bar","ms bar"],"summary":"Specifies plain mild steel bars used as concrete reinforcement.","year":"1982"},
    {"id":"IS_6003","standard":"IS 6003","title":"Indented Wire for Prestressed Concrete – Specification","category":"Steel","keywords":["prestressed wire","indented wire","prestressed concrete","pc wire","high tensile wire"],"summary":"High-tensile indented wire for prestressed concrete.","year":"2010"},
    # ── CONCRETE ─────────────────────────────────────────────────────────────
    {"id":"IS_456","standard":"IS 456","title":"Plain and Reinforced Concrete – Code of Practice","category":"Concrete","keywords":["concrete","rcc","reinforced concrete","plain concrete","concrete mix","m20","m25","m30","structural concrete","concrete code"],"summary":"Primary code for plain and reinforced concrete structures. Grades M10–M80, mix design, durability.","year":"2000"},
    {"id":"IS_10262","standard":"IS 10262","title":"Concrete Mix Proportioning – Guidelines","category":"Concrete","keywords":["concrete mix design","mix proportioning","concrete mix","water cement ratio","trial mix"],"summary":"Guidelines for proportioning concrete mixes to achieve desired strength and workability.","year":"2019"},
    {"id":"IS_516","standard":"IS 516","title":"Method of Tests for Strength of Concrete","category":"Concrete","keywords":["concrete testing","cube test","compressive strength test","concrete strength","flexural strength"],"summary":"Test methods for compressive, flexural, and tensile splitting strength of concrete.","year":"2018"},
    # ── AGGREGATES ───────────────────────────────────────────────────────────
    {"id":"IS_383","standard":"IS 383","title":"Coarse and Fine Aggregates for Concrete – Specification","category":"Aggregates","keywords":["aggregates","coarse aggregate","fine aggregate","sand","gravel","crushed stone","river sand","m-sand","manufactured sand"],"summary":"Natural and manufactured aggregates for concrete. Grading, deleterious substances, physical/chemical requirements.","year":"2016"},
    {"id":"IS_2386_1","standard":"IS 2386 (Part 1)","title":"Methods of Test for Aggregates – Particle Size and Shape","category":"Aggregates","keywords":["aggregate testing","sieve analysis","particle size","grading","flakiness index","elongation index"],"summary":"Methods to determine particle size distribution and shape characteristics of aggregates.","year":"2016"},
    {"id":"IS_2386_3","standard":"IS 2386 (Part 3)","title":"Methods of Test for Aggregates – Specific Gravity, Density, Voids, Absorption","category":"Aggregates","keywords":["aggregate density","specific gravity","water absorption","voids","aggregate testing"],"summary":"Test methods for specific gravity, bulk density, voids, water absorption of aggregates.","year":"2016"},
    {"id":"IS_2386_4","standard":"IS 2386 (Part 4)","title":"Methods of Test for Aggregates – Mechanical Properties","category":"Aggregates","keywords":["aggregate impact value","aggregate crushing value","los angeles abrasion","aggregate strength"],"summary":"Test methods for AIV, ACV, Los Angeles abrasion, and 10% fines value.","year":"2016"},
    # ── BRICKS & MASONRY ─────────────────────────────────────────────────────
    {"id":"IS_1077","standard":"IS 1077","title":"Common Burnt Clay Building Bricks – Specification","category":"Bricks & Masonry","keywords":["bricks","clay bricks","burnt clay bricks","masonry","red bricks","building bricks"],"summary":"Common burnt clay building bricks. Classes by compressive strength. Water absorption and efflorescence requirements.","year":"1992"},
    {"id":"IS_2185_1","standard":"IS 2185 (Part 1)","title":"Concrete Masonry Units – Hollow and Solid Concrete Blocks","category":"Bricks & Masonry","keywords":["concrete blocks","hollow blocks","solid blocks","masonry blocks","cmu","block masonry"],"summary":"Hollow and solid concrete masonry blocks – dimensions, grades, physical requirements.","year":"2005"},
    {"id":"IS_2185_3","standard":"IS 2185 (Part 3)","title":"Autoclaved Cellular (Aerated) Concrete Blocks","category":"Bricks & Masonry","keywords":["aac blocks","autoclaved aerated concrete","cellular concrete","lightweight blocks","aac masonry"],"summary":"AAC blocks for masonry. Density grades, compressive strength, thermal insulation requirements.","year":"1984"},
    {"id":"IS_3495_1","standard":"IS 3495 (Part 1)","title":"Methods of Tests for Burnt Clay Building Bricks – Compressive Strength","category":"Bricks & Masonry","keywords":["brick testing","brick strength","compressive strength brick","clay brick test"],"summary":"Method for determining compressive strength of burnt clay bricks.","year":"1992"},
    # ── MORTAR ───────────────────────────────────────────────────────────────
    {"id":"IS_2250","standard":"IS 2250","title":"Preparation and Use of Masonry Mortars – Code of Practice","category":"Mortar","keywords":["mortar","masonry mortar","cement mortar","lime mortar","brickwork mortar","plastering mortar"],"summary":"Materials, mix proportions, preparation, and use of masonry mortars (cement, lime, composite).","year":"1981"},
    # ── SCMs ─────────────────────────────────────────────────────────────────
    {"id":"IS_3812_1","standard":"IS 3812 (Part 1)","title":"Pulverised Fuel Ash – Specification for Use as Pozzolana","category":"Supplementary Cementitious Materials","keywords":["fly ash","pfa","pulverised fuel ash","pozzolana","supplementary cementitious","admixture"],"summary":"Fly ash (PFA) requirements for use as pozzolanic material in cement and concrete.","year":"2003"},
    # ── ADMIXTURES ───────────────────────────────────────────────────────────
    {"id":"IS_9103","standard":"IS 9103","title":"Concrete Admixtures – Specification","category":"Admixtures","keywords":["admixture","plasticiser","superplasticiser","retarder","accelerator","concrete admixture","chemical admixture"],"summary":"Chemical admixtures for concrete: plasticisers, superplasticisers, retarders, accelerators, air-entraining agents.","year":"1999"},
    # ── GLASS ────────────────────────────────────────────────────────────────
    {"id":"IS_2835","standard":"IS 2835","title":"Flat Transparent Sheet Glass – Specification","category":"Glass","keywords":["glass","sheet glass","window glass","flat glass","transparent glass","glazing"],"summary":"Quality, dimensions, and tolerances for flat transparent sheet glass for general glazing.","year":"1987"},
    {"id":"IS_2553_1","standard":"IS 2553 (Part 1)","title":"Safety Glass – Specification (General Purpose)","category":"Glass","keywords":["safety glass","toughened glass","tempered glass","laminated glass","glass safety"],"summary":"Safety glass (toughened or laminated) requirements for buildings and vehicles.","year":"1990"},
    # ── PIPES ─────────────────────────────────────────────────────────────────
    {"id":"IS_1239_1","standard":"IS 1239 (Part 1)","title":"Mild Steel Tubes, Tubulars and Other Wrought Steel Fittings – Specification","category":"Pipes & Tubes","keywords":["ms pipe","mild steel tube","gi pipe","galvanised pipe","steel pipe","plumbing pipe","water pipe"],"summary":"Mild steel and GI pipes for water, gas, and steam. Light, medium, heavy duty classes.","year":"2004"},
    {"id":"IS_4985","standard":"IS 4985","title":"Unplasticised PVC Pipes for Potable Water Supplies – Specification","category":"Pipes & Tubes","keywords":["upvc pipe","pvc pipe","water pipe","plastic pipe","potable water pipe"],"summary":"uPVC pressure pipes for conveying potable water.","year":"2000"},
    # ── TILES ────────────────────────────────────────────────────────────────
    {"id":"IS_13630","standard":"IS 13630","title":"Ceramic Tiles – Methods of Test","category":"Tiles","keywords":["ceramic tiles","floor tiles","wall tiles","tiles testing","vitrified tiles"],"summary":"Test methods for ceramic tiles: dimensions, surface quality, water absorption, breaking strength.","year":"2006"},
    {"id":"IS_15622","standard":"IS 15622","title":"Pressed Ceramic Tiles – Specification","category":"Tiles","keywords":["ceramic tiles","pressed tiles","vitrified tiles","porcelain tiles","floor tiles specification"],"summary":"Dry/semi-dry-pressed ceramic tiles. Dimensions, tolerances, water absorption, mechanical properties.","year":"2006"},
    # ── WATERPROOFING ────────────────────────────────────────────────────────
    {"id":"IS_2645","standard":"IS 2645","title":"Integral Cement Waterproofing Compounds – Specification","category":"Waterproofing","keywords":["waterproofing","waterproof compound","integral waterproofing","cement waterproofing","admixture waterproofing"],"summary":"Integral cement waterproofing compounds added to concrete or mortar.","year":"2005"},
    # ── TIMBER ───────────────────────────────────────────────────────────────
    {"id":"IS_1708","standard":"IS 1708","title":"Methods of Testing of Small Clear Specimens of Timber","category":"Timber","keywords":["timber","wood","timber testing","lumber","modulus of rupture","wood strength"],"summary":"Methods for testing small clear specimens of timber for strength properties.","year":"1986"},
    # ── DOORS & WINDOWS ──────────────────────────────────────────────────────
    {"id":"IS_1038","standard":"IS 1038","title":"Steel Doors, Windows and Ventilators – Specification","category":"Doors & Windows","keywords":["steel door","steel window","steel ventilator","metal door","metal window"],"summary":"Materials, dimensions, and performance requirements for steel doors, windows, and ventilators.","year":"1983"},
]



def _load_chunks_from_pdf(path: Path) -> Optional[List[Dict]]:
    """
    Load chunks from data/chunks.json (produced by ingest.py).
    Each chunk: chunk_id, standard (optional), text, page (optional).
    Returns None if file doesn't exist or is malformed.
    """
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        if not isinstance(chunks, list) or len(chunks) == 0:
            return None
        logger.info(f"[RAG] Loaded {len(chunks)} chunks from {path}")
        return chunks
    except Exception as e:
        logger.warning(f"[RAG] Could not load chunks from {path}: {e}")
        return None


def _guess_category(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["cement", "opc", "ppc", "psc"]): return "Cement"
    if any(w in t for w in ["steel", "tmt", "rebar", "bar", "structural"]): return "Steel"
    if any(w in t for w in ["concrete", "rcc", "mix design"]): return "Concrete"
    if any(w in t for w in ["aggregate", "sand", "gravel", "crushed"]): return "Aggregates"
    if any(w in t for w in ["brick", "block", "masonry", "aac"]): return "Bricks & Masonry"
    if any(w in t for w in ["tile", "ceramic", "vitrified"]): return "Tiles"
    if any(w in t for w in ["pipe", "tube", "pvc", "upvc"]): return "Pipes & Tubes"
    if any(w in t for w in ["glass", "glazing"]): return "Glass"
    if any(w in t for w in ["waterproof", "damp"]): return "Waterproofing"
    if any(w in t for w in ["admixture", "plasticiser", "superplasticiser"]): return "Admixtures"
    if any(w in t for w in ["fly ash", "pozzolana", "slag"]): return "SCM"
    return "Building Materials"


def _guess_year(text: str) -> str:
    m = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", text)
    return m.group(1) if m else ""


def _chunks_to_docs(chunks: List[Dict]) -> List[Dict]:

    docs = []
    for c in chunks:
        text = c.get("text", "")
        std_id = c.get("standard", "").strip()
        if not std_id:
            m = re.search(r"\bIS\s*[\d]+(?:\s*[\(\-]\s*(?:PART|Part)\s*\d+\s*[\)\-])?", text, re.I)
            std_id = m.group(0).strip().upper() if m else f"CHUNK_{c.get('chunk_id','?')}"

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        title = lines[0][:120] if lines else std_id
        keywords = list(set(re.findall(r"[a-zA-Z]{3,}", text.lower())))[:40]

        docs.append({
            "id": c.get("chunk_id", std_id),
            "standard": std_id.upper(),
            "title": title,
            "category": c.get("category", _guess_category(text)),
            "keywords": keywords,
            "summary": text[:400],
            "year": c.get("year", _guess_year(text)),
            "_raw_text": text,
        })
    return docs



def _tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if len(t) > 2]


def _build_index(docs: List[Dict]) -> Dict:
    corpus_tokens = []
    for doc in docs:
        raw = doc.get("_raw_text", "")
        base = f"{doc.get('title','')} {doc.get('category','')} {' '.join(doc.get('keywords',[]))} {doc.get('summary','')}"
        tokens = _tokenize(raw if raw else base)
        corpus_tokens.append(tokens)

    N = len(docs)
    df: Counter = Counter()
    for tokens in corpus_tokens:
        for t in set(tokens):
            df[t] += 1
    idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}

    vectors = []
    for tokens in corpus_tokens:
        tf = Counter(tokens)
        total = len(tokens) or 1
        vec = {t: (tf[t] / total) * idf.get(t, 1) for t in tf}
        vectors.append(vec)

    return {"idf": idf, "vectors": vectors}


def _cosine(a: Dict, b: Dict) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb + 1e-9)




def _init_knowledge_base():
    
    raw_chunks = _load_chunks_from_pdf(_CHUNKS_PATH)
    if raw_chunks:
        docs = _chunks_to_docs(raw_chunks)
        source = f"BIS SP-21 PDF — {len(docs)} chunks (data/chunks.json)"
    else:
        docs = _FALLBACK_DB
        source = f"Built-in KB — {len(docs)} standards (run ingest.py to upgrade)"

    index = _build_index(docs)
    logger.info(f"[RAG] Knowledge base ready: {source}")
    return docs, index, source


_DOCS, _INDEX, DATA_SOURCE = _init_knowledge_base()


def reload_knowledge_base():
    """Re-initialise from disk (call after running ingest.py without restarting)."""
    global _DOCS, _INDEX, DATA_SOURCE
    _DOCS, _INDEX, DATA_SOURCE = _init_knowledge_base()
    return DATA_SOURCE



def retrieve(query: str, top_k: int = 5) -> List[Dict]:
    q_tokens = _tokenize(query)
    idf = _INDEX["idf"]
    tf = Counter(q_tokens)
    q_vec = {t: (tf[t] / (len(q_tokens) or 1)) * idf.get(t, 1) for t in tf}

    scores = []
    for i, vec in enumerate(_INDEX["vectors"]):
        score = _cosine(q_vec, vec)
        doc_kws = set(_tokenize(" ".join(_DOCS[i].get("keywords", []))))
        overlap = len(doc_kws & set(q_tokens))
        score += overlap * 0.15
        scores.append((score, i))

    scores.sort(key=lambda x: -x[0])
    results = []
    for score, idx in scores[:top_k]:
        if score > 0.01:
            results.append({**_DOCS[idx], "score": round(score, 4)})
    return results




def _call_anthropic(product_desc: str, standards: List[Dict]) -> Optional[Dict[str, str]]:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        stds_text = "\n".join(
            f"- {s['standard']}: {s['title']} ({s['category']})" for s in standards
        )
        prompt = f"""You are a BIS (Bureau of Indian Standards) compliance expert.

Product description: {product_desc}

Top retrieved BIS standards:
{stds_text}

For each standard listed, write a 1-sentence rationale explaining exactly why it applies to this product.
Respond ONLY as valid JSON: {{"IS 269": "rationale", ...}} using the exact standard number as the key.
Do not invent standards not listed above."""

        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"[RAG] Anthropic API unavailable: {e}. Using fallback rationale.")
        return None


def _fallback_rationale(product_desc: str, standard: Dict) -> str:
    kw_matches = [kw for kw in standard.get("keywords", []) if kw.lower() in product_desc.lower()]
    if kw_matches:
        return (
            f"{standard['standard']} applies because the product involves "
            f"{', '.join(kw_matches[:3])}, governed by this {standard['category']} standard."
        )
    return (
        f"{standard['standard']} ({standard['title']}) is relevant for "
        f"{standard['category']} products. {standard.get('summary','')[:120]}..."
    )




def recommend(product_description: str, top_k: int = 5) -> Dict[str, Any]:

    t0 = time.time()
    candidates = retrieve(product_description, top_k=max(top_k, 7))[:top_k]
    api_rationales = _call_anthropic(product_description, candidates)

    results = []
    for std in candidates:
        if api_rationales and std["standard"] in api_rationales:
            rationale = api_rationales[std["standard"]]
        else:
            rationale = _fallback_rationale(product_description, std)

        results.append({
            "standard_id": std["standard"],
            "title": std["title"],
            "category": std["category"],
            "year": std.get("year", ""),
            "rationale": rationale,
            "relevance_score": std["score"],
            "summary": std.get("summary", "")[:300],
        })

    return {
        "query": product_description,
        "retrieved_standards": results,
        "latency_seconds": round(time.time() - t0, 3),
        "data_source": DATA_SOURCE,
    }
