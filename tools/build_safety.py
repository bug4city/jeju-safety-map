#!/usr/bin/env python3
"""제주 안전비상벨·보안등 위치를 추려 data/bells.json, data/lights.json을 만든다.

사용법:
  python3 tools/build_safety.py                      # 비상벨: config.json의 safemap 키 사용
  DATA_GO_KR_KEY=<인증키> python3 tools/build_safety.py   # 보안등(+비상벨 폴백)도 생성

비상벨 소스 (둘 중 되는 쪽을 쓴다):
  1. 생활안전지도 IF_0032 — config.json의 safemapKey. 단 safemap은 데이터셋별
     활용신청제라 safemap.go.kr에서 "안전비상벨(objtId=137)" 활용신청이 승인돼 있어야 한다.
  2. 공공데이터포털 전국안전비상벨위치표준데이터(15028206) — DATA_GO_KR_KEY.

보안등 소스: 공공데이터포털 전국보안등정보표준데이터(15017320) — DATA_GO_KR_KEY 필수.
odcloud 표준데이터 uddi는 개정판마다 바뀔 수 있어 후보 경로를 순서대로 시도한다.
"""
import json
import os
import urllib.parse
import urllib.request

KEY = os.environ.get("DATA_GO_KR_KEY")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
try:
    with open(os.path.join(DATA_DIR, "..", "config.json")) as f:
        SAFEMAP_KEY = json.load(f).get("safemapKey")
except OSError:
    SAFEMAP_KEY = None

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
        for key in (k, k.upper(), k.lower()):
            v = row.get(key)
            if v not in (None, ""):
                return v
    return None


def to_points(rows):
    """행 목록에서 제주 좌표만 [lat, lng]로 추린다. 필드명은 소스별 후보를 순서대로 본다."""
    pts = []
    for r in rows:
        sido = str(pick(r, "ctprvnNm", "시도명", "ctprvn_nm") or "")
        addr = str(pick(r, "rdnmadr", "소재지도로명주소", "lnmadr", "소재지지번주소", "adres") or "")
        if sido and "제주" not in sido:
            continue
        if not sido and addr and "제주" not in addr:
            continue
        try:
            lat = float(pick(r, "latitude", "위도", "lat", "y", "WGS84위도"))
            lng = float(pick(r, "longitude", "경도", "lon", "lng", "x", "WGS84경도"))
        except (TypeError, ValueError):
            continue
        if not (33.0 < lat < 34.1 and 126.0 < lng < 127.1):
            continue
        pts.append([round(lat, 5), round(lng, 5)])
    return pts


def fetch_safemap_bells():
    """생활안전지도 IF_0032 (활용신청 승인 필요). 전국 응답이라 to_points에서 제주만 남긴다."""
    rows, page = [], 1
    while True:
        q = urllib.parse.urlencode({
            "serviceKey": SAFEMAP_KEY, "pageNo": page, "numOfRows": 1000, "type": "json",
        })
        with urllib.request.urlopen(f"https://www.safemap.go.kr/openapi2/IF_0032?{q}", timeout=60) as r:
            d = json.load(r)
        header = d.get("header") or {}
        if header.get("resultCode") not in ("00", "0", None):
            raise RuntimeError(header.get("errorMsg") or header.get("resultMsg"))
        items = (d.get("body") or {}).get("items") or {}
        batch = items.get("item") if isinstance(items, dict) else items
        if not batch:
            return rows
        if isinstance(batch, dict):
            batch = [batch]
        rows += batch
        if len(batch) < 1000:
            return rows
        page += 1


def write_out(ds, pts, total):
    out = os.path.join(DATA_DIR, ds["out"])
    with open(out, "w") as f:
        json.dump({"source": ds["source"], "count": len(pts), "points": pts}, f, ensure_ascii=False)
    print(f"제주 {ds['name']} {len(pts)}곳 → data/{ds['out']} (전체 응답 {total}행)")


for ds in DATASETS:
    rows, src, last_err = None, ds["source"], None
    if ds["name"] == "안전비상벨" and SAFEMAP_KEY:
        try:
            rows = fetch_safemap_bells()
            src = "행정안전부 생활안전지도 안전비상벨(IF_0032)"
        except Exception as e:  # noqa: BLE001 — 표준데이터로 폴백
            last_err = f"safemap IF_0032: {e}"
            print(f"[안내] {last_err} → 공공데이터포털 표준데이터로 폴백")
    if rows is None and KEY:
        for route in ds["routes"]:
            try:
                rows = fetch_rows(route)
                break
            except Exception as e:  # noqa: BLE001 — 경로 후보 시도
                last_err = f"{route}: {e}"
    if rows is None:
        need = "safemap 활용신청(objtId=137)" if ds["name"] == "안전비상벨" else "DATA_GO_KR_KEY"
        print(f"[실패] {ds['name']}: {last_err or need + ' 필요'}")
        continue
    ds["source"] = src
    write_out(ds, to_points(rows), len(rows))
