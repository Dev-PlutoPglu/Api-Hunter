"""Central configuration: endpoints, probe paths, tunables and the offline fallback catalog."""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Remote catalogs
# ---------------------------------------------------------------------------

# The classic GitHub catalog of free/public APIs (markdown tables).
PUBLIC_APIS_README = (
    "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md"
)

# APIs.guru machine-readable directory of OpenAPI/Swagger specs (real base URLs + endpoints).
APISGURU_LIST = "https://api.apis.guru/v2/list.json"
APISGURU_METRICS = "https://api.apis.guru/v2/metrics.json"

# GitHub repository search (unauthenticated: 10 req/min — keep per_page small).
GITHUB_API = "https://api.github.com"
GITHUB_SEARCH_REPOS = GITHUB_API + "/search/repositories"
GITHUB_RAW_README = "https://raw.githubusercontent.com/{full_name}/{branch}/README.md"

# Default GitHub queries used to find more free-API lists on GitHub.
GITHUB_DEFAULT_QUERIES = [
    "awesome public apis",
    "free api list",
    "public apis no key",
]

# ---------------------------------------------------------------------------
# Metadata / machine-readable-descriptor probing
# ---------------------------------------------------------------------------

# Paths appended to a working base URL to discover *metadata APIs*:
# OpenAPI/Swagger descriptors, OpenID discovery, actuator/health endpoints...
METADATA_PROBE_PATHS = [
    "/openapi.json",
    "/swagger.json",
    "/api-docs",
    "/v2/api-docs",
    "/v3/api-docs",
    "/.well-known/openid-configuration",
    "/metadata",
    "/api/v1/metadata",
    "/health",
    "/actuator",
]

# ---------------------------------------------------------------------------
# Testing tunables
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 10          # seconds per HTTP request
DEFAULT_WORKERS = 12          # concurrent testers
DEFAULT_RETRIES = 1           # retries on network errors
DEFAULT_LIMIT = 60            # max APIs kept after filtering (0 = no limit)
DEFAULT_SPECS = 30            # max APIs.guru specs fetched for endpoint extraction
DEFAULT_MAX_ENDPOINTS = 3     # max real endpoints tested per API in deep mode

# Example values used to fill path/query parameters so endpoints can be tested.
PARAM_EXAMPLES = {
    "lat": "0", "latitude": "0", "lon": "0", "lng": "0", "longitude": "0",
    "id": "1", "userid": "1", "user": "1", "q": "api", "query": "api",
    "search": "api", "name": "api", "limit": "3", "count": "3", "size": "3",
    "page": "1", "offset": "0", "symbol": "BTC", "ticker": "BTC",
    "city": "Pune", "country": "IN", "region": "IN", "date": "2024-01-01",
    "start": "1", "end": "10", "slug": "api", "repo": "public-apis/public-apis",
    "username": "octocat", "email": "hunter@example.com", "ip": "8.8.8.8",
    "domain": "example.com", "url": "https://example.com", "code": "USD",
    "base": "USD", "target": "EUR", "amount": "1",
}

# ---------------------------------------------------------------------------
# Offline fallback catalog — known-free, no-key APIs with real base URLs.
# Used when the network catalogs are unreachable, so the tool always works.
# ---------------------------------------------------------------------------

BUILTIN_APIS = [
    {"name": "Cat Facts", "url": "https://catfact.ninja", "category": "Animals",
     "auth": "none", "https": True,
     "description": "Daily cat facts, breeds and random facts."},
    {"name": "Dog CEO", "url": "https://dog.ceo/api", "category": "Animals",
     "auth": "none", "https": True,
     "description": "Random dog pictures, breeds list and sub-breeds."},
    {"name": "JSONPlaceholder", "url": "https://jsonplaceholder.typicode.com",
     "category": "Development", "auth": "none", "https": True,
     "description": "Fake online REST API for testing and prototyping."},
    {"name": "HTTPBin", "url": "https://httpbin.org", "category": "Development",
     "auth": "none", "https": True,
     "description": "HTTP request/response inspection service."},
    {"name": "IPify", "url": "https://api.ipify.org", "category": "Geocoding",
     "auth": "none", "https": True, "description": "Simple public IP address API."},
    {"name": "IP-API", "url": "http://ip-api.com", "category": "Geocoding",
     "auth": "none", "https": False, "description": "IP geolocation and ASN lookup."},
    {"name": "CoinGecko", "url": "https://api.coingecko.com/api/v3",
     "category": "Cryptocurrency", "auth": "none", "https": True,
     "description": "Cryptocurrency prices, market data and exchanges."},
    {"name": "CoinDesk", "url": "https://api.coindesk.com/v1",
     "category": "Cryptocurrency", "auth": "none", "https": True,
     "description": "Bitcoin price index and historical data."},
    {"name": "Open-Meteo", "url": "https://api.open-meteo.com/v1",
     "category": "Weather", "auth": "none", "https": True,
     "description": "Free weather forecasts, no key required."},
    {"name": "Open-Meteo Geocoding", "url": "https://geocoding-api.open-meteo.com/v1",
     "category": "Geocoding", "auth": "none", "https": True,
     "description": "Free city name to coordinates geocoding."},
    {"name": "Frankfurter", "url": "https://api.frankfurter.app",
     "category": "Currency Exchange", "auth": "none", "https": True,
     "description": "Exchange rates published by the ECB, no key."},
    {"name": "REST Countries", "url": "https://restcountries.com/v3.1",
     "category": "Geocoding", "auth": "none", "https": True,
     "description": "Country information: names, flags, currencies, languages."},
    {"name": "Agify", "url": "https://api.agify.io", "category": "Data Validation",
     "auth": "none", "https": True, "description": "Predict age from a name."},
    {"name": "Genderize", "url": "https://api.genderize.io", "category": "Data Validation",
     "auth": "none", "https": True, "description": "Predict gender from a name."},
    {"name": "Nationalize", "url": "https://api.nationalize.io", "category": "Data Validation",
     "auth": "none", "https": True, "description": "Predict nationality from a name."},
    {"name": "Bored API", "url": "https://www.boredapi.com/api",
     "category": "Entertainment", "auth": "none", "https": True,
     "description": "Find random activities to cure boredom."},
    {"name": "Advice Slip", "url": "https://api.adviceslip.com",
     "category": "Entertainment", "auth": "none", "https": True,
     "description": "Random advice slips."},
    {"name": "Chuck Norris", "url": "https://api.chucknorris.io",
     "category": "Entertainment", "auth": "none", "https": True,
     "description": "Hand-curated Chuck Norris jokes."},
    {"name": "Kanye REST", "url": "https://api.kanye.rest", "category": "Entertainment",
     "auth": "none", "https": True, "description": "Random Kanye West quotes."},
    {"name": "Jokes API (SV443)", "url": "https://v2.jokeapi.dev",
     "category": "Entertainment", "auth": "none", "https": True,
     "description": "Programming, misc and dark jokes."},
    {"name": "Open Trivia DB", "url": "https://opentdb.com/api.php",
     "category": "Entertainment", "auth": "none", "https": True,
     "description": "Trivia questions by category/difficulty."},
    {"name": "PokeAPI", "url": "https://pokeapi.co/api/v2", "category": "Games",
     "auth": "none", "https": True, "description": "All Pokemon data."},
    {"name": "SWAPI", "url": "https://swapi.dev/api", "category": "Entertainment",
     "auth": "none", "https": True, "description": "Star Wars universe data."},
    {"name": "Studio Ghibli", "url": "https://ghibliapi.vercel.app",
     "category": "Entertainment", "auth": "none", "https": True,
     "description": "Studio Ghibli films and characters."},
    {"name": "Deck of Cards", "url": "https://deckofcardsapi.com/api",
     "category": "Games", "auth": "none", "https": True,
     "description": "Virtual deck of cards API."},
    {"name": "Open Notify (ISS)", "url": "http://api.open-notify.org",
     "category": "Science", "auth": "none", "https": False,
     "description": "ISS position and astronauts in space."},
    {"name": "Numbers API", "url": "http://numbersapi.com", "category": "Data Validation",
     "auth": "none", "https": False, "description": "Interesting facts about numbers."},
    {"name": "Universities (Hipolabs)", "url": "http://universities.hipolabs.com",
     "category": "Education", "auth": "none", "https": False,
     "description": "Universities by country and name."},
    {"name": "Postman Echo", "url": "https://postman-echo.com", "category": "Development",
     "auth": "none", "https": True, "description": "Echo service for request testing."},
    {"name": "APIs.guru Directory", "url": "https://api.apis.guru/v2/list.json",
     "category": "Development", "auth": "none", "https": True,
     "description": "Machine-readable directory of 2500+ OpenAPI specs."},
]

USER_AGENT = "api-hunter/1.0 (free-API discovery & testing CLI)"
