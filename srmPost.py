#!/usr/bin/env python3

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

def upload_file(file_path, api_url, project_id, headers):
    with open(file_path, 'rb') as file:
        response = requests.post(f"{api_url}srm/api/projects/{project_id}/analysis", files={'file': file}, headers=headers)
    if response.status_code == 202:
        print('File uploaded successfully.')
    else:
        print('Failed to upload file.')
        print(response.text)
        print(response.status_code)

def main(apiKey, api_url, project_name, file_path):
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

    if project_id is not None:
        upload_file(file_path, api_url, project_id, headers)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file_path', help='Path to the .xml file')
    parser.add_argument('project_name', nargs='?', default=None, help='SRM project name')
    parser.add_argument('--url', help='URL for SRM')
    parser.add_argument('--api_key', required=True, help='API key for authentication')
    args = parser.parse_args()

    main(args.api_key, args.url, args.project_name, args.file_path)
    