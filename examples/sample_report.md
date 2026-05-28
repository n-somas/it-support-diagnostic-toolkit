# IT Support Diagnostic Report

Erstellt am: 28.05.2026 17:30:00

---

## Systeminformationen

| Prüfung         | Ergebnis        |
| --------------- | --------------- |
| Computername    | DESKTOP-EXAMPLE |
| Benutzername    | example-user    |
| Betriebssystem  | Windows         |
| Windows-Version | 10.0.xxxxx      |
| Windows-Release | 11              |
| Architektur     | AMD64           |
| Prozessor       | Example CPU     |
| CPU-Kerne       | 8               |
| Speicher Gesamt | 512.00 GB       |
| Speicher Belegt | 390.00 GB       |
| Speicher Frei   | 122.00 GB       |

## Netzwerkprüfung

| Prüfung                     | Ergebnis        |
| --------------------------- | --------------- |
| Aktive IP-Adresse           | 192.168.x.x     |
| Standardgateway             | 192.168.x.1     |
| Ping Google DNS 8.8.8.8     | OK              |
| Ping Cloudflare DNS 1.1.1.1 | OK              |
| DNS-Auflösung google.com    | OK              |
| DNS-IP google.com           | 142.xxx.xxx.xxx |

## Speicherplatzprüfung

| Prüfung                    | Ergebnis  |
| -------------------------- | --------- |
| Laufwerk                   | C:        |
| Gesamtspeicher             | 512.00 GB |
| Belegter Speicher          | 390.00 GB |
| Freier Speicher            | 122.00 GB |
| Freier Speicher in Prozent | 23.83 %   |
| Bewertung                  | OK        |

## Firewallprüfung

| Prüfung             | Ergebnis |
| ------------------- | -------- |
| Domänenprofil       | Aktiv    |
| Privates Profil     | Aktiv    |
| Öffentliches Profil | Aktiv    |
| Bewertung           | OK       |

## Defenderprüfung

| Prüfung                | Ergebnis            |
| ---------------------- | ------------------- |
| Echtzeitschutz         | Aktiv               |
| Antivirus aktiviert    | Aktiv               |
| Signaturversion        | 1.xxx.xxx.0         |
| Letztes Signaturupdate | 28.05.2026 08:00:00 |
| Bewertung              | OK                  |

## Windows Update Prüfung

| Prüfung                      | Ergebnis                                                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Windows Update Dienst        | Gestoppt                                                                                                            |
| Letztes installiertes Update | HotFixID: KBxxxxxxx<br>InstalledOn: 27.05.2026 00:00:00                                                             |
| Hinweis                      | Windows Update Dienst läuft aktuell nicht dauerhaft. Das kann normal sein, da der Dienst bei Bedarf gestartet wird. |
| Bewertung                    | OK                                                                                                                  |

## Offene Ports Prüfung

| Prüfung                            | Ergebnis                                                                                                                                         |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Anzahl offener TCP-Listening-Ports | 38                                                                                                                                               |
| Nur lokal erreichbare Ports        | 16                                                                                                                                               |
| Im Netzwerk erreichbare Ports      | 22                                                                                                                                               |
| Auffällige Standardports           | 135 (Windows RPC) → svchost [PID: xxxx], 139 (NetBIOS) → System [PID: x], 445 (SMB) → System [PID: x], 3306 (MySQL/MariaDB) → mysqld [PID: xxxx] |
| Bewertung                          | WARNUNG                                                                                                                                          |
| Hinweis                            | Port 3306 ist häufig MySQL/MariaDB. Der Dienst sollte nicht unnötig im Netzwerk erreichbar sein.                                                 |

## BitLocker Prüfung

| Prüfung                    | Ergebnis                                                                                     |
| -------------------------- | -------------------------------------------------------------------------------------------- |
| Laufwerk                   | C:                                                                                           |
| Verschlüsselungsstatus     | Nicht ermittelbar                                                                            |
| Schutzstatus               | Nicht ermittelbar                                                                            |
| Verschlüsselung in Prozent | Nicht ermittelbar                                                                            |
| Sperrstatus                | Nicht ermittelbar                                                                            |
| Bewertung                  | HINWEIS                                                                                      |
| Hinweis                    | BitLocker-Informationen konnten wegen fehlender Administratorrechte nicht ausgelesen werden. |
