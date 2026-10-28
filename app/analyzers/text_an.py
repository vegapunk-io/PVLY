"""Text analyzers.

LIVE:   Unicode hygiene (hidden code points, homoglyphs, bidi controls) with safe normalisation.
LIVE:   Transparent stylometric *features* + a deliberately 'weak' heuristic (never a verdict).
LIVE:   Educational green-list watermark demo (Kirchenbauer et al. 2023) with a *known* key.
MANUAL: Binoculars / Fast-DetectGPT (GPU), vendor text watermark detectors (SynthID-Text, textGrain, Claude mark), no public third-party detector exists today; EU CoP requires providers to expose detection by 2 Feb 2027.
"""
from __future__ import annotations

import hashlib
import math
import re
import statistics
import unicodedata

from .base import Analyzer, Context, Signal

SUSPECT = {
    "\u200b": "ZERO WIDTH SPACE", "\u200c": "ZERO WIDTH NON-JOINER (legit in Indic/Arabic/emoji)",
    "\u200d": "ZERO WIDTH JOINER (legit in Indic/Arabic/emoji)", "\u2060": "WORD JOINER",
    "\ufeff": "BYTE ORDER MARK / ZWNBSP", "\u00ad": "SOFT HYPHEN",
    "\u202f": "NARROW NO-BREAK SPACE (seen in o3/o4-mini output Apr 2025; also French typography)",
    "\u00a0": "NO-BREAK SPACE", "\u2009": "THIN SPACE", "\u200a": "HAIR SPACE",
    "\u2028": "LINE SEPARATOR", "\u2029": "PARAGRAPH SEPARATOR",
    "\u202a": "LRE (bidi)", "\u202b": "RLE (bidi)", "\u202c": "PDF (bidi)", "\u202d": "LRO (bidi)", "\u202e": "RLO (bidi)",
    "\u2066": "LRI (bidi)", "\u2067": "RLI (bidi)", "\u2068": "FSI (bidi)", "\u2069": "PDI (bidi)",
    "\u180e": "MONGOLIAN VOWEL SEPARATOR",
}
VISIBLE_SPACES = "\u202f\u00a0\u2009\u200a\u2028\u2029"
VS_RANGES = [(0xFE00, 0xFE0F), (0xE0100, 0xE01EF), (0xE0000, 0xE007F)]
HOMOGLYPHS = {"а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i", "ѕ": "s", "ј": "j",
              "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T",
              "Х": "X", "ο": "o", "ν": "v", "α": "a"}

# Excess-vocabulary list (Kobak et al. 2024/25 and similar corpus studies). Population-level signal only.
EXCESS_WORDS = ["delve", "delves", "delving", "showcasing", "showcase", "underscores", "underscore", "intricate",
                "intricacies", "pivotal", "realm", "tapestry", "meticulous", "meticulously", "crucial", "notably",
                "furthermore", "moreover", "comprehensive", "garner", "foster", "leverage", "robust", "seamless",
                "testament", "landscape", "navigate", "embark", "elevate", "holistic", "paramount", "streamline",
                "unparalleled", "unwavering", "vibrant", "utilize", "facilitate", "encompass", "multifaceted",
                "ever-evolving", "groundbreaking", "transformative", "harness", "nuanced", "commendable"]


def scan_unicode(text: str) -> dict:
    findings = []
    for i, ch in enumerate(text):
        cp = ord(ch)
        if ch in SUSPECT:
            findings.append({"pos": i, "cp": f"U+{cp:04X}", "name": SUSPECT[ch]})
        elif any(lo <= cp <= hi for lo, hi in VS_RANGES):
            findings.append({"pos": i, "cp": f"U+{cp:04X}", "name": unicodedata.name(ch, "VARIATION SELECTOR / TAG")})
        elif ch in HOMOGLYPHS:
            left = text[i - 1] if i > 0 else " "
            right = text[i + 1] if i + 1 < len(text) else " "
            if left.isascii() and right.isascii() and (left.isalpha() or right.isalpha()):
                findings.append({"pos": i, "cp": f"U+{cp:04X}",
                                 "name": f"HOMOGLYPH of '{HOMOGLYPHS[ch]}' ({unicodedata.name(ch, '?')})"})
    by_name: dict[str, int] = {}
    for f in findings:
        by_name[f["name"]] = by_name.get(f["name"], 0) + 1
    return {"findings": findings[:200], "count": len(findings), "by_type": by_name,
            "stats": {"chars": len(text), "em_dashes": text.count("\u2014"),
                      "curly_quotes": sum(text.count(q) for q in "\u2018\u2019\u201c\u201d"),
                      "double_spaces": len(re.findall(r"(?<=\S)  (?=\S)", text)),
                      "trailing_space_lines": sum(1 for l in text.splitlines() if l.endswith((" ", "\t")))}}


def clean_unicode(text: str, keep_joiners: bool = True, ascii_dashes: bool = False) -> str:
    out = []
    for ch in text:
        cp = ord(ch)
        if ch in ("\u200c", "\u200d") and keep_joiners:
            out.append(ch)
            continue
        if ch in SUSPECT:
            # visible-width spaces/separators become a plain space; zero-width/control characters are dropped
            if ch in VISIBLE_SPACES:
                out.append("\n" if ch in "\u2028\u2029" else " ")
            continue
        if any(lo <= cp <= hi for lo, hi in VS_RANGES):
            continue
        out.append(HOMOGLYPHS.get(ch, ch))
    s = unicodedata.normalize("NFC", "".join(out))
    if ascii_dashes:
        s = s.replace("\u2014", " - ").replace("\u2013", "-")
    return s


def stylometry(text: str) -> dict:
    sents = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
    lw = [w.lower() for w in words]
    n = max(1, len(words))
    sl = [len(re.findall(r"\w+", s)) for s in sents] or [0]
    excess = {w: lw.count(w) for w in EXCESS_WORDS if w in lw}
    feats = {
        "words": len(words), "sentences": len(sents),
        "mean_sentence_len": round(statistics.mean(sl), 1),
        "sentence_len_stdev": round(statistics.pstdev(sl), 1) if len(sl) > 1 else 0.0,
        "burstiness_cv": round((statistics.pstdev(sl) / statistics.mean(sl)), 2) if len(sl) > 1 and statistics.mean(sl) else 0.0,
        "type_token_ratio": round(len(set(lw)) / n, 3),
        "em_dash_per_100w": round(100 * text.count("\u2014") / n, 2),
        "excess_vocab_hits": excess, "excess_vocab_per_1000w": round(1000 * sum(excess.values()) / n, 1),
        "bullet_lines": sum(1 for l in text.splitlines() if re.match(r"\s*([-*•]|\d+\.)\s", l)),
        "avg_word_len": round(sum(len(w) for w in words) / n, 2),
    }
    # Heuristic score in [0,1]: only *weak* evidence, published as such. Deliberately coarse.
    score = 0.0
    if feats["words"] >= 120:
        if feats["burstiness_cv"] < 0.35:
            score += 0.25
        if feats["excess_vocab_per_1000w"] > 6:
            score += 0.25
        if feats["em_dash_per_100w"] > 1.2:
            score += 0.15
        if feats["type_token_ratio"] < 0.42:
            score += 0.15
        if feats["bullet_lines"] >= 4 and feats["sentences"] < 40:
            score += 0.1
    feats["heuristic_score"] = round(min(1.0, score), 2)
    return feats


# ---------------------------------------------------------------- educational green-list watermark demo
def _is_green(prev_tok: str, tok: str, key: str, gamma: float) -> bool:
    h = hashlib.sha256(f"{key}|{prev_tok}|{tok}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2 ** 64 < gamma


def greenlist_zscore(tokens: list[str], key: str, gamma: float = 0.5) -> dict:
    T = len(tokens) - 1
    if T < 10:
        return {"error": "need at least 11 tokens"}
    g = sum(_is_green(tokens[i - 1], tokens[i], key, gamma) for i in range(1, len(tokens)))
    z = (g - gamma * T) / math.sqrt(T * gamma * (1 - gamma))
    p = 0.5 * math.erfc(z / math.sqrt(2))
    return {"green": g, "scored_tokens": T, "z": round(z, 2), "p_one_sided": p, "verdict": "watermark" if z > 4 else "no evidence"}


def greenlist_generate(key: str, n: int = 300, gamma: float = 0.5, strength: float = 0.9, seed: int = 7) -> list[str]:
    """Toy 'language model': picks from 8 random candidate words, preferring green ones with prob=strength."""
    import random
    rnd = random.Random(seed)
    vocab = ("the of and to in a is that for it as with on be by this are from at or an which you one all were we "
             "when your can said there use each she how their if will up other about out many then them these so some "
             "her would make like him into time has look two more write go see number no way could people my than first "
             "water been call who oil its now find long down day did get come made may part model signal data report "
             "provenance label content check verify platform policy trust watermark image audio video text file").split()
    toks = ["<s>"]
    for _ in range(n):
        cands = rnd.sample(vocab, 8)
        green = [c for c in cands if _is_green(toks[-1], c, key, gamma)]
        toks.append(rnd.choice(green) if green and rnd.random() < strength else rnd.choice(cands))
    return toks


class TextAnalyzer(Analyzer):
    name = "text"
    modalities = ("text",)

    def run(self, ctx: Context) -> list[Signal]:
        text = ctx.text or ""
        u = scan_unicode(text)
        if u["count"]:
            status, grade = "detected", "weak"
            summary = f"{u['count']} hidden/unusual code points found ({', '.join(list(u['by_type'])[:3])}). Not a provider watermark — but worth cleaning before publishing."
        else:
            status, grade, summary = "absent", "none", "No hidden code points, homoglyphs or bidi controls."
        sig_unicode = Signal(kind="text_hygiene", name="Unicode hygiene", status=status, evidence_grade=grade,
                             summary=summary, data=u, method="code-point scan (see /tools for the cleaner)")
        f = stylometry(text)
        if f["words"] < 120:
            s_status, s_summary = "skipped", f"Only {f['words']} words — stylometric features are meaningless below ~120 words."
        else:
            s_status = "info"
            s_summary = (f"Heuristic score {f['heuristic_score']:.2f} (weak evidence by design). burstiness CV={f['burstiness_cv']}, "
                         f"excess-vocab/1000w={f['excess_vocab_per_1000w']}, TTR={f['type_token_ratio']}. "
                         "Known bias: formulaic and non-native English writing scores higher. Never use as sole evidence.")
        sig_style = Signal(kind="passive", name="Stylometric features (transparent heuristic)", status=s_status,
                           evidence_grade="weak" if f["words"] >= 120 and f["heuristic_score"] >= 0.5 else "none",
                           summary=s_summary, data=f, method="hand-written features; Binoculars/Fast-DetectGPT recommended")
        sig_vendor = Signal(kind="vendor_watermark", name="Provider text watermarks (SynthID-Text / textGrain / Claude)",
                            status="not_configured", evidence_grade="none",
                            summary="Keyed statistical watermarks can only be detected by the provider. Gemini: SynthID-Text (public detector exposes media only); "
                                    "ChatGPT/Codex EU: textGrain (no public detector yet); Claude: model-level mark (detector planned). "
                                    "EU Code of Practice obliges providers to offer detection + an interoperable solution by 2 Feb 2027.",
                            manual_integration="Register for provider detection APIs as they ship; add connectors in analyzers/vendor_an.py (TextVendorConnector)")
        sig_zero = Signal(kind="passive", name="Zero-shot detector (Binoculars / Fast-DetectGPT)", status="not_installed",
                          evidence_grade="none", summary="Needs two 7B-class models on a GPU; run on Modal/RunPod as a worker.",
                          manual_integration="pip install torch transformers; deploy ahans30/Binoculars as a service; report score + published FPR")
        out = [sig_unicode, sig_style, sig_vendor, sig_zero]
        key = (ctx.options or {}).get("greenlist_key")
        if key:
            toks = ["<s>"] + text.split()
            r = greenlist_zscore(toks, key, float((ctx.options or {}).get("greenlist_gamma", 0.5)))
            if "error" in r:
                st, gr, summ = "skipped", "none", r["error"]
            elif r["z"] > 4:
                st, gr, summ = "detected", "moderate", f"Green-list z={r['z']} over {r['scored_tokens']} tokens (p={r['p_one_sided']:.1e}) with the supplied key."
            else:
                st, gr, summ = "absent", "none", f"z={r['z']} — no evidence of a green-list watermark under this key."
            out.append(Signal(kind="text_watermark", name="Green-list watermark z-test (keyed)", status=st, evidence_grade=gr,
                              summary=summ, data=r, method="Kirchenbauer et al. 2023 statistic over whitespace tokens (educational scheme)"))
        return out
