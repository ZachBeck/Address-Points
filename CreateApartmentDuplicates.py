import arcpy
import re
import agrc
from agrc import parse_address


def addBaseAddress(inAddressPoints):
    def returnEmptyIfNull(word):
        if word == None:
            word = ''
        return word

    baseAddList = []
    allAddsDict = {}

    addressCoordDict = {}
    addressAttributeDict = {}

    flds = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType',
            'SuffixDir', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State', 'PtType', 'AddSource', 
            'LoadDate', 'Status', 'USNG', 'SHAPE@XY']
    hwy_exceptions = ['OLD HWY 89']

    with arcpy.da.SearchCursor(inAddressPoints, flds) as sCursor:
        for row in sCursor:
            stripStr = ' {} {}'.format(row[9], row[10])
            if '#' in row[1]:
                stripStr = ' # {}'.format(row[10])
            baseAdd = re.sub(stripStr, '', row[1])
            baseAddList.append(baseAdd)
            allAddsDict.setdefault(row[1])

        baseAddSet = set(baseAddList)

        sCursor.reset()
        for row in sCursor:
            stripStr = ' {} {}'.format(row[9], row[10])
            if '#' in row[1]:
                stripStr = ' # {}'.format(row[10])
            baseAdd = re.sub(stripStr, '', row[1])

            if baseAdd in baseAddSet and baseAdd not in allAddsDict:
                addCoords = addressCoordDict.setdefault(baseAdd, [])
                addCoords.append(row[20])
                addAttributes = addressAttributeDict.setdefault(baseAdd, [])
                addAttributes.extend([row[0], row[11], row[12], row[13], row[15], row[17], row[19]])

    iCursror = arcpy.da.InsertCursor(inAddressPoints, flds)

    for key, value in addressCoordDict.items():
        if len(value) < 2:
            continue
        else:
            if key in addressAttributeDict:
                count = len(value)
                addSys = addressAttributeDict[key][0]
                utAddPtID = key
                fullAdd = utAddPtID.split('|')[1].rstrip('#').strip()
                address = parse_address.parse(fullAdd)
                addNum = returnEmptyIfNull(address.houseNumber)
                addNumSuf = returnEmptyIfNull(address.houseNumberSuffix)
                preDir = returnEmptyIfNull(address.prefixDirection)
                sName = returnEmptyIfNull(address.streetName)
                sufDir = returnEmptyIfNull(address.suffixDirection)
                sType = returnEmptyIfNull(address.suffixType)
                if sName[:2].isdigit():
                    sType = ''
                if sName.isdigit() == False:
                    sufDir = ''
                city = addressAttributeDict[key][1]
                zip = addressAttributeDict[key][2]
                county = addressAttributeDict[key][3]
                state = 'UT'
                ptType = 'BASE ADDRESS'
                addSrc = 'AGRC'
                loadDate = addressAttributeDict[key][5]
                usng = addressAttributeDict[key][6]
                coords = value
                xSum = 0
                ySum = 0
                for coord in coords:
                    x = coord[0]
                    y = coord[1]
                    xSum = xSum + x
                    ySum = ySum + y

                xCoord = xSum / count
                yCoord = ySum / count
                xyCoord = [xCoord, yCoord]

                iCursror.insertRow((addSys, utAddPtID, fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '',\
                                    city, zip, county, state, ptType, addSrc, loadDate, 'COMPLETE', usng, xyCoord))


