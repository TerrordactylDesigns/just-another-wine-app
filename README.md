# Just Another Wine App

A Home Assistant add-on for tracking a wine cellar — bottles, multiple cellars
and zones, climate sensors, live cameras, and alerts — all running locally
inside Home Assistant OS.

## Features

- **Multi-cellar, multi-zone** — track one cellar or several, each with
  independently monitored zones (racks, fridges, rooms)
- **Full wine records** — producer, name, vintage, region, grapes, tasting
  notes, purchase history, consumption history, and label photos
- **Drinking windows** — automatic Ready to Drink, Currently Aging, and Past
  Peak views
- **Wishlist** — track wines you want, and move them straight into inventory
  with one action once purchased
- **Climate sensors** — temperature, humidity, light, vibration, CO2, and
  barometric pressure per zone, with history charts
- **Cameras** — live RTSP/HLS/snapshot feeds per zone, with snapshot history
  and health monitoring
- **Unified alerts** — configurable rules across sensors, wine status,
  inventory levels, cameras, and system health, with a single alert log

## Installation

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**
2. Click the **⋮** menu, choose **Repositories**, and add this repository's
   URL
3. Find **Just Another Wine App** in the store and click **Install**
4. Configure the add-on options (log level, retention windows) if desired
5. Click **Start**, then open **Just Another Wine App** from the sidebar

## Data Storage

All data is stored locally inside Home Assistant's persistent `/config` and
`/media` directories, so it survives add-on restarts and updates. No data
leaves your network unless you choose to add an external link to a wine or
fetch a label image from a URL you provide.

## Support

This add-on has no external dependencies beyond ffmpeg (bundled in the
container) for camera streaming. Cameras and sensors are added manually
through the UI — there is no discovery step required.
