import requests

BASE_URL = "http://127.0.0.1:5000"

checks = [
    ("GET", "/health"),
    ("GET", "/demo/velma"),
    ("POST", "/assess/velma"),
    ("GET", "/patient/SYN-001"),
    ("POST", "/assess/SYN-001"),
]

print("ACHOO API smoke test")
print("=" * 40)

for method, path in checks:
    url = f"{BASE_URL}{path}"

    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, timeout=10)

        print(f"{method} {path} -> {response.status_code}")

        if not response.ok:
            print(response.text)
            raise SystemExit(1)

    except requests.RequestException as exc:
        print(f"FAILED: {method} {path}")
        print(exc)
        raise SystemExit(1)

print("=" * 40)
print("All ACHOO API endpoints passed.")
print("Pharmacist review required before any medication change.")