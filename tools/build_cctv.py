#!/usr/bin/env python3
"""전국CCTV표준데이터 API에서 제주 방범 CCTV만 추려 data/cctv.json을 만든다.

사용법: DATA_GO_KR_KEY=<인증키(Decoding)> python3 tools/build_cctv.py

원본 CSV를 저장소에 커밋하지 않는 이유: 35만 행 전국 데이터라 크고,
갱신 때마다 API에서 다시 뽑는 편이 깨끗하다.
"""
import json, os, sys, urllib.parse, urllib.request

KEY = os.environ.get("DATA_GO_KR_KEY")
if not KEY:
    sys.exit("DATA_GO_KR_KEY 환경변수에 공공데이터포털 인증키(Decoding)를 넣어라")

BASE = "https://api.odcloud.kr/api/15013094/v1/standard-cctv"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "cctv.json")

rows, page = [], 1
while True:
    q = urllib.parse.urlencode({
        "serviceKey": KEY, "page": page, "perPage": 5000,
        "cond[ctprvnNm::EQ]": "제주특별자치도",
    })
    with urllib.request.urlopen(f"{BASE}?{q}", timeout=60) as r:
        d = json.load(r)
    data = d.get("data", [])
    rows += data
    if len(data) < 5000:
        break
    page += 1

# 방범 목적만 남긴다. 교통 단속 카메라는 "안심" 신호가 아니다.
pts = []
for r in rows:
    purpose = str(r.get("instlPurposeType") or r.get("설치목적구분") or "")
    if "방범" not in purpose and "생활방범" not in purpose:
        continue
    try:
        lat, lng = float(r.get("latitude") or r.get("위도")), float(r.get("longitude") or r.get("경도"))
    except (TypeError, ValueError):
        continue
    if not (33.0 < lat < 34.1 and 126.0 < lng < 127.1):
        continue
    cnt = r.get("cameraCnt") or r.get("카메라대수") or 1
    pts.append([round(lat, 5), round(lng, 5), int(cnt)])

with open(OUT, "w") as f:
    json.dump({"source": "행정안전부 전국CCTV표준데이터 (방범 목적만)", "count": len(pts), "points": pts}, f, ensure_ascii=False)
print(f"제주 방범 CCTV {len(pts)}개 → data/cctv.json (전체 응답 {len(rows)}행)")
