from pathlib import Path
import base64
import shutil

PAYLOADS = {'src/gui/theme.py': 'IiIiWmVudHJhbGUgRGVzaWdud2VydGUgZsO8ciBkaWUgRGVza3RvcG9iZXJmbMOkY2hlLiIiIgoKCmNsYXNzIENvbG9yczoKICAgIFNVUkZBQ0UgPSAoIiNGRkZGRkYiLCAiIzFGMjkzNyIpCiAgICBCT1JERVIgPSAoIiNEOUUxRUMiLCAiIzM3NDE1MSIpCiAgICBURVhUID0gKCIjMTExODI3IiwgIiNGOEZBRkMiKQogICAgTVVURUQgPSAoIiM2NDc0OEIiLCAiIzk0QTNCOCIpCgoKU1RBVFVTX0NPTE9SUyA9IHsKICAgICJPSyI6ICIjMjJDNTVFIiwKICAgICJJTkZPIjogIiMzQjgyRjYiLAogICAgIkhJTldFSVMiOiAiI0E4NTVGNyIsCiAgICAiV0FSTlVORyI6ICIjRjU5RTBCIiwKICAgICJLUklUSVNDSCI6ICIjRUY0NDQ0IiwKICAgICJGRUhMRVIiOiAiI0RDMjYyNiIsCn0K', 'src/services/__init__.py': 'IiIiQW53ZW5kdW5nc2RpZW5zdGUuIiIiCg==', 'src/services/scan_history_service.py': 'IiIiU3BlaWNoZXJ0IERpYWdub3NlbMOkdWZlIGbDvHIgVmVybGF1ZnNkaWFncmFtbWUuIiIiCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQganNvbgpmcm9tIGNvbGxlY3Rpb25zIGltcG9ydCBDb3VudGVyCmZyb20gZGF0ZXRpbWUgaW1wb3J0IGRhdGV0aW1lCmZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aAoKCmNsYXNzIFNjYW5IaXN0b3J5U2VydmljZToKICAgIGRlZiBfX2luaXRfXyhzZWxmLCBkaXJlY3Rvcnk6IHN0ciB8IFBhdGggPSAiZGF0YS9zY2FucyIpIC0+IE5vbmU6CiAgICAgICAgc2VsZi5kaXJlY3RvcnkgPSBQYXRoKGRpcmVjdG9yeSkKCiAgICBkZWYgc2F2ZShzZWxmLCByZXN1bHRzOiBsaXN0W3R1cGxlW3N0ciwgZGljdF1dKSAtPiBQYXRoOgogICAgICAgIHNlbGYuZGlyZWN0b3J5Lm1rZGlyKHBhcmVudHM9VHJ1ZSwgZXhpc3Rfb2s9VHJ1ZSkKICAgICAgICBub3cgPSBkYXRldGltZS5ub3coKQogICAgICAgIGNvdW50cyA9IENvdW50ZXIoc2VsZi5fcmF0aW5nKHJlc3VsdCkgZm9yIF8sIHJlc3VsdCBpbiByZXN1bHRzKQoKICAgICAgICBwYXlsb2FkID0gewogICAgICAgICAgICAiY3JlYXRlZF9hdCI6IG5vdy5pc29mb3JtYXQodGltZXNwZWM9InNlY29uZHMiKSwKICAgICAgICAgICAgInN0YXR1c19jb3VudHMiOiB7CiAgICAgICAgICAgICAgICBzdGF0dXM6IGNvdW50cy5nZXQoc3RhdHVzLCAwKQogICAgICAgICAgICAgICAgZm9yIHN0YXR1cyBpbiAoCiAgICAgICAgICAgICAgICAgICAgIk9LIiwKICAgICAgICAgICAgICAgICAgICAiSU5GTyIsCiAgICAgICAgICAgICAgICAgICAgIkhJTldFSVMiLAogICAgICAgICAgICAgICAgICAgICJXQVJOVU5HIiwKICAgICAgICAgICAgICAgICAgICAiS1JJVElTQ0giLAogICAgICAgICAgICAgICAgICAgICJGRUhMRVIiLAogICAgICAgICAgICAgICAgKQogICAgICAgICAgICB9LAogICAgICAgIH0KCiAgICAgICAgcGF0aCA9IHNlbGYuZGlyZWN0b3J5IC8gbm93LnN0cmZ0aW1lKAogICAgICAgICAgICAic2Nhbl8lWS0lbS0lZF8lSC0lTS0lUy5qc29uIgogICAgICAgICkKICAgICAgICBwYXRoLndyaXRlX3RleHQoCiAgICAgICAgICAgIGpzb24uZHVtcHMocGF5bG9hZCwgZW5zdXJlX2FzY2lpPUZhbHNlLCBpbmRlbnQ9MiksCiAgICAgICAgICAgIGVuY29kaW5nPSJ1dGYtOCIsCiAgICAgICAgKQogICAgICAgIHJldHVybiBwYXRoCgogICAgZGVmIGxvYWRfcmVjZW50KHNlbGYsIGxpbWl0OiBpbnQgPSAxMCkgLT4gbGlzdFtkaWN0XToKICAgICAgICBpZiBub3Qgc2VsZi5kaXJlY3RvcnkuZXhpc3RzKCk6CiAgICAgICAgICAgIHJldHVybiBbXQoKICAgICAgICByZWNvcmRzID0gW10KCiAgICAgICAgZm9yIHBhdGggaW4gc29ydGVkKAogICAgICAgICAgICBzZWxmLmRpcmVjdG9yeS5nbG9iKCJzY2FuXyouanNvbiIpLAogICAgICAgICAgICByZXZlcnNlPVRydWUsCiAgICAgICAgKVs6bGltaXRdOgogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICByZWNvcmRzLmFwcGVuZCgKICAgICAgICAgICAgICAgICAgICBqc29uLmxvYWRzKHBhdGgucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpKQogICAgICAgICAgICAgICAgKQogICAgICAgICAgICBleGNlcHQgKE9TRXJyb3IsIGpzb24uSlNPTkRlY29kZUVycm9yKToKICAgICAgICAgICAgICAgIGNvbnRpbnVlCgogICAgICAgIHJldHVybiBsaXN0KHJldmVyc2VkKHJlY29yZHMpKQoKICAgIEBzdGF0aWNtZXRob2QKICAgIGRlZiBfcmF0aW5nKHJlc3VsdDogZGljdCkgLT4gc3RyOgogICAgICAgIHZhbHVlID0gcmVzdWx0LmdldCgKICAgICAgICAgICAgIkJld2VydHVuZyIsCiAgICAgICAgICAgIHJlc3VsdC5nZXQoIlN0YXR1cyIsICJJTkZPIiksCiAgICAgICAgKQogICAgICAgIHJldHVybiBzdHIodmFsdWUpLnVwcGVyKCkK', 'src/gui/components/dashboard_extra_charts.py': 'IiIiU3BlaWNoZXItIHVuZCBWZXJsYXVmc2RpYWdyYW1tZSBkZXMgRGFzaGJvYXJkcy4iIiIKCmZyb20gX19mdXR1cmVfXyBpbXBvcnQgYW5ub3RhdGlvbnMKCmltcG9ydCBjdXN0b210a2ludGVyIGFzIGN0awpmcm9tIG1hdHBsb3RsaWIuYmFja2VuZHMuYmFja2VuZF90a2FnZyBpbXBvcnQgRmlndXJlQ2FudmFzVGtBZ2cKZnJvbSBtYXRwbG90bGliLmZpZ3VyZSBpbXBvcnQgRmlndXJlCgpmcm9tIHNyYy5ndWkudGhlbWUgaW1wb3J0IENvbG9ycywgU1RBVFVTX0NPTE9SUwoKClNUQVRVU19PUkRFUiA9IFsKICAgICJPSyIsCiAgICAiSU5GTyIsCiAgICAiSElOV0VJUyIsCiAgICAiV0FSTlVORyIsCiAgICAiS1JJVElTQ0giLAogICAgIkZFSExFUiIsCl0KClNUQVRVU19MQUJFTFMgPSB7CiAgICAiT0siOiAiT0siLAogICAgIklORk8iOiAiSW5mbyIsCiAgICAiSElOV0VJUyI6ICJIaW53ZWlzZSIsCiAgICAiV0FSTlVORyI6ICJXYXJudW5nZW4iLAogICAgIktSSVRJU0NIIjogIktyaXRpc2NoIiwKICAgICJGRUhMRVIiOiAiRmVobGVyIiwKfQoKCmNsYXNzIEJhc2VDaGFydChjdGsuQ1RrRnJhbWUpOgogICAgZGVmIF9faW5pdF9fKAogICAgICAgIHNlbGYsCiAgICAgICAgbWFzdGVyLAogICAgICAgIHRpdGxlOiBzdHIsCiAgICAgICAgc3VidGl0bGU6IHN0ciwKICAgICAgICBoZWlnaHQ6IGludCwKICAgICkgLT4gTm9uZToKICAgICAgICBzdXBlcigpLl9faW5pdF9fKAogICAgICAgICAgICBtYXN0ZXIsCiAgICAgICAgICAgIGNvcm5lcl9yYWRpdXM9MTIsCiAgICAgICAgICAgIGJvcmRlcl93aWR0aD0xLAogICAgICAgICAgICBib3JkZXJfY29sb3I9Q29sb3JzLkJPUkRFUiwKICAgICAgICAgICAgZmdfY29sb3I9Q29sb3JzLlNVUkZBQ0UsCiAgICAgICAgKQogICAgICAgIHNlbGYuZ3JpZF9jb2x1bW5jb25maWd1cmUoMCwgd2VpZ2h0PTEpCgogICAgICAgIGN0ay5DVGtMYWJlbCgKICAgICAgICAgICAgc2VsZiwKICAgICAgICAgICAgdGV4dD10aXRsZSwKICAgICAgICAgICAgYW5jaG9yPSJ3IiwKICAgICAgICAgICAgZm9udD1jdGsuQ1RrRm9udChzaXplPTE3LCB3ZWlnaHQ9ImJvbGQiKSwKICAgICAgICAgICAgdGV4dF9jb2xvcj1Db2xvcnMuVEVYVCwKICAgICAgICApLmdyaWQoCiAgICAgICAgICAgIHJvdz0wLAogICAgICAgICAgICBjb2x1bW49MCwKICAgICAgICAgICAgcGFkeD0xOCwKICAgICAgICAgICAgcGFkeT0oMTYsIDIpLAogICAgICAgICAgICBzdGlja3k9ImV3IiwKICAgICAgICApCgogICAgICAgIGN0ay5DVGtMYWJlbCgKICAgICAgICAgICAgc2VsZiwKICAgICAgICAgICAgdGV4dD1zdWJ0aXRsZSwKICAgICAgICAgICAgYW5jaG9yPSJ3IiwKICAgICAgICAgICAgZm9udD1jdGsuQ1RrRm9udChzaXplPTEyKSwKICAgICAgICAgICAgdGV4dF9jb2xvcj1Db2xvcnMuTVVURUQsCiAgICAgICAgKS5ncmlkKAogICAgICAgICAgICByb3c9MSwKICAgICAgICAgICAgY29sdW1uPTAsCiAgICAgICAgICAgIHBhZHg9MTgsCiAgICAgICAgICAgIHBhZHk9KDAsIDYpLAogICAgICAgICAgICBzdGlja3k9ImV3IiwKICAgICAgICApCgogICAgICAgIHNlbGYuZmlndXJlID0gRmlndXJlKGZpZ3NpemU9KDYsIDIuNSksIGRwaT0xMDApCiAgICAgICAgc2VsZi5heGVzID0gc2VsZi5maWd1cmUuYWRkX3N1YnBsb3QoMTExKQogICAgICAgIHNlbGYuY2FudmFzID0gRmlndXJlQ2FudmFzVGtBZ2coCiAgICAgICAgICAgIHNlbGYuZmlndXJlLAogICAgICAgICAgICBtYXN0ZXI9c2VsZiwKICAgICAgICApCiAgICAgICAgY2FudmFzX3dpZGdldCA9IHNlbGYuY2FudmFzLmdldF90a193aWRnZXQoKQogICAgICAgIGNhbnZhc193aWRnZXQuY29uZmlndXJlKGhlaWdodD1oZWlnaHQpCiAgICAgICAgY2FudmFzX3dpZGdldC5ncmlkKAogICAgICAgICAgICByb3c9MiwKICAgICAgICAgICAgY29sdW1uPTAsCiAgICAgICAgICAgIHBhZHg9MTIsCiAgICAgICAgICAgIHBhZHk9KDAsIDEyKSwKICAgICAgICAgICAgc3RpY2t5PSJldyIsCiAgICAgICAgKQoKICAgIGRlZiBhcHBseV90aGVtZShzZWxmKSAtPiBOb25lOgogICAgICAgIGRhcmsgPSBjdGsuZ2V0X2FwcGVhcmFuY2VfbW9kZSgpID09ICJEYXJrIgogICAgICAgIGJhY2tncm91bmQgPSAiIzFGMjkzNyIgaWYgZGFyayBlbHNlICIjRkZGRkZGIgogICAgICAgIGZvcmVncm91bmQgPSAiI0Y4RkFGQyIgaWYgZGFyayBlbHNlICIjMTExODI3IgoKICAgICAgICBzZWxmLmZpZ3VyZS5wYXRjaC5zZXRfZmFjZWNvbG9yKGJhY2tncm91bmQpCiAgICAgICAgc2VsZi5heGVzLnNldF9mYWNlY29sb3IoYmFja2dyb3VuZCkKICAgICAgICBzZWxmLmF4ZXMudGlja19wYXJhbXMoCiAgICAgICAgICAgIGF4aXM9ImJvdGgiLAogICAgICAgICAgICBjb2xvcnM9Zm9yZWdyb3VuZCwKICAgICAgICAgICAgbGFiZWxzaXplPTksCiAgICAgICAgKQogICAgICAgIHNlbGYuYXhlcy54YXhpcy5sYWJlbC5zZXRfY29sb3IoZm9yZWdyb3VuZCkKICAgICAgICBzZWxmLmF4ZXMueWF4aXMubGFiZWwuc2V0X2NvbG9yKGZvcmVncm91bmQpCgogICAgICAgIGZvciBzcGluZSBpbiBzZWxmLmF4ZXMuc3BpbmVzLnZhbHVlcygpOgogICAgICAgICAgICBzcGluZS5zZXRfdmlzaWJsZShGYWxzZSkKCiAgICBkZWYgZmluaXNoKHNlbGYpIC0+IE5vbmU6CiAgICAgICAgc2VsZi5maWd1cmUudGlnaHRfbGF5b3V0KHBhZD0xLjApCiAgICAgICAgc2VsZi5jYW52YXMuZHJhd19pZGxlKCkKCiAgICBkZWYgc2hvd19lbXB0eShzZWxmLCB0ZXh0OiBzdHIpIC0+IE5vbmU6CiAgICAgICAgc2VsZi5heGVzLmNsZWFyKCkKICAgICAgICBzZWxmLmFwcGx5X3RoZW1lKCkKICAgICAgICBzZWxmLmF4ZXMudGV4dCgKICAgICAgICAgICAgMC41LAogICAgICAgICAgICAwLjUsCiAgICAgICAgICAgIHRleHQsCiAgICAgICAgICAgIGhhPSJjZW50ZXIiLAogICAgICAgICAgICB2YT0iY2VudGVyIiwKICAgICAgICAgICAgdHJhbnNmb3JtPXNlbGYuYXhlcy50cmFuc0F4ZXMsCiAgICAgICAgICAgIGNvbG9yPSgKICAgICAgICAgICAgICAgICIjOTRBM0I4IgogICAgICAgICAgICAgICAgaWYgY3RrLmdldF9hcHBlYXJhbmNlX21vZGUoKSA9PSAiRGFyayIKICAgICAgICAgICAgICAgIGVsc2UgIiM2NDc0OEIiCiAgICAgICAgICAgICksCiAgICAgICAgKQogICAgICAgIHNlbGYuYXhlcy5zZXRfeHRpY2tzKFtdKQogICAgICAgIHNlbGYuYXhlcy5zZXRfeXRpY2tzKFtdKQogICAgICAgIHNlbGYuZmluaXNoKCkKCgpjbGFzcyBEaXNrVXNhZ2VDaGFydChCYXNlQ2hhcnQpOgogICAgZGVmIF9faW5pdF9fKHNlbGYsIG1hc3RlcikgLT4gTm9uZToKICAgICAgICBzdXBlcigpLl9faW5pdF9fKAogICAgICAgICAgICBtYXN0ZXIsCiAgICAgICAgICAgICJTcGVpY2hlcmJlbGVndW5nIiwKICAgICAgICAgICAgIkJlbGVndGVyIHVuZCBmcmVpZXIgU3BlaWNoZXIgYXVmIExhdWZ3ZXJrIEM6IiwKICAgICAgICAgICAgMjUwLAogICAgICAgICkKICAgICAgICBzZWxmLnNob3dfZW1wdHkoIk5vY2gga2VpbmUgU3BlaWNoZXJ3ZXJ0ZSB2b3JoYW5kZW4uIikKCiAgICBkZWYgdXBkYXRlX3Jlc3VsdHMoCiAgICAgICAgc2VsZiwKICAgICAgICByZXN1bHRzOiBsaXN0W3R1cGxlW3N0ciwgZGljdF1dLAogICAgKSAtPiBOb25lOgogICAgICAgIGRpc2tfcmVzdWx0ID0gbmV4dCgKICAgICAgICAgICAgKAogICAgICAgICAgICAgICAgcmVzdWx0CiAgICAgICAgICAgICAgICBmb3IgdGl0bGUsIHJlc3VsdCBpbiByZXN1bHRzCiAgICAgICAgICAgICAgICBpZiAic3BlaWNoZXIiIGluIHRpdGxlLmxvd2VyKCkKICAgICAgICAgICAgICAgIG9yICJkaXNrIiBpbiB0aXRsZS5sb3dlcigpCiAgICAgICAgICAgICksCiAgICAgICAgICAgIE5vbmUsCiAgICAgICAgKQoKICAgICAgICBpZiBub3QgZGlza19yZXN1bHQ6CiAgICAgICAgICAgIHNlbGYuc2hvd19lbXB0eSgiS2VpbmUgU3BlaWNoZXJ3ZXJ0ZSBnZWZ1bmRlbi4iKQogICAgICAgICAgICByZXR1cm4KCiAgICAgICAgdXNlZCA9IHNlbGYuX251bWJlcigKICAgICAgICAgICAgZGlza19yZXN1bHQuZ2V0KCJCZWxlZ3RlciBTcGVpY2hlciIpCiAgICAgICAgKQogICAgICAgIGZyZWUgPSBzZWxmLl9udW1iZXIoCiAgICAgICAgICAgIGRpc2tfcmVzdWx0LmdldCgiRnJlaWVyIFNwZWljaGVyIikKICAgICAgICApCgogICAgICAgIGlmIHVzZWQgaXMgTm9uZSBvciBmcmVlIGlzIE5vbmU6CiAgICAgICAgICAgIHNlbGYuc2hvd19lbXB0eSgiU3BlaWNoZXJ3ZXJ0ZSBuaWNodCBhdXN3ZXJ0YmFyLiIpCiAgICAgICAgICAgIHJldHVybgoKICAgICAgICBzZWxmLmF4ZXMuY2xlYXIoKQogICAgICAgIHNlbGYuYXBwbHlfdGhlbWUoKQoKICAgICAgICBzZWxmLmF4ZXMuYmFyaCgKICAgICAgICAgICAgWyJDOiJdLAogICAgICAgICAgICBbdXNlZF0sCiAgICAgICAgICAgIGNvbG9yPSIjM0I4MkY2IiwKICAgICAgICAgICAgbGFiZWw9IkJlbGVndCIsCiAgICAgICAgICAgIGhlaWdodD0wLjM4LAogICAgICAgICkKICAgICAgICBzZWxmLmF4ZXMuYmFyaCgKICAgICAgICAgICAgWyJDOiJdLAogICAgICAgICAgICBbZnJlZV0sCiAgICAgICAgICAgIGxlZnQ9W3VzZWRdLAogICAgICAgICAgICBjb2xvcj0iIzIyQzU1RSIsCiAgICAgICAgICAgIGxhYmVsPSJGcmVpIiwKICAgICAgICAgICAgaGVpZ2h0PTAuMzgsCiAgICAgICAgKQogICAgICAgIHNlbGYuYXhlcy5zZXRfeGxhYmVsKCJHaWdhYnl0ZSIpCiAgICAgICAgc2VsZi5heGVzLmxlZ2VuZCgKICAgICAgICAgICAgbG9jPSJ1cHBlciBjZW50ZXIiLAogICAgICAgICAgICBiYm94X3RvX2FuY2hvcj0oMC41LCAxLjE4KSwKICAgICAgICAgICAgbmNvbD0yLAogICAgICAgICAgICBmcmFtZW9uPUZhbHNlLAogICAgICAgICAgICBsYWJlbGNvbG9yPSgKICAgICAgICAgICAgICAgICIjRjhGQUZDIgogICAgICAgICAgICAgICAgaWYgY3RrLmdldF9hcHBlYXJhbmNlX21vZGUoKSA9PSAiRGFyayIKICAgICAgICAgICAgICAgIGVsc2UgIiMxMTE4MjciCiAgICAgICAgICAgICksCiAgICAgICAgKQogICAgICAgIHNlbGYuZmluaXNoKCkKCiAgICBAc3RhdGljbWV0aG9kCiAgICBkZWYgX251bWJlcih2YWx1ZSkgLT4gZmxvYXQgfCBOb25lOgogICAgICAgIGlmIHZhbHVlIGlzIE5vbmU6CiAgICAgICAgICAgIHJldHVybiBOb25lCgogICAgICAgIHRleHQgPSBzdHIodmFsdWUpLnJlcGxhY2UoIiwiLCAiLiIpCiAgICAgICAgY2xlYW5lZCA9ICIiLmpvaW4oCiAgICAgICAgICAgIGNoYXJhY3RlcgogICAgICAgICAgICBmb3IgY2hhcmFjdGVyIGluIHRleHQKICAgICAgICAgICAgaWYgY2hhcmFjdGVyLmlzZGlnaXQoKQogICAgICAgICAgICBvciBjaGFyYWN0ZXIgaW4gIi4tIgogICAgICAgICkKCiAgICAgICAgdHJ5OgogICAgICAgICAgICByZXR1cm4gZmxvYXQoY2xlYW5lZCkKICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgcmV0dXJuIE5vbmUKCgpjbGFzcyBIaXN0b3J5Q2hhcnQoQmFzZUNoYXJ0KToKICAgIGRlZiBfX2luaXRfXyhzZWxmLCBtYXN0ZXIpIC0+IE5vbmU6CiAgICAgICAgc3VwZXIoKS5fX2luaXRfXygKICAgICAgICAgICAgbWFzdGVyLAogICAgICAgICAgICAiRGlhZ25vc2V2ZXJsYXVmIiwKICAgICAgICAgICAgIkdlc3RhcGVsdGUgU3RhdHVzZW50d2lja2x1bmcgZGVyIGxldHp0ZW4gemVobiBTY2FucyIsCiAgICAgICAgICAgIDMwMCwKICAgICAgICApCiAgICAgICAgc2VsZi5zaG93X2VtcHR5KAogICAgICAgICAgICAiTmFjaCBtZWhyZXJlbiBTY2FucyBlcnNjaGVpbnQgaGllciBkaWUgRW50d2lja2x1bmcuIgogICAgICAgICkKCiAgICBkZWYgdXBkYXRlX3JlY29yZHMoc2VsZiwgcmVjb3JkczogbGlzdFtkaWN0XSkgLT4gTm9uZToKICAgICAgICBpZiBub3QgcmVjb3JkczoKICAgICAgICAgICAgc2VsZi5zaG93X2VtcHR5KAogICAgICAgICAgICAgICAgIk5hY2ggbWVocmVyZW4gU2NhbnMgZXJzY2hlaW50IGhpZXIgZGllIEVudHdpY2tsdW5nLiIKICAgICAgICAgICAgKQogICAgICAgICAgICByZXR1cm4KCiAgICAgICAgbGFiZWxzID0gWwogICAgICAgICAgICBzZWxmLl9sYWJlbChyZWNvcmQuZ2V0KCJjcmVhdGVkX2F0IiwgIiIpKQogICAgICAgICAgICBmb3IgcmVjb3JkIGluIHJlY29yZHMKICAgICAgICBdCgogICAgICAgIHZhbHVlcyA9IHsKICAgICAgICAgICAgc3RhdHVzOiBbCiAgICAgICAgICAgICAgICBpbnQoCiAgICAgICAgICAgICAgICAgICAgcmVjb3JkLmdldCgKICAgICAgICAgICAgICAgICAgICAgICAgInN0YXR1c19jb3VudHMiLAogICAgICAgICAgICAgICAgICAgICAgICB7fSwKICAgICAgICAgICAgICAgICAgICApLmdldChzdGF0dXMsIDApCiAgICAgICAgICAgICAgICApCiAgICAgICAgICAgICAgICBmb3IgcmVjb3JkIGluIHJlY29yZHMKICAgICAgICAgICAgXQogICAgICAgICAgICBmb3Igc3RhdHVzIGluIFNUQVRVU19PUkRFUgogICAgICAgIH0KCiAgICAgICAgc2VsZi5heGVzLmNsZWFyKCkKICAgICAgICBzZWxmLmFwcGx5X3RoZW1lKCkKCiAgICAgICAgc2VsZi5heGVzLnN0YWNrcGxvdCgKICAgICAgICAgICAgbGFiZWxzLAogICAgICAgICAgICBbdmFsdWVzW3N0YXR1c10gZm9yIHN0YXR1cyBpbiBTVEFUVVNfT1JERVJdLAogICAgICAgICAgICBsYWJlbHM9WwogICAgICAgICAgICAgICAgU1RBVFVTX0xBQkVMU1tzdGF0dXNdCiAgICAgICAgICAgICAgICBmb3Igc3RhdHVzIGluIFNUQVRVU19PUkRFUgogICAgICAgICAgICBdLAogICAgICAgICAgICBjb2xvcnM9WwogICAgICAgICAgICAgICAgU1RBVFVTX0NPTE9SU1tzdGF0dXNdCiAgICAgICAgICAgICAgICBmb3Igc3RhdHVzIGluIFNUQVRVU19PUkRFUgogICAgICAgICAgICBdLAogICAgICAgICAgICBhbHBoYT0wLjc1LAogICAgICAgICkKCiAgICAgICAgcHJvYmxlbXMgPSBbCiAgICAgICAgICAgIHZhbHVlc1siV0FSTlVORyJdW2luZGV4XQogICAgICAgICAgICArIHZhbHVlc1siS1JJVElTQ0giXVtpbmRleF0KICAgICAgICAgICAgKyB2YWx1ZXNbIkZFSExFUiJdW2luZGV4XQogICAgICAgICAgICBmb3IgaW5kZXggaW4gcmFuZ2UobGVuKGxhYmVscykpCiAgICAgICAgXQoKICAgICAgICBzZWxmLmF4ZXMucGxvdCgKICAgICAgICAgICAgbGFiZWxzLAogICAgICAgICAgICBwcm9ibGVtcywKICAgICAgICAgICAgbWFya2VyPSJvIiwKICAgICAgICAgICAgbGluZXdpZHRoPTIsCiAgICAgICAgICAgIGNvbG9yPSgKICAgICAgICAgICAgICAgICIjRkZGRkZGIgogICAgICAgICAgICAgICAgaWYgY3RrLmdldF9hcHBlYXJhbmNlX21vZGUoKSA9PSAiRGFyayIKICAgICAgICAgICAgICAgIGVsc2UgIiMxMTE4MjciCiAgICAgICAgICAgICksCiAgICAgICAgICAgIGxhYmVsPSJQcm9ibGVtZSBnZXNhbXQiLAogICAgICAgICkKICAgICAgICBzZWxmLmF4ZXMuc2V0X3lsYWJlbCgiQW56YWhsIikKICAgICAgICBzZWxmLmF4ZXMuZ3JpZChheGlzPSJ5IiwgYWxwaGE9MC4xNikKICAgICAgICBzZWxmLmF4ZXMudGlja19wYXJhbXMoYXhpcz0ieCIsIHJvdGF0aW9uPTI1KQogICAgICAgIHNlbGYuYXhlcy5sZWdlbmQoCiAgICAgICAgICAgIGxvYz0idXBwZXIgY2VudGVyIiwKICAgICAgICAgICAgYmJveF90b19hbmNob3I9KDAuNSwgMS4yNSksCiAgICAgICAgICAgIG5jb2w9NCwKICAgICAgICAgICAgZnJhbWVvbj1GYWxzZSwKICAgICAgICAgICAgZm9udHNpemU9OCwKICAgICAgICAgICAgbGFiZWxjb2xvcj0oCiAgICAgICAgICAgICAgICAiI0Y4RkFGQyIKICAgICAgICAgICAgICAgIGlmIGN0ay5nZXRfYXBwZWFyYW5jZV9tb2RlKCkgPT0gIkRhcmsiCiAgICAgICAgICAgICAgICBlbHNlICIjMTExODI3IgogICAgICAgICAgICApLAogICAgICAgICkKICAgICAgICBzZWxmLmZpbmlzaCgpCgogICAgQHN0YXRpY21ldGhvZAogICAgZGVmIF9sYWJlbCh2YWx1ZTogc3RyKSAtPiBzdHI6CiAgICAgICAgdHJ5OgogICAgICAgICAgICBkYXRlX3BhcnQsIHRpbWVfcGFydCA9IHZhbHVlLnNwbGl0KCJUIiwgMSkKICAgICAgICAgICAgcmV0dXJuIGYie2RhdGVfcGFydFs1Ol19IHt0aW1lX3BhcnRbOjVdfSIKICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgcmV0dXJuIHZhbHVlCg=='}

root = Path.cwd()
app_path = root / "src/gui/app.py"
backup_dir = root / "backup_before_dashboard_upgrade"

if not app_path.exists():
    raise SystemExit(
        "Das Skript muss im Hauptordner "
        "von it-support-diagnostic-toolkit ausgeführt werden."
    )

backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(app_path, backup_dir / "app.py")

for relative_path, encoded_content in PAYLOADS.items():
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(encoded_content))
    print(f"Erstellt: {relative_path}")

content = app_path.read_text(encoding="utf-8")

import_anchor = (
    "from src.gui.components.charts.status_bar_chart "
    "import StatusBarChart\n"
)
extra_imports = (
    "from src.gui.components.dashboard_extra_charts import "
    "DiskUsageChart, HistoryChart\n"
    "from src.services.scan_history_service import "
    "ScanHistoryService\n"
)

if extra_imports not in content:
    if import_anchor not in content:
        raise RuntimeError("Importposition nicht gefunden.")

    content = content.replace(
        import_anchor,
        import_anchor + extra_imports,
        1,
    )

state_anchor = (
    "        self.latest_report_path: Path | None = None\n"
)
state_line = (
    "        self.history_service = ScanHistoryService()\n"
)

if state_line not in content:
    if state_anchor not in content:
        raise RuntimeError("Konstruktorposition nicht gefunden.")

    content = content.replace(
        state_anchor,
        state_anchor + state_line,
        1,
    )

chart_anchor = """        self.status_chart.grid_remove()

        self.summary_frame.grid_remove()
"""

chart_block = """        self.status_chart.grid_remove()

        self.extra_charts_frame = ctk.CTkFrame(
            self.summary_frame,
            fg_color="transparent",
        )
        self.extra_charts_frame.grid(
            row=2,
            column=0,
            columnspan=len(statuses),
            padx=6,
            pady=(0, 10),
            sticky="ew",
        )
        self.extra_charts_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        self.disk_chart = DiskUsageChart(
            self.extra_charts_frame,
        )
        self.disk_chart.grid(
            row=0,
            column=0,
            pady=(0, 10),
            sticky="ew",
        )

        self.history_chart = HistoryChart(
            self.extra_charts_frame,
        )
        self.history_chart.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        self.extra_charts_frame.grid_remove()
        self.summary_frame.grid_remove()
"""

if "self.extra_charts_frame = ctk.CTkFrame(" not in content:
    if chart_anchor not in content:
        raise RuntimeError("Diagrammposition nicht gefunden.")

    content = content.replace(
        chart_anchor,
        chart_block,
        1,
    )

finished_anchor = """        self._create_default_report(results)

        self.scan_button.configure(
"""

finished_block = """        try:
            self.history_service.save(results)
        except OSError:
            pass

        self.disk_chart.update_results(results)
        self.history_chart.update_records(
            self.history_service.load_recent(limit=10)
        )
        self.extra_charts_frame.grid()

        self._create_default_report(results)

        self.scan_button.configure(
"""

if "self.history_service.save(results)" not in content:
    if finished_anchor not in content:
        raise RuntimeError(
            "Scanabschlussposition nicht gefunden."
        )

    content = content.replace(
        finished_anchor,
        finished_block,
        1,
    )

reset_anchor = """        self.status_chart.clear()
        self.status_chart.grid_remove()
"""

reset_block = """        self.status_chart.clear()
        self.status_chart.grid_remove()
        self.extra_charts_frame.grid_remove()
"""

reset_part = content.split(
    "    def _reset_summary_dashboard",
    1,
)

if (
    len(reset_part) == 2
    and "self.extra_charts_frame.grid_remove()"
    not in reset_part[1].split("\n    def ", 1)[0]
):
    if reset_anchor not in content:
        raise RuntimeError("Resetposition nicht gefunden.")

    content = content.replace(
        reset_anchor,
        reset_block,
        1,
    )

app_path.write_text(content, encoding="utf-8")
print("Aktualisiert: src/gui/app.py")

requirements_path = root / "requirements.txt"
requirements = (
    requirements_path.read_text(encoding="utf-8")
    if requirements_path.exists()
    else ""
)

if not any(
    line.lower().startswith("matplotlib")
    for line in requirements.splitlines()
):
    requirements += "\nmatplotlib>=3.9,<4.0\n"
    requirements_path.write_text(
        requirements.lstrip(),
        encoding="utf-8",
    )
    print("Aktualisiert: requirements.txt")

build_path = root / "build_exe.ps1"

if build_path.exists():
    build_content = build_path.read_text(encoding="utf-8")

    if '--collect-all "matplotlib"' not in build_content:
        build_anchor = '    --collect-all "customtkinter" `'

        if build_anchor in build_content:
            build_content = build_content.replace(
                build_anchor,
                build_anchor
                + '\n    --collect-all "matplotlib" `',
                1,
            )
            build_path.write_text(
                build_content,
                encoding="utf-8",
            )
            print("Aktualisiert: build_exe.ps1")

print()
print("Dashboard-Upgrade wurde erfolgreich eingespielt.")
print(f"Sicherung: {backup_dir}")
print()
print("Jetzt ausführen:")
print("python -m pip install -r requirements.txt")
print("python -m compileall .\\src")
print("python -m src.gui.app")
