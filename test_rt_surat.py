import requests

base_url = 'http://127.0.0.1:8000'

# Login as RT
login_data = {
    "nik": "3200000000000014",
    "password": "password123"
}
r = requests.post(f"{base_url}/login", json=login_data)
if r.status_code != 200:
    print("Login failed:", r.status_code, r.text)
    exit(1)

token = r.json().get('access_token')
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

r = requests.get(f"{base_url}/surat?status=pending&limit=10", headers=headers)
if r.status_code != 200:
    print("Fetch surat failed:", r.status_code, r.text)
    exit(1)

surat_list = r.json().get('items', [])
if not surat_list:
    surat_data = {
        "kategori": "ktp",
        "keterangan": "Test surat"
    }
    r = requests.post(f"{base_url}/surat", json=surat_data, headers=headers)
    print("Created surat:", r.json())
    surat_id = r.json().get('id')
else:
    surat_id = surat_list[0]['id']

print("Approving surat_id:", surat_id)
# Approve surat
patch_data = {
    "status": "approved",
    "file_ttd_digital": "data:image/png;base64,123",
    "catatan": "Okelah"
}
r = requests.patch(f"{base_url}/surat/{surat_id}", json=patch_data, headers=headers)
print("Patch response:", r.status_code, r.text)
