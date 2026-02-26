# Utah Building Trends Explorer — Deployment Guide

## What's in this package

- `utah_building_trends.html` — The interactive map tool (single file)
- This guide

## How to deploy

### If your website allows file uploads (WordPress, custom CMS, static site):

1. Upload `utah_building_trends.html` to your web server
   (e.g., in an `/assets/tools/` or `/static/` directory).

2. On the page where you want the map to appear, add this embed code:

```html
<iframe
  src="/path/to/utah_building_trends.html"
  width="100%"
  height="700"
  style="border: none; border-radius: 8px;"
  title="Utah Building Trends Explorer"
  loading="lazy"
></iframe>
```

3. Adjust `height` (in pixels) to fit your page layout. `width="100%"`
   makes it fill the container.

### If you're on Squarespace:

Squarespace doesn't support raw HTML file uploads. Two approaches:

**Approach A — External hosting (recommended):**
1. Host `utah_building_trends.html` on a static hosting service. Free options:
   - GitHub Pages (free, reliable)
   - Netlify (free tier, drag-and-drop deploy)
   - Vercel (free tier)
2. Once hosted, you'll have a public URL like:
   `https://your-org.github.io/building-trends/utah_building_trends.html`
3. In your Squarespace page editor:
   - Add a "Code" block (in the block menu under "More")
   - Paste the iframe embed code above, using the full URL as the `src`

**Approach B — Squarespace Code Injection:**
1. Host the HTML file externally (same as Approach A)
2. Go to Settings > Advanced > Code Injection
3. Add the iframe code in the appropriate page's code injection field

### Requirements
- The HTML file must be served over HTTPS (same as your main site)
- The map loads its base map tiles and Leaflet.js from external CDNs,
  so the page needs normal internet access
- No server-side processing is needed — the map is fully client-side

## How to use the map

- **Pan and zoom** to explore different areas of Utah
- **Hover** over any colored circle to see a quick preview (county, % new construction)
- **Click** any circle for detailed housing data with state-level context
- **Toggle layers** using the control in the top-right:
  - "Building Trends" — the primary layer showing new construction rates
  - "Upward Mobility" — background shading showing economic mobility data from Opportunity Atlas
  - "County Boundaries" — dashed outlines for geographic reference

## Updating the map

When new data is available (typically annually when ACS releases a new vintage),
Socio will provide an updated `utah_building_trends.html` file. Simply replace
the existing file on your server — no other changes needed.

## Questions?

Contact Tyler Dial at Socio.
