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
        user_id = res_data["user_info"]["id"]
except Exception as e:
    print(f"Login Failed: {e}")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

def request(method, url, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

print("--- Testing CRUD Aset ---")
# CREATE
status, res = request("POST", f"{base_url}/aset/", {
    "nama_aset": "Test Aset CRUD",
    "deskripsi": "Test description",
    "jumlah": 5,
    "status": "tersedia",
    "kepemilikan": "aset_rt",
    "pemilik_id": user_id
})
print(f"CREATE: {status}")
aset_id = res.get("id")

if aset_id:
    # UPDATE
    status, res = request("PUT", f"{base_url}/aset/{aset_id}", {
        "nama_aset": "Test Aset Updated",
        "jumlah": 10
    })
    print(f"UPDATE: {status}")

    # GET
    status, res_get = request("GET", f"{base_url}/aset/")
    print(f"GET (List): {status}")

    # DELETE
    status, res = request("DELETE", f"{base_url}/aset/{aset_id}")
    print(f"DELETE: {status}")
else:
    print("Failed to create aset, cannot test update/delete")

print("\n--- Testing CRUD Pemberitahuan ---")
# CREATE
status, res = request("POST", f"{base_url}/pemberitahuan/", {
    "judul": "Test Pemberitahuan",
    "isi": "Testing CRUD",
    "target_rt": "01",
    "target_rw": "01",
    "is_publik": True
})
print(f"CREATE: {status}")
p_id = res.get("id")

if p_id:
    # UPDATE
    status, res = request("PUT", f"{base_url}/pemberitahuan/{p_id}", {
        "judul": "Test Pemberitahuan Updated"
    })
    print(f"UPDATE: {status}")

    # GET
    status, res_get = request("GET", f"{base_url}/pemberitahuan/")
    print(f"GET (List): {status}")

    # DELETE
    status, res = request("DELETE", f"{base_url}/pemberitahuan/{p_id}")
    print(f"DELETE: {status}")
else:
    print(res)
    print("Failed to create pemberitahuan")
