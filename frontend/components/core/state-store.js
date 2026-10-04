/* Core state store: operational mode, route metadata caching, and lookup helpers */
let MODE = "LIVE";
let ROUTE_NAMES = {};

async function ensureRouteNames() {
  if (Object.keys(ROUTE_NAMES).length) return;
  try {
    const r = await jget("/routes?limit=200");
    r.forEach((x) => {
      ROUTE_NAMES[x.id] = x.short_name || x.long_name || x.external_route_id;
    });
  } catch {
    /* names stay raw IDs if endpoint is unavailable */
  }
}

function routeLabel(id) {
  return ROUTE_NAMES[id] || id || "Unknown route";
}
