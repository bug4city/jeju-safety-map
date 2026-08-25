#!/usr/bin/env python3
"""전국 표준데이터에서 제주 안전비상벨·보안등을 추려 data/bells.json, data/lights.json을 만든다.

사용법:
  DATA_GO_KR_KEY=<인증키(Decoding)> python3 tools/build_safety.py

키는 공공데이터포털(data.go.kr)에서 아래 두 표준데이터 활용신청 후 발급받는다
(build_cctv.py와 같은 키를 쓴다):
  - 전국안전비상벨위치표준데이터 (15028206)
  - 전국보안등정보표준데이터 (15017320)

odcloud 표준데이터 경로는 uddi가 개정판마다 바뀔 수 있어, 후보 경로를 순서대로
시도하고 실패하면 어떤 경로가 안 됐는지 출력한다.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

KEY = os.environ.get("DATA_GO_KR_KEY")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

DATASETS = [
    {
        "name": "안전비상벨",
        "out": "bells.json",
        "source": "행정안전부 전국안전비상벨위치표준데이터",
        "routes": [
            "15028206/v1/uddi:9fa7f510-a7ed-475c-952d-bbb823f5b0dd",
            "15028206/v1/standard-safetybell",
        ],
    },
    {
        "name": "보안등",
        "out": "lights.json",
        "source": "행정안전부 전국보안등정보표준데이터",
        "routes": [
            "15017320/v1/standard-securityLight",
            "15017320/v1/standard-security-light",
        ],
    },
]


def fetch_rows(route):
    rows, page = [], 1
    while True:
        q = urllib.parse.urlencode({
            "serviceKey": KEY, "page": page, "perPage": 5000,
            "cond[ctprvnNm::EQ]": "제주특별자치도",
        })
        with urllib.request.urlopen(f"https://api.odcloud.kr/api/{route}?{q}", timeout=60) as r:
            d = json.load(r)
        if "data" not in d:
            raise RuntimeError(d.get("msg") or str(d)[:200])
        rows += d["data"]
        if len(d["data"]) < 5000:
            return rows
        page += 1


def pick(row, *keys):
    for k in keys:
        v = row.get(k)
        if v not in (None, ""):
            return v
    return None


if not KEY:
    sys.exit("DATA_GO_KR_KEY 환경변수가 필요하다. data.go.kr에서 표준데이터 활용신청 후 발급.")

for ds in DATASETS:
    rows, last_err = None, None
    for route in ds["routes"]:
        try:
            rows = fetch_rows(route)
            break
        except Exception as e:  # noqa: BLE001 — 경로 후보 시도
            last_err = f"{route}: {e}"
    if rows is None:
        print(f"[실패] {ds['name']}: {last_err}")
        continue
    pts = []
    for r in rows:
        sido = str(pick(r, "ctprvnNm", "시도명") or "")
        if sido and "제주" not in sido:
            continue
        try:
            lat = float(pick(r, "latitude", "위도", "WGS84위도"))
            lng = float(pick(r, "longitude", "경도", "WGS84경도"))
        except (TypeError, ValueError):
            continue
        if not (33.0 < lat < 34.1 and 126.0 < lng < 127.1):
            continue
        pts.append([round(lat, 5), round(lng, 5)])
    out = os.path.join(DATA_DIR, ds["out"])
    with open(out, "w") as f:
        json.dump({"source": ds["source"], "count": len(pts), "points": pts}, f, ensure_ascii=False)
    print(f"제주 {ds['name']} {len(pts)}곳 → data/{ds['out']} (전체 응답 {len(rows)}행)")
