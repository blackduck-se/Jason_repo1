#!/usr/bin/env python3

import os
import pprint
import requests
import argparse
import string
import random
from random import choice
import nltk
from nltk.corpus import wordnet
from nltk.corpus import words
import sys

def generate_random_project_name():
    english_words = words.words()
    return '-'.join(choice(english_words) for _ in range(2))

def check_project_exists(project_name, existing_projects):
    return project_name in existing_projects

def get_project_branches(project_id, api_url, headers):
    response = requests.get(f"{api_url}srm/x/projects/{project_id}/branches", headers=headers)
    if response.status_code == 200:
        branches = response.json()

        for branch in branches:
            if branch.get("isDefault") is True:
                default_branch = branch.get("name")
                break

        return branches, default_branch
    else:
        print('Failed to retrieve project branches, with status code: '+str(response.status_code))
        return {}    

def get_existing_projects(api_url, headers):
    response = requests.get(f"{api_url}srm/api/projects", headers=headers)
    if response.status_code == 200:
        projects = response.json()['projects']
        return {project['name']: project['id'] for project in projects}
    else:
        print('Failed to retrieve projects, with status code: '+str(response.status_code))
        return {}
    
def create_project(api_url, project_name, headers):
    response = requests.post(f"{api_url}srm/api/projects", json={'name': project_name}, headers=headers)
    if response.status_code == 201:
        print(f'{project_name} created successfully.')
        return response.json()['id']
    else:
        print('Failed to create project. Status code: '+str(response.status_code))
        print('Failed to create project Name: '+ project_name)
        return None

def start_analysis(api_url, headers, project_id, branch_name, file_path):
    jsonBody= {
            "projectId": project_id
    }
    response = requests.post(f"{api_url}srm/api/analysis-prep",json=jsonBody, headers=headers)
    if response.status_code == 200:
        resp = response.json()
        prep_id = resp["prepId"]
        print(f"Got PrepId {prep_id} for analysis run")
    else:
        print('ERROR: Failed to get analysis-prep, with status code: '+str(response.status_code)+" error message: "+ response.text)
        return None
        
    if branch_name is not None or branch_name != "":
        # first get the branches and default branch:
        branches, default_branch = get_project_branches(project_id,api_url,headers)

        # check if branch already exists:
        existing_branch = False
        for branch in branches:
            if branch_name.lower() == branch.get("name").lower():
                existing_branch = True
                break
            
        if existing_branch is True:
            print(f'Branch {branch_name} already exists, running analysis on existing branch.')
            jsonBody = {"branch": branch_name }
        else:
            print(f'Branch {branch_name} does not exist, creating new branch {branch_name} from the project default branch: {default_branch}.')
            jsonBody = {"branch":{"parent": default_branch, "name": branch_name }}

        branch_request = requests.put(f"{api_url}srm/x/analysis-prep/{prep_id}/branch",json=jsonBody, headers=headers)
    
    if branch_request.status_code != 200:
        print('ERROR: Failed to set project branch for analysis, with status code: '+str(branch_request.status_code)+" error message: "+ branch_request.text)
        return None
    else:
        print(f"Successfully set branch for analysis.") 
        #print(f"{str(branch_request.status_code)} error message: {branch_request.text}") 

    # upload file for analysis
    print(f"Uploading file...")
    with open(file_path, 'r') as file:
        content = file.read()
        # add appropriate headers to request:
        upload_response = requests.post(f'{api_url}srm/api/analysis-prep/{prep_id}/upload', files={'file': content}, headers=headers)

    if upload_response.status_code == 202:
        print('File uploaded successfully.')
    else:
        print(f'ERROR: Failed to upload file with response code {str(upload_response.status_code)} error message: {upload_response.text}')
        return None

    # Run analysis:
    run_analysis = requests.post(f"{api_url}srm/api/analysis-prep/{prep_id}/analyze", headers=headers)
    if run_analysis.status_code == 202:
        analysis_response = run_analysis.json()
        jobId = analysis_response["jobId"]
        analysis_id = analysis_response["analysisId"]
        print(f"Successfully started analysis on project id {project_id}, jobId: {jobId} analysisId: {analysis_id}")
        return analysis_response
    else:
        print(f"ERROR: Failed to start analysis on project id: {project_id}"+str(run_analysis.status_code)+" error message: "+ run_analysis.text)

def upload_file(file_path, api_url, project_id, headers):
    with open(file_path, 'rb') as file:
        response = requests.post(f"{api_url}srm/api/projects/{project_id}/analysis", files={'file': file}, headers=headers)
    if response.status_code == 202:
        print('File uploaded successfully.')
    else:
        print(f'ERROR: Failed to upload file with response code {str(response.status_code)} error message: {response.text}')

def main(apiKey, api_url, project_name, file_path, branch_name=None):
    headers = {'Authorization': 'Bearer ' + apiKey}
    # add trailing slash to srm url if needed:
    if not api_url.endswith("/"):
        api_url += "/"
    
    existing_projects = {k.lower(): v for k, v in get_existing_projects(api_url, headers).items()}
    if project_name is None:
        project_name = generate_random_project_name()
        project_id = create_project(api_url, project_name, headers)
    elif project_name.lower() not in existing_projects:
        project_id = create_project(api_url, project_name, headers)
    else:
        project_id = existing_projects[project_name.lower()]

    if project_id is not None and (branch_name is None or branch_name == ""):
        upload_file(file_path, api_url, project_id, headers)
    else:
        start_analysis(api_url, headers, project_id, branch_name, file_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file_path', help='Path to the .xml file')
    parser.add_argument('project_name', nargs='?', default=os.environ.get('SRM_PROJECT_NAME'), help='SRM project name')
    parser.add_argument('branch_name', default=None, required=False ,help='Optional, project branch name')
    parser.add_argument('--url', default=os.environ.get('SRM_URL'), help='URL for SRM')
    parser.add_argument('--api_key', default=os.environ.get('SRM_API_KEY'), help='API key for authentication')
    args = parser.parse_args()

    main(args.api_key, args.url, args.project_name, args.file_path)
    