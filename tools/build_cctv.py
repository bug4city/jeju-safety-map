#!/usr/bin/env python3
"""전국CCTV표준데이터에서 제주 공공 CCTV를 추려 data/cctv.json을 만든다.

사용법:
  python3 tools/build_cctv.py
  DATA_GO_KR_KEY=<인증키(Decoding)> python3 tools/build_cctv.py

원본 CSV를 저장소에 커밋하지 않는 이유: 35만 행 전국 데이터라 크고,
갱신 때마다 API에서 다시 뽑는 편이 깨끗하다.
"""
import csv
import json
import os
import urllib.parse
import urllib.request

KEY = os.environ.get("DATA_GO_KR_KEY")
API_BASE = "https://api.odcloud.kr/api/15013094/v1/standard-cctv"
CSV_URL = "https://file.localdata.go.kr/file/download/cctv_info/info?orgCode=6500000_ALL"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "cctv.json")


def api_rows():
    rows, page = [], 1
    while True:
        q = urllib.parse.urlencode({
            "serviceKey": KEY, "page": page, "perPage": 5000,
            "cond[ctprvnNm::EQ]": "제주특별자치도",
        })
        with urllib.request.urlopen(f"{API_BASE}?{q}", timeout=60) as r:
            d = json.load(r)
        data = d.get("data", [])
        rows += data
        if len(data) < 5000:
            return rows
        page += 1


def csv_rows():
    req = urllib.request.Request(CSV_URL, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Referer": "https://file.localdata.go.kr/file/cctv_info/info",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp949")
    return list(csv.DictReader(text.splitlines()))


if KEY:
    rows = api_rows()
else:
    rows = csv_rows()

# "근처 CCTV 존재" 확인이 목적이므로 방범만 남기지 않는다.
# 대신 목적을 함께 저장해 방범 CCTV처럼 오해하지 않게 표시한다.
pts = []
purpose_counts = {}
for r in rows:
    sido = str(r.get("ctprvnNm") or r.get("시도명") or "")
    if sido and sido != "제주특별자치도":
        continue
    purpose = str(r.get("instlPurposeType") or r.get("설치목적구분") or "")
    try:
        lat = float(r.get("latitude") or r.get("위도") or r.get("WGS84위도"))
        lng = float(r.get("longitude") or r.get("경도") or r.get("WGS84경도"))
    except (TypeError, ValueError):
        continue
    if not (33.0 < lat < 34.1 and 126.0 < lng < 127.1):
        continue
    try:
        cnt = int(r.get("cameraCnt") or r.get("카메라대수") or 1)
    except (TypeError, ValueError):
        cnt = 1
    label = purpose or "기타"
    purpose_counts[label] = purpose_counts.get(label, 0) + cnt
    pts.append([round(lat, 5), round(lng, 5), cnt, label])

with open(OUT, "w") as f:
    json.dump({
        "source": "행정안전부 전국CCTV표준데이터 (공공 CCTV 전체)",
        "count": len(pts),
        "cameraTotal": sum(p[2] for p in pts),
        "purposeCounts": purpose_counts,
        "points": pts,
    }, f, ensure_ascii=False)
print(f"제주 공공 CCTV {len(pts)}곳/{sum(p[2] for p in pts)}대 → data/cctv.json (전체 응답 {len(rows)}행)")
