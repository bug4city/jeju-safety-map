#!/usr/bin/env python3
"""제주 인구정책 통합플랫폼(통신사 빅데이터)에서 읍면동별 유동인구를 뽑아 data/pop.json을 만든다.

사용법: python3 tools/build_pop.py [YYYYMMDD]
날짜를 안 주면 플랫폼 페이지가 알려주는 최신 기준일을 쓴다.

좌표는 읍면동 중심 근사값이다. 행정경계 choropleth 대신 원(버블)으로 그리므로
수십~수백 m 오차는 표시에 영향이 없다.
"""
import json, os, re, sys, urllib.parse, urllib.request

BASE = "https://www.jeju.go.kr"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "pop.json")
UA = {"User-Agent": "Mozilla/5.0 (jeju-safety-map)"}

COORDS = {
    "한림읍": (33.410, 126.269), "애월읍": (33.463, 126.331), "구좌읍": (33.530, 126.856),
    "조천읍": (33.538, 126.635), "한경면": (33.350, 126.180), "추자면": (33.960, 126.300),
    "우도면": (33.505, 126.955), "대정읍": (33.225, 126.250), "남원읍": (33.280, 126.720),
    "성산읍": (33.385, 126.895), "안덕면": (33.255, 126.315), "표선면": (33.325, 126.830),
    "일도1동": (33.513, 126.528), "일도2동": (33.507, 126.537), "이도1동": (33.507, 126.523),
    "이도2동": (33.495, 126.535), "삼도1동": (33.508, 126.517), "삼도2동": (33.513, 126.512),
    "용담1동": (33.512, 126.508), "용담2동": (33.508, 126.492), "건입동": (33.517, 126.535),
    "화북동": (33.520, 126.565), "삼양동": (33.523, 126.588), "봉개동": (33.480, 126.605),
    "아라동": (33.470, 126.545), "오라동": (33.490, 126.515), "연동": (33.489, 126.498),
    "노형동": (33.485, 126.480), "외도동": (33.495, 126.432), "이호동": (33.500, 126.455),
    "도두동": (33.505, 126.468),
    "송산동": (33.245, 126.570), "정방동": (33.248, 126.565), "중앙동": (33.248, 126.560),
    "천지동": (33.246, 126.556), "효돈동": (33.255, 126.610), "영천동": (33.270, 126.585),
    "동홍동": (33.258, 126.567), "서홍동": (33.255, 126.550), "대륜동": (33.245, 126.510),
    "대천동": (33.250, 126.490), "중문동": (33.250, 126.435), "예래동": (33.245, 126.400),
}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", "replace")

day = sys.argv[1] if len(sys.argv) > 1 else None
if not day:
    page = get(f"{BASE}/livingpopulation/staying/index.htm")
    m = re.search(r"var DAY *= *'(\d{8})'", page)
    if not m:
        sys.exit("기준일을 페이지에서 못 찾았다. 날짜를 인자로 넘겨라.")
    day = m.group(1)

regions = []
for name, (lat, lng) in COORDS.items():
    q = urllib.parse.urlencode({"day": day, "hdong": "true", "destHdongNm": name})
    d = json.loads(get(f"{BASE}/population/chart/getFloatingRegionHDong?{q}"))
    total = int(d.get("total") or 0)
    region = {"name": name, "lat": lat, "lng": lng, "total": total}
    # 도민(totalLocal) vs 외지인(totalOther) 분리값 — 없으면 생략하고 프론트에서 숨긴다.
    local, other = int(d.get("totalLocal") or 0), int(d.get("totalOther") or 0)
    if local and other:
        region["local"], region["other"] = local, other
    regions.append(region)
    print(f"{name}: {total:,} (도민 {local:,} · 외지인 {other:,})")

regions.sort(key=lambda r: -r["total"])
with open(OUT, "w") as f:
    json.dump({
        "source": "제주 인구정책 통합플랫폼(통신사 빅데이터 기반 유동인구)",
        "day": day,
        "regions": regions,
    }, f, ensure_ascii=False)
print(f"\n{day} 기준 {len(regions)}개 읍면동 → data/pop.json")
