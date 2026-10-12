# Nachrechnung W3C public-agent-conformance 2026Oct/0051

Stand 2026-10-12. Alle Werte unten sind in diesen Läufen beobachtet. Was nicht
beobachtet ist, steht in Abschnitt 6.

## 1 Quellen

Die Mails und der Anhang liegen nicht in diesem Repo. Sie sind öffentlich archiviert,
die Hashes der gezogenen Bytes stehen hier:

| Quelle | SHA-256 der gezogenen Bytes |
|---|---|
| `https://lists.w3.org/Archives/Public/public-agent-conformance/2026Oct/0051.html` | `f29ac24c3d489e14ef009f8b5625e47fb825f45399a7f854a905cf91dd138ff4` |
| `…/2026Oct/att-0051/receipt-observation.json` | `73d31d3e6c95795230be2412ea7a1b65e414946d3ccc0b47651ea74ce91c05cc` |
| `…/2026Oct/0049.html` | `e83373c0caab1ed09161ca5310a6096fe4d98ca41e137f44fbd37a01f3f5568a` |
| `…/2026Oct/0042.html` | `5c7b0bacb875bb255c5ed76971df230357641effb04956d40d30e6e39350fb8f` |

Aus 0051 und dem Anhang übernommen sind:

- das Repository `https://github.com/DSHCorrectover/ccs-conformance-vectors`, das 0042
  ebenfalls nennt;
- die Revision `effff90f231d11bb3be93d3d0d0792f36934cc78`;
- der Befehl `python checkers/independent_checker.py vectors/v1.4.0-conformance`;
- die Selektion: 66 Fälle, also jedes Verzeichnis unter `vectors/v1.4.0-conformance`
  mit einer `expected.json`;
- die zwei Kontrollen:
  - B: Die `01-allow`-Signatur wird durch `AA==` ersetzt und der Manifest-Eintrag der
    Kopie nachgezogen.
  - C: Eine unveränderte Kopie von `01-allow` liegt als `zz-additional-unlisted-case`
    außerhalb des Manifests.

0049 benennt das canonicalization-v1-Subset ohne Pfad und ohne Revision. Für diese
Läufe wird es nicht gebraucht.

## 2 Aufbau

- **Klon:** auf den Commit-SHA gepinnt, mit `git fetch origin <sha>` und `checkout
  FETCH_HEAD`. `rev-parse HEAD` liefert `effff90f231d11bb3be93d3d0d0792f36934cc78`.
- **Checker** `checkers/independent_checker.py`, SHA-256
  `7b399035a1b85a05087e5de2bb224474a36410cb63a9d52d7c44c80557e2fc7a`, gleich dem Anhang.
- **Manifest** `manifest.json`, SHA-256
  `ad54da9ce62cb147adfc555f828ba36347aa1147318f816063455dadffc94d08`, gleich dem Anhang.
  Es pinnt 513 Dateien und führt keine Fall-Liste.
- **Laufzeit:** Python 3.14.3; cryptography 50.0.2, cffi 2.1.1, pycparser 3.1, jcs 0.2.1.
- **Hash-Seed:** `PYTHONHASHSEED=2` für alle Läufe, siehe Befund 3.

`tools/run_one.py` startet den Checker unverändert mit dem Befehl aus 0051 als eigenen
Prozess. Festgehalten werden Stdout, Stderr und Exit-Code. Danach lädt das Skript
dieselbe Datei als Modul und ruft je Fall die checker-eigene Funktion `verify_case` auf.
Aus diesen Datensätzen kommen natives Verdict, nativer Grund und die eigene Nachzählung.
Die gedruckte Zeile `✓ PASS`/`✗ FAIL` je Fall wird mit dem Datensatz abgeglichen. In
allen drei Läufen gab es keine Abweichung.

Der Eingabe-Digest ist `sha256(JCS({relativer Pfad: sha256(Bytes)}))` über jede Datei im
Corpus-Verzeichnis der jeweiligen Kopie. Die Einzel-Hashes stehen in jeder
Ergebnisdatei unter `input.files`.

`sh tools/reproduce.sh` baut Klon, Kopien und die drei Ergebnisdateien neu. Zwei
Durchgänge lieferten byte-gleiche Dateien.

## 3 Ergebnis

| Lauf | gedruckte Fußzeile | eigene Nachzählung | Exit | Eingabe-Digest |
|---|---|---|---|---|
| A Reproduktion | `Checks: 1477/1549 passed` · `Cases:  66/66 matched expected outcome` | 66/66; 1549 Checks, 72 false | 0 | `9109b36a6a8f1463ffd0aae6101f3d747185bc6f4d45da4965cda50d4726ed8e` |
| B Signaturtausch | `Checks: 1476/1549 passed` · `Cases:  66/66 matched expected outcome` | **65/66**, `01-allow` FAIL; 1549 Checks, 73 false | 1 | `e67d506c403bc37782ccd8e1652fd309bbcffa0406baf5d2573343e563c052b0` |
| C Fall außerhalb Manifest | `Checks: 1517/1589 passed` · `Cases:  67/67 matched expected outcome` | 67/67; 1589 Checks, 72 false | 0 | `88cf0b16ebf293eeb8f53a94b334c0a275203caae77cc7c34c6fe021efe2768d` |

| Stdout | SHA-256 dieser Lauf (Seed 2) | SHA-256 laut Anhang 0051 |
|---|---|---|
| A | `d675e859ee61149f4e3699314012124962690bdcbb8d536b122573fe6a554537` | `d675e859ee61149f4e3699314012124962690bdcbb8d536b122573fe6a554537` |
| B | `bf62868699bff8f61cc707631669ec979a05d92c525ea9da2ebd445807a3f903` | `2464888fa3ae65a4625e0fa43f88e38429fd595e9c0f8b869710c70a8aaee2c9` |
| C | `1ac1244e9c840f5dcaae661a2ab84b3c1cc81b6531798bc356edd1d1caa583f9` | nicht angegeben |

In Lauf B hat die Manifest-Kopie den SHA-256
`b037b813aea8b90b901d380478f4cb82ee4fd3b79160ba248abd49b6f3f361c4`. In Lauf C bleibt das
Manifest unverändert.

Lauf A deckt sich mit Sankalp Gildas Lauf, soweit der Anhang Belege enthält:

- Stdout ist byte-gleich, Stderr ist leer.
- Alle 66 nativen Fall-Datensätze sind nach JCS byte-gleich mit `cases[].native`.
- Die Fall-Liste ist identisch.
- Es sind 1549 Boolean-Checks, davon 72 false.

In Lauf B weichen Fußzeile und Nachzählung voneinander ab. `01-allow` scheitert mit dem
nativen Grund `signature mismatch` (Check `signature:ed25519`, `signature must be 64
bytes, got 1`). Die Fall-Zeile lautet `✗ FAIL  01-allow`, der Exit-Code ist 1. Die
Fußzeile meldet trotzdem `66/66`, siehe Befund 1.

In Lauf C nimmt die Manifest-Prüfung die erweiterte Population an. `verify_manifest`
(`independent_checker.py:728–744` @ effff90) prüft nur, ob die gelisteten Dateien
vorhanden und hash-gleich sind. `find_case_dirs` (`:1225`) nimmt jedes Verzeichnis mit
`expected.json` auf. Die Nachzählung endet bei 67 Fällen. Der Zusatzfall hat 8 Dateien,
und keine davon steht im Manifest.

## 4 Befunde

Fundstellen beziehen sich auf `checkers/independent_checker.py` @
`effff90f231d11bb3be93d3d0d0792f36934cc78`.

1. **Fußzeile (`:1293`).** Die Zeile bildet beide Seiten der Angabe aus
   `len(case_dirs)`: `Cases:  {len(case_dirs)}/{len(case_dirs)} matched expected
   outcome`. Wie viele Fälle getroffen wurden, geht nicht ein. Die Fußzeile kann deshalb
   in keinem Lauf einen Mismatch anzeigen, Lauf B ist nur ein Beispiel dafür. Den Fehler
   zeigen die Fall-Zeilen, die `Checks:`-Zeile und der Exit-Code an.
2. **`signature.sig` wird nicht gelesen.** Der Checker öffnet die Datei nirgends. Wird
   `01-allow/signature.sig` durch `AA==` ersetzt und der Manifest-Eintrag nachgezogen,
   endet der Lauf mit 66/66 und Exit 0. Geprüft wird nur das Feld `signature` in
   `receipt.json`.
3. **Ungeordnete Menge in Stdout (`:990`).** Für Fall 10c druckt der Checker
   `trace_ids differ: {trace_ids}` mit einem Python-`set`. Dessen Reihenfolge hängt von
   der Hash-Randomisierung des Prozesses ab. Ein Sweep über `PYTHONHASHSEED` 0–15 ergab
   je Lauf genau zwei Stdout-Varianten. Ein Stdout-Hash belegt deshalb nur dann etwas,
   wenn der Lauf seinen Hash-Seed deklariert. Diese Läufe verwenden
   `PYTHONHASHSEED=2`.
4. **`custody.nativeCaseArraySHA256` ist nicht nachrechenbar.** Den Wert
   `de7fd622ffc4f0b7faa6b65ce44018c8a438b659f0dd329356e7dc2587075dbe` nennt der Anhang,
   die Serialisierung, über die er gebildet ist, aber nicht. Sieben naheliegende
   Serialisierungen der Fall-Liste trafen nicht. Die Fall-Datensätze selbst sind
   einzeln nach JCS gleich (Abschnitt 3).
5. **Python-Version.** Diese Läufe liefen unter 3.14.3, Sankalp Gilda nennt 3.14.7.
   Lauf A ist trotzdem byte-gleich. Eine Aussage über 3.14.7 folgt daraus nicht.

## 5 Was die Läufe nicht belegen

Der Checker erklärt JCS (RFC 8785). Die Läufe liefern kein eigenes numerisches
Admission-Profil und zeigen keine Äquivalenz zu einem anderen Kanonisierungsprofil. Die
15-Vektor-Admission-Menge (`vectors/mustfail-v1`) wurde nicht ausgeführt.

Ein Receipt, das hier besteht, passt zur Signatur und zu den Regeln des Checkers. Ob die
beschriebene Handlung stattgefunden hat und ob der Handelnde dazu befugt war, folgt
daraus nicht.

Die erwarteten Antworten (`expected.json` je Fall) waren vor Lauf A sichtbar, sie liegen
offen im Repo. Lauf A ist damit eine Wiederholung mit bekannten Antworten. Er belegt,
dass dieser Checker auf diesen Bytes diese Ausgaben erzeugt.

## 6 Offen

Sankalp Gildas Stdout-Hash für Lauf B,
`2464888fa3ae65a4625e0fa43f88e38429fd595e9c0f8b869710c70a8aaee2c9`, ist nicht
reproduziert und unerklärt. Unter Seed 0–15 entstehen in Lauf B nur zwei Varianten:
`bf62868699bff8f61cc707631669ec979a05d92c525ea9da2ebd445807a3f903` und
`018ea8236e369e0f3f219464603a9a5f8c8bce66f0c63acdb65a90e66f308f03`. Ersetzt man die
Signatur zusätzlich in `signature.sig`, entstehen dieselben zwei.

## 7 Dateien

| Datei | Inhalt |
|---|---|
| `lauf-A.json`, `lauf-B.json`, `lauf-C.json` | Ergebnis je Lauf (JCS): Quelle, Eingabe mit Datei-Hashes, nativer Prozess, Fußzeile, Nachzählung, Fall-Datensätze mit nativem Objekt |
| `lauf-A.stdout.txt`, `lauf-B.stdout.txt`, `lauf-C.stdout.txt` | Checker-Stdout verbatim |
| `tools/run_one.py`, `tools/reproduce.sh` | Harness und Neuaufbau |
| `SHA256SUMS` | Hashes über das Arbeitsverzeichnis, 1575 Dateien: Ergebnisdateien, Tools, die drei Corpus-Kopien `runs/` und die gezogenen Quellen `src/mail/`. `runs/` entsteht neu mit `tools/reproduce.sh`. `src/mail/` liegt nicht im Repo, die Quellen stehen in Abschnitt 1. |
