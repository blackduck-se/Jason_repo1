#!/usr/bin/env python3

from datetime import datetime
import json
import os
import argparse
import pprint
import xml.etree.ElementTree as ET
import xml.dom.minidom

def mapSeverity(nativeSeverity):
  nativeSeverity = nativeSeverity.lower()
  if nativeSeverity == "low" or nativeSeverity == "medium" or nativeSeverity == "high" or nativeSeverity == "critical":
    return nativeSeverity
  elif nativeSeverity == "minimal":
    return "info"
  else:
    return "unspecified"
  
def add_string(list, value):
    if value not in list:
        list.append(value)

def createSRMXML(inputFile,outputFile):
  # Load JSON data
  with open(inputFile, 'r', encoding='utf-8') as f:
    json_data = json.load(f)
  
  detection_methods = []
  # Tool name used for the findings to be imported into SRM
  toolName=json_data.get("generatedBy","tort")
  # Using end date of the json output for test date
  testDate = json_data.get("metadata").get("endDate")
  # Not currently used
  testType = json_data.get("metadata").get("testType")
  # Not currently used
  versionNumber=json_data.get("metadata").get("versionNumber")
  # Not currently used
  applicationType=json_data.get("metadata").get("applicationType")
  # Currently used for finding location, if fixLocation is blank
  packageName=json_data.get("metadata").get("packageName")
  
  #Load individual issues from the json output.
  issues = json_data.get("findings")

  # Ensure the vulnerabilities data is a list, throw error if no findings are found
  if not isinstance(issues, list):
      raise ValueError("Issues Found In the Input File.")  
  else:
    print(f"Converting issues to SRM XML format...")

  # Create a new root element 'report' with 'date' and 'tool' attributes
  report = ET.Element('report', date=testDate, tool=toolName)
  findings = ET.SubElement(report, 'findings')

  # Loop through issues and populate the SRM findings field
  for issue in issues:
    # Get all top level info:
    # QUESTION: Just set finding category to "Security"
    findingCategory="Security" 
    nativeToolId=str(issue.get("identifier","")) #
    toolCode=issue.get("name","") #
    notes = issue.get("note","")

    # QUESTION: these results don't really associate a "name" or "finding type" so for now I'm using the risk type
    nativeToolName=issue.get("risk",[]).get("type","")
    description=issue.get("description", "") #
    remediation=issue.get("remediation", "") #
    stepsToReproduce=issue.get("stepsToReproduce", "")
    
    # we should probably use methodType for this:
    foundByMethod = issue.get("foundBy")
    
    # get severity from risk section, if unpopulated return "unspecified"
    severity=mapSeverity(issue.get("risk").get("severity", "unspecified"))

    cweID=issue.get("cweId","")
    # TORT results can sometimes contain multiple cwe's in a single issue
    cweList= cweID.split(",")
    methodType=issue.get("foundBy","")
    # add detection method to list:
    if methodType != "":
      add_string(detection_methods, methodType)

    # Will be used if populated for location
    fixLocation=issue.get("fixLocation","")
    # Not currently used
    systemic=issue.get("systemic","")
    likelihoodDescription=issue.get("likelihoodDescription","")
    impactDescription=issue.get("impactDescription","")
    pciInfo = False
    pciDetails=issue.get("pciDetails","")
    pciId=issue.get("pciId","")
    pciDesc=issue.get("pciDesc","")
    if pciId == "N/A":
      pciId = ""
    if pciDetails != "" or pciId != "" or pciDesc != "":
      pciInfo = True
    
    riskObject=issue.get("risk",[])

    # These are not currently used
    flawCount=issue.get("flawCount","")
    cweIdFlawName=issue.get("cweIdFlawName","")
    cweIdCategory=issue.get("cweIdCategory","")
    owasp16CODE=issue.get("owasp16CODE","")
    cvdId=issue.get("cvdId","")
    itrc=issue.get("itrc","")
    appscanTitle=issue.get("appscanTitle","")
    status=issue.get("status","")
    retestScope=issue.get("retestScope","")
    isUpdated=issue.get("isUpdated","")


    # just store the instance data for now, we will map this to "evidence" in SRM and dynamically write the XML later
    # I need more info here since all the instance data in my example are blank.
    instances = issue.get("instances",[])   
    urls = []
    for instance in instances:
      urls.append(instance.get("url",""))
  



    # Now that we have all the data lets build the XML finding
    finding = ET.SubElement(findings, 'finding', severity=severity, type=methodType)
    tool = ET.SubElement(finding, 'tool', name=toolName, category=findingCategory, code=toolCode)
    

    for cw in cweList:
      cwe = ET.SubElement(finding, 'cwe', id=cw)
    
    nativeIDKey=toolName.upper()+" Finding ID"
    nativeTool = ET.SubElement(finding, 'native-id', name=nativeIDKey, value=nativeToolId)
    descriptionXML = ET.SubElement(finding, 'description', format='html', include_in_hash='false')
    # add additional items to description
    description = "<h3>Description:</h3>"+description
    if remediation != "":
      description+="<br><br><h3>Remediation:</h3>"+remediation
    if stepsToReproduce != "":
      description+="<br><br><h3>Steps to Reproduce:</h3>"+str(stepsToReproduce)
    if notes != "":
      description+="<br><br><h3>Notes:</h3>"+notes      
    if likelihoodDescription != "":
      description+="<br><br><h3>Likelihood:</h3>"+likelihoodDescription
    if pciInfo != False:
      description+="<br><br><h3>PCI Info:</h3>"
      if pciDetails != "":
        description+="PCI Details:"+pciDetails +"<br>"
      if pciId != "":
        description+="PCI ID: "+pciId+"<br>"
      if pciDesc != "":
        description+="PCI Description: "+pciDesc+"<br>"
    if impactDescription != "":
      description+="<br><br><h3>Impact Description:</h3>"+impactDescription        
    if riskObject is not None:
        description+="<br><br><h3>Risk:</h3>Impact: "+riskObject.get("impact","N/A")+"<br>Likelihood: "+riskObject.get("likelihood","N/A")+"<br>Classification: "+riskObject.get("classification","N/A")+"<br>Type: "+riskObject.get("type","N/A")+"<br>Severity: "+riskObject.get("severity","N/A")+"<br>Priority: "+str(riskObject.get("priority","N/A"))


    descriptionXML.text = description
    pathToIssue=""
    issueType="file"

    if fixLocation == "":
      pathToIssue = packageName
    else:
      pathToIssue = fixLocation

    # if pathToIssue is still blank, then we need to look at the URLs extracted from above
    if pathToIssue == "":
      for url in urls:
        pathToIssue += url +"," 
      # trim last ,
      pathToIssue = pathToIssue[:-1]

    if "https" in pathToIssue:
      issueType="url"
      

    location = ET.SubElement(finding, 'location', type=issueType, path=pathToIssue)
    # variants = ET.SubElement(location, 'variants')

    # # Loop through instances and add variants to xml
    # I need more info here since all the instance data in my example are blank.    
    # for evidence in instances:
    #   variant_element = ET.SubElement(variants, 'variant')
    #   bodyText = "N/A"
    #   links = evidence.get("_links")
    
    
    # Parse the 'report' element instead of the 'root' element
    dom = xml.dom.minidom.parseString(ET.tostring(report, 'utf-8'))
    pretty_xml_as_string = dom.toprettyxml()
    # Write XML to file
    with open(outputFile, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_as_string)

  # return list of detection methods to add to SRM if needed
  return detection_methods

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--inputFileName', help='Name of the json export to be converted to SRM XML format')
  parser.add_argument('--outputFileName', default="srm-output.xml", help='Name of the SRM XML output file.')
  args = parser.parse_args()

  if not args.inputFileName or not args.outputFileName:
    parser.print_help()
  else:
    outputFile = args.outputFileName
    inputFile = args.inputFileName
    createSRMXML(inputFile,outputFile)
