"""Tests für Netzwerkadapter und Verbindungsqualität."""

from __future__ import annotations

import unittest

from src.checks.network_check import (
    evaluate_network_quality,
    is_virtual_adapter,
    parse_json_payload,
    parse_link_speed_mbps,
)


def adapter(**overrides) -> dict:
    value = {
        "Name": "Ethernet",
        "InterfaceDescription": "Intel Ethernet Controller",
        "Status": "Up",
        "MediaType": "802.3",
        "LinkSpeed": "1 Gbps",
        "Dhcp": "Enabled",
        "IPv4Address": ["192.168.1.20"],
        "IPv4DefaultGateway": ["192.168.1.1"],
        "DnsServers": ["192.168.1.1"],
        "NetworkCategory": "Private",
    }
    value.update(overrides)
    return value


def probe(target: str = "1.1.1.1", **overrides) -> dict:
    value = {
        "Target": target,
        "Sent": 4,
        "Received": 4,
        "LossPercent": 0,
        "AverageMs": 18,
    }
    value.update(overrides)
    return value


DNS_OK = {"Status": "OK", "Adressen": "13.107.246.40"}


class NetworkQualityTests(unittest.TestCase):
    def test_healthy_connection_is_ok(self) -> None:
        result = evaluate_network_quality(
            [adapter()],
            [probe(), probe("8.8.8.8")],
            DNS_OK,
        )
        self.assertEqual(result["Bewertung"], "OK")

    def test_apipa_is_warning(self) -> None:
        result = evaluate_network_quality(
            [adapter(IPv4Address=["169.254.10.20"])],
            [probe()],
            DNS_OK,
        )
        self.assertEqual(result["Bewertung"], "WARNUNG")

    def test_partial_packet_loss_is_hint(self) -> None:
        result = evaluate_network_quality(
            [adapter()],
            [probe(Received=3, LossPercent=25)],
            DNS_OK,
        )
        self.assertEqual(result["Bewertung"], "HINWEIS")

    def test_high_latency_is_warning(self) -> None:
        result = evaluate_network_quality(
            [adapter()],
            [probe(AverageMs=300)],
            DNS_OK,
        )
        self.assertEqual(result["Bewertung"], "WARNUNG")

    def test_dns_failure_is_warning(self) -> None:
        result = evaluate_network_quality(
            [adapter()],
            [probe()],
            {"Status": "FEHLER"},
        )
        self.assertEqual(result["Bewertung"], "WARNUNG")

    def test_virtual_adapter_detection(self) -> None:
        self.assertTrue(
            is_virtual_adapter(
                {
                    "Name": "vEthernet",
                    "InterfaceDescription": "Hyper-V Virtual Adapter",
                }
            )
        )

    def test_link_speed_conversion(self) -> None:
        self.assertEqual(parse_link_speed_mbps("1 Gbps"), 1000)
        self.assertEqual(parse_link_speed_mbps("100 Mbps"), 100)

    def test_single_json_object_becomes_list(self) -> None:
        parsed = parse_json_payload(
            '{"Name":"Ethernet","Status":"Up"}'
        )
        self.assertEqual(len(parsed), 1)


if __name__ == "__main__":
    unittest.main()
