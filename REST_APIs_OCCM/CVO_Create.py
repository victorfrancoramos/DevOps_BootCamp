# -*- coding: cp1252 -*-
# Source kindly shared by Jose Gomez @NetApp

import requests
import settings_config as cfg

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def login(req, base_url, username, password):
    print("Getting token...")

    header = {"content-type": "application/json"}

    url_ss = base_url + "/occm/system/support-services"
    # We get domain, audience and clientId required for the authentication payload
    r = req.get(url=url_ss, headers=header, verify=False)

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


def create_cvo_aws(req, payload, token):
    hed = {'Authorization': 'Bearer ' + token}
    url = cfg.base_url + "/vsa/working-environments"
    s = req.post(url=url, json=payload, headers=hed, verify=False)

    print(s.text)


def main():
    s = requests.Session()
    token = login(s, cfg.base_url, cfg.username, cfg.password)
    payload = {"name": "CVO_DevOps",
               "volume": {
                   "exportPolicyInfo": {
                       "policyType": "custom",
                       "ips": ["0.0.0.0/0"]
                   },
                   "snapshotPolicyName": "default",
                   "name": "Test_API",
                   "enableThinProvisioning": True,
                   "enableDeduplication": True,
                   "enableCompression": True,
                   "size": {
                       "size": 10,
                       "unit": "GB"
                   }
               },
               "tenantId": "workspace-integ",
               "region": "eu-west-1",
               "packageName": "aws_poc",
               "dataEncryptionType": "NONE",
               "vsaMetadata": {
                   "ontapVersion": "ONTAP-9.6X28.T1",
                   "licenseType": "cot-explore-paygo",
                   "instanceType": "m5.xlarge"
               },
               "saasSubscriptionId": "subs1",
               "writingSpeedState": "NORMAL",
               "subnetId": "subnet-6",
               "svmPassword": "passwd",
               "vpcId": "vpc-4",
               "ontapEncryptionParameters": None,
               "ebsVolumeType": "gp2",
               "ebsVolumeSize": {
                   "size": 500,
                   "unit": "GB",
                   "_identifier": "500 GB"
               },
               "awsTags": [],
               "optimizedNetworkUtilization": False,
               "instanceTenancy": "default",
               "iops": None,
               "cloudProviderAccount": "CloudProviderAccount-gfKR9Swu",
               "backupVolumesToCbs": False,
               "enableCompliance": True
               }

    create_cvo_aws(s, payload, token)


### Main program
main()