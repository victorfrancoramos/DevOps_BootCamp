import requests
import time
import json
import texttable as tt
import settings_config as cfg
import yaml
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def login(req, base_url, username, password):
    print("Getting token...")

    header = {"content-type": "application/json"}

    # We get domain, audience and clientId required for the authentication payload
    r = req.get(url="https://occm.demo.netapp.com:443/occm/api/occm/system/support-services", headers=header,
                verify=False)

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


def get_k8s_clusters(req, token):
    # We add the token to the header and issue a GET command to extract the k8s clusters already registered in OCCM
    hed = {'Authorization': 'Bearer ' + token}
    s = req.get(url="https://occm.demo.netapp.com/occm/api/k8s/clusters", headers=hed, verify=False)

    # We format the output making use of the texttable library
    ctr = 0
    clusters = s.json()
    tab = tt.Texttable()
    header = ['K8s cluster name', 'clusterEndpoint', 'k8sVersion', 'tridentVersion']
    tab.header(header)
    tab.set_cols_align(['c', 'c', 'c', 'c'])
    for i in clusters:
        ctr = ctr + 1
        clus = i['clusterName']
        cep = i['clusterEndpoint']
        ver = i['k8sVersion']
        trid = i['tridentVersion']
        row = [clus, cep, ver, trid]
        tab.add_row(row)
        tab.set_cols_align(['c', 'c', 'c', 'c'])
    print("K8s clusters in the OCCM instance:{}".format(ctr))
    setdisplay = tab.draw()
    print(setdisplay)


def post_k8s_cluster(req, kubeconfig, contextname, token):
    print("Registering K8s cluster => ", contextname)

    payload = {"k8sconfig": kubeconfig, "contextNames": [contextname]}
    header_save = {"content-type": "application/json", 'Authorization': 'Bearer ' + token}
    b = req.post(url="https://occm.demo.netapp.com/occm/api/k8s/save", json=payload, headers=header_save, verify=False)
    print(b.text)


def install_trident(req, k8sCluster, ontapcluster, ips, token):
    # We get the kubernetes cluster id and workingenvironment id of the clusters passed in the arguments
    header_get = {"content-type": "application/json", 'Authorization': 'Bearer ' + token}
    r = req.get(url="https://occm.demo.netapp.com/occm/api/k8s/clusters", headers=header_get, verify=False)

    response = r.json()

    k8sClusterId = "0"
    for i in response:
        if i["clusterName"] == k8sCluster:
            k8sClusterId = i["publicId"]
    print(k8sClusterId)
    if k8sClusterId != "0":

        r = req.get(url="https://occm.demo.netapp.com/occm/api/working-environments", headers=header_get, verify=False)

        response2 = r.json()

        workingEnvironmentId = "0"
        for i in response2["onPremWorkingEnvironments"]:
            if i["name"] == ontapcluster:
                workingEnvironmentId = i["publicId"]

        if workingEnvironmentId != "0":
            header = {"content-type": "application/json", 'Authorization': 'Bearer ' + token}
            payload = {"ips": [ips], "setDefaultStorageClass": "true", "setSanDefaultStorageClass": "false"}
            url_trident = cfg.base_url + "/k8s/connect-on-prem/" + k8sClusterId + "/" + workingEnvironmentId
            print(url_trident)
            b = req.post(url=url_trident, json=payload, headers=header, verify=False)
            print("Instalando Trident en k8s cluster ", k8sCluster, "...")
            time.sleep(5)

        else:
            print("workingenvironment non existent =>", ontapcluster)
    else:
        print("k8s cluster non existent => ", k8sCluster)


def main():
    # Opening session
    s = requests.Session()
    # Calling login function to authenticate and get the token
    token = login(s, cfg.base_url, cfg.username, cfg.password)

    # Opening kubeconfig local file and storing it as yaml dump
    with open(cfg.kube_config_local) as file:
        kcl = yaml.load(file, Loader=yaml.FullLoader)
    kubeconfig_local = yaml.dump(kcl)

    # Registering K8s local cluster in OCCM
    post_k8s_cluster(s, kubeconfig_local, cfg.k8s_local_context_name, token)

    # Opening kubeconfig remote file and storing it as yaml dump
    with open(cfg.kube_config_remote) as file:
        kcr = yaml.load(file, Loader=yaml.FullLoader)
    kubeconfig_remote = yaml.dump(kcr)

    # Registering K8s remote cluster in OCCM
    post_k8s_cluster(s, kubeconfig_remote, cfg.k8s_remote_context_name, token)

    # Installing Trident in K8s local cluster
    install_trident(s, "k8s1-onPrem", "onPrem", "192.168.0.0/24", token)

    # Installing Trident in K8s remote cluster
    install_trident(s, "k8s2-remote", "remote", "192.168.0.0/24", token)

    print("Verifyng OCCM registration...")
    time.sleep(10)
    # Listing kubernetes clusters linked to OCCM
    get_k8s_clusters(s, token)


### Main program
main()
