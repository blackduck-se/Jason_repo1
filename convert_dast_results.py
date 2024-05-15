#!/usr/bin/env python3

from datetime import datetime
import json
import os
import requests
import argparse
import base64
from random import choice
import pprint
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from email.parser import BytesParser
import xml.dom.minidom

def getLinkData(url, apiKey):
  headers = {'Api-token': apiKey}
  response = requests.get(f"{url}", headers=headers)

  if response.status_code == 200:
    return base64.b64decode(response.text)
  else:
    print("ERROR: Failed to retrieve request response details")
    return ""


def createSRMXML(inputFile,outputFile,apiKey):
  toolName="fAST-DAST"
  # Load JSON data
  with open(inputFile, 'r', encoding='utf-8') as f:
    json_data = json.load(f)
  
  #Load Issues
  issues = json_data.get("_items", [0])
  #pprint.pprint(issues, compact=True)

  # Ensure the vulnerabilities data is a list
  if not isinstance(issues, list):
      raise ValueError("No Issues Found In the Input File.")  
  else:
    print(f"Converting issues to SRM XML format...")

  # Create a new root element 'report' with 'date' and 'tool' attributes
  report = ET.Element('report', date=datetime.now().strftime('%Y-%m-%d'), tool=toolName)
  findings = ET.SubElement(report, 'findings')

  # Loop through issues and populate the SRM findings field
  for issue in issues:
    # Get all top level info:
    findingCategory="Security"
    nativeToolId=issue.get("id")
    toolCode=issue.get("type").get("name")
    nativeToolName=issue.get("type").get("_localized").get("name")
    otherDetails=issue.get("type").get("_localized").get("otherDetail")

    # get all info in otherDetails:
    description=""
    remediation=""
    additionalInfo=""
    #get data from "other details section"
    for detail in otherDetails:
      if detail.get("key") == 'description':
        description = detail.get("value")
      elif detail.get("key") == 'remediation':
        remediation = detail.get("value")
      elif detail.get("key") == "additional-information":
        additionalInfo = detail.get("value")
    
    # get data from attributes section
    severity=""
    cweID=""
    methodType=""
    locationPath=""
    locationQuery=""
    overallScore=""
    scores=""
    attackScope=""
    attackTarget=""
    version=""
    attributes = issue.get("attributes")
    for attribute in attributes:
      if attribute.get("key") == "severity":
        severity = attribute.get("value")
      elif attribute.get("key") == "cwe":
        cweID = attribute.get("value"," - ")
        # just get ID number
        cweID = cweID.split("-")[1]
      elif attribute.get("key") == "method":
        methodType = attribute.get("value") 
      elif attribute.get("key") == "location":
        locationPathParsed = attribute.get("value")
        locationPathParsed = urlparse(locationPathParsed)
        locationPath = locationPathParsed.path
        if locationPathParsed.query != "":
          locationQuery = locationPathParsed.query
      elif attribute.get("key") == "evidence":
        # just store the evidence data for now, we will dynamically write the XML later
        evidenceData = attribute.get("value")
      elif attribute.get("key") == "attack-scope":
        attackScope = attribute.get("value")
      elif attribute.get("key") == "attack-target":
        attackTarget = attribute.get("value")
      elif attribute.get("key") == "overall-score":
        overallScore = attribute.get("value")
      elif attribute.get("key") == "version":
        version = attribute.get("value")   
      elif attribute.get("key") == "scores":
        scores = attribute.get("value")

    # Now that we have all the data lets build the XML finding
    finding = ET.SubElement(findings, 'finding', severity=severity, type='dynamic')
    tool = ET.SubElement(finding, 'tool', name=toolName, category=findingCategory, code=toolCode)
    cwe = ET.SubElement(finding, 'cwe', id=cweID)
    nativeTool = ET.SubElement(finding, 'native-id', name=nativeToolName, value=nativeToolId)
    descriptionXML = ET.SubElement(finding, 'description', format='html', include_in_hash='false')
    # add additional items to description
    if remediation != "":
      description+="<br><br><h3>Remediation:</h3><br>"+remediation
    if overallScore != "":
      description+="<br><br><h3>Overall Score:</h3><br>"+str(overallScore)
    if scores != "":
      description+="<br><br><h3>Scores:</h3><br>"+scores
    descriptionXML.text = description
    location = ET.SubElement(finding, 'location', type='url', path=locationPath)
    variants = ET.SubElement(location, 'variants')

    # Loop through evidence and add variants to xml
    for evidence in evidenceData:
      variant_element = ET.SubElement(variants, 'variant')
      bodyText = evidence.get("attack").get("payload","")
      links = evidence.get("_links")
      # loop through links here:
      for link in links:
        if link.get("rel") == "request":
          # Create the request element with method, path, and query attributes
          rr_element = ET.Element('request', method=link.get("method", ''), path=locationPath, query=locationQuery)
          headerText = getLinkData(link.get("href"),apiKey).decode("utf-8")
          header_element = ET.SubElement(rr_element, 'headers')
          header_element.text = headerText
          body_element = ET.SubElement(rr_element, 'body', truncated="false", original_length=str(len(bodyText)),length=str(len(bodyText))) 
          body_element.text = base64.b64encode(bodyText.encode()).decode()
          #print(body_element.text)
          variant_element.append(rr_element)
        elif link.get("rel") == "response":
          # get data from polaris
          linkText = getLinkData(link.get("href"),apiKey)
          # Extract headers and body from text since Polaris puts it in one big blob
          parser = BytesParser()
          message = parser.parsebytes(linkText)
          headers = str(message).split('\n\n',1)[0]
          body = str(message).split('\n\n',1)[1]
          originalBodyLength=str(len(body))
          body= base64.b64encode(body.encode()).decode()
          # get response code
          resp_code = headers.split('\n')[1].split(" ")[1]
          rr_element = ET.Element("response", code=resp_code)
          header_element = ET.SubElement(rr_element, 'headers')
          header_element.text = headers
          body_element = ET.SubElement(rr_element, 'body', truncated="false", original_length=originalBodyLength,length=str(len(body)))               
          body_element.text = body
          variant_element.append(rr_element)
      
    # Parse the 'report' element instead of the 'root' element
    dom = xml.dom.minidom.parseString(ET.tostring(report, 'utf-8'))
    pretty_xml_as_string = dom.toprettyxml()
    # Write XML to file
    with open(outputFile, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_as_string)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--inputFileName', help='Name of the json export to be converted to SRM XML format')
  parser.add_argument('--outputFileName', default="srm-output.xml", help='Name of the SRM XML output file.')
  parser.add_argument('--polarisAPIKey', default=os.environ.get('POLARIS_API_KEY'), help='Polaris API Key, Used to retrieve request/response details.')
  args = parser.parse_args()

  if not args.inputFileName or not args.outputFileName:
    parser.print_help()
  else:
    outputFile = args.outputFileName
    inputFile = args.inputFileName
    apiKey = args.polarisAPIKey
    createSRMXML(inputFile,outputFile, apiKey)
