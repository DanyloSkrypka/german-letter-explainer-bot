"""Generate 5 FICTIONAL German official letters (HTML -> PNG) + expected.json for tests.

All names, addresses, numbers and the town "Lindenau" are invented. No real letters are used.
Run:  .venv/bin/python scripts/make_samples.py   (uses the installed Google Chrome via Playwright)
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "samples"

CSS = """
* { box-sizing: border-box; }
body { margin: 0; background: #fff; }
.page { width: 1000px; min-height: 1414px; padding: 70px 90px 60px; font-family: Arial, Helvetica, sans-serif;
        font-size: 18px; line-height: 1.5; color: #1a1a1a; background: #fff; position: relative; }
.logo { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px; }
.logo .org { font-size: 26px; font-weight: 700; letter-spacing: .01em; }
.logo .org small { display: block; font-size: 16px; font-weight: 400; color: #444; }
.logo .mark { width: 74px; height: 74px; border-radius: 12px; display: grid; place-items: center; color: #fff;
              font-weight: 800; font-size: 26px; }
.sender-line { font-size: 12px; color: #555; border-bottom: 1px solid #999; display: inline-block; margin-bottom: 6px; }
.addr { line-height: 1.4; }
.info { position: absolute; right: 90px; top: 210px; font-size: 15px; line-height: 1.55; text-align: left; }
.info b { display: inline-block; width: 150px; font-weight: 400; color: #555; }
h2 { font-size: 19px; margin: 70px 0 24px; }
p { margin: 0 0 14px; }
table { border-collapse: collapse; margin: 10px 0 18px; width: 100%; }
td { padding: 5px 4px; border-bottom: 1px solid #ddd; }
td.r { text-align: right; white-space: nowrap; }
tr.sum td { font-weight: 700; border-top: 2px solid #333; border-bottom: 0; }
ul { margin: 0 0 14px; padding-left: 24px; }
.foot { position: absolute; left: 90px; right: 90px; bottom: 40px; font-size: 12px; color: #666;
        border-top: 1px solid #bbb; padding-top: 8px; display: flex; justify-content: space-between; }
"""


def page(org, sub, color, mark, sender_line, addr, info, subject, body, foot):
    info_html = "".join(f"<div><b>{k}</b>{v}</div>" for k, v in info)
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="page">
  <div class="logo"><div class="org">{org}<small>{sub}</small></div>
    <div class="mark" style="background:{color}">{mark}</div></div>
  <div class="sender-line">{sender_line}</div>
  <div class="addr">{addr}</div>
  <div class="info">{info_html}</div>
  <h2>{subject}</h2>
  {body}
  <div class="foot">{foot}</div>
</div></body></html>"""


LETTERS = [
    {
        "id": "01_jobcenter",
        "title": "Jobcenter · Mitwirkung",
        "expected": {"sender": "jobcenter", "deadline": "2026-12-04", "amount": None, "type": "mitwirkung"},
        "html": page(
            "Jobcenter Lindenau", "Grundsicherung für Arbeitsuchende", "#c8102e", "JC",
            "Jobcenter Lindenau · Am Markt 3 · 32999 Lindenau",
            "Frau<br>Oksana Melnyk<br>Birkenweg 14<br>32999 Lindenau",
            [("Datum:", "17.11.2026"), ("BG-Nummer:", "32999BG0048211"), ("Ihr Zeichen:", "—"),
             ("Telefon:", "05999 4410-0")],
            "Aufforderung zur Mitwirkung – Weiterbewilligungsantrag",
            """<p>Sehr geehrte Frau Melnyk,</p>
<p>für die Prüfung Ihres Weiterbewilligungsantrags für den Bewilligungszeitraum 01.01.2027 bis 30.06.2027
benötigen wir noch Unterlagen. Ihr aktueller Regelbedarf beträgt 563,00 € monatlich.</p>
<p>Bitte reichen Sie folgende Unterlagen bis zum 04.12.2026 ein:</p>
<ul><li>Kontoauszüge aller Konten der letzten drei Monate</li>
<li>aktuelle Mietbescheinigung des Vermieters</li>
<li>Nachweis über Ihr Einkommen aus dem Minijob (Oktober 2026)</li></ul>
<p>Wenn Sie bis zum genannten Termin nicht mitwirken, können die Leistungen ganz oder teilweise bis zur
Nachholung der Mitwirkung versagt werden (§§ 60, 66 Erstes Buch Sozialgesetzbuch – SGB I).</p>
<p>Sie können die Unterlagen auch online über jobcenter.digital hochladen.</p>
<p>Mit freundlichen Grüßen<br>Im Auftrag<br>T. Hoffmeister</p>""",
            "<span>Jobcenter Lindenau · Am Markt 3 · 32999 Lindenau</span><span>Öffnungszeiten: Mo–Fr 8–12 Uhr</span>",
        ),
    },
    {
        "id": "02_finanzamt",
        "title": "Finanzamt · Steuerbescheid",
        "expected": {"sender": "finanzamt", "deadline": "2026-12-21", "amount": "487.00", "type": "bescheid"},
        "html": page(
            "Finanzamt Lindenau", "Land Nordrhein-Westfalen", "#1f4e8c", "FA",
            "Finanzamt Lindenau · Postfach 1120 · 32990 Lindenau",
            "Herrn<br>Dmytro Savchuk<br>Lindenstraße 7a<br>32999 Lindenau",
            [("Datum:", "18.11.2026"), ("Steuernummer:", "331/5123/4567"), ("Telefon:", "05999 880-0")],
            "Bescheid für 2025 über Einkommensteuer",
            """<p>Die Steuer wird festgesetzt. Die Festsetzung beruht auf Ihrer Steuererklärung vom 02.06.2026.</p>
<table>
<tr><td>Festgesetzte Einkommensteuer</td><td class="r">2.914,00 €</td></tr>
<tr><td>Solidaritätszuschlag</td><td class="r">0,00 €</td></tr>
<tr><td>abzüglich Steuerabzug vom Lohn</td><td class="r">2.427,00 €</td></tr>
<tr class="sum"><td>Verbleibende Nachzahlung</td><td class="r">487,00 €</td></tr>
</table>
<p>Bitte zahlen Sie 487,00 € bis zum 21.12.2026 auf eines der unten genannten Konten des Finanzamts.
Geben Sie als Verwendungszweck Ihre Steuernummer an.</p>
<p>Wird nicht rechtzeitig gezahlt, entstehen Säumniszuschläge von 1 % des Betrags für jeden angefangenen Monat.</p>
<p><b>Rechtsbehelfsbelehrung:</b> Der Bescheid kann mit dem Einspruch angefochten werden. Der Einspruch ist
innerhalb eines Monats nach Bekanntgabe dieses Bescheids beim Finanzamt Lindenau schriftlich oder elektronisch
einzulegen.</p>""",
            "<span>Finanzamt Lindenau · Steuerstraße 1</span><span>IBAN DE00 0000 0000 0000 0000 00 (Muster)</span>",
        ),
    },
    {
        "id": "03_krankenkasse",
        "title": "Krankenkasse · Mahnung",
        "expected": {"sender": "krankenkasse", "deadline": "2026-11-30", "amount": "158.80", "type": "mahnung"},
        "html": page(
            "Nordwest Gesundheitskasse", "Ihre Krankenkasse", "#0a8f6a", "NG",
            "Nordwest Gesundheitskasse · Postfach 4400 · 32990 Lindenau",
            "Herrn<br>Andrii Bondar<br>Mühlenweg 22<br>32999 Lindenau",
            [("Datum:", "12.11.2026"), ("Versichertennr.:", "N842193307"), ("Kundennummer:", "7744120")],
            "Zahlungserinnerung – Beitragsrückstand",
            """<p>Sehr geehrter Herr Bondar,</p>
<p>leider konnten wir für die folgenden Monate keinen Zahlungseingang für Ihre Beiträge zur Kranken- und
Pflegeversicherung feststellen:</p>
<table>
<tr><td>Beitrag September 2026</td><td class="r">78,40 €</td></tr>
<tr><td>Beitrag Oktober 2026</td><td class="r">78,40 €</td></tr>
<tr><td>Säumniszuschlag</td><td class="r">2,00 €</td></tr>
<tr class="sum"><td>Gesamtbetrag</td><td class="r">158,80 €</td></tr>
</table>
<p>Bitte überweisen Sie den Gesamtbetrag von 158,80 € bis spätestens 30.11.2026.</p>
<p>Sollten Sie nicht zahlen, müssen wir weitere Säumniszuschläge erheben und das Mahnverfahren einleiten.
Bei längeren Rückständen ruht Ihr Leistungsanspruch bis auf Notfallbehandlungen.</p>
<p>Wenn Sie den Betrag nicht auf einmal zahlen können, sprechen Sie uns bitte an – eine Ratenzahlung ist möglich.</p>
<p>Freundliche Grüße<br>Ihre Nordwest Gesundheitskasse</p>""",
            "<span>Nordwest Gesundheitskasse · Kassenweg 5</span><span>Service-Telefon 0800 000 0000</span>",
        ),
    },
    {
        "id": "04_vermieter",
        "title": "Hausverwaltung · Nebenkosten",
        "expected": {"sender": "vermieter", "deadline": "2026-12-16", "amount": "238.15", "type": "abrechnung"},
        "html": page(
            "Brandt &amp; Söhne Immobilien GmbH", "Hausverwaltung", "#7a4b1e", "BS",
            "Brandt &amp; Söhne Immobilien GmbH · Ringstraße 40 · 32999 Lindenau",
            "Frau<br>Iryna Tkachenko<br>Ahornallee 3, Whg. 5<br>32999 Lindenau",
            [("Datum:", "16.11.2026"), ("Mieternummer:", "AH3-05"), ("Objekt:", "Ahornallee 3")],
            "Betriebskostenabrechnung 2025",
            """<p>Sehr geehrte Frau Tkachenko,</p>
<p>anbei erhalten Sie die Abrechnung der Betriebskosten für den Abrechnungszeitraum 01.01.2025 – 31.12.2025.</p>
<table>
<tr><td>Heizung und Warmwasser</td><td class="r">1.012,40 €</td></tr>
<tr><td>Wasser / Abwasser</td><td class="r">318,25 €</td></tr>
<tr><td>Müllabfuhr</td><td class="r">164,10 €</td></tr>
<tr><td>Hausreinigung und Treppenhausstrom</td><td class="r">243,60 €</td></tr>
<tr><td>Grundsteuer und Versicherung</td><td class="r">179,80 €</td></tr>
<tr><td>Gesamtkosten Ihrer Wohnung</td><td class="r">1.918,15 €</td></tr>
<tr><td>abzüglich Ihrer Vorauszahlungen</td><td class="r">1.680,00 €</td></tr>
<tr class="sum"><td>Nachzahlung</td><td class="r">238,15 €</td></tr>
</table>
<p>Bitte überweisen Sie den Nachzahlungsbetrag innerhalb von 30 Tagen nach Erhalt dieses Schreibens.</p>
<p>Ab dem 01.01.2027 beträgt Ihre monatliche Vorauszahlung 160,00 €.</p>
<p>Die Belege können nach Terminvereinbarung in unserem Büro eingesehen werden.</p>
<p>Mit freundlichen Grüßen<br>K. Brandt</p>""",
            "<span>Brandt &amp; Söhne Immobilien GmbH · Ringstraße 40</span><span>HRB 0000 (Muster)</span>",
        ),
    },
    {
        "id": "05_auslaenderbehoerde",
        "title": "Ausländerbehörde · Termin",
        "expected": {"sender": "auslaenderbehoerde", "deadline": "2026-12-08", "amount": "93.00", "type": "termin"},
        "html": page(
            "Stadt Lindenau", "Ausländerbehörde", "#5b2a86", "SL",
            "Stadt Lindenau · Ausländerbehörde · Rathausplatz 1 · 32999 Lindenau",
            "Frau<br>Natalia Shevchuk<br>Kastanienweg 9<br>32999 Lindenau",
            [("Datum:", "13.11.2026"), ("Aktenzeichen:", "32.1-AB-77310"), ("Zimmer:", "2.14")],
            "Einladung zur Vorsprache – Verlängerung der Aufenthaltserlaubnis",
            """<p>Sehr geehrte Frau Shevchuk,</p>
<p>Ihre Aufenthaltserlaubnis nach § 24 AufenthG ist gültig bis 04.03.2027. Zur Verlängerung laden wir Sie ein.</p>
<p>Termin am 08.12.2026 um 09:30 Uhr, Rathausplatz 1, Zimmer 2.14.</p>
<p>Bitte bringen Sie mit:</p>
<ul><li>gültigen Reisepass und aktuellen elektronischen Aufenthaltstitel</li>
<li>ein aktuelles biometrisches Passfoto</li>
<li>Meldebescheinigung und Nachweis der Krankenversicherung</li></ul>
<p>Die Gebühr in Höhe von 93,00 € ist beim Termin zu zahlen (EC-Karte).</p>
<p>Können Sie den Termin nicht wahrnehmen, sagen Sie bitte rechtzeitig ab. Ohne gültigen Aufenthaltstitel kann
der Aufenthalt unerlaubt werden.</p>
<p>Mit freundlichen Grüßen<br>Im Auftrag<br>S. Wagner</p>""",
            "<span>Stadt Lindenau · Rathausplatz 1</span><span>Termine nur nach Vereinbarung</span>",
        ),
    },
]


PHOTO_TPL = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;width:1000px;height:1414px;overflow:hidden;background:#6b5a48;
  background-image:radial-gradient(ellipse at 30% 20%,#8a7560 0%,#5a4a3a 70%);}
img{position:absolute;left:40px;top:38px;width:920px;transform:rotate(-1.6deg);filter:blur(.45px) contrast(.94) brightness(.97);
  box-shadow:0 18px 40px rgba(0,0,0,.45);}
.light{position:absolute;inset:0;background:linear-gradient(115deg,rgba(255,255,255,.10) 0%,rgba(0,0,0,0) 40%,rgba(0,0,0,.16) 100%);}
</style></head><body><img src="{SRC}"><div class="light"></div></body></html>"""


def main() -> None:
    OUT.mkdir(exist_ok=True)
    expected = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page_ = browser.new_page(viewport={"width": 1000, "height": 1414}, device_scale_factor=1.5)
        for L in LETTERS:
            html_path = OUT / f"{L['id']}.html"
            html_path.write_text(L["html"], encoding="utf-8")
            page_.goto(html_path.as_uri())
            page_.locator(".page").screenshot(path=str(OUT / f"{L['id']}.png"))
            # "phone photo" variant: slightly rotated sheet on a table, uneven light, a bit soft
            photo_html = OUT / f"_{L['id']}_photo.html"
            photo_html.write_text(PHOTO_TPL.replace("{SRC}", f"{L['id']}.png"), encoding="utf-8")
            page_.goto(photo_html.as_uri())
            page_.wait_for_timeout(150)
            page_.screenshot(path=str(OUT / f"{L['id']}_photo.jpg"), type="jpeg", quality=82)
            photo_html.unlink()
            expected[L["id"]] = {"title": L["title"], **L["expected"]}
            print("ok", L["id"])
        browser.close()
    (OUT / "expected.json").write_text(json.dumps(expected, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
