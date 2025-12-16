import os
import uuid
import requests


def main():
    auth_key = os.getenv("GIGACHAT_BASIC_AUTH")
    auth_url = (
        os.getenv("GIGACHAT_AUTH_URL")
        or os.getenv("GIGACHAT_AUTH")
        or "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    )
    scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

    print("AUTH_URL =", auth_url)
    print("AUTH_KEY present =", bool(auth_key))
    if not auth_key:
        print("Missing GIGACHAT_BASIC_AUTH in environment")
        return

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {auth_key}",
    }
    data = f"scope={scope}&grant_type=client_credentials"

    try:
        resp = requests.post(auth_url, headers=headers, data=data, timeout=30, verify=False)
        print("STATUS:", resp.status_code)
        print("BODY:", resp.text[:1000])
    except Exception as exc:
        print("EXCEPTION:", type(exc).__name__, exc)


if __name__ == "__main__":
    main()

