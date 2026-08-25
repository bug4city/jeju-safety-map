# 제주 안전지도 Design Contract

## 1. Visual Source

The left search panel follows the supplied Geojimap-style reference: fixed desktop sidebar, compact tab row, large rounded search input, adjacent utility buttons, filter chips, sortable/list rows, and map-linked results. The implementation keeps the current 제주 안전지도 safety-map identity rather than copying the reference brand.

## 2. Tokens

- Color: `--ink` primary text, `--sub` secondary text, `--card` panels, `--line` hairlines, `--line-strong` controls, `--accent` incident red, `--brand` safety green, `--brand-soft` selected green tint, `--panel-muted` quiet panel background, `--blue` location/distance affordance, `--cctv` CCTV data teal, `--cctv-soft` CCTV tint.
- Radius: `--r-sm` controls, `--r-lg` panel/card shells, pill controls use `999px`.
- Shadow: `--shadow-1` controls and chips, `--shadow-2` fixed panels and floating primary controls.
- Type: `--fs-title`, `--fs-body`, `--fs-ui`, `--fs-sub`, `--fs-cap`.
- Spacing: `--sp-1` 4px, `--sp-2` 8px, `--sp-3` 12px, `--sp-4` 16px.
- App header: `--header-h` fixed top chrome height. Header uses `--panel-muted` over a `--line` bottom hairline, with dark pill actions for external community/profile links.

## 3. Layout

- Desktop uses a 360px fixed left panel below the fixed app header and keeps map tools outside the panel offset by `--panel-w`.
- Mobile uses the existing bottom sheet, with the search and utility actions staying at the top of the sheet.
- The list owns vertical scrolling; the map remains fixed.

## 4. Components

- `SafetySearchBox`: full-width rounded input with icon, clear button, and CJK-safe placeholder text for hotel, accommodation, restaurant, cafe, beach, or attraction lookup. It is the primary conversion path and opens one shared safety-check surface; broad queries show selectable place candidates before the shareable card is generated.
- `PanelActions`: current location and map-reset buttons in a two-column grid.
- `ResultMeta`: compact row that explains the safety-check search action while preserving the browsable incident/region list below.
- `ResultItem`: list row with semantic color dot, primary label, secondary label, optional metric, and selected-state background.
- `LocationMarker`: map-native blue marker/ring for the browser geolocation result.
- `IncidentFactMarker`: map-native white pill marker for confirmed fatality incidents. The primary line shows the outcome count (`사망 1명`), the secondary line shows the confirmation date/time when available (`8.24 확인`, `8.24 08:40 확인`). Confirmation state is carried by the red icon and border, not by spending the text slot on `현장 확인 완료`.
- `ReturnJejuButton`: floating map button shown after the user leaves the 제주 overview via current location or place search; one tap returns to the 제주 center and restores the island-level map.
- `AppHeader`: fixed top brand bar with favicon + 제주안전맵 on the left and compact external action pills on the right. Mobile preserves the brand and collapses long labels before icons.
- `CctvLayer`: optional map overlay using compact teal dots for public CCTV locations; at close zoom each dot labels the camera count so CCTV coverage is visible without competing with incident pins. Purpose labels clarify that the layer mixes traffic, facility, disaster, and safety cameras.
- `RegionContextPills`: compact data badges for population rank and nearby reported incidents. Map labels show only the crowding tier at middle zoom, then add quiet-rank and people count at close zoom. Panels and share cards can show the full two-line context because they have more room.
- `MapPlaceInspector`: map-click detail surface for provider-backed place data. Kakao searches nearby POI categories around the clicked coordinate and reuses the place-candidate/card flow; tile-only fallback maps explain that rendered labels are not clickable data.
- `NearestHelpPanel`: current-location result surface that shows the nearest police station and emergency hospital as actionable rows with distance, phone, and map focus. It is a direct assistance feature, separate from viral/shareable safety cards.
- `HelpPlaceMarker`: map-native blue/green outlined marker for police and hospital candidates found from Kakao category search or static fallback data. It uses concise labels and never competes with red incident markers.
## 5. States

- Safety search submits on Enter, shows a loading state, lists multiple candidate places for broad searches such as hotel or restaurant, pans the map to the selected place, and renders a shareable card with nearby incidents, regional crowding, and caveat copy.
- Region labels progressively disclose detail by zoom: island view uses color only, mid zoom uses region name plus crowding tier, close zoom adds `한적 N위` and estimated daily population. Nearby reported incidents are framed as public-report context, not an official crime-risk score.
- Map click on the provider-backed map opens nearby public place candidates. Selecting a candidate generates the same safety card; if the provider has no POI for that coordinate, the empty state explains the data limitation.
- Empty state explains no matching item was found without replacing the search controls.
- Current location button shows locating, success, unsupported, and permission/error states through label text and toast.
- After current location succeeds, the detail panel switches to nearby help mode and lists the closest police and hospital. If provider search is unavailable, the app uses curated fallback 제주 public-safety locations.
- Return-to-Jeju stays hidden on the 제주 overview and appears after current-location or place-search navigation.
- Focus states use the brand or blue outline and never remove keyboard visibility.
- Header links open external destinations in a new tab, have visible focus rings, and expose clear Korean `aria-label` text for icon-only actions.
