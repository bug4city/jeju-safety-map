# 제주 안전지도 Design Contract

## 1. Visual Source

The left search panel follows the supplied Geojimap-style reference: fixed desktop sidebar, compact tab row, large rounded search input, adjacent utility buttons, filter chips, sortable/list rows, and map-linked results. The implementation keeps the current 제주 안전지도 safety-map identity rather than copying the reference brand.

## 2. Tokens

- Color: `--ink` primary text, `--sub` secondary text, `--card` panels, `--line` hairlines, `--line-strong` controls, `--accent` incident red, `--brand` safety green, `--brand-soft` selected green tint, `--panel-muted` quiet panel background, `--blue` location/distance affordance.
- Radius: `--r-sm` controls, `--r-lg` panel/card shells, pill controls use `999px`.
- Shadow: `--shadow-1` controls and chips, `--shadow-2` fixed panels and floating primary controls.
- Type: `--fs-title`, `--fs-body`, `--fs-ui`, `--fs-sub`, `--fs-cap`.
- Spacing: `--sp-1` 4px, `--sp-2` 8px, `--sp-3` 12px, `--sp-4` 16px.

## 3. Layout

- Desktop uses a 360px fixed left panel and keeps map tools outside the panel offset by `--panel-w`.
- Mobile uses the existing bottom sheet, with the search and utility actions staying at the top of the sheet.
- The list owns vertical scrolling; the map remains fixed.

## 4. Components

- `SearchBox`: full-width rounded input with icon, clear button, and CJK-safe placeholder text.
- `PanelActions`: current location and tab-aware reset buttons in a two-column grid.
- `ResultMeta`: compact row showing the current result count or empty-search state.
- `ResultItem`: list row with semantic color dot, primary label, secondary label, optional metric, and selected-state background.
- `LocationMarker`: map-native blue marker/ring for the browser geolocation result.

## 5. States

- Search filters the active tab only and updates count text immediately.
- Empty state explains no matching item was found without replacing the search controls.
- Current location button shows locating, success, unsupported, and permission/error states through label text and toast.
- Focus states use the brand or blue outline and never remove keyboard visibility.
