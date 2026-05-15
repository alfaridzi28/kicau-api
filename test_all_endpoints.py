import urllib.request
import urllib.parse
import json

base_url = "http://localhost:8000"
nik_superadmin = "3215252801990001"
password = "password"

# 1. Login
data = json.dumps({"nik": nik_superadmin, "password": password}).encode("utf-8")
req = urllib.request.Request(f"{base_url}/login", data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode())
        token = res_data["access_token"]
        print(f"[OK] Login Success, Token: {token[:10]}...")
except Exception as e:
    print(f"[ERROR] Login Failed: {e}")
    exit(1)

endpoints = [
    "/warga/",
    "/iuran/",
    "/iuran-setting/",
    "/bansos/",
    "/stats/dashboard",
    "/aduan/",
    "/surat/",
    "/aset/",
    "/pemberitahuan/"
]

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

all_ok = True
for ep in endpoints:
    url = f"{base_url}{ep}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            print(f"[OK] {ep} -> {response.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[FAIL] {ep} -> {e.code}: {body}")
        all_ok = False
    except Exception as e:
        print(f"[ERROR] {ep} -> {e}")
        all_ok = False

if all_ok:
    print("\n✅ All GET endpoints are responding successfully.")
else:
    print("\n❌ Some endpoints failed.")
