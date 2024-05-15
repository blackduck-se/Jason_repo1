#!/usr/bin/env python3

import json
import os
import requests
import argparse
import sys
import pprint

def getPortfolioId(api_url,headers):
    endpoint="/api/portfolio/portfolios"
    response = requests.get(f"{api_url}/{endpoint}", headers=headers)
    statusCode=response.status_code

    if statusCode == 200:
        # parse the response
        portfolioID = response.json()["_items"][0]["id"]
    else:
      print("ERROR: Failed to retrieve portfolio id, http request failed with code: "+ statusCode)
      sys.exit(2)

    return portfolioID

def getPortfolioItemId(api_url,headers,portfolioID,projectName):
    endpoint=f"/api/portfolio/portfolios/{portfolioID}/portfolio-items?_filter=name=={projectName}&_limit=10"
    response = requests.get(f"{api_url}/{endpoint}", headers=headers)
    statusCode=response.status_code

    if statusCode == 200:
        # parse the response
        #pprint.pprint(response.json(), compact=True)
        portfolioItemID = response.json()["_items"][0]["id"]
    else:
      print("ERROR: Failed to retrieve project id, http request failed with code: "+ statusCode)
      sys.exit(2)

    return portfolioItemID

def getPortfolioSubItemId(api_url,headers,portfolioItemID):
    endpoint=f"/api/portfolio/portfolio-items/{portfolioItemID}/portfolio-sub-items"
    response = requests.get(f"{api_url}/{endpoint}", headers=headers)
    statusCode=response.status_code

    portfolioSubItemID=""

    if statusCode == 200:
      # parse the response
      # find the DAST subitem
      entries = response.json()['_items']
      for entry in entries:
        if entry["subItemType"] == "DAST":
            portfolioSubItemID = entry["id"]
    else:
      print(f"ERROR: Failed to retrieve DAST SubItem, http request failed with code: {statusCode}")
      sys.exit(2)

    if portfolioSubItemID=="":
      print(f"ERROR: Failed to retrieve DAST SubItem from portfolio ID: {portfolioItemID}, no DAST subItem found, are you sure there are DAST results associated with this projectName?")

    return portfolioSubItemID

def getIssues(api_url, headers, portfolioSubItemID, exportFile):
    endpoint=f"/api/specialization-layer-service/issues/_actions/list?portfolioSubItemId={portfolioSubItemID}&testId=latest&_first=500&_includeAttributes=true"
    response = requests.get(f"{api_url}/{endpoint}", headers=headers)
    statusCode=response.status_code

    if statusCode == 200:
      # parse the response, we only want the issues not all the other stuff
      issues = response.json()
      #pprint.pprint(response.json(), compact=True)
      print("Writing issue json file...")
      with open(exportFile, 'w', encoding='utf-8') as f:
        json.dump(issues, f, ensure_ascii=False, indent=4)
    else:
      print(f"ERROR: Failed to retrieve DAST Issues, http request failed with code: {statusCode}, ERROR MESSAGE: ")
      pprint.pprint(response.json(), compact=True)
      sys.exit(2)

    print(f"Successfully wrote {exportFile}")

def main(api_url, projectName, exportFile, apiKey):
  headers = {'Api-token': apiKey}
  # get portfolio ID
  portfolioID = getPortfolioId(api_url, headers)
  print("Portfolio ID: "+portfolioID)
  # get project ID
  portfolioItemID = getPortfolioItemId(api_url,headers, portfolioID, projectName)
  print("Portfolio Item ID: "+portfolioItemID)

  # get projects (or as Polaris calls them SubPortfolioItemIDs)
  dastSubItemID = getPortfolioSubItemId(api_url, headers, portfolioItemID)
  print("Portfolio DAST SubItem ID: "+ dastSubItemID)

  dastIssues = getIssues(api_url, headers, dastSubItemID, exportFile)   

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--fileName', help='Name of the json export, include a path if you want do not want it in the current directory')
  parser.add_argument('--projectName', nargs='?', default=os.environ.get('POLARIS_PROJECT_NAME'), help='Polaris project name')
  parser.add_argument('--url', default=os.environ.get('POLARIS_URL'), help='Polaris URL')
  parser.add_argument('--apiKey', default=os.environ.get('POLARIS_API_KEY'), help='API key for authentication to polaris')
  args = parser.parse_args()

  api_url = args.url
  projectName = args.projectName
  exportFile = args.fileName
  apiKey = args.apiKey

  main(api_url, projectName, exportFile, apiKey)
