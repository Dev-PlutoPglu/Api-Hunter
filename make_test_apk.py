"""Build a synthetic APK for testing reverse-apk (no real app involved).

Strings are separated by non-printable bytes, the way a real DEX string pool
length-prefixes each entry.
"""
import zipfile
from pathlib import Path

# write the samples next to this script, wherever the repo lives
OUT_DIR = Path(__file__).resolve().parent

SEP = b"\x00\x1a"  # non-printable, like ULEB128 length prefixes in a real DEX

dex_strings = SEP.join([
    b"Lcom/syntheticapp/MainActivity;",
    b"https://api.syntheticapp.com/v1/",
    b"https://auth.syntheticapp.com/oauth/token",
    b"https://cdn.syntheticapp.com/api/v2/feed",
    b"/api/v1/users/{user_id}",
    b"/api/v1/messages",
    b"/v1/search?q=",
    b"api_key=sk_live_9f8a7b6c5d4e3f2a1b0c",
    b"Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    b"graphql endpoint https://api.syntheticapp.com/graphql",
    b"firebase https://syntheticapp-prod.firebaseio.com",
    b"Lokhttp3/OkHttpClient;",
    b"Lretrofit2/Retrofit;",
    b"https://docs.syntheticapp.com/guide/getting-started",
    b"https://www.syntheticapp.com/privacy-policy",
    b"x-api-key: 7f3d9a2b1c8e4f6a0d5b3c7e9a1f2d4b",
    b"secret_key = 9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d",
])

manifest_strings = SEP.join([
    b"com.syntheticapp.mobile",
    b"android.permission.INTERNET",
    b"android.permission.ACCESS_FINE_LOCATION",
    b"android.permission.CAMERA",
    b"com.syntheticapp.mobile.LoginActivity",
    b"https://api.syntheticapp.com/v1/",
])

config_json = b'''{
  "base_url": "https://cdn.syntheticapp.com/api/v2",
  "api_key": "AKIAIOSFODNN7EXAMPLE",
  "auth_endpoint": "https://auth.syntheticapp.com/oauth/token",
  "analytics": "https://www.google-analytics.com/collect",
  "docs": "https://docs.syntheticapp.com/sdk"
}'''

strings_xml = b'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="api_base">https://api.syntheticapp.com/v1/</string>
    <string name="app_name">SyntheticApp</string>
    <string name="graphql_url">https://api.syntheticapp.com/graphql</string>
</resources>'''

with zipfile.ZipFile(OUT_DIR / "synthetic-app.apk", "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("AndroidManifest.xml", manifest_strings)
    zf.writestr("classes.dex", dex_strings)
    zf.writestr("classes2.dex", b"Lcom/syntheticapp/NetworkModule;" + SEP +
                b"https://api.syntheticapp.com/v1/status")
    zf.writestr("assets/config.json", config_json)
    zf.writestr("res/values/strings.xml", strings_xml)
    zf.writestr("resources.arsc", b"com.syntheticapp.mobile\x00drawable/ic_launcher")
    zf.writestr("META-INF/MANIFEST.MF", b"Manifest-Version: 1.0")
    zf.writestr("res/drawable/icon.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)

print("synthetic APK created")
