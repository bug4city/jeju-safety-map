#!/usr/bin/env python3
"""한국관광공사 TourAPI(국문 관광정보 서비스, KorService2)에서 제주 주요 관광지를
추려 data/tour.json을 만든다.

사용법:
  TOUR_API_KEY=<data.go.kr 인증키(인코딩된 형태 그대로)> python3 tools/build_tour.py

제주 전체 관광지(contentTypeId=12, lDongRegnCd=50)를 전부 받은 뒤
FAMOUS 키워드에 걸리는 곳만 남긴다. 전부 찍으면 핀이 수백 개라 지도가 안 읽혀서,
누구나 아는 대표 관광지만 큐레이션한다.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

KEY = os.environ.get("TOUR_API_KEY") or os.environ.get("DATA_GO_KR_KEY")
BASE = "https://apis.data.go.kr/B551011/KorService2/areaBasedList2"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# 대표 관광지 키워드. title에 키워드가 포함되면 채택하되, 키워드당 1곳만 남긴다.
FAMOUS = [
    "성산일출봉", "한라산", "섭지코지", "만장굴", "천지연폭포", "천제연폭포",
    "정방폭포", "주상절리", "협재해수욕장", "함덕해수욕장", "이호테우해변",
    "중문색달해수욕장", "곽지해수욕장", "김녕해수욕장", "월정리해변", "용두암",
    "용머리해안", "산방산", "카멜리아힐", "에코랜드", "비자림",
    "절물자연휴양림", "새별오름", "쇠소깍", "외돌개", "마라도",
    "가파도", "우도", "수월봉", "금오름", "아부오름", "백약이오름",
    "광치기해변", "도두봉", "표선해수욕장", "한림공원", "송악산",
]

def remainder(title, kw):
    """키워드·지역명·괄호 부연을 뺀 나머지. 짧을수록 그 관광지 자체에 가깝다.
    (예: '제주 서귀포 산방산'→'' 이 '산방산랜드'→'랜드' 를 이긴다)"""
    t = title.replace(kw, "")
    for word in ("제주도", "제주", "서귀포", "국가지질공원", "유네스코", "세계자연유산"):
        t = t.replace(word, "")
    return len(t.replace(" ", "").strip("()[]"))

# 관광지(12) 타입에 없어서 키워드 검색으로 보완하는 곳 (숲길·문화시설·시장 등)
EXTRA_KEYWORDS = ["오설록 티뮤지엄", "사려니숲길", "동문재래시장"]
SEARCH = "https://apis.data.go.kr/B551011/KorService2/searchKeyword2"


def fetch_all():
    rows, page = [], 1
    while True:
        q = urllib.parse.urlencode({
            "numOfRows": 100, "pageNo": page, "MobileOS": "ETC",
            "MobileApp": "jejuSafetyMap", "_type": "json",
            "contentTypeId": 12, "lDongRegnCd": 50, "arrange": "O",
        })
        url = f"{BASE}?serviceKey={KEY}&{q}"
        with urllib.request.urlopen(url, timeout=30) as r:
            body = json.load(r)["response"]["body"]
        items = body.get("items") or {}
        batch = items.get("item") or []
        rows.extend(batch)
        if page * 100 >= int(body.get("totalCount", 0)) or not batch:
            return rows
        page += 1


def search_keyword(kw):
    q = urllib.parse.urlencode({
        "numOfRows": 10, "pageNo": 1, "MobileOS": "ETC",
        "MobileApp": "jejuSafetyMap", "_type": "json",
        "keyword": kw, "lDongRegnCd": 50,
    })
    with urllib.request.urlopen(f"{SEARCH}?serviceKey={KEY}&{q}", timeout=30) as r:
        body = json.load(r)["response"]["body"]
    hits = ((body.get("items") or {}).get("item") or [])
    hits = [h for h in hits if kw.replace(" ", "") in h["title"].replace(" ", "")]
    return sorted(hits, key=lambda h: len(h["title"]))[0] if hits else None


def add_spot(spots, matched, hit):
    if hit["contentid"] in matched:
        return
    matched.add(hit["contentid"])
    spots.append({
        "id": hit["contentid"],
        "name": hit["title"],
        "lat": round(float(hit["mapy"]), 5),
        "lng": round(float(hit["mapx"]), 5),
        "addr": hit.get("addr1", ""),
        "img": hit.get("firstimage2") or hit.get("firstimage") or "",
    })


def main():
    if not KEY:
        sys.exit("TOUR_API_KEY 환경변수에 data.go.kr 인증키를 넣어 실행하세요.")
    rows = fetch_all()
    print(f"제주 관광지 전체 {len(rows)}건 수신")
    spots, matched = [], set()
    for kw in FAMOUS:
        # 키워드와 이름이 정확히 같은 곳 우선, 없으면 포함되는 곳 중 이름이 짧은 곳
        hits = [r for r in rows if kw in r.get("title", "")]
        if not hits:
            print(f"  ! 미발견: {kw}")
            continue
        hit = sorted(hits, key=lambda r: (r["title"] != kw, remainder(r["title"], kw)))[0]
        add_spot(spots, matched, hit)
    for kw in EXTRA_KEYWORDS:
        hit = search_keyword(kw)
        if hit:
            add_spot(spots, matched, hit)
        else:
            print(f"  ! 미발견: {kw}")
    out = {
        "source": "한국관광공사 TourAPI 국문 관광정보 서비스(KorService2)",
        "count": len(spots),
        "spots": sorted(spots, key=lambda s: s["name"]),
    }
    path = os.path.join(DATA_DIR, "tour.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{len(spots)}곳 → {path}")


if __name__ == "__main__":
    main()
