import sys, os
sys.path.insert(0, os.path.abspath('backend'))
from fastapi.testclient import TestClient
from main import app
from config import JWT_SECRET, JWT_ALGORITHM
from jose import jwt

# Generate token for Super Admin (user_id = 1)
token = jwt.encode({"sub": "1", "email": "kedar@azad.org"}, JWT_SECRET, algorithm=JWT_ALGORITHM)

client = TestClient(app)
resp = client.get("/api/ak-dashboard/charts", headers={"Authorization": f"Bearer {token}"})
print("Status code:", resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print("Has state_outreach:", "state_outreach" in data, len(data.get("state_outreach", [])))
    print("Has centre_outreach:", "centre_outreach" in data, len(data.get("centre_outreach", [])))
    print("Has batch_outreach:", "batch_outreach" in data, len(data.get("batch_outreach", [])))
    print("\nState outreach data:")
    for r in data.get("state_outreach", []):
        print(" ", r)
else:
    print("Response error:", resp.text[:500])
