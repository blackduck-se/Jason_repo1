#!/usr/bin/env python3

import json
import os
import pprint
import requests
import argparse
import sys
from srmPost import get_existing_projects, create_project


def get_project_id(api_url, headers, srmProjectName):
    print(f"Checking if {srmProjectName} exists...")
    existing_projects = {k.lower(): v for k, v in get_existing_projects(api_url, headers).items()}
    if srmProjectName.lower() not in existing_projects:
        print(f"{srmProjectName} does not exists, creating new project...")
        return create_project(api_url, srmProjectName, headers)
    else:
        print(f"{srmProjectName} found...")
        return existing_projects[srmProjectName.lower()]

def get_addin_tool_id(api_url, headers, tool_name):
    response = requests.get(f"{api_url}srm/x/admin/addin-tools", headers=headers)
    if response.status_code != 200:
        print("ERROR: Failed to create add-in tool, HTTP Response: " + str(response.status_code))
        print("ERROR: Error Message: " + response.text)
    else:
        print("Successfully retrieved list of tool ids")
        data=response.json()
        for item in data:
            if tool_name.lower() == item.get('name').lower():
                print("Found add in tool: "+tool_name)
                return item.get('id')
        return "-1"

def create_addin_tool(api_url, headers, tool_name):  
    scanRequestFile = open("scan_request_file.txt", 'r').read()
    jsonBody={
        "id":"",
        "name":tool_name,
        "acceptedTags":[],
        "toolDeclaration": scanRequestFile
        }
    response = requests.post(f"{api_url}srm/x/admin/addin-tools",  json=jsonBody, headers=headers)
    if response.status_code != 200:
        print("ERROR: Failed to create add-in tool, HTTP Response: " + str(response.status_code))
        print("ERROR: Error Message: " + response.text)
    else:
        print("Successfully created add in tool")
        return response.json()['id']

def add_project_secret(srmURL, headers, secretValue, projectId, secretName="polariskey", secretKey="apikey"):
    # first check to make sure secret doesn't already exist
    response = requests.get(f"{srmURL}srm/x/toolservice/secrets/{projectId}", headers=headers)
    secretId="-1"
    if response.status_code != 200:
        print("ERROR: Failed to get project secrets, HTTP Response: " + str(response.status_code))
        print("ERROR: Error Message: " + response.text)
    else:
        data=response.json()
        for secret in data:
            if secretName.lower() == secret.get('name').lower():
                print("Found secret")
                return secret.get('name')
    if secretId=="-1":
        # create new secret
        jsonBody = {
            "name": secretName,
            "fields": [
                {
                "key": secretKey,
                "value": secretValue,
                "isSensitive": True
                }
            ]
        }
        response = requests.post(f"{srmURL}srm/x/toolservice/secrets/{projectId}", json=jsonBody, headers=headers)
        if response.status_code != 200:
            print("ERROR: Failed to create project secret, HTTP Response: " + str(response.status_code))
            print("ERROR: Error Message: " + response.text)
        else:
            print("Successfully created project secret")
            return secretName       


def configure_tool_service(srmURL, headers, projectId, toolId, polarisApiKey, polarisURL, polarisProjectName):
    # Add project secret
    secretId = add_project_secret(srmURL, headers, polarisApiKey, projectId)

    # Add tool configuration
    tomlConfig=f"[polaris]\nproject=\"{polarisProjectName}\"\nurl=\"{polarisURL}\""
    jsonBody = {
        "newContent": tomlConfig,
        "allowedSecrets": [ secretId ],
        "isEnabled": True
    }
    response = requests.post(f"{srmURL}srm/x/toolservice/addin-tools/{projectId}/{toolId}", json=jsonBody, headers=headers)
    if response.status_code != 200:
        print("ERROR: Failed to configure tool configuration for project: "+str(projectId)+", HTTP Response: " + str(response.status_code))
        print("ERROR: Error Message: " + response.text)
    else:
        print("Successfully configured tool config for project: "+str(projectId))

def main(apiKey, srmURL, polarisProjectName, srmProjectName, polarisURL, addInToolName, polarisApiKey):
    headers = {'Authorization': 'Bearer ' + apiKey}

    # add trailing slash to srm url if needed:
    if not srmURL.endswith("/"):
        srmURL += "/"
    
    # Configure add in tool if it doesn't already exist
    toolId = get_addin_tool_id(srmURL, headers, addInToolName)
    if toolId == "-1":
        print("Creating add in tool...")
        toolId = create_addin_tool(srmURL, headers, addInToolName)

    # Check if SRM project name exists, if not create it
    project_id = get_project_id(srmURL, headers, srmProjectName)

    configure_tool_service(srmURL, headers, project_id, toolId, polarisApiKey, polarisURL, polarisProjectName)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--polarisURL', default=os.environ.get('POLARIS_URL'), help='Path to the .xml file')
    parser.add_argument('--polarisProjectName', default=os.environ.get('POLARIS_PROJECT_NAME'), help='Polaris project name to to pull DAST results from')
    parser.add_argument('--polarisApiKey', default=os.environ.get('POLARIS_API_KEY'), help='Polaris API Key')    
    parser.add_argument('--srmProjectName', default=None, help='SRM project name to create or add configuration to, if left blank the Polaris Project name will be used')
    parser.add_argument('--srmURL', default=os.environ.get('SRM_URL'), help='URL for SRM')
    parser.add_argument('--apiKey', default=os.environ.get('SRM_API_KEY'), help='SRM API key for authentication')
    parser.add_argument('--addInToolName', default="Polaris DAST", help='Name of the add in tool to create, or assign to the project if it already exists')
    args = parser.parse_args()

    srmProjectName = ""
    if args.srmProjectName is None:
        srmProjectName = args.polarisProjectName
    else:
        srmProjectName = args.srmProjectName
        
    main(args.apiKey, args.srmURL, args.polarisProjectName, srmProjectName, args.polarisURL, args.addInToolName, args.polarisApiKey)
