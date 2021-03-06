# -*- coding: cp1252 -*-
# Source kindly shared by Jose Gomez @NetApp
import requests as req
import settings_config as cfg

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def login(req, base_url, username, password):
    print("Getting token...")

    header = {"content-type": "application/json"}

    ss_url = base_url + "/occm/api/occm/system/support-services"
    # We get domain, audience and clientId required for the authentication payload
    r = req.get(url=ss_url, headers=header, verify=False)

    response = r.json()
    print("domain: ", response["portalService"]["auth0Information"]["domain"])
    domain = response["portalService"]["auth0Information"]["domain"]
    print("audience: ", response["portalService"]["auth0Information"]["audience"])
    audience = response["portalService"]["auth0Information"]["audience"]
    print("clientId: ", response["portalService"]["auth0Information"]["clientId"])
    clientId = response["portalService"]["auth0Information"]["clientId"]

    auth_url = "https://" + domain + "/oauth/token"

    auth_payload = {"grant_type": "password", "username": username, "password": password, "audience": audience,
                    "scope": "profile", "client_id": clientId}

    # We issue a POST command to get the token
    a = req.post(url=auth_url, json=auth_payload, headers=header, verify=False)

    response = a.json()
    token = response["access_token"]

    return token


def get_current_user(req, token):
    hed = {'Authorization': 'Bearer ' + token}
    cuser_url = cfg.base_url + "/occm/api/auth/current-user"
    s = req.get(url=cuser_url, headers=hed, verify=False)
    response = s.json()
    print("Current user RESPONSE: ", response)


def main():
    s = req.Session()
    token = login(s, cfg.base_url, cfg.username, cfg.password)
    get_current_user(s,token)


### Main program
main()
