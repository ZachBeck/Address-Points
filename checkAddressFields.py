import arcpy
import re

blankVals = ['', ' ', None]

def dirCheck(dir):
    dirList = ['N', 'S', 'E', 'W', 'NORTH', 'SOUTH', 'EAST', 'WEST',\
               'North', 'South', 'East', 'West', ' ', '', None]

    if dir in blankVals:
        return ''
    else:
        if dir.strip() not in dirList:
            return '[Bad pre/suf direction]'
        else:
            return ''


def checkAddNum(addNum):
    if addNum == None:
        return '[Bad address number]'
    elif addNum.isdigit() is False:
        return '[Bad address number]'
    else:
        return ''


def checkStreetType(sType):

    sTypeList = {'ALY', 'ALLEY', 'AVE', 'AVENUE', 'BAY', 'BND', 'BEND', 'BLVD', 'BOULEVARD', 'CYN', 'CANYON', \
                 'CTR', 'CENTER', 'CIR', 'CIRCLE', 'COR', 'CORNER', 'CT', 'COURT', 'CV', 'COVE', 'CRK', 'CREEK', \
                 'CRES', 'CRESCENT', 'XING', 'CROSSING', 'DR', 'DRIVE', 'EST', 'ESTATE', 'ESTS', 'ESTATES', \
                 'EXPY', 'EXPRESSWAY', 'FLT', 'FLAT', 'FRK', 'FORK', 'FWY', 'FREEWAY', 'GLN', 'GLEN', 'GRV', 'GROVE', \
                 'HTS', 'HEIGHTS', 'HWY', 'HIGHWAY', 'HL', 'HILL', 'HOLW', 'HOLLOW', 'JCT', 'JUNCTION', 'LN', 'LANE', \
                 'LOOP', 'MNR', 'MANOR', 'MDW', 'MEADOW', 'PARK', 'PKWY', 'PARKWAY', 'PASS', 'PL', 'PLACE', 'PLZ', \
                 'PLAZA', 'PT', 'POINT', 'RAMP', 'RNCH', 'RANCH', 'RDG', 'RIDGE', 'RD', 'ROAD', 'RTE', 'ROUTE', \
                 'ROW', 'RUN', 'SQ', 'SQUARE', 'ST', 'STREET', 'TER', 'TERRACE', 'TRCE', 'TRACE', 'TRL', 'TRAIL', \
                 'VW', 'VIEW', 'VLG', 'VILLAGE', 'WY', 'WAY', ' ', '', None}

    if sType != None:
        if sType.strip() not in sTypeList:
            return '[Bad Street Type]'
        else:
            return ''
    else:
        return ''


def createStreetDict(cofips):
    global rdDict
    rdDict = {}
    sgid10 = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde'
    roadsFC = sgid10 + '\\SGID10.TRANSPORTATION.Roads'
    sql = """"COFIPS" = '{}'""".format(cofips)
    roadsFL = arcpy.MakeFeatureLayer_management(roadsFC, 'roadsFL', sql)

    #rdFlds = ['STREETNAME', 'ZIPRIGHT']
    rdFlds = ['STREETNAME', 'ADDR_SYS']

    with arcpy.da.SearchCursor(roadsFL, rdFlds) as sCursor:
        for row in sCursor:
            rdName = row[0]
            key = row[1]

            if key not in rdDict:
                rdDict[key] = list()
            rdDict[key].append(rdName)


def countyRoadList(cofips):
    global countyRdList
    countyRdList = []
    sgid10 = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde'
    roadsFC = sgid10 + '\\SGID10.TRANSPORTATION.Roads'
    sql = """"COFIPS" = '{}'""".format(cofips)
    roadsFL = arcpy.MakeFeatureLayer_management(roadsFC, 'roadsFL', sql)
    rdFlds = ['STREETNAME']

    with arcpy.da.SearchCursor(roadsFL, rdFlds) as sCursor:
        for row in sCursor:
            rdName = row[0]
            set(countyRdList.append(rdName))


def flagDuplicates(addressPts, objectID, addsysFld, fullAddFld, flagFld):
    addDict = {}
    with arcpy.da.SearchCursor(addressPts, [objectID, addsysFld, fullAddFld]) as sCursor:
        empty = [None, '', ' ']
        for row in sCursor:
            if row[1] and row[2] not in empty:
                addKey = '{} {}'.format(row[1], row[2])
                objectid = row[0]

                if addKey not in addDict:
                    addDict[addKey] = list()
                addDict[addKey].append(objectid)

    with arcpy.da.UpdateCursor(addressPts, [objectID, addsysFld, fullAddFld, flagFld]) as uCursor:
        for row in uCursor:
            addKey = '{} {}'.format(row[1], row[2])

            if addKey in addDict:
                if len(addDict[addKey]) > 1:
                    row[3] = '{} {}'.format(row[3], '[Duplicate address]')
                    uCursor.updateRow(row)



def checkStreetName(sName, key):  # key can be either zip or addSys
    errorList = [None, '', ' ', '00']

    if sName in errorList:
        return '[Street name error]'
    if key in rdDict:
        if sName.strip() not in rdDict[key]:
            return '[Possible street name or add sys error]'
    if re.match(r'.*[%\$\^\*\@\!\?\&\~\#\*\_\(\)\:\;\'\"\{\}\[\]].*', sName):
        return '[Street name error]'
    else:
        return ''
