"""
docs/make_workflow_docx.py — a teljes PLAXIS-munkafolyamat Word-dokumentumként.

A docs/PLAXIS_WORKFLOW_TELJES.md tartalmát állítja elő formázott .docx-ként, valódi
Word-táblázatokkal. Futtatás:  py docs/make_workflow_docx.py
Kimenet:  PLAXIS surrogate — teljes munkafolyamat.docx  (a projekt gyökerében)
"""
from __future__ import annotations

import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):        # Windows-konzol UTF-8 (✔, °, φ)
    try:
        _s.reconfigure(encoding="utf-8")   # type: ignore[union-attr]
    except Exception:
        pass

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "PLAXIS surrogate — teljes munkafolyamat.docx"

ACCENT = RGBColor(0x1F, 0x4E, 0x79)
MUTED = RGBColor(0x5B, 0x66, 0x75)


def add_table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        r = hdr[i].paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(val))
            run.font.size = Pt(9.5)
    doc.add_paragraph()
    return t


def h(doc, text, level):
    p = doc.add_heading(text, level=level)
    return p


def para(doc, text, *, italic=False, size=10.5, color=None, bold=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.italic = italic
    r.bold = bold
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    return p


def bullets(doc, items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        parts = it.split("**")
        bold = False
        for seg in parts:
            run = p.add_run(seg)
            run.bold = bold
            run.font.size = Pt(10.5)
            bold = not bold


def build() -> None:
    doc = Document()
    # alap betűméret
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)

    # Címlap
    title = doc.add_heading("A teljes PLAXIS-munkafolyamat", level=0)
    sub = doc.add_paragraph()
    sr = sub.add_run("Síkalap surrogate oktatóeszköz — lépésről lépésre a valódi PLAXIS-tól a látványos élő demóig")
    sr.italic = True
    sr.font.size = Pt(12)
    sr.font.color.rgb = MUTED
    doc.add_paragraph()

    para(doc,
         "Ez a dokumentum végigvezet az egészen: hogyan vesszük fel a paramétereket, mit "
         "származtatunk és milyen elv alapján, hány PLAXIS-futás kell, mit kell a PLAXIS-ban "
         "csinálni, mit nyerünk ki és hogyan, milyen pontosságot várunk, és ki mit csinál. A "
         "végcél: a mostani mock-demóval egyenértékű, de valódi FE-adatból működő élő eszköz — "
         "animált süllyedés- ÉS nyírásalakváltozás-mező, p–s görbe, EC7-összevetés több "
         "biztonsági szinttel.")

    # 0
    h(doc, "0. A nagy kép", 1)
    para(doc, "Paraméterek → Származtatás → Mintavétel → PLAXIS futások → Kinyerés → "
              "Tanítás → Export → Web app", bold=True)
    para(doc, "A [Mintavétel → Export] szoftver már felépült és fut (mock-adaton). A valódi "
              "PLAXIS-nál a futások és a kinyerés adatforrása vált, és a tanításhoz jön a "
              "POD-ROM mező-modell (ez adja az animált valós mezőt). Az adatszerződés "
              "(DATA_CONTRACT) miatt a csere drop-in.")

    # 1
    h(doc, "1. A bemeneti paraméterek (mik változtathatók, milyen határok között)", 1)
    para(doc, "Mind a 9 bemenet szabadon állítható; a tanítás a lenti tartományokon belül "
              "mintázik. A tartományok magyar talajokra (lösz/agyag) igazítva, a config.yaml-ben "
              "egy helyen módosíthatók.")
    add_table(doc,
              ["#", "Jel", "Jelentés", "Tartomány", "Egység", "Megjegyzés"],
              [
                  ["1", "B", "alapszélesség", "0,5 – 4,0", "m", "strip (folyóméteres)"],
                  ["2", "D", "alapsík mélysége", "0,4 – 3,0", "m", "beágyazás"],
                  ["3", "φ'", "belső súrlódási szög", "20 – 38", "°", "lösz ~28–35"],
                  ["4", "c'", "kohézió", "0 – 40", "kPa", "lösz ~5–25"],
                  ["5", "γ", "térfogatsúly", "16 – 21", "kN/m³", ""],
                  ["6", "E'", "E50ref @100 kPa", "5 – 60", "MPa", "lösz ~8–25"],
                  ["7", "GWL", "talajvízszint mélysége", "0,5 – 8,0", "m", ""],
                  ["8", "α", "teherferdeség", "0 – 25", "°", "H/V = tan α"],
                  ["9", "talajtípus", "homok / iszap / agyag", "—", "—", "a korrelációkat vezérli"],
              ])
    para(doc, "Elv: kevés, mérnökileg értelmezhető, egymástól viszonylag független bemenet. A "
              "sok kisalakváltozási HSsmall-paramétert nem tesszük bemenetté — azokat "
              "származtatjuk (2. pont), így a tanulási tér 9 dimenziós marad.")

    # 2
    h(doc, "2. Származtatott HSsmall-paraméterek — hogyan és milyen elv alapján", 1)
    para(doc, "A 4 talaj-bemenetből (φ', c', γ, E') + a talajtípusból determinisztikusan áll "
              "elő a teljes HSsmall-készlet (plaxis/derive_hssmall.py). A geometriai/terhelési "
              "bemenetek (B, D, GWL, α) a modell geometriájába/terhelésébe mennek.")
    add_table(doc,
              ["HSsmall param", "Származtatás", "Elv / forrás", "homok", "iszap", "agyag"],
              [
                  ["E50ref", "= E' (bemenet)", "definíció", "–", "–", "–"],
                  ["Eoedref", "arány · E50ref", "típusfüggő", "×1,00", "×0,90", "×0,80"],
                  ["Eurref", "arány · E50ref", "HS-default", "×3,0", "×3,0", "×3,0"],
                  ["m (feszültség-kitevő)", "típusfüggő", "Janbu / HS", "0,50", "0,65", "0,90"],
                  ["G0ref", "(G0/Gur)·Gur", "Benz (2007)", "×2,50", "×2,75", "×3,00"],
                  ["γ0.7", "típusfüggő", "Wichtmann–Triantafyllidis", "1·10⁻⁴", "1,5·10⁻⁴", "2·10⁻⁴"],
                  ["ψ (dilatancia)", "max(φ'−30°,0) / 0", "Bolton", "φ'−30", "0", "0"],
                  ["K0nc", "1 − sin φ'", "Jáky", "✓", "✓", "✓"],
                  ["ν_ur", "0,20", "HS-default", "✓", "✓", "✓"],
                  ["Rf", "0,90", "HS-default", "✓", "✓", "✓"],
                  ["p_ref", "100 kPa", "HS-default", "✓", "✓", "✓"],
              ])
    para(doc, "Auditálhatóság: minden futáshoz kiírjuk a származtatott készletet "
              "(doe_hssmall.csv). A típusonkénti értékek mérnöki alapértékek — a hallgató a ti "
              "PLAXIS-verziótokban validálja őket.")

    # 3
    h(doc, "3. Mintavételezés — hogyan választjuk ki, miket futtatunk", 1)
    bullets(doc, [
        "**Módszer:** Latin Hypercube Sampling (LHS) a 8 folytonos paraméterre → egyenletes, "
        "hézagmentes lefedés. A talajtípus rétegzett (mindhárom típusra közel azonos számú minta).",
        "**Miért LHS:** kevés futásból is jól lefedi a teret; a peremeket is eléri.",
        "**Szakaszos bővítés:** pilot 100 → alap ~800–1500 → teljes ~3000–6000 futás.",
        "**Később adaptív mintavétel:** ahol a modell bizonytalan, oda célzottan teszünk új futásokat.",
    ])
    para(doc, "Futásszám hüvelykujj: a skalár/p–s modellhez ~500–1000 futás/talajtípus már "
              "erős; a mezőmodellhez több segít. Reális célszám a 3000–5000 konvergált futás. A "
              "konvergencia-arány 85–93%, ezért ~10–15%-kal túlmintázunk.")

    # 4
    h(doc, "4. Mit adok a PLAXIS-hoz, és mit kell ott futtatni", 1)
    para(doc, "Amit ÉN adok (kész vagy elkészítem):", bold=True)
    bullets(doc, [
        "plaxis/sampling.py — a kísérlet-terv (doe.csv) generálása.",
        "plaxis/plaxis_api.py + RealPlaxisBackend — a Remote Scripting réteg (a vázat megírom).",
        "plaxis/run_generation.py — a hurok: checkpoint/resume, hibatűrés, azonnali mentés.",
        "plaxis/extract_results.py — a görbe- és mező-kinyerés.",
        "docs/PLAXIS_TEMPLATE.md — pontos leírás a sablon-modellhez.",
    ])
    para(doc, "Amit a hallgatónak KELL (egyszeri kézi lépés + felügyelet):", bold=True)
    bullets(doc, [
        "**Sablon-modell** megépítése egyszer: homogén féltér, HSsmall talaj, paraméterezhető "
        "síkalap (B, D), vízszint (GWL), fázisok (K0 → alap aktiválás → erővezérelt terhelés "
        "H/V=tan α a törésig), curve point az alaptest közepén.",
        "**Remote Scripting** bekapcsolása (port + jelszó).",
        "**A tulajdonságnevek hitelesítése** a ti PLAXIS-verziótokban (pl. E50ref vs E50Ref).",
        "**A köteg indítása és felügyelete:** py plaxis/sampling.py --n 5500 ; "
        "py plaxis/run_generation.py --api real",
    ])
    para(doc, "Időigény: egy 2D HSsmall síkalap törésig ~1–4 perc. 3000–5000 futás így több "
              "tíz–száz gépóra → éjszakákon/napokon át fut. Egy licenc = soros; több gép = "
              "párhuzamosítható. Ezért kulcs a checkpoint/resume.")

    # 5
    h(doc, "5. Mit kell kinyerni a PLAXIS-ból, és hogyan", 1)
    para(doc, "5/A. Skalárok + p–s görbe (a curve point-ból)", bold=True)
    bullets(doc, [
        "R_k = a törőteher függőleges komponense az adott α-nál.",
        "s_max = a süllyedés a törésnél.",
        "p–s görbe: a curve point (teher, süllyedés) párjai, 20 rögzített teher-szintre "
        "újramintázva (p/R_k = 0,05…1,00) → ps_01…ps_20.",
        "Hogyan: plxscripting-gel a curve point sorozatát olvassuk, resample_ps() interpolál.",
    ])
    para(doc, "5/B. Mező-pillanatképek (a POD-ROM-hoz — az animációhoz)", bold=True)
    bullets(doc, [
        "Mit: a 2D tartomány csomóponti értékei több teher-szinten (8–10 szint): elmozdulás "
        "(|u|, ux, uy) és inkrementális deviatorikus nyírásalakváltozás (γs).",
        "Hol: durva, rögzített rácson (pl. ~40×30 pont), NEM a teljes finom hálón.",
        "**Kulcs-fogás — normalizált tartomány:** mivel B és D változik, minden mezőt B-vel "
        "normalizált referencia-tartományra (x/B, z/B) képezünk, hogy közös rácson legyenek; a "
        "böngészőben visszaskálázzuk a valódi méretre.",
        "Hogyan: a PLAXIS output-ból a mezőt rácsra interpoláljuk és CSV-be írjuk; ezt a "
        "RealPlaxisBackend végzi ugyanabban a hurokban.",
    ])

    # 6
    h(doc, "6. A surrogate tanítása (három modell-réteg)", 1)
    bullets(doc, [
        "**Skalárok + p–s (kész):** 22 XGBoost-modell + Optuna-hangolás + SHAP + k-fold CV.",
        "**Mező (POD-ROM — új):** a pillanatképeket SVD-vel (POD) néhány tíz térbeli módra "
        "bontjuk; a mód-együtthatókat a (9 bemenet + teher-szint) függvényében regresszáljuk; a "
        "böngészőben mező = átlag + Σ ak·Φk, majd visszaskálázás.",
        "**Bizonytalanság (kvantilis):** 0,1 / 0,5 / 0,9 kvantilis-modellek → bizonytalansági sáv.",
    ])

    # 7
    h(doc, "7. Export böngészőbe", 1)
    bullets(doc, [
        "Skalárok/p–s: m2cgen → tiszta JS (kész, paritás-ellenőrzéssel).",
        "Mező-ROM: a Φ-bázis + az együttható-modellek JS-be; a rekonstrukció mátrix–vektor szorzás.",
        "Payload-kezelés: fa-mélység/szám korlát, lazy betöltés; a POD miatt a mező olcsó.",
    ])

    # 8
    h(doc, "8. A végső web app — a „wow” demó", 1)
    bullets(doc, [
        "Animált metszet: valós B/D geometrián a teher 0→törés animációval, süllyedés- ÉS "
        "nyírásalakváltozás-mező (valódi FE-ből, POD-ROM-mal), nézet-kapcsolóval.",
        "p–s görbe mozgó teher-ponttal + bizonytalansági sáv.",
        "EC7-összevetés több biztonsági szinten: karakterisztikus vs tervezési ellenállás, "
        "parciális tényezők (DA1/DA2/DA3 jellegű) — a teljes EC7-motorotokból portolva.",
        "Szép, téma-tudatos, magyar tipográfiával — bemutatóra és tantárgyi használatra.",
    ])

    # 9
    h(doc, "9. Milyen lesz a pontosság", 1)
    bullets(doc, [
        "Skalárok (R_k, s_max): ~3000+ konvergált futással tipikusan R² > 0,97 (0,98–0,99). A "
        "törés-közeli tartomány a legnehezebb — külön nézzük.",
        "p–s görbe: pontonként hasonló; a monotonitást kényszerrel/clamppel biztosítjuk.",
        "Mező-ROM: a rekonstrukció relatív hibája néhány %.",
        "Mérés: train/test split, k-fold CV, R²/RMSE/MAE kimenetenként, külön a failure-region "
        "pontosság, fizikai konzisztencia. Az átlagos R² önmagában nem elég.",
        "Skálázás: a pontosság a konvergált futások számával nő; az adaptív mintavétel a "
        "leggyorsabb út a maradék hibák letöréséhez.",
    ])

    # 10
    h(doc, "10. Ki mit csinál — felelősség-táblázat", 1)
    add_table(doc,
              ["Lépés", "ÉN (Claude)", "HALLGATÓ", "TE (konzulens)"],
              [
                  ["Paramétertartományok", "javaslat + kódba", "—", "jóváhagyás (mérnöki)"],
                  ["derive_hssmall korrelációk", "megírom", "verzió-validálás", "elvi jóváhagyás"],
                  ["sampling / doe", "megírom, futtatom", "—", "—"],
                  ["PLAXIS sablon-modell", "pontos leírás", "megépíti (egyszer)", "ellenőrzi"],
                  ["Remote Scripting bekötés", "a kód-váz", "hitelesíti + bekapcsolja", "—"],
                  ["A köteg futtatása", "a hurok-kód", "elindítja, felügyeli", "—"],
                  ["Kinyerés (skalár+mező)", "megírom", "a scriptet futtatja", "—"],
                  ["ML + POD-ROM + kvantilis", "én építem", "—", "eredmény-értékelés"],
                  ["Export + web app", "én építem", "—", "tartalmi visszajelzés"],
                  ["Validáció / integritás", "metrikák, ellenőrzők", "adatminőség", "szakmai hitelesítés"],
              ])
    para(doc, "Egy mondatban: minden kódot, pipeline-t, ROM-ot, exportot és a web appot ÉN "
              "csinálom; a HALLGATÓ a PLAXIS-sablont építi meg egyszer, hitelesíti a "
              "tulajdonságneveket és futtatja a köteget; TE a mérnöki döntéseket hagyod jóvá és "
              "validálod az eredményt.", bold=True)

    # 11
    h(doc, "11. Futásszám és idő — összefoglaló", 1)
    add_table(doc,
              ["Kör", "Tervezett futás", "Konvergált (~88%)", "Cél"],
              [
                  ["Pilot", "100", "~88", "csővezeték + sablon ellenőrzés"],
                  ["Alap", "1 000", "~880", "első használható surrogate"],
                  ["Teljes", "5 500", "~5 000", "legjobb pontosság + stabil mező-ROM"],
                  ["Adaptív (opcionális)", "+500…1000", "—", "a maradék hibák célzott letörése"],
              ])
    para(doc, "Idő: futásonként ~1–4 perc → a teljes kör nagyságrendileg több tíz–száz gépóra, "
              "éjszakai/napokon átnyúló, folytatható kötegben.")

    doc.save(str(OUT))
    print(f"✔ Word-dokumentum kiírva → {OUT}")


if __name__ == "__main__":
    build()
