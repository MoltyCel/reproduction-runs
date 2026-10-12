# Nachrechnung agentproto-privacy-preserving-dialog-recovery @ 278fbf57 (v0.2.2)

Gelaufen ist die von Nikhil genannte Revision v0.2.2, im Arbeitsverzeichnis
`/tmp/mt-runs/278fbf57/`. Ein früherer Lauf desselben Commits mit denselben
Skripten und Parametern lag in einem Verzeichnis, dessen Pfad einen
Personennamen enthält, und kam zu denselben Ergebnissen; sein `SHA256SUMS` hat
die SHA-256 `8f8b04a733d3476eeff95f030581d66e1df309bbead4361c8dbc9e856e80e080`.
Dieser Lauf ersetzt ihn für die Veröffentlichung. Ein Lauf 1 gegen `a940acea`
(v0.2.1) existiert, wird aber nicht veröffentlicht.

| | |
|---|---|
| Repo | https://github.com/nikhilred2619/agentproto-privacy-preserving-dialog-recovery |
| Gepinnter Commit | `278fbf573522b6a45366c9e7f33a0235f4f715b8`. `git ls-remote` am 12.10.2026 um 12:37 UTC vor den Läufen: `HEAD` und `refs/heads/master` zeigen auf diesen Commit, Tags gibt es keine (`inputs/ls-remote-2026-10-12.txt`). Commit-Datum 2026-10-12 06:36:50 -0500, „docs: place v0.2.2 documentation in docs/ directory". Vorgänger `f2384736` („v0.2.2: validate safe operation recovery after Agent A process restart"), davor `a940acea` (v0.2.1). |
| Git-Tree | `5ccc6f1990392b840c8451436b028bfbb3dda5bb` |
| SHA-256 `git archive` (tar, `--prefix=agentproto-recovery-278fbf5/`, git 2.50.1) | `8acbf47fd55dfa35e3ad6440f82ed17ce455560aae397641a5b6d20686d53b4d`. Installiert wurde aus dem Tar ohne Präfix: `8b301dd6562b9eb60f6ef3407ac664d8a3ff8d5cb67a924e50da85f12ea52b7a` (`inputs/git-archive-sha256.txt`). |
| SHA-256 Manifest aller 67 verfolgten Dateien | `245d589b6dc51015425ceffdc41600107db3c1a2f8a53eaab573be1c25f0493d` (`inputs/tracked-files.sha256`) |
| SHA-256 Manifest Paketquelle (15 `.py`) | `8e80a60e8d5730a0806d030776e45d89ff8a98c4150f37748d276564624894b2` (`inputs/package-source.sha256`). Gegenüber v0.2.1 geändert: `__init__.py`, `agents.py`, `gateways.py`. |
| Umgebung | CPython 3.12.12 (Build „main, Feb 12 2026", von uv 0.10.4 nach `env/python/` installiert), macOS 26.6.2 arm64, SQLite 3.50.4, cryptography 50.0.1, pytest 9.1.1, 10 CPUs |
| PYTHONHASHSEED | Referenzläufe ohne festen Seed: `noseedA` (Referenz) und `noseedB`, beide mit `sys.flags.hash_randomization = 1`. Kontrolllauf `seed0` mit `PYTHONHASHSEED=0`. Zusatzlauf `extra-noseed` (ohne Seed) nur für das Neustart-Szenario. |

## Ergebnis

In allen drei Varianten liefen die 14 Treiber-Prozesse (6 Konfigurationen plus
Negativkontrolle, je Szenarien und Fehlerinjektion) mit Exit-Code 0, ohne
Ausnahme und ohne stderr-Ausgabe. Die 14 Datensatz-Dateien haben in `noseedA`,
`noseedB` und `seed0` dieselbe SHA-256 und sind bytegleich mit denen aus dem
früheren Lauf und aus Lauf 1. Die nativen CLI-Dateien `scenario_matrix.csv`,
`scenario_summary.json`, `fault_schedule.csv`, `fault_summary.json`,
`privacy.json` und `privacy.csv` sind in allen drei Varianten bytegleich mit
den committeten Dateien unter `results/`.

Die Nachzählung prüft 97 Angaben aus `docs/results.md`, `README.md` und
`docs/experiment_methodology.md`. 96 stimmen. Abweichung:
`docs/experiment_methodology.md:27` nennt für die Negativkontrolle in der
Fehlerinjektion 23 Fehler, nachgezählt sind 13, wie in `docs/results.md:313`
und `README.md:43`.

Die Testsuite lief dreimal vollständig: je 379 passed, 0 failed, 0 skipped.
Bei zehn weiteren Läufen der beiden Neustart-Dateien schlug in Lauf 02 ein
Test fehl (`test_a_b_…[global-store]`, 1 failed, 73 passed). Der
Controller des Test-Harness bekam beim Verbindungsaufbau
`ConnectionRefusedError`, bevor eine Neustart-Zusicherung geprüft wurde.
Einzelheiten im Abschnitt Schritt 4.

Das Neustart-Szenario trennt „Quittung nicht erhalten" von „Operation nicht
ausgeführt": Agent A markiert die offene Operation als `IN_DOUBT` und schickt
nichts erneut; `NOT_EXECUTED` setzt Agent A erst, wenn Agent B das nach einer
Sperre (Fence) meldet. In `scoped-endpoint-noticket` endet jeder der 270
Fault-Versuche mit `MAPPING_NOT_FOUND`; der Befund aus Lauf 1 gilt unverändert.

## Schritt 1: Doku gegen Auftragsparameter

Auftrag: Seeds 1, 2, 3 über `random.Random(seed)`, 90 Dialoge je Konfiguration
und Seed, 3 Wiederholungen je Zelle, Privacy 50 Dialoge, Negativkontrolle läuft
mit, kein fester `PYTHONHASHSEED`, Identifikatoren aus OS-Zufall.

Übereinstimmend dokumentiert:

- Seeds und Dialoge: `docs/experiment_methodology.md:47-49` „For each seed in
  {1, 2, 3} and each mode: 90 dialogs are established … one fault drawn with
  `random.Random(seed)`". Code: `cli.py:94`, Standardwerte `cli.py:258-259`.
- Wiederholungen: `docs/experiment_methodology.md:35-36` „plus 2
  negative-control cells, each repeated 3 times"; `docs/results.md:283`
  „152 cells … 3 repeats each". Code: `cli.py:257`.
- Privacy: `docs/experiment_methodology.md:69` „Workload: 50 dialogs";
  `docs/results.md:328`. Code: `cli.py:260`.
- Negativkontrolle: `docs/experiment_methodology.md:13-15`; läuft in
  `cli.py:67` (Szenarien T05, T06) und `cli.py:158` (Fehlerinjektion) ohne
  Schalter immer mit.
- Identifikatoren: `docs/experiment_methodology.md:64-65` „Identifier *values*
  are not (they come from the OS CSPRNG on purpose), and no result depends on
  them."

Abweichungen, einzeln:

1. Zahl der Negativkontrolle. `docs/experiment_methodology.md:26-27`: „The
   negative control shows the oracle detects errors (T06: `OK ✗WRONG`; fault
   schedule: 23)." `docs/results.md:313` druckt 13, `README.md:42-43` „did so
   13 times in 270". Nachgezählt: 13 falsche Zuordnungen, alle bei
   `mapping_deleted`.
2. `PYTHONHASHSEED` steht in keiner der 67 verfolgten Dateien. Die Doku legt
   den Seed also nicht fest; das deckt sich mit dem Auftrag, ist aber nirgends
   ausgesprochen.
3. Das Neustart-Szenario hat in `docs/experiment_methodology.md` keinen
   Abschnitt. Seeds, 90 Dialoge und 3 Wiederholungen gelten dort nicht: jeder
   Fall läuft je pytest-Aufruf einmal pro Modus, ohne Seed. Als Wiederholung
   nennt `docs/results.md:252` „4 consecutive runs on Python 3.13" und
   `docs/results.md:256-257` „run 10 more times together: green every time".
4. Reproduktionsbefehl `docs/experiment_methodology.md:133-135`:
   `pip install -e ".[test]"` und `agentproto-recovery all --out results`.
   `all` startet auch den Benchmark (`cli.py:281`) und schreibt in das
   `results/` des Repos, überschreibt also die committeten Dateien. Die
   Parameter entsprechen den Standardwerten; das Editable-Install verbietet der
   Auftrag. Hier liefen `scenarios`, `faults`, `privacy` einzeln mit eigenem
   `--out`.
5. Herkunft der Zahlen: `docs/results.md:3-6` „Version 0.2.0. All numbers below
   come from one run of `agentproto-recovery all --out results` on 2026-10-11
   (Python 3.13.16, SQLite 3.45.1, … Linux x86_64 container, 2 vCPU". Für
   v0.2.2 verweist `docs/results.md:19-23` auf einen Nachlauf mit Vergleich
   (`results/v0.2.2_rerun_check.txt`).
6. Außerhalb der beiden Dokumente: `.github/workflows/tests.yml:22-23` fährt
   die Experimente mit `--repeats 1 --fault-dialogs 30 --seeds 1
   --privacy-dialogs 10`, als „Smoke-run experiments (small)" bezeichnet
   (`tests.yml:20`). Die Datei lief hier nicht.

## Tabelle A: Szenario-Matrix T01–T23 je Konfiguration

25 Szenarien × 3 Wiederholungen = 75 Fälle je Konfiguration, Referenz
`noseedA`. „nicht-det." zählt Szenarien, deren drei Wiederholungen
unterschiedlich ausgingen; die falsche Zuordnung zählt an Wiederholung 0, wie
im CLI.

| Konfiguration | Exit | Fälle | Zellen | nicht-det. | falsche Zuordnung | Exceptions | SHA-256 Eingabe-Bündel | SHA-256 Datensätze |
|---|---|---|---|---|---|---|---|---|
| `global-store` | 0 | 75 | 25 | 0 | 0 | 0 | `fa9b88b0…` | `6a4a5147…` |
| `global-endpoint` | 0 | 75 | 25 | 0 | 0 | 0 | `a50df3f2…` | `53edd9af…` |
| `scoped-store` | 0 | 75 | 25 | 0 | 0 | 0 | `14fb37f4…` | `3fad4568…` |
| `scoped-endpoint-noticket` | 0 | 75 | 25 | 0 | 0 | 0 | `613a1755…` | `a4522f5b…` |
| `scoped-endpoint-ticket` | 0 | 75 | 25 | 0 | 0 | 0 | `573a411e…` | `4ee88aa0…` |
| `scoped-endpoint-medticket` | 0 | 75 | 25 | 0 | 0 | 0 | `70e7543b…` | `73145612…` |
| Negativkontrolle `scoped-store+UNSAFE_GUESS` (nur T05, T06) | 0 | 6 | 2 | 0 | 1 (T06) | 0 | `8a69d92c…` | `1d8aa5ec…` |

Summe 152 Zellen. Datensatz-Hashes und Eingabe-Bündel sind dieselben wie im
früheren Lauf, weil Paketquelle, `driver.py` und Aufrufe dieselben Bytes haben.
Eingabe-Bündel = SHA-256 über (Paketquell-Manifest ‖ `driver.py` ‖
Aufruf-JSON). Volle Hashes: `inputs/digests.json`, `recount/recount.json`.

Gedruckte Zusammenfassung des nativen CLI (`agentproto-recovery scenarios`,
Standardargumente, Exit 0), Wortlaut:

```
scenarios: {"repeats_per_cell": 3, "cells": 152, "cells_with_nondeterministic_outcome": {}, "incorrect_associations": 1, "incorrect_associations_excluding_negative_control": 0}
```

## Tabelle B: Fehlerinjektion je Konfiguration

3 Seeds × 90 Dialoge = 270 Versuche je Konfiguration. Die gezogene Fault-Folge
hat in allen Konfigurationen und Varianten die SHA-256
`22fd23dd8660e4e70f9323762c378e55cf4a66352823322fc628ccdc0822fbf1`, wie im
früheren Lauf. Sicherheitsverletzungen sind neu berechnet (wiederhergestellt
und falsch zugeordnet, oder Fault in `MUST_FAIL`); Nikhils Flag liefert
dieselben Zahlen.

| Konfiguration | Exit | Versuche | wiederhergestellt | explizit abgelehnt | falsche Zuordnung | Sicherheitsverletzung | Quote, wo erlaubt | SHA-256 Datensätze |
|---|---|---|---|---|---|---|---|---|
| `global-store` | 0 | 270 | 70 | 200 | 0 | 0 | 0.6195 | `74cfc3b1…` |
| `global-endpoint` | 0 | 270 | 113 | 157 | 0 | 0 | 1.0 | `c5c2262a…` |
| `scoped-store` | 0 | 270 | 70 | 200 | 0 | 0 | 0.6195 | `7aee6a64…` |
| `scoped-endpoint-noticket` | 0 | 270 | 0 | 270 | 0 | 0 | 0.0 | `d49b9d76…` |
| `scoped-endpoint-ticket` | 0 | 270 | 67 | 203 | 0 | 0 | 0.5929 | `2c0ab489…` |
| `scoped-endpoint-medticket` | 0 | 270 | 67 | 203 | 0 | 0 | 0.5929 | `9028f5e2…` |
| Negativkontrolle `scoped-store+UNSAFE_GUESS` | 0 | 270 | 78 | 192 | 13 | 13 | 0.6903 | `833e44f0…` |

Ergebniscodes je Fault:

| Fault | n | `global-store` | `global-endpoint` | `scoped-store` | `scoped-endpoint-noticket` | `scoped-endpoint-ticket` | `scoped-endpoint-medticket` | Kontrolle |
|---|---|---|---|---|---|---|---|---|
| none | 24 | OK 24 | OK 24 | OK 24 | MAPPING_NOT_FOUND 24 | OK 24 | OK 24 | OK 22, STALE_REFERENCE 2 |
| mapping_deleted | 19 | MAPPING_NOT_FOUND 19 | OK 19 | MAPPING_NOT_FOUND 19 | MAPPING_NOT_FOUND 19 | OK 19 | OK 19 | OK 13, MAPPING_INTEGRITY_FAILURE 6 |
| mapping_tampered | 24 | MAPPING_INTEGRITY_FAILURE 24 | OK 24 | MAPPING_INTEGRITY_FAILURE 24 | MAPPING_NOT_FOUND 24 | OK 24 | OK 24 | MAPPING_INTEGRITY_FAILURE 24 |
| ticket_lost | 22 | OK 22 | OK 22 | OK 22 | MAPPING_NOT_FOUND 22 | MAPPING_NOT_FOUND 22 | MAPPING_NOT_FOUND 22 | OK 21, STALE_REFERENCE 1 |
| foreign_ticket | 24 | OK 24 | OK 24 | OK 24 | MAPPING_NOT_FOUND 24 | TICKET_MISMATCH 21, MAPPING_NOT_FOUND 3 | TICKET_MISMATCH 21, MAPPING_NOT_FOUND 3 | OK 22, STALE_REFERENCE 2 |
| revoked | 24 | AUTHZ_REVOKED 24 | AUTHZ_REVOKED 24 | AUTHZ_REVOKED 24 | MAPPING_NOT_FOUND 24 | AUTHZ_REVOKED 24 | AUTHZ_REVOKED 24 | AUTHZ_REVOKED 24 |
| expired | 31 | AUTHZ_EXPIRED 31 | AUTHZ_EXPIRED 31 | AUTHZ_EXPIRED 31 | MAPPING_NOT_FOUND 31 | AUTHZ_EXPIRED 31 | AUTHZ_EXPIRED 31 | AUTHZ_EXPIRED 31 |
| terminated | 35 | DIALOG_TERMINATED 35 | DIALOG_TERMINATED 35 | DIALOG_TERMINATED 35 | MAPPING_NOT_FOUND 35 | DIALOG_TERMINATED 35 | DIALOG_TERMINATED 35 | DIALOG_TERMINATED 35 |
| stale_replay | 37 | STALE_REFERENCE 37 | STALE_REFERENCE 37 | STALE_REFERENCE 37 | MAPPING_NOT_FOUND 37 | STALE_REFERENCE 37 | STALE_REFERENCE 37 | STALE_REFERENCE 37 |
| wrong_principal | 30 | PRINCIPAL_MISMATCH 30 | PRINCIPAL_MISMATCH 30 | PRINCIPAL_MISMATCH 30 | MAPPING_NOT_FOUND 30 | PRINCIPAL_MISMATCH 30 | PRINCIPAL_MISMATCH 30 | PRINCIPAL_MISMATCH 30 |

Alle 13 Sicherheitsverletzungen der Negativkontrolle fallen auf
`mapping_deleted` mit `OK` und falscher Zuordnung. Die Tabelle ist Zeile für
Zeile dieselbe wie im früheren Lauf und in Lauf 1.

## Schritt 6: `scoped-endpoint-noticket`

Ja, jeder Fault endet mit `MAPPING_NOT_FOUND`: alle zehn Fault-Typen, 270 von
270 Versuchen, in `noseedA`, `noseedB` und `seed0` (Datensatz-Dateien
bytegleich). Je Fault: none 24, mapping_deleted 19, mapping_tampered 24,
ticket_lost 22, foreign_ticket 24, revoked 24, expired 31, terminated 35,
stale_replay 37, wrong_principal 30. Ausnahmen gibt es keine. Der Befund aus
Lauf 1 gilt: in dieser Konfiguration scheitert der Ersatz-Gateway an der
fehlenden Zuordnung, bevor eine Prüfung auf Widerruf, Ablauf oder falschen
Principal greift, und die 0 Sicherheitsverletzungen sagen über
Fehlererkennung nichts aus.

## Abgleich mit Nikhils Angaben

Referenz `noseedA`, Nachzählung ohne Import des Pakets
(`scripts/recount.py`). Alle 97 Vergleiche einzeln in
`recount/recount.json` unter `claims`.

| Angabe (Quelle) | Gedruckt | Nachgezählt | Gleich |
|---|---|---|---|
| E2-Tabelle, 7 Zeilen × 5 Werte (`docs/results.md:307-313`) | siehe Tabelle B | Tabelle B | ja, 35 von 35 (Quote auf 3 Stellen gerundet: 0.620, 1.000, 0.000, 0.593, 0.690) |
| 270 Versuche je Modus (`docs/results.md:301`) | 270 | 270 | ja |
| `foreign_ticket` 24 je Modus (`docs/results.md:315`) | 24 | 24 | ja |
| `foreign_ticket` Store- und global-endpoint 24 OK (`docs/results.md:315-316`) | 24 OK | 24 OK in allen drei | ja |
| `foreign_ticket` Ticket-Modi 21 TICKET_MISMATCH, 3 MAPPING_NOT_FOUND (`docs/results.md:316-317`) | 21 / 3 | 21 / 3 in beiden | ja |
| 1.620 Versuche, 0 falscher Dialog, 0 aus `MUST_FAIL` wiederhergestellt (`docs/results.md:321-323`, `README.md:40-43`) | 1.620 / 0 / 0 | 1.620 / 0 / 0 | ja |
| noticket 0 von 270 (`README.md:35-36`) | 0 / 270 | 0 / 270 | ja |
| Kontrolle 13 von 270 (`README.md:42-43`) | 13 / 270 | 13 / 270 | ja |
| Kontrolle Fehlerinjektion (`docs/experiment_methodology.md:26-27`) | 23 | 13 | **nein** |
| Kontrolle T06 `OK ✗WRONG` (`docs/experiment_methodology.md:27`) | OK, falsch | OK, falsch | ja |
| E1 152 Zellen (`docs/results.md:283`, `:20`) | 152 | 152 | ja |
| 3 Wiederholungen je Zelle (`docs/results.md:283`) | 3 | 3 | ja |
| Zellen mit abweichenden Wiederholungen (`docs/results.md:285`) | 0 | 0 | ja |
| falsche Zuordnungen außerhalb der Kontrolle (`docs/results.md:286`) | 0 | 0 | ja |
| falsche Zuordnungen Kontrolle, T06 (`docs/results.md:286-287`) | 1 | 1 | ja |
| T21: TICKET_MISMATCH in Ticket-Modi, OK und richtig in Store- und global-endpoint, noticket scheitert (`docs/results.md:288-290`) | wie links | wie links; noticket MAPPING_NOT_FOUND | ja |
| T22: IN_PROGRESS, NOT_EXECUTED, OPERATION_ABORTED, Retry OK, 1 Ausführung, jeder Modus (`docs/results.md:291-294`) | wie links | in allen 6 Modi identisch | ja |
| T23: SEQUENCE_CONFLICT, 1 Ausführung, Retry dedupliziert, jeder Modus (`docs/results.md:295-296`) | wie links | in allen 6 Modi identisch | ja |
| Nachlauf v0.2.2: 152 Zellen, 1.890 Zeilen, Privacy identisch (`docs/results.md:19-22`) | identisch | eigene Läufe: 152/152, 1.890/1.890, `privacy.json` und `privacy.csv` bytegleich | ja |
| E3, 6 Zeilen × 6 Werte (`docs/results.md:333-338`) | siehe dort | 36 von 36 gleich, abgelesen aus der nativen `privacy.json` dieses Laufs | ja |
| E3 50 Dialoge je Modus (`docs/results.md:328`) | 50 | 50 | ja |
| pytest gesamt (`README.md:83-84`, `:187`; `docs/results.md:246`, `:252`) | 379 passed | 379 passed, je Vollauf | ja |
| davon Fehler, Fehlerabbrüche, Skips (`docs/results.md:246`) | 0 | 0 in den drei Volläufen | ja |
| `test_process_restart.py` (`docs/results.md:60-61`, `:255`) | 66 passed | 66 | ja |
| `test_process_restart_regression.py` (`docs/results.md:60`, `:255`) | 8 passed | 8 | ja |
| beide zusammen (`docs/results.md:61-62`, `README.md:218`) | 74 | 74 | ja |
| Tests mit echten OS-Prozessen (`README.md:187`) | 74 | 74 (die zwei Neustart-Dateien) | ja |
| `test_review_v022.py` (`docs/results.md:108`, `:247-248`, `:255`; `README.md:77`, `:220`) | 72 passed | 72 | ja |
| Tests aus v0.2.1 (`docs/results.md:247`) | 233 | 233 | ja |
| `test_operation_ledger_integrity.py` (`docs/results.md:195`, `README.md:105`) | 44 | 44 | ja |
| 2a und 2b zusammen 24 Fälle (`docs/results.md:132`) | 24 | 12 + 12 | ja |
| Restart-Tabelle, Fallzahl je Zeile A,B bis unsupported (`docs/results.md:66-77`) | 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 1 | dieselben 12 Werte | ja, 12 von 12 |
| Restart-Tabelle, zugesichertes Verhalten je Zeile (`docs/results.md:66-77`) | 12 Zeilen | in jedem beobachteten Lauf von `noseedA` eingetreten (18, 15 bzw. 3 Läufe je Zeile) | ja, 12 von 12 |
| v0.2.1-Baseline: Regressionstests schlagen fehl (`docs/results.md:53`, `README.md:60-61`) | 8 failed | 8 failed (eigener Lauf gegen v0.2.1, s. u.) | ja |
| committete `results/scenario_matrix.csv`, `fault_schedule.csv`, `*_summary.json`, `privacy.*` | Dateien | bytegleich, alle drei Varianten | ja |

Nicht nachprüfbar, weil der Stand nicht im Repo liegt oder nicht lief: 44
failed / 28 passed auf dem Entwurf vor dem Audit (`docs/results.md:104`; der
Entwurf ist nicht committet, nur Quell-Hashes in
`results/v0.2.2_review_before_fix.txt:3-4`), die 307 passed des Entwurfs
(`docs/results.md:261`), Python 3.11 und 3.13 (`docs/results.md:253-255`,
`README.md:84`), die Wiederholungszahlen auf Nikhils Maschine
(`docs/results.md:252`, `:256-257`), E4.

## Schritt 4: Testsuite

| Lauf | Aufruf | Ergebnis | Dauer |
|---|---|---|---|
| `noseedA` | volle Suite | 379 passed, Exit 0 | 18,8 s |
| `noseedB` | volle Suite | 379 passed, Exit 0 | 18,4 s |
| `seed0` | volle Suite | 379 passed, Exit 0 | 19,2 s |
| `extra-noseed` 01–10 | nur `test_process_restart.py` und `test_process_restart_regression.py` | neunmal 74 passed; Lauf 02: 1 failed, 73 passed, Exit 1 | je 16–17 s |
| `baseline-v021` | `test_process_restart_regression.py` dieser Revision gegen das v0.2.1-Paket | 8 failed, Exit 1 | 1,7 s |

Erwartet waren 379; gezählt sind 379 in jedem Vollauf, ohne Skip und ohne
Fehler. Die Aufteilung je Datei steht in `recount/recount.json`
(`pytest.<lauf>.per_file`). Die Volläufe dauerten hier rund 3,5 s länger als
im früheren Lauf (15,2 bis 15,6 s); die Ursache ist nicht untersucht.

Fehlschlag in `extra-noseed` Lauf 02:
`test_process_restart.py::test_a_b_sent_survives_restart_with_identity[global-store]`,
an `tests/test_process_restart.py:44`
(`assert c.ctl("wait_entered", gate=gate)`). Der Controller öffnet dafür eine
neue Verbindung zum Harness-Server (`tests/restart_harness.py:426`), und
`connect` auf den AF_UNIX-Socket endete mit
`ConnectionRefusedError: [Errno 61] Connection refused`
(`runs/extra-noseed/pytest-restart/pytest-02.stdout`). Der Test scheitert damit
an seiner Vorbedingung, bevor eine Neustart-Zusicherung geprüft wird. In den
1.406 Beobachtungsläufen dieses Laufs (3 × 222 plus 740) erreichte jeder Fall
seinen Haltepunkt.

Im früheren Lauf schlug ein anderer Test fehl (Lauf 06,
`test_c_…[scoped-endpoint-noticket]`, `assert False` an derselben Zeile: die
Antwort des Controllers kam an und meldete, dass P1 den Haltepunkt nicht
erreicht hatte), dazu 1 von 1.406 Beobachtungsläufen (`noseedB`, Fall R1,
`global-store`, Index 2). Damals war vermutet, am Einzelfall aber nicht
belegt: Der Harness-Server öffnet
`Listener(address, family="AF_UNIX", authkey=…)` (`tests/restart_harness.py:181`)
mit dem Standard-Backlog 1 von `multiprocessing.connection`; ein einziger
Thread nimmt Verbindungen an und führt dabei den Auth-Handshake aus. In
`crash_p1` verbinden sich P1 (Invoke) und der Controller (`wait_entered`)
fast gleichzeitig. Der Fehlschlag hier zeigt eine abgewiesene Verbindung am
Controller direkt im Traceback. Ob im früheren Fall P1s Verbindung abgewiesen
wurde, bleibt offen. Der eigene Nachbau ohne Repo-Code
(`scripts/listener_backlog_probe.py`) ergab bei 2 gleichzeitigen Clients 104
von 4.000 abgewiesene Verbindungen (`ConnectionRefusedError`), bei 3 Clients
2.008 von 6.000, bei 8 Clients 2.997 von 4.000, mit Backlog 16 0 von 4.000
(`runs/diag/listener-backlog-probe.jsonl`; früherer Lauf: 82, 2.006, 3.000,
0). Ob Linux, Nikhils Plattform, bei vollem AF_UNIX-Backlog ebenso abweist,
ist hier nicht geprüft.

## Schritt 5: Neustart-Szenario „Agent A process restart"

Das Szenario steht nur in den Tests (`tests/restart_harness.py`,
`tests/test_process_restart.py`, `tests/test_process_restart_regression.py`),
nicht im Experiment-CLI. Ablauf laut `docs/results.md:30-33`: P1 speichert
eine Operation als `SENT`, wird per SIGKILL beendet, bevor die Quittung
ankommt; ein neuer Prozess P2 öffnet dasselbe SQLite-Ledger; die ursprüngliche
Ausführung bei B läuft weiter und endet spät. P1 wird an einem von zwei
Haltepunkten gestoppt (`tests/test_process_restart.py:35-46`): `tool` (B hat
`PENDING` geschrieben, das Werkzeug läuft) oder `pre_b` (B hat die Anfrage
noch nicht).

Fälle (Code und `docs/results.md:64-77`):

| ID | Haltepunkt | Was der Fall tut | Modi |
|---|---|---|---|
| A,B | tool | P2 liest das Ledger, `recover` setzt `SENT` → `IN_DOUBT`, Identität, Payload, Attempt, `next_seq` bleiben | 6 |
| C | tool | erster Abgleich solange B ausführt, dann spätes Ende der Originalausführung, zweiter Abgleich | 6 |
| D | pre_b | Abgleich, bevor B die Anfrage hat; danach trifft das Original ein; dann `retry_op` | 6 |
| D2 | tool | simulierter B-Neustart (neue Inkarnations-ID im selben Prozess), Abgleich sperrt beim Werkzeug, `retry_op` | 6 |
| E | tool | zweimal `resume` mit offener Operation, danach Abgleich | 6 |
| F | tool | `seq=1` mit anderem Payload, in Zweifel und nach Commit; gleicher Payload nach Commit | 6 |
| G | pre_b | erste Abgleich-Antwort wird in P2 zurückgehalten, bis ein Retry committet ist | 6 |
| H | tool | nach Commit zwei weitere Abgleiche, P2 per SIGKILL beendet, P3 startet | 6 |
| H2 | tool | P2 stirbt vor der Klärung, P3 klärt | 6 |
| I | tool | B-Speicher nicht erreichbar, dann G1 aus; lokaler Retry und `retry_op` | 6 |
| failover | tool | G1 fällt zusätzlich aus, P2 geht über G2 | 5 (ohne noticket) |
| unsupported | tool | wie failover, nur `scoped-endpoint-noticket` | 1 |
| R1 | tool | Regression: P2 ruft `invoke(seq=1)` mit gleichem Payload | 4 |
| R2 | tool | Regression: `resume`, `settle` vor und nach dem späten Ende | 4 |

Beobachtet mit `scripts/restart_observe_v1.py` (`noseedA`, `noseedB`, `seed0`)
und `scripts/restart_observe.py` (`extra-noseed`): derselbe Schrittablauf wie
in den Tests, über Nikhils `Cluster` aus `tests/restart_harness.py`, ohne
Assertions, jeder Rückgabewert protokolliert, Identifikatoren nicht. 3
Wiederholungen je Fall und Modus in `noseedA`, `noseedB`, `seed0`, dazu 10 in
`extra-noseed`. Jeder Fall × Modus hatte über alle 19 Läufe eine einzige
Ergebnis-Signatur.

Ergebniscodes je Schritt, summiert über `noseedA`, `noseedB`, `seed0`
(je Fall 3 Wiederholungen × Modi × 3 Varianten; Format
`outcome/code/status`):

| Fall | Läufe | Schritt → Ergebnis (Anzahl) | Endzustand A / B / Ausführungen |
|---|---|---|---|
| A,B | 54 | `recover` gibt die Zeile zurück (54); `unresolved`: `IN_DOUBT` (54); P2-Invokes 0 (54) | `IN_DOUBT` / `PENDING` / 0 |
| C | 54 | Abgleich 1: `UNRESOLVED/OUTCOME_UNKNOWN/IN_PROGRESS` (54); späte Antwort an P1: `OK/COMMITTED` (54); Abgleich 2: `COMMITTED/OK/COMMITTED` (54) | `COMMITTED` Attempt 1 / `COMMITTED` / 1, Schlüssel `…:1:1` |
| D | 54 | Abgleich: `NOT_EXECUTED/OK/NOT_EXECUTED`, Detail „no record at B; fenced" (54); spätes Original: `OPERATION_ABORTED/NOT_EXECUTED` (54); `retry_op`: `OK/COMMITTED` (54) | `COMMITTED` Attempt 2 / `COMMITTED` Attempt 1 / 1, Schlüssel `…:1:1` |
| D2 | 54 | Abgleich: `NOT_EXECUTED`, „fenced at tool" (54); altes Original: `OPERATION_ABORTED` (54); `retry_op`: `OK/COMMITTED` (54) | `COMMITTED` Attempt 2 / Attempt 2 / 1, Schlüssel `…:1:2` |
| E | 54 | `resume` ×2: `OK` (54), Zustand unverändert (54), nur `resume`-Aufrufe (54); Abgleich: `COMMITTED` (54) | `COMMITTED` / `COMMITTED` / 1 |
| F | 54 | anderer Payload in Zweifel: `SEQUENCE_CONFLICT`, Status `SENT`, kein Aufruf (54); nach Commit: `SEQUENCE_CONFLICT` (54); gleicher Payload: `OK`, „deduplicated" (54) | `COMMITTED` / `COMMITTED` / 1 |
| G | 54 | Abgleich 2: `NOT_EXECUTED` (54); `retry_op`: `OK/COMMITTED` (54); zurückgehaltene Antwort: `NOT_EXECUTED`, `applied: false` (54); spätes Original: `OK/COMMITTED`, „deduplicated" (54) | `COMMITTED` Attempt 2 / Attempt 1 / 1 |
| H | 54 | Abgleich 1: `COMMITTED` (54); Abgleich 2, 3 und P3 `recover`/`reconcile`/`settle`: leer (54); P3 gleicher Payload: `OK`, „deduplicated" (54); P3-Aufrufe 0 (54) | `COMMITTED` / `COMMITTED` / 1 |
| H2 | 54 | P2-Abgleich: `UNRESOLVED/IN_PROGRESS` (54); P3 `unresolved`: `IN_DOUBT` (54); P3-Abgleich: `COMMITTED` (54) | `COMMITTED` / `COMMITTED` / 1 |
| I | 54 | B-Speicher aus: `UNRESOLVED/DOWNSTREAM_UNAVAILABLE` (54); G1 aus: `UNRESOLVED/GATEWAY_DOWN` (54), `settle`: `GATEWAY_DOWN` (54), `invoke`: `OUTCOME_UNKNOWN/IN_DOUBT` (54), `retry_op`: `INVALID_STATE` (54); danach `COMMITTED` (54) | `COMMITTED` / `COMMITTED` / 1 |
| failover | 45 | `resume` über G2: `OK` (45); Abgleich 1: `UNRESOLVED/IN_PROGRESS` (45); Abgleich 2: `COMMITTED` (45) | `COMMITTED` / `COMMITTED` / 1 |
| unsupported | 9 | `resume` über G2: `MAPPING_NOT_FOUND` (9); beide Abgleiche: `UNRESOLVED/MAPPING_NOT_FOUND` (9) | `IN_DOUBT` / `COMMITTED` / 1 |
| R1 | 36 | `invoke(seq=1)`: `OUTCOME_UNKNOWN/IN_DOUBT` (36); P2-Invokes 0 (36) | `IN_DOUBT` / `COMMITTED` / 1 (36) |
| R2 | 36 | `settle` 1: `OUTCOME_UNKNOWN/UNRESOLVED` (36); `settle` 2: `OK/COMMITTED` (36) | `COMMITTED` / `COMMITTED` / 1 |

Je Modus aufgeschlüsselt stehen die Werte in
`runs/<variante>/restart/restart-observe.jsonl`, summiert in
`recount/recount.json` unter `restart`. Im früheren Lauf endete ein R1-Lauf
ohne erreichten Haltepunkt (`IN_DOUBT` / keine Zeile / 0); hier traf das in
keinem Lauf zu.

### Wo „Quittung nicht erhalten" und „nicht ausgeführt" getrennt werden

Agent A unterscheidet beides über zwei Zustände. Eine Zeile, die ein toter
Prozess als `SENT` hinterlassen hat, wird `IN_DOUBT` und nicht erneut
gesendet:

```
src/agentproto_recovery/agents.py:671  orphan = row["state"] == "SENT" and row["owner"] != self.incarnation
src/agentproto_recovery/agents.py:672  if row["state"] == "IN_DOUBT" or orphan:
src/agentproto_recovery/agents.py:678      return OpResult(Code.OUTCOME_UNKNOWN, "IN_DOUBT", None,
src/agentproto_recovery/agents.py:679                      "outcome of an attempt sent before a restart is unknown; "
src/agentproto_recovery/agents.py:680                      "reconcile before retrying")
src/agentproto_recovery/agents.py:735  c.execute("UPDATE ops SET state='IN_DOUBT' WHERE state='SENT' "
src/agentproto_recovery/agents.py:736            "AND (owner IS NULL OR owner != ?)", (self.incarnation,))
```

`NOT_EXECUTED` schreibt Agent A nur aus einer Antwort von B und nur auf den
Attempt, nach dem gefragt wurde:

```
src/agentproto_recovery/agents.py:772  elif (res.ok and res.status == "NOT_EXECUTED") or res.code is Code.SEQUENCE_CONFLICT:
src/agentproto_recovery/agents.py:774      sql = (f"UPDATE ops SET state=? WHERE dialog_id=? AND seq=? AND attempt=? AND state IN "
src/agentproto_recovery/agents.py:777  else:
src/agentproto_recovery/agents.py:778      return {"seq": seq, "outcome": "UNRESOLVED", ...  "applied": False}
```

Die Entscheidung fällt bei Agent B in `_resolve_observe`:

```
src/agentproto_recovery/agents.py:409  if not rows:
src/agentproto_recovery/agents.py:410      return None, "fence_unseen"
src/agentproto_recovery/agents.py:415  if row["state"] == "COMMITTED":
src/agentproto_recovery/agents.py:416      return OpResult(Code.OK, "COMMITTED", row["result"]), None
src/agentproto_recovery/agents.py:423  if row["incarnation"] == self.incarnation and row["lease_until"] > self.clock.now():
src/agentproto_recovery/agents.py:424      return OpResult(Code.OUTCOME_UNKNOWN, "IN_PROGRESS", None,
src/agentproto_recovery/agents.py:428  if self.tool.lookup(f"{dialog_id}:{seq}:{row['attempt']}") is not None:
src/agentproto_recovery/agents.py:429      return None, "settle_executed"
src/agentproto_recovery/agents.py:430  return None, "fence_started"
```

Hat B keine Zeile, trägt B `NOT_EXECUTED` ein und sperrt alle Attempts bis zum
angefragten (`agents.py:444-447`). Eine noch unterwegs befindliche Kopie wird
dann beim Eintreffen in derselben Transaktion abgewiesen, in der B sonst
`PENDING` schreiben würde:

```
src/agentproto_recovery/agents.py:298  if fence is not None and (client_attempt is None
src/agentproto_recovery/agents.py:299                            or client_attempt <= fence["fenced_through"]):
src/agentproto_recovery/agents.py:300      return OpResult(Code.OPERATION_ABORTED, "NOT_EXECUTED", None,
```

Hat B die Ausführung begonnen und ist die Lease abgelaufen oder die
Inkarnation neu, entscheidet das Werkzeug atomar
(`agents.py:103-111`, `fence`): ausgeführt → `COMMITTED`, sonst Sperre →
`NOT_EXECUTED` (`agents.py:459-467`).

Fälle, die beides auseinanderhalten: C und D unterscheiden sich nur im
Haltepunkt und landen bei `COMMITTED` bzw. `NOT_EXECUTED`; D2 trennt
„begonnen, aber nicht ausgeführt" über die Werkzeug-Sperre; G zeigt, dass eine
veraltete `NOT_EXECUTED`-Antwort einen späteren Commit nicht überschreibt
(`applied: false`); `unsupported` und R1 zeigen den Fall, in dem A die
Ausführung nicht erfahren kann: die Operation lief einmal, A bleibt bei
`IN_DOUBT` und sendet nichts.

Zwei Stellen, an denen die Trennung nicht greift oder anders aussieht:

- Im laufenden Prozess (ohne Neustart) legt `_record` eine Sperr-Antwort mit
  Transportfehlern zusammen:
  `agents.py:705-707` „`if res.code in (Code.DOWNSTREAM_UNAVAILABLE, Code.GATEWAY_DOWN, Code.OPERATION_ABORTED):` …
  `new_state = "UNKNOWN"  # cannot tell (or fenced): resend same seq later`".
  `settle_unknown_ops` sendet `UNKNOWN` mit gleicher `seq` erneut
  (`agents.py:812-813`). Das Neustart-Szenario berührt diesen Pfad nicht, kein
  Fall prüft ihn.
- In D führt B die Wiederholung unter dem Werkzeug-Schlüssel `…:1:1` aus,
  obwohl A sie als Attempt 2 führt. B legt die Sperrzeile mit Attempt 0 an
  (`agents.py:445`) und zählt beim Retry von dort hoch (`agents.py:310`). Das
  ursprüngliche Attempt 1 wird bei B abgewiesen (`agents.py:298-300`), bevor es
  das Werkzeug erreicht; eine doppelte Ausführung trat in keinem der 54
  D-Läufe auf. In D2 stimmen beide Zählungen (`…:1:2`).

`docs/results.md:39-41` nennt „every wait is on an event with a 60 s failure
bound". Die Haltepunkte selbst warten bis zu 240 s
(`tests/restart_harness.py:98`, `:253`, `WAIT * 4`); als Fehlschlag zählt
dort nichts.

## Methode und Abweichungen vom Auftrag

Das Arbeitsverzeichnis `/tmp/mt-runs/278fbf57/` war vorher leer. Der Klon
liegt in `src/repo` (vorher leer), Hooks abgeschaltet
(`core.hooksPath=/dev/null`), Checkout detached auf den SHA. Eigene Skripte in
`scripts/`, die venv in `env/venv312`, gebaut mit `uv venv` gegen ein
CPython 3.12.12, das uv mit `UV_PYTHON_INSTALL_DIR=env/python` frisch nach
`env/python/` installiert hat; den uv-Cache hielt `UV_CACHE_DIR=env/uv-cache`
ebenfalls im Arbeitsverzeichnis. Das Paket kam ohne Abhängigkeiten aus dem
`git archive`-Tar per `uv pip install --no-deps` in die venv; ausgepackt und
gebaut wurde in `.scratch/`, außerhalb des Repos. Die übrigen Pakete sind auf
die Versionen des früheren Laufs festgelegt (cryptography 50.0.1, pytest
9.1.1, cffi 2.1.1, pycparser 3.11, iniconfig 2.3.1, packaging 26.3, pluggy
1.6.0, pygments 2.21.0); dort waren nur cryptography und pytest gepinnt, die
installierte Liste ist dieselbe. Die 15 installierten `.py` sind bytegleich
mit dem Quellbaum. Kein `pip install -e`. Der Repo-Baum ist nach allen Läufen
unverändert (`git status --porcelain --ignored` leer).

Alle Varianten liefen mit `env -i` und `python -P -s -B`, ohne `-I`, damit
`PYTHONHASHSEED` in `seed0` greift und alle Varianten dieselben Flags haben.
In der Umgebung standen `PATH`, `HOME` (`.scratch/home`, leer geblieben),
`TMPDIR` (in `.scratch/`) und `PYTHONDONTWRITEBYTECODE=1`; letzteres, weil der
Neustart-Harness Unterprozesse ohne Interpreter-Flags startet.
Arbeitsverzeichnis war je ein leeres Verzeichnis in `.scratch/`.

`scripts/` ist eine Kopie der Skripte des früheren Laufs. Geändert ist nur
`run_all.sh`, dazu kommt `scripts/pytest_plugin/junit_nohostname.py`. Der
vollständige Diff steht in `inputs/scripts_earlier_run_to_this_run.diff`:

```diff
--- earlier-run/scripts/run_all.sh
+++ this-run/scripts/run_all.sh
@@ -7,17 +7,19 @@
 # that subprocesses started by the repo's restart harness write no bytecode either.
 # TMPDIR points into .scratch (the harness itself hard-codes /tmp for its sockets).
 set -u
-T="$HOME/Downloads/block-1012/tab-nikhil-v022"
+T="/private/tmp/mt-runs/278fbf57"   # = /tmp/mt-runs/278fbf57 (canonical form, so pytest prints relative paths as before)
 PY="$T/env/venv312/bin/python"
 DRV="$T/scripts/driver.py"
-OBS="$T/scripts/restart_observe.py"
+OBS="$T/scripts/restart_observe_v1.py"   # noseedA/noseedB/seed0 ran with v1 in the earlier run
 V="$1"
 OUT="$T/runs/$V"
 SCR="$T/.scratch/$V"
 mkdir -p "$OUT/per-config" "$OUT/native" "$OUT/restart" "$SCR/tmp"
 WORK=$(mktemp -d "$SCR/cwd-XXXX")   # empty cwd, nothing importable
 cd "$WORK"
-BASEENV=(PATH=/usr/bin:/bin HOME="$HOME" TMPDIR="$SCR/tmp" PYTHONDONTWRITEBYTECODE=1)
+BASEENV=(PATH=/usr/bin:/bin HOME="$T/.scratch/home" TMPDIR="$SCR/tmp" PYTHONDONTWRITEBYTECODE=1)
+# pytest only: plugin that keeps the machine name out of the JUnit XML hostname attribute
+runpt() { local BASEENV=("${BASEENV[@]}" PYTHONPATH="$T/scripts/pytest_plugin"); run -m pytest -p junit_nohostname "$@"; }
 case "$V" in
   seed*)   SEED="${V#seed}"
            run() { env -i "${BASEENV[@]}" PYTHONHASHSEED="$SEED" "$PY" -P -s -B "$@"; } ;;
@@ -52,7 +54,7 @@
 done
 # full test suite, cache plugin off so nothing is written into the repo
 t0=$SECONDS
-run -m pytest -p no:cacheprovider -rA --junitxml "$OUT/native/pytest-junit.xml" \
+runpt -p no:cacheprovider -rA --junitxml "$OUT/native/pytest-junit.xml" \
     --basetemp "$SCR/pytest" --rootdir "$T/src/repo" "$T/src/repo/tests" \
     > "$OUT/native/pytest.stdout" 2> "$OUT/native/pytest.stderr"
 printf "pytest\tall\t%s\t-\t%s\n" "$?" "$((SECONDS-t0))" >> "$MANIFEST"
```

Dazu die neue Datei `scripts/pytest_plugin/junit_nohostname.py` (19 Zeilen,
im Diff vollständig). Zu den drei Änderungen über die Pfadkonstante hinaus:

- `T` zeigt auf `/private/tmp/…`, die Form, die macOS für `/tmp/…` als
  aktuelles Verzeichnis zurückgibt. Mit `/tmp/…` druckt pytest die Testpfade
  relativ als `../../../../../../../tmp/mt-runs/…` statt
  `../../../src/repo/…`; die Ausgaben wären damit schlechter vergleichbar.
- `OBS` zeigt auf `restart_observe_v1.py`. Im früheren Lauf liefen `noseedA`,
  `noseedB` und `seed0` mit dieser ersten Fassung; `run_all.sh` zeigte dort
  am Ende auf die spätere Fassung, weil die Diagnosezeilen erst nach diesen
  drei Varianten dazukamen. So bekommen die drei Varianten hier dieselbe
  Fassung wie damals.
- pytest schreibt in jede JUnit-XML `hostname=platform.node()`. Der
  Rechnername dieser Maschine enthält einen Personennamen und lässt sich auf
  macOS nur als root ändern. Das Plugin ersetzt `platform` nur im Modul
  `_pytest.junitxml`, das Attribut lautet dann `localhost`. Tests und Paket
  sehen den echten `platform`. Es lief bei allen pytest-Aufrufen dieses Laufs
  mit (`-p junit_nohostname`, `PYTHONPATH=scripts/pytest_plugin` nur für
  pytest). Im früheren Lauf stand der Rechnername in 14 JUnit-Dateien.

Der Treiber `scripts/driver.py` ist gegenüber Lauf 1 nur in der Kopfzeile
geändert (`inputs/driver_run1_to_run2.diff`); `evaluation.py`, `cli.py` und
`failure_injection.py` sind zwischen a940ace und 278fbf5 unverändert, die
öffentliche Schnittstelle (`run_scenario`, `cli._fault_run`) also auch.
`run_all.sh` ruft gegenüber Lauf 1 zusätzlich `privacy`, die volle Suite mit
JUnit-XML und die Neustart-Beobachtung auf (`inputs/run_all_run1_to_run2.diff`,
neu erzeugt, enthält damit auch die Änderungen oben).

`extra-noseed`, `baseline-v021` und `runs/diag` haben kein eigenes Skript; sie
liefen mit denselben Befehlen wie im früheren Lauf, angepasst um denselben
Pfad, `HOME` und das Plugin:

- `extra-noseed`: `scripts/restart_observe.py … --repeats 10`, danach zehnmal
  `pytest -p no:cacheprovider -rfE --junitxml … --basetemp … --rootdir src/repo`
  über die beiden Neustart-Dateien, jede Iteration ein eigener Prozess.
- `baseline-v021`: zweite venv `env/venv312-v021` aus `git archive a940ace`
  (gleiches Verfahren, gleiche Paketversionen), `package.txt` aus einem
  Import des Pakets, dann `pytest -p no:cacheprovider -v -rf --junitxml …`
  über `tests/test_process_restart_regression.py` aus dem Baum von v0.2.2.
- `runs/diag`: `scripts/listener_backlog_probe.py` mit `env -i PATH=…` und
  `python -I -B`, Socket-Verzeichnis `.scratch/sock`, Argumente
  `2000 2`, `2000 3`, `500 8`, `500 8 16`.

`scripts/restart_observe.py` ist eigener Code, nutzt aber Nikhils
`tests/restart_harness.py` unverändert. Die Diagnosezeilen der zweiten
Fassung schreiben nur bei nicht erreichtem Haltepunkt
(`inputs/restart_observe_v1_to_v2.diff`); bei erreichtem Haltepunkt sind die
Datensätze beider Fassungen gleich gebaut.

Der Harness legt seine Sockets fest unter `/tmp/apr-*` an
(`tests/restart_harness.py:410`) und räumt sie wieder ab; nach den Läufen lag
dort nichts.

Die Nachzählung `scripts/recount.py` (Systempython, `python3 -B -I`)
importiert das Paket nicht. Ein eingepflanzter Unterschied in Zeile 100 von
`scoped-store.faults.jsonl` einer Kopie der Läufe (`.scratch/plant`) wurde
dreifach gefunden: gegen den nativen CLI-Lauf, gegen `results/` und im
Variantenvergleich. Die E3-Werte stammen aus Nikhils eigener Analyse
(`privacy.json`); geprüft ist, dass Lauf, committete Datei und Tabelle
übereinstimmen.

Python 3.12 statt Nikhils 3.13: lag vor, steht in der CI-Matrix. Die
GitHub-Actions-Datei lief nicht. Ein Listen-Post-Entwurf liegt nicht bei,
ebenso kein Tar des fremden Repos.

### Keine Pfade und Namen in den Ausgaben

Vor dem Abschluss liefen über alle Dateien in `SHA256SUMS` zwei Suchen ohne
Groß-/Kleinschreibung, einmal nur über Textdateien (`grep -rIil`), einmal
auch über Binärdateien (`grep -rlai`). Gesucht waren Benutzername, Vor- und
Nachname, das macOS-Benutzerverzeichnis, die Mail-Domain und der Firmenname,
in einer dritten Suche die drei Formen des Rechnernamens. Alle drei ergaben 0
Dateien. Die Suchbegriffe stehen hier nicht, weil sie selbst den Namen
enthalten. In `SHA256SUMS` liegen keine
`.pyc`- und keine SQLite-Dateien. Absolute Pfade in den Lauf-Ausgaben
beginnen mit `/private/tmp/mt-runs/278fbf57/` (venv, Repo, `--out`); dazu
kommt einmal der Socket des Harness unter `/tmp/apr-…` im Traceback von
`extra-noseed` Lauf 02.

### Vergleich mit dem früheren Lauf

Bytegleich sind 193 der 242 Dateien, die beide Läufe unter `runs/`, `inputs/`
und `recount/` haben, darunter alle 126 `per-config`-Dateien, alle nativen
CLI-Ergebnisdateien, `inputs/digests.json`, `inputs/package-source.sha256`
und die Neustart-Datensätze von `noseedA`, `seed0` und `extra-noseed`. Die
übrigen 49 unterscheiden sich so:

- Pfade: `environment_*.json` (`args.out`), `privacy.stdout`,
  `baseline-v021/package.txt`, `rootdir:` und JUnit-Pfad in
  `baseline-v021/pytest.stdout`. Ohne `out`, Zeitstempel und Laufzeit sind
  die `environment_*.json` gleich.
- JUnit-XML: `hostname`, `timestamp`, `time`; sonst gleich, bei
  `baseline-v021` dazu die PIDs in den Fehlermeldungen.
- `pytest.stdout` der Volläufe: Laufzeit und die Reihenfolge der
  `resume_failed`-Logzeilen im Abschnitt PASSES (Gateway-Namen `g2`/`g3`,
  `race0`–`race7`). Diese Reihenfolge wechselt schon zwischen `noseedA` und
  `noseedB` des früheren Laufs (16 Zeilen).
- `process-status.tsv`: Startzeiten und Sekunden; Konfiguration, Teil und
  Exit-Code sind gleich.
- `noseedB/restart/restart-observe.jsonl`: nur der R1-Datensatz, der im
  früheren Lauf den Haltepunkt nicht erreichte.
- `extra-noseed`: der Fehlschlag liegt in Lauf 02 statt 06, sonst Laufzeiten.
- `runs/diag`: Zählwerte des Socket-Nachbaus (s. Schritt 4).
- `recount/recount.json`: 51 von 5.514 Werten, alle aus den drei Punkten
  davor oder Laufzeiten; die 97 Angaben und ihr Ergebnis (96 gleich) sind
  unverändert.
- `inputs/run_all_run1_to_run2.diff`: neu erzeugt, enthält die Änderungen an
  `run_all.sh`. Neu ist `inputs/scripts_earlier_run_to_this_run.diff`.

## Was die Läufe nicht belegen

Die Übereinstimmung zeigt, dass v0.2.2 auf dieser Maschine dieselben
Experiment-Dateien erzeugt, die Nikhil committet hat, und dass die
Testzahlen stimmen. Ob Szenarien und Faults ein brauchbares Modell eines
Gateway-Ausfalls sind, prüfen die Läufe nicht; Orakel für „richtig
zugeordnet" ist weiter Nikhils `Deployment.truth`.

Für das Neustart-Szenario gilt die Beobachtung nur für die 14 Fälle mit je
einer Operation, einem Agent-A-Ledger und einem Downstream-Prozess auf einem
Rechner. Agent B startet nur simuliert neu (`docs/threat_model.md`, M11). Die
Sicherheit bei begonnener Ausführung hängt an der atomaren Sperre des
Werkzeugs (M7), das Nikhil dafür geschrieben hat; ein echtes externes System
kann das anders halten. Annahme M9 (ein lebender Agent-A-Prozess je Ledger)
setzt nichts durch, kein Fall prüft zwei gleichzeitige Prozesse. Der Pfad
`OPERATION_ABORTED` → `UNKNOWN` → erneut senden im laufenden Prozess ist durch
die Neustart-Fälle nicht abgedeckt.

Determinismus der Experiment-Dateien ist für 3 Varianten × 3 Wiederholungen
belegt, dazu bytegleich mit dem früheren Lauf und mit Lauf 1.
Identifikatoren, Schlüssel und Nonces kommen aus `secrets` und `os.urandom`
und wurden nicht verglichen. Die Neustart-Fälle hatten in allen 1.406
Läufen je Fall und Modus eine einzige Signatur. Das schließt seltene Abläufe
nicht aus. Die Testsuite ist auf macOS mit Python 3.12 nicht in jedem Lauf
grün: in beiden Läufen zusammen 2 Fehlschläge in 1.924 ausgeführten
Neustart-Tests, beide an der Vorbedingung `wait_entered`, einer davon
nachweislich mit abgewiesener Socket-Verbindung.

Nicht gelaufen: E4 (Benchmark), Python 3.11 und 3.13, Linux x86_64,
Mehrrechner- und Netzbetrieb, der Entwurf vor dem v0.2.2-Audit (nicht
committet) und die übrigen `*_before_fix.txt` außer der Neustart-Regression.

## Ablage

```
278fbf57/
  run-summary.md            diese Datei
  SHA256SUMS                über alles außer src/, env/ und .scratch/
  inputs/
    ls-remote-2026-10-12.txt
    git-tree-sha1.txt, git-archive-sha256.txt
    tracked-files.sha256, package-source.sha256
    digests.json
    driver_run1_to_run2.diff, run_all_run1_to_run2.diff,
    restart_observe_v1_to_v2.diff, scripts_earlier_run_to_this_run.diff
  runs/{noseedA,noseedB,seed0}/
    process-status.tsv
    per-config/<konfig>.{scenarios,faults}.{jsonl,stdout,stderr}
    native/                 CLI-Ausgaben, pytest (stdout, stderr, JUnit-XML)
    restart/                Beobachtung Neustart-Szenario
  runs/extra-noseed/        10× Neustart-Beobachtung, 10× Neustart-Testdateien
  runs/baseline-v021/       Regressionstests gegen v0.2.1
  runs/diag/                Socket-Backlog-Nachbau
  recount/recount.json      Nachzählung, alle Vergleiche, 97 Angaben
  scripts/                  driver.py, run_all.sh, recount.py, digests.py,
                            restart_observe.py, restart_observe_v1.py,
                            listener_backlog_probe.py,
                            pytest_plugin/junit_nohostname.py
  src/repo                  fremder Code, gepinnt (nicht in SHA256SUMS)
  env/python                CPython 3.12.12 von uv (nicht in SHA256SUMS)
  env/venv312, env/venv312-v021   venvs (nicht in SHA256SUMS)
  env/uv-cache              uv-Cache (nicht in SHA256SUMS)
  .scratch/                 Arbeitsdateien, Tars, Pflanztest (nicht in SHA256SUMS)
```
