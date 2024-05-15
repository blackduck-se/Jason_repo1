#!/usr/bin/env python3

import argparse
import os
import pull_dast_results
import convert_dast_results
import srmPost

def main(sourceProjectName, sourceURL, sourceAPIKey, srmProjectName, srmURL, srmAPIKey):
  # first pull the results
  exportFile = "sourceExport.json"
  pull_dast_results.main(sourceURL, sourceProjectName, exportFile, sourceAPIKey)

  # Second, convert the data to SRM XML Format
  importFile = "sourceSRMXML.xml"
  convert_dast_results.createSRMXML(exportFile, importFile, sourceAPIKey)

  # Finally, push the results to SRM
  srmPost.main(srmAPIKey, srmURL, srmProjectName, importFile)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--sourceProjectName', default=os.environ.get('POLARIS_PROJECT_NAME'), help='Name of the project Name from the source system (system of origin)')
  parser.add_argument('--sourceURL', default=os.environ.get('POLARIS_URL'), help='URL of the source system (system of origin)')
  parser.add_argument('--sourceAPIKey', default=os.environ.get('POLARIS_API_KEY'), help='API Key to pull results from the source system, Used to retrieve request/response details.')
  parser.add_argument('--srmProjectName', help='Name of the existing, or to be created SRM project name.')
  parser.add_argument('--srmURL', default=os.environ.get('SRM_URL'), help='SRM URL to import the results to.')
  parser.add_argument('--srmAPIKey', default=os.environ.get('SRM_API_KEY'), help='SRM API Key')

  args = parser.parse_args()

  if not args.sourceProjectName or not args.sourceURL or not args.sourceAPIKey or not args.srmURL or not args.srmAPIKey:
    parser.print_help()
  else:
    if args.srmProjectName is None:
      args.srmProjectName = args.sourceProjectName
      
    main(args.sourceProjectName, args.sourceURL, args.sourceAPIKey, args.srmProjectName, args.srmURL, args.srmAPIKey)
