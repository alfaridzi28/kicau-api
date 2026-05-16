import requests

base_url = 'http://127.0.0.1:8000'

# Login as RT
login_data = {
    "nik": "3200000000000014",
    "password": "password123"
}
r = requests.post(f"{base_url}/login", json=login_data)
token = r.json().get('access_token')
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

surat_id = "134b69ff-61d5-4a81-9682-71d1ca5ab29e"

patch_data = {
    "status": "approved",
    "file_ttd_digital": "data:image/png;base64,123",
    "catatan": "Test user error"
}
r = requests.patch(f"{base_url}/surat/{surat_id}", json=patch_data, headers=headers)
print("Patch response:", r.status_code, r.text)
