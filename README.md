# IT Support Diagnostic Toolkit

Ein Python-basiertes Diagnose-Tool für typische Windows-Supportfälle.

Das Tool prüft grundlegende System-, Netzwerk- und Sicherheitsparameter eines Windows-Systems und erstellt daraus einen strukturierten Markdown-Bericht. Ziel ist es, wiederkehrende Support-Prüfungen schneller, nachvollziehbarer und dokumentierbar zu machen.

## Funktionen

- Auslesen grundlegender Systeminformationen
- Prüfung der aktiven Netzwerkverbindung
- DNS-Auflösung testen
- Ping-Test zu bekannten DNS-Servern
- Speicherplatzprüfung von Laufwerk C:
- Bewertung des freien Speicherplatzes
- Prüfung der Windows-Firewall-Profile
- Prüfung des Microsoft Defender Status
- Prüfung des Windows Update Status
- Prüfung lokal offener TCP-Listening-Ports
- Zuordnung auffälliger Ports zu Prozessnamen
- Prüfung des BitLocker-Status von Laufwerk C:
- Erstellung eines Markdown-Supportberichts
- Erstellung einer Gesamtbewertung aus allen Diagnosebereichen

## Aktuelle Diagnosebereiche

| Bereich | Beschreibung |
|---|---|
| Systeminformationen | Computername, Benutzername, Betriebssystem, Architektur, CPU-Kerne und Speicherplatz |
| Netzwerkprüfung | Aktive IP-Adresse, Standardgateway, Ping-Test und DNS-Auflösung |
| Speicherplatzprüfung | Freier Speicherplatz in GB und Prozent mit Bewertung |
| Firewallprüfung | Status der Windows-Firewall für Domänen-, privates und öffentliches Profil |
| Defenderprüfung | Echtzeitschutz, Antivirus-Status, Signaturversion und letztes Signaturupdate |
| Windows Update Prüfung | Windows Update Dienst, letztes installiertes Update, Hinweis und Bewertung |
| Offene Ports Prüfung | Anzahl offener TCP-Listening-Ports, Netzwerk-Erreichbarkeit, auffällige Standardports und Prozessnamen |
| BitLocker Prüfung | Verschlüsselungsstatus, Schutzstatus, Verschlüsselungsgrad und Hinweis bei fehlenden Rechten |
| Markdown-Report | Automatische Erstellung eines Support-Berichts als Markdown-Datei |
| Gesamtbewertung | Zählt OK, HINWEIS, WARNUNG und KRITISCH und erstellt einen Gesamtstatus |

## Beispielausgabe

```text
IT Support Diagnostic Toolkit
===================================

Systeminformationen:
-----------------------------------
Computername: DESKTOP-EXAMPLE
Benutzername: user
Betriebssystem: Windows
Windows-Version: 10.0.xxxxx
Windows-Release: 11
Architektur: AMD64
CPU-Kerne: 8

Netzwerkprüfung:
-----------------------------------
Aktive IP-Adresse: 192.168.x.x
Standardgateway: 192.168.x.1
Ping Google DNS 8.8.8.8: OK
Ping Cloudflare DNS 1.1.1.1: OK
DNS-Auflösung google.com: OK

Speicherplatzprüfung:
-----------------------------------
Laufwerk: C:
Freier Speicher in Prozent: 21.21 %
Bewertung: OK
```

## Voraussetzungen

* Windows 10 oder Windows 11
* Python 3.12 oder neuer
* PowerShell
* VS Code empfohlen

## Projekt starten

Repository klonen oder lokal öffnen:

```powershell
cd C:\Users\nsoma\documents\it-support-diagnostic-toolkit
```

Virtuelle Umgebung erstellen:

```powershell
python -m venv .venv
```

Virtuelle Umgebung aktivieren:

```powershell
.venv\Scripts\activate
```

Programm starten:

```powershell
python src\main.py
```

## Bericht erzeugen

Nach dem Start erstellt das Tool automatisch einen Markdown-Bericht:

```text
reports/support_report.md
```

Der Ordner `reports/` ist absichtlich in `.gitignore` eingetragen, damit lokale Systemdaten nicht versehentlich auf GitHub veröffentlicht werden.

## Hinweis zum Datenschutz

Das Tool liest lokale System- und Sicherheitsinformationen aus. Erzeugte Berichte können Gerätenamen, Benutzernamen, IP-Adressen und Update-Informationen enthalten. Diese Berichte sollten nicht ungeprüft veröffentlicht werden. Besonders die Abschnitte zu offenen Ports, Prozessnamen, IP-Adressen und BitLocker sollten vor einer Veröffentlichung geprüft oder anonymisiert werden.

## Ziel des Projekts

Dieses Projekt dient als praxisnahes Portfolio-Projekt für IT-Support, Systemadministration und Cybersecurity-Grundlagen.

Es zeigt unter anderem:

* Automatisierung mit Python
* Ausführung von PowerShell-Befehlen aus Python
* Strukturierte Fehlerdiagnose
* Bewertung typischer Windows-Supportfälle
* Erstellung eines nachvollziehbaren Support-Berichts

## Status

Aktueller Stand: funktionsfähiger Prototyp mit mehreren Diagnose-Checks und Markdown-Report.
