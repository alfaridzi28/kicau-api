import requests

url = "http://localhost:8000/surat"
# Get a user token
login_res = requests.post("http://localhost:8000/users/login", data={"username": "3215252801990001", "password": "password"})
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get surats
surats = requests.get(url, headers=headers).json()
if surats["items"]:
    surat_id = surats["items"][0]["id"]
    # Patch
    patch_url = f"{url}/{surat_id}"
    res = requests.patch(patch_url, headers=headers, json={"status": "approved", "file_ttd_digital": "data:image/png;base64,abc", "catatan": "test"})
    print(res.status_code)
    print(res.text)
else:
    print("No surat found")
