#!/usr/bin/env python3

import sys
# setting path so we can include functions from the srmPost python file.
sys.path.append('../')
import argparse
import os
import convert_mast_results
import srmPost

def get_mast_results(location):
  file = ""
  return file

def main(sourcePath, srmProjectName, projectBranchName, srmURL, srmAPIKey):
  # Convert the data to SRM XML Format
  print(f"Converting {sourcePath} to SRM XML format...")
  importFile = "sourceSRMXML.xml"
  detection_methods = convert_mast_results.createSRMXML(sourcePath, importFile)

  # add detection methods, if needed
  if detection_methods != []:
    headers = {'Authorization': 'Bearer ' + srmAPIKey}
    # add trailing slash to srm url if needed:
    if not srmURL.endswith("/"):
        srmURL += "/"  
    for method in detection_methods:
      srmPost.create_detection_method(srmURL, method, headers)

  # Push the results to SRM
  if projectBranchName is None or projectBranchName == "":
    print(f"Uploading results to {srmURL} project {srmProjectName}...")
  else:
    print(f"Uploading results to {srmURL} Project: {srmProjectName} Branch: {projectBranchName}...")    
  srmPost.main(srmAPIKey, srmURL, srmProjectName, importFile, projectBranchName)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('sourcePath', help='Location of the MAST json results file to be imported into SRM.')
  parser.add_argument('--srmProjectName', default=os.environ.get('SRM_PROJECT_NAME'), help='Name of the project in SRM to import the results to, if the project does not exist it will be created. If not provided, the value of the SRM_PROJECT_NAME environment variable is used.')
  parser.add_argument('--srmURL', default=os.environ.get('SRM_URL'), help='SRM URL to import the results to. If not provided, the value of the SRM_URL environment variable is used.')
  parser.add_argument('--srmAPIKey', default=os.environ.get('SRM_API_KEY'), help='The SRM API Key used to authenticate to SRM. If not provided, the value of the SRM_API_KEY environment variable is used.')
  parser.add_argument('--projectBranchName', default=os.environ.get('SRM_PROJECT_BRANCH_NAME'), required=False ,help='Optional, SRM project branch name to run the analysis on, if the branch does not currently exist, if will be created with the default branch as the parent. If not provided, the value of the SRM_PROJECT_BRANCH_NAME environment variable is used if that is not set the default project branch will be used.')


  args = parser.parse_args()

  if not args.sourcePath or not args.srmProjectName or not args.srmURL or not args.srmAPIKey:
    parser.print_help()
  else:     
    main(args.sourcePath, args.srmProjectName, args.projectBranchName, args.srmURL, args.srmAPIKey)
