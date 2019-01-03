import arcpy
import datetime, time
import sys
import re
import os
import agrc
import CreateApartmentDuplicates

from arcpy import env
from agrc import parse_address
from CreateApartmentDuplicates import addBaseAddress
from DeleteDuplicatePoints import deleteDuplicatePts
from CreateErrorPts import createErrorPts
from ReturnDuplicateAddresses import returnDuplicateAddresses
from ReturnDuplicateAddresses import updateErrorPts


global sgid10, agrcAddFLDS, errorList

sgid10 = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde'

today = str(datetime.datetime.today().strftime("%m/%d/%Y"))

agrcAddFLDS = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', \
               'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State', \
               'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'LoadDate', 'Status', 'Editor', \
               'ModifyDate', 'StreetAlias', 'Notes', 'USNG', 'SHAPE@']

dirs = {'N': ['N', 'NORTH', 'NO'], 'S': ['S', 'SOUTH', 'SO'], 'E': ['E', 'EAST', 'EA'], 'W': ['W', 'WEST', 'WE']}
dirs2 = {'N':'NORTH', 'S':'SOUTH', 'E':'EAST', 'W':'WEST'}
longDirs = {'NORTH', 'SOUTH', 'EAST', 'WEST'}

sTypeDir = {'ALY':'ALLEY', 'AVE':'AVENUE', 'BAY':'BAY', 'BND':'BEND', 'BLVD':'BOULEVARD', 'CYN':'CANYON', \
            'CTR':'CENTER', 'CIR':'CIRCLE', 'COR':'CORNER', 'CT':'COURT', 'CV':'COVE', 'CRK':'CREEK', \
            'CRES':'CRESCENT', 'XING':'CROSSING', 'DR':'DRIVE', 'EST':'ESTATE', 'ESTS':'ESTATES', \
            'EXPY':'EXPRESSWAY', 'FLT':'FLAT', 'FRK':'FORK', 'FWY':'FREEWAY', 'GLN':'GLEN', 'GRV':'GROVE', \
            'HTS':'HEIGHTS','HWY':'HIGHWAY', 'HL':'HILL', 'HOLW':'HOLLOW', 'JCT':'JUNCTION', 'LN':'LANE', \
            'LNDG':'LANDING', 'LOOP':'LOOP', 'MNR':'MANOR','MDW':'MEADOW', 'MDWS':'MEADOWS', 'PARK':'PARK', 'PKWY':'PARKWAY', \
            'PASS':'PASS', 'PL':'PLACE', 'PLZ':'PLAZA', 'PT':'POINT', 'RAMP':'RAMP', 'RNCH':'RANCH', 'RDG':'RIDGE', \
            'RD':'ROAD', 'RTE':'ROUTE', 'ROW':'ROW', 'RUN':'RUN', 'SQ':'SQUARE', 'ST':'STREET', \
            'TER':'TERRACE', 'TRCE':'TRACE', 'TRL':'TRAIL', 'VW':'VIEW', 'VLG':'VILLAGE', 'WAY':['WY','WAY']}

sTypeList = {'ALY', 'AVE', 'BAY', 'BND', 'BLVD', 'CYN', 'CTR', 'CIR', 'COR', 'CT', 'CV', 'CRK', 'CRES', 'XING', \
             'DR', 'EST', 'ESTS', 'EXPY', 'FLT', 'FRK', 'FWY', 'GLN', 'GRV', 'HTS','HWY', 'HL', 'HOLW', 'JCT', \
             'LN', 'LNDG', 'LOOP', 'MNR','MDW', 'MDWS', 'PARK', 'PKWY', 'PASS', 'PL', 'PLZ', 'PT', 'RAMP', 'RNCH', \
             'RDG', 'RD', 'RTE', 'ROW', 'RUN', 'SQ', 'ST', 'TER', 'TRCE', 'TRL', 'VW', 'VLG', 'WAY'}

addNumSufList = ['1/8', '1/4', '1/3', '1/2', '2/3', '3/4', 'A', 'B', 'C', 'D', 'E', 'F']

unitTypeDir = {'APT':'APARTMENT', 'BSMT':'BASEMENT', 'BLDG':'BUILDING', 'DEPT':'DEPARTMENT', 'FL':['FLOOR', 'FLR'],\
               'FRNT':'FRONT', 'HNGR':'HANGAR', 'KEY':'KEY', 'LBBY':'LOBBY', 'LOT':'LOT', 'LOWR':'LOWER', 'OFC':'OFFICE', \
               'PH':'PENTHOUSE', 'PIER':'PIER', 'REAR':'REAR', 'RM':'ROOM', 'SIDE':'SIDE', 'SLIP':'SLIP', \
               'SPC':['SP', 'SPACE'], 'STOP':'STOP', 'STE':'SUITE', 'TRLR':['TRAILER', 'TRL'], 'UNIT':'UNIT', 'UPPR':'UPPER'}

unitTypeList = ['APT', 'APARTMENT', 'BSMT', 'BASEMENT', 'BLDG', 'BUILDING', 'DEPT', 'DEPARTMENT', 'FL', 'FLOOR', 'FLR',\
               'FRNT', 'FRONT', 'HNGR', 'HANGAR', 'KEY', 'KEY', 'LBBY', 'LOBBY', 'LOT', 'LOWR', 'LOWER', 'OFC', 'OFFICE', \
               'PH', 'PENTHOUSE', 'PIER', 'REAR', 'RM', 'ROOM', 'SIDE', 'SLIP', 'SPC', 'SP', 'SPACE', 'STOP', 'STE', \
                'SUITE', 'TRLR', 'TRAILER', 'TRL', 'UNIT', 'UPPR']


noUnitIds = ['BSMT', 'FRNT', 'LBBY', 'LOWR', 'OFC', 'PH', 'REAR', 'SIDE', 'UPPR']

errorList = [None, False, 'None', '<Null>', 'NULL', '', ' ', '#', '####', '--', '.', '~', '-?', '--?', '?', '0', \
             '00', 0, '??0', '0 STREET', '*', 'Unknown', 'UNKNOWN', '09-0000-01', ',ILLER']

leadingSpaceTypes = []
for t in sTypeDir:
    leadingSpaceTypes.append(' {}'.format(t))
    leadingSpaceTypes.append(' STREET')

def replaceByDictionary(string, dict):
    for i in dict:
        if i in string:
            return string.replace(i, dict[i])
    return string

def checkWord(word, d):
    for key, value in d.iteritems():
        if word in value:
            return key
    # if nothing is found
    return ''

def returnKey(word, d):
    if word == None:
        word = ''
    word = word.upper()
    for key, value in d.iteritems():
        if word == '':
            return ''
        if word == key:
            return key
        if type(value) is str:
            if word == value:
                return key
        else:
            for v in value:
                if word == v:
                    return key
    return ''

def removeBadValues(word, badVals):
    if word in badVals:
        word = ''
    if word == None:
        word = ''
    return word.upper().strip()

def addNone(word, badVals):
    if word in badVals:
        word = None
    return word

def removeNone(word):
    if word == None:
        word = ''
    return word

def formatValues(word, inValues):
    removeBadValues(word, errorList)
    if word != None:
        if word.upper().strip() in inValues:
            return word.upper().strip()
        return ''
    return ''

def formatUnitID(unitID):
    if unitID != None:
        unitID = unitID.strip()
        if unitID.startswith('#') is True:
            if unitID[1] != ' ':
                return '{} {}'.format(unitID[0], unitID.strip('#')).upper()
            return unitID
        elif unitID.startswith('#') is False:
            if unitID not in errorList:
                return '# ' + unitID.upper()
            return unitID
    return ''

def formatAddressNumber(addNum):
    removeBadValues(addNum, errorList)
    addNum.strip()
    if addNum.startswith('0'):
        addNum = addNum.lstrip('0')
    return addNum

def removeDuplicateWords(words):
    slist = words.split()
    return " ".join(sorted(set(slist), key=slist.index))

def truncateOldCountyPts(inPts):
    pointCount = int(arcpy.GetCount_management(inPts).getOutput(0))
    if pointCount > 0:
        arcpy.TruncateTable_management(inPts)
        print 'Deleted {} points in {}'.format(pointCount, inPts)
    else:
        print 'No points to delete'

def splitVals(word, list):
    if word == None:
        return ('', '')
    srch = re.compile('|'.join(list))
    match = re.match(srch, word)

    if match != None:
        v1 = match.group()
        v2 = word.strip(v1).strip()
        sVals = (v1, v2)
        return sVals
    else:
        return ('' , word)

def returnStart(str, startList):
  for s in startList:
    if str.startswith(s):
      return s

def returnEnd(str, endList):
  for s in endList:
    if str.endswith(s):
      return s

def createRoadSet(countyNumber):
    sgidRds = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde\SGID10.TRANSPORTATION.Roads'
    rdFlds = ['COUNTY_L', 'NAME', 'POSTTYPE']
    rdList = []

    with arcpy.da.SearchCursor(sgidRds, rdFlds) as sCursorRds:
        for rowRd in sCursorRds:
            if rowRd[0] == countyNumber and rowRd[1] != '':
                rdList.append(rowRd[1].upper())
    countyRdNameSet = set(rdList)
    return countyRdNameSet



def beaverCounty():
    beaverCoAddPts = r'C:\ZBECK\Addressing\Beaver\BeaverCounty.gdb\Address_pts'
    agrcAddPts_beaverCo = r'C:\ZBECK\Addressing\Beaver\Beaver.gdb\AddressPoints_Beaver'
    cntyFldr = r'C:\ZBECK\Addressing\Beaver'

    beaverCoAddFLDS = ['Address_', 'Prefix', 'St_Name', 'Dir_Type', 'Unit_Num', 'Grid', 'SHAPE@']

    checkRequiredFields(beaverCoAddPts, beaverCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_beaverCo)

    errorPtsDict = {}

    iCursor = arcpy.da.InsertCursor(agrcAddPts_beaverCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(beaverCoAddPts, beaverCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] not in errorList:
                addNum = row[0]
                preDir = formatValues(row[1], dirs)
                sufDir = formatValues(row[3].upper(), dirs)
                sType = formatValues(row[3].upper(), sTypeDir)
                sName = row[2].upper().replace('HIGHWAY', 'HWY')
                if sName.endswith((' N', ' S', ' E', ' W')):
                    sufDir = sName.split()[1]
                    sType = ''
                    sName = sName.split()[0]

                if row[3].upper() == 'TR':
                    sType = 'TRL'

                unitID = removeBadValues(row[4], errorList)
                if unitID != '':
                    unitID_hash = '# ' + unitID
                else:
                    unitID_hash = ''

                addSys = row[5].upper()
                shp = row[6]

                fullAdd = '{} {} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType, unitID_hash)
                fullAdd = ' '.join(fullAdd.split())

                utPtID = '{} | {}'.format(addSys, fullAdd)

                if sufDir == '' and sType == '' and 'HWY' not in sName:
                    addressErrors = errorPtsDict.setdefault(fullAdd, [])
                    addressErrors.extend(['missing street type', row[6]])
                if preDir != '' and preDir == sufDir:
                    addressErrors = errorPtsDict.setdefault(fullAdd, [])
                    addressErrors.extend(['predir = sufdir', row[6]])

                iCursor.insertRow((addSys, utPtID, fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '',\
                                   '', unitID, '', '', '49001', 'UT', '', '', '', '', 'BEAVER COUNTY', today,\
                                   'COMPLETE', '', None, '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'Beaver_ErrorPts.shp', 'Address', beaverCoAddPts)

    del iCursor

    intersectPolyDict = {'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
                         'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
                         'USNG': ['SGID10.INDICES.NationalGrid', 'USNG']}

    addPolyAttributes(sgid10, agrcAddPts_beaverCo, intersectPolyDict)
    addBaseAddress(agrcAddPts_beaverCo)
    deleteDuplicatePts(agrcAddPts_beaverCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def boxElderCounty():
    boxelderCoAddPts = r'C:\ZBECK\Addressing\BoxElder\BoxElderCounty.gdb\Address_Points'
    agrcAddPts_boxelderCo = r'C:\ZBECK\Addressing\BoxElder\BoxElder.gdb\AddressPoints_BoxElder'
    cntyFldr = r'C:\ZBECK\Addressing\BoxElder'

    boxelderCoAddFLDS = ['FullAddr', 'HouseNum', 'PreDir', 'StreetName', 'StreetType', 'SufDir', 'UnitNumber', 'UnitType', 'City', \
                         'ZipCode', 'Parcel_ID', 'Structure', 'COMPLEX_NA', 'Use_Classi', 'last_edited_date', 'SHAPE@']

    useDict = {'AGR':'Agricultural', 'COM':'Commercial', 'EDU':'Education', 'GOV':'Government', 'MED':'Other', 'RES':'Residential',\
              'MHU':'Residential', 'MOB':'Residential', 'REL':'Other', 'VAC':'Vacant'}

    excludeUnit = ['UPSTAIRS', 'UP', 'MANAGER', 'DOWNSTAIRS', 'DOWN', 'CLUB', 'BASEMENT']

    checkRequiredFields(boxelderCoAddPts, boxelderCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_boxelderCo)

    errorPtsDict = {}

    iCursor = arcpy.da.InsertCursor(agrcAddPts_boxelderCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(boxelderCoAddPts, boxelderCoAddFLDS) as sCursor:
        for row in sCursor:

            addNum = removeBadValues(row[1], errorList)
            if addNum != '' and row[3] not in errorList:
                addSys = ''

                if ' ' in addNum:
                    addNumSuf = addNum.split()[1]
                    addNum = addNum.split()[0]
                else:
                    addNumSuf = ''

                preDir = removeBadValues(row[2], errorList)
                sName = row[3]

                if row[4] in errorList:
                    sType = ''
                else:
                    sType = row[4].strip()

                sufDir = removeBadValues(row[5], errorList)
                if sType != '':
                    sufDir = ''

                if row[6] not in errorList:
                    unitNum = row[6].strip().upper()
                    if unitNum not in excludeUnit:
                        fullAddUnitNum = unitNum
                else:
                    unitNum = ''
                    fullAddUnitNum = ''

                if row[7] not in errorList:
                    unitType = unitTypeDir[row[7]]
                    unitTypeAbrv = row[7]
                else:
                    unitType = ''
                    unitTypeAbrv = ''

                if fullAddUnitNum != '' and unitType == '':
                    fullAddUnitNum = ''

                city = ''
                zip = row[9]
                parcelID = row[10]
                structure = removeBadValues(row[11], errorList)
                building = removeBadValues(row[12], errorList)

                if row[13] in useDict:
                    ptType = useDict[row[13]]
                elif row[13] in errorList:
                    ptType = ''
                else:
                    ptType = row[13]

                addSource = 'BOX ELDER COUNTY'
                modDate = row[14]
                loadDate = today
                shp = row[15]

                fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sType, sufDir, unitTypeAbrv, fullAddUnitNum)
                fullAdd = ' '.join(fullAdd.split())

    #-----------Create Error Points-----------
                if preDir == sufDir and sType == '':
                    addressErrors = errorPtsDict.setdefault(fullAdd, [])
                    addressErrors.extend(['predir = sufdir', row[15]])
                if row[3] not in row[0]:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[3], row[0]), [])
                    addressErrors.extend(['StreetName not in FullAddr', row[15]])

                iCursor.insertRow((addSys, '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', building, unitTypeAbrv,\
                                   unitNum, city, zip, '49003', 'UT', '', ptType, structure, parcelID, addSource, loadDate, \
                                   'COMPLETE', '', modDate, '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'BoxElder_ErrorPts.shp', 'Address', boxelderCoAddPts)

    del iCursor
    del sCursor


    inputDict = {'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
                 'USNG':['SGID10.INDICES.NationalGrid', 'USNG'],
                 'City': ['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],}

    addPolyAttributes(sgid10, agrcAddPts_boxelderCo, inputDict)
    addBaseAddress(agrcAddPts_boxelderCo)
    deleteDuplicatePts(agrcAddPts_boxelderCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def cacheCounty():
    cacheCoAddPts = r'C:\ZBECK\Addressing\Cache\CacheCounty.gdb\CacheAddressPoints'
    agrcAddPts_cacheCo = r'C:\ZBECK\Addressing\Cache\Cache.gdb\AddressPoints_Cache'
    cntyFldr = r'C:\ZBECK\Addressing\Cache'

    cacheCoAddFLDS = ['addsystem', 'fulladd', 'addnum', 'addnumsuffix', 'prefixdir', 'streetname', 'streettype', 'suffixdir', \
                      'landmarkname', 'building', 'unittype', 'unitid', 'ptlocation', 'pttype', 'structure', 'parcelid', \
                      'addsource', 'last_edited_date', 'last_edited_user', 'SHAPE@']

    flrDict = {'BSMT':['FLR BSMT','FLR BMST', 'FLR BSMT EAST', 'FLR BSMT RIGHT', 'FLR BSMT S', 'FLR DWNSTRS'], \
               'REAR':['FLR REAR'], 'UPPR':['FLR UPPER', 'FLR UPSTRS', 'FLR UPSTRS; APT 1', 'UPSTRS'],
               'FRNT':['FR', 'FRONT'], 'OFC':['OFFICE'], 'RM':['ROOM']}

    cacheTypesDict = {'ALY':'ALLEY', 'AVE':'AVENUE', 'BAY':'BAY', 'BND':'BEND', 'BLVD':'BOULEVARD', 'CYN':'CANYON', \
            'CTR':'CENTER', 'CIR':'CIRCLE', 'COR':'CORNER', 'CT':'COURT', 'CV':'COVE', 'CRK':'CREEK', \
            'CRES':'CRESCENT', 'XING':'CROSSING', 'DR':'DRIVE', 'EST':'ESTATE', 'ESTS':'ESTATES', \
            'EXPY':'EXPRESSWAY', 'FLT':'FLAT', 'FRK':'FORK', 'FWY':'FREEWAY', 'GLN':'GLEN', 'GRV':'GROVE', \
            'HTS':'HEIGHTS','HWY':'HIGHWAY', 'HL':'HILL', 'HOLW':'HOLLOW', 'JCT':'JUNCTION', 'LN':'LANE', \
            'LNDG':'LANDING', 'LOOP':['LP', 'LOOP'], 'MNR':'MANOR','MDW':'MEADOW', 'MDWS':'MEADOWS', 'PARK':'PARK', \
            'PKWY':'PARKWAY', 'PASS':'PASS', 'PL':'PLACE', 'PLZ':'PLAZA', 'PT':'POINT', 'RAMP':'RAMP', 'RNCH':'RANCH', \
            'RDG':'RIDGE', 'RD':'ROAD', 'RTE':'ROUTE', 'ROW':'ROW', 'RUN':'RUN', 'SQ':'SQUARE', 'ST':'STREET', \
            'TER':'TERRACE', 'TRCE':'TRACE', 'TRL':'TRAIL', 'VW':'VIEW', 'VLG':'VILLAGE', 'WAY':'WAY'}


    checkRequiredFields(cacheCoAddPts, cacheCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_cacheCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49005')

    iCursor = arcpy.da.InsertCursor(agrcAddPts_cacheCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(cacheCoAddPts, cacheCoAddFLDS) as sCursor:
        for row in sCursor:

            addnum = removeBadValues(row[2], errorList)
            sName = removeBadValues(row[5], errorList)
            building = ''

            if addnum not in errorList and sName not in errorList and row[0] != 'Franklin County':
                preDirSrc = removeBadValues(row[4], errorList)
                if len(preDirSrc) <= 2:
                    predir = returnKey(preDirSrc.strip(), dirs)
                else:
                    continue

                addnumsuf = removeBadValues(row[3], errorList)

                for a in addNumSufList:
                    if len(addnum) > 2:
                        if ' {}'.format(a) in addnum:
                            addnumsuf = a
                            addnum = addnum.strip(' {}'.format(addnumsuf))
                            if '-' in addnum:
                                if addnum.split('-')[1] == row[9]:
                                    addnumsuf = ''
                                    building = 'BLDG {}'.format(row[9])
                                addnum = addnum.split('-')[0]
                        if '.5' in addnum:
                            addnumsuf = '1/2'
                            addnum = addnum.split('.')[0]

                modTypes = removeNone(row[6])
                sType = returnKey(modTypes.strip(), cacheTypesDict)
                sufdir = formatValues(row[7], dirs)

                if sName == 'US 91':
                    sName = 'HWY 91'

                if sName.isdigit() == False:
                    sufdir = ''
                if sName.isdigit() == True:
                    sType = ''

                if predir == sType and sName != 'BOULEVARD':
                    continue

                landName = removeBadValues(row[8], errorList)

                unitType = returnKey(row[10], unitTypeDir)
                unitId_src = removeBadValues(row[11], errorList)
                unitId_src = str(unitId_src).translate(None, '#()').strip()
                if unitType not in noUnitIds and unitId_src == '':
                    unitType = ''
                if len(unitId_src) < 14:
                    if ';' in unitId_src:
                        if unitId_src.split(';')[0].startswith('BLDG'):
                            building = unitId_src.split(';')[0]
                            unitType = unitId_src.split()[2]
                            unitId = unitId_src.split()[3]
                    elif unitId_src.startswith('BLDG'):
                        building = unitId_src
                        unitId = ''
                    elif unitId_src.startswith('FLR'):
                        if unitId_src == 'FLR MAIN':
                            unitType = 'FL'
                            unitId = 'MAIN'
                        else:
                            unitId = returnKey(unitId_src.strip('FLR '), flrDict)
                    elif len(unitId_src.split()) > 1:
                        if returnKey(unitId_src.split()[0], flrDict) != '':
                            unitType = returnKey(unitId_src.split()[0], flrDict)
                            if unitId_src.split()[-1].isdigit():
                                unitId = unitId_src.split()[-1]
                    elif returnKey(unitId_src, flrDict) != '':
                        unitId = returnKey(unitId_src, flrDict)
                        if len(unitId_src.split()) > 1:
                            if unitId_src.split()[-1].isdigit():
                                unitId = unitId_src.split()[-1]
                    else:
                        unitId = unitId_src
                else:
                    unitId = ''

                parcelId = removeBadValues(row[15], errorList)
                addSrc = removeBadValues(row[16], errorList)
                modDate = row[17]
                loadDate = today
                editor = removeBadValues(row[18], errorList)
                shp = row[19]

                if sName == 'BOULEVARD':
                    sType = 'ST'

                if unitType != '' and unitId == '':
                    unitType = ''

                if unitType == '' and unitId != '' and unitId not in flrDict:
                    fullAdd = '{} {} {} {} {} {} {} {} # {}'.format(addnum, addnumsuf, predir, sName, sType, sufdir, building, unitType, unitId)
                    fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = '{} {} {} {} {} {} {} {} {}'.format(addnum, addnumsuf, predir, sName, sType, sufdir, building, unitType, unitId)
                    fullAdd = ' '.join(fullAdd.split())

    #--------------Create Error Points--------------
                if sName != '' and sName[0].isdigit() == True and sName[-1].isdigit() == False:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[1],row[5]), [])
                    addressErrors.extend(['bad street name', row[19]])
                if 'HWY' not in sName and sName not in rdSet:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[1],row[5]), [])
                    addressErrors.extend(['street name not in roads', row[19]])
                # if sName.isdigit() == False and sType == '' and 'HWY ' not in sName and 'SR ' not in sName and 'US ' not in sName:
                #     addressErrors = errorPtsDict.setdefault(row[1], [])
                #     addressErrors.extend(['no street type', row[19]])
                if sName not in row[1].strip():
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[1], row[5]), [])
                    addressErrors.extend(['mixed street names', row[19]])
                if predir == sufdir and sType == '':
                    addressErrors = errorPtsDict.setdefault('{} | {} | {}'.format(row[1], row[4], row[7]), [])
                    addressErrors.extend(['predir = sufdir', row[19]])
                if row[6] != 'LP' and removeNone(row[6]).strip() not in cacheTypesDict and row[6] not in errorList:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[1], row[6]), [])
                    addressErrors.extend(['bad street type', row[19]])


                iCursor.insertRow(('', '', fullAdd, addnum, addnumsuf, predir, sName, sType, sufdir, landName, building, unitType, unitId, '',\
                                   '', '49005', 'UT', '', '', '', parcelId, 'Cache County', loadDate, 'COMPLETE', editor, modDate, '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'Cache_ErrorPts.shp', cacheCoAddFLDS[1], cacheCoAddPts)

    del sCursor
    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_cacheCo, inputDict)
    addBaseAddress(agrcAddPts_cacheCo)
    deleteDuplicatePts(agrcAddPts_cacheCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def carbonCounty():
    carbonCoAddPts = r'C:\ZBECK\Addressing\Carbon\CarbonCounty.gdb\CarbonAddressPoints'
    agrcAddPts_carbonCo = r'C:\ZBECK\Addressing\Carbon\Carbon.gdb\AddressPoints_Carbon'
    cntyFldr = r'C:\ZBECK\Addressing\Carbon'

    carbonCoAddFLDS = ['NAME', 'BUILD_TYPE', 'WHOLE_ADD', 'INDIC_ADDR', 'PRE_DIR', 'ST_NAME', 'ST_TYPE', 'SUF_DIR', 'UNIT_NUM', \
                       'BLDG_NUM', 'PARCEL_NUM', 'GPS_DATE', 'SHAPE@', 'OBJECTID']

    type = {
    'other' : ['GOVERMENT', 'EDUCATIONAL', 'FIRE HYDRANT', 'MISSING', 'OTHER', 'OUTBUILDING', 'OUT BUILDING', 'PUBLIC', 'PUBLIC WATER TANK', 'RELIGIOUS', 'STREET SIGN', 'TRAIN', 'WATER TANK'],
    'residential' : ['RESIDENTIAL', 'RESIDEENTIAL', 'RESIDENTIAL/COMMERCI'],
    'commercial' : ['COMMERCIAL', 'GARAGE', 'HELPER GUN CLUB', ''],
    'industrial': ['UTILITY']
    }

    units = {'APT' : ['APT.'], 'STE' : ['STE.', 'SUITE']}
    sNameSuffs = [' N', ' S', ' E', ' W']
    stripTypes = [' AVE', ' DR', ' LN', ' RD', ' ST', ' WAY']

    checkRequiredFields(carbonCoAddPts, carbonCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_carbonCo)
    rdSet = createRoadSet('49007')

    errorPtsDict = {}

    iCursor = arcpy.da.InsertCursor(agrcAddPts_carbonCo, agrcAddFLDS)

    unitID = ''

    with arcpy.da.SearchCursor(carbonCoAddPts, carbonCoAddFLDS) as sCursor_carbon:
        for row in sCursor_carbon:

            #------- Errror Pts --------
            if row[4] not in dirs and row[4] not in longDirs and row[4] not in errorList:
                addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[4]), [])
                addressErrors.extend(['bad pre dir', row[12]])
            if row[5].endswith((' N', ' S', ' E', ' W')):
                addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[5]), [])
                addressErrors.extend(['suf dir in street name', row[12]])
            if row[5].isdigit() and row[4] == row[7] and row[4] not in errorList:
                addressErrors = errorPtsDict.setdefault('{} | {} | {}'.format(row[2], row[4], row[7]), [])
                addressErrors.extend(['pre dir = suf dir', row[12]])
            if row[7] not in dirs and row[7] not in longDirs and row[7] not in errorList:
                addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[7]), [])
                addressErrors.extend(['bad suf dir', row[12]])
            if row[5] not in row[2] and row[5] not in errorList and  row[2] not in errorList:
                addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[5]), [])
                addressErrors.extend(['street name not in whole_add', row[12]])
            if row[5].endswith((tuple(leadingSpaceTypes))):
                addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[5]), [])
                addressErrors.extend(['street type in street name', row[12]])
            #---------------------------


            if row[3] not in errorList and row[5] not in errorList:
                # if row[3][0] != '#':
                #     addNum = row[3]
                if row[3].startswith('#') or row[2][0] == '#':
                    continue
                elif '#' in row[3]:
                    addNum = row[3].split()[0]
                    #unitID = row[3].split('#')[1]
                elif len(row[3]) <= 5:
                    if row[3].isalpha():
                        continue
                    if row[3][-1] == 'E':
                        continue
                    addNum = row[3]
                else:
                    continue

                if '.5' in addNum:
                    addNumSuf = '1/2'
                    addNum = re.sub('.5', '', addNum)
                elif ' 1/2' in addNum:
                    addNumSuf = '1/2'
                    addNum = re.sub(' 1/2', '', addNum)
                else:
                    addNumSuf = ''

                preDir = returnKey(row[4], dirs)
                sName = row[5].upper()

                sType = checkWord(row[6], parse_address.sTypes)
                sufDir = returnKey(row[7], dirs)
                if sufDir != '' and sType != '':
                    sType = ''

                if sName[-2:] in sNameSuffs:
                    sName = sName[:-2]
                    if sName.isdigit() == True:
                        sufDir = row[5][-1:]
                        print sufDir
                    sType = ''

                if sName.endswith((' AVE', ' DR', ' LN', ' RD', ' ST', ' STREET', ' WAY')):
                    sType = returnKey(sName.split()[-1], sTypeDir)
                    sName = ' '.join(sName.split()[:-1])
                if sType == '' and row[2][-3:] in stripTypes:
                    sType = row[2][-3:].strip()
                if sName.isdigit() == False and sType != '':
                    sufDir = ''
                if sName == 'MAIN':
                    sType = 'ST'

                if sType == '' and sName.isdigit() == False and sName[0].isdigit() == False:
                    sType = returnKey(row[6], sTypeDir)
                    sufDir = ''

                if row[6] != '' and row[6] != ' ' and row[6] not in sTypeDir:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[6], row[2]), [])
                    addressErrors.extend(['bad or missing street type', row[12]])

                if row[9] not in errorList and row[9] != 'OFFICE':
                    if 'BLDG' in row[9]:
                        building = str(row[9]).translate(None, '.')
                    else:
                        building = 'BLDG {}'.format(row[9])
                else:
                    building = ''

                cntyUnits = removeBadValues(str(row[8]).translate(None, '.#'), errorList)
                if len(cntyUnits.split()) > 1:
                    unitType = returnKey(cntyUnits.split()[0], units)
                    unitID = cntyUnits.split()[1]
                else:
                    unitID = cntyUnits
                    unitType = ''

                if unitType == '' and unitID != '':
                   unitID_hash = '# {}'.format(unitID)
                   fullAdd = '{} {} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sType, sufDir, building, unitType, unitID_hash)
                   fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = '{} {} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sType, sufDir, building, unitType, unitID)
                    fullAdd = ' '.join(fullAdd.split())

            elif row[2][0].isdigit() and len(row[2]) > 7:
                address = parse_address.parse(row[2])
                addNum = address.houseNumber
                addNumSuf = ''
                preDir = address.prefixDirection
                if preDir == None:
                    preDir = ''
                sName = address.streetName
                sType = address.suffixType
                if sType == None:
                    sType = ''
                sufDir = address.suffixDirection
                if sufDir == None:
                    sufDir = ''
                fullAdd = row[2]

            else:
                continue

            ptType = checkWord(unitType, type)
            if ptType == False:
                ptType = ''

            addSys = ''
            utAddId = ''
            city = ''
            zip = ''
            fips = '49007'
            state = 'UT'
            ptLocation = ''
            structure = ''
            landmark = removeBadValues(row[0], errorList)
            parcel = row[10]
            addSource = 'CARBON COUNTY'
            loadDate = today
            status = 'COMPLETE'
            editor = ''
            shp = row[12]

            if row[5].upper() not in rdSet and row[5] != '' and 'HWY' not in sName:
                addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[5]), [])
                addressErrors.extend(['street name not found in roads', row[12]])
            if sName.endswith((' ALY', ' AVE', ' BAY', ' BND', ' BLVD', ' CYN', ' CTR', ' CIR', ' COR', ' CT', ' CV', \
                                ' CRK', ' CRES', ' XING', ' DR', ' EST', ' ESTS', ' EXPY', ' FLT', ' FRK', ' FWY', \
                                ' GLN', 'GRV', ' HTS', ' HWY', ' HL', ' HOLW', ' JCT', ' LN', ' LNDG', ' LOOP', \
                                ' MNR', ' MDW', ' MDWS', ' PARK', ' PKWY', ' PASS', ' PL', ' PLZ', ' PT', ' RAMP', \
                                ' RNCH', ' RDG', ' RD', ' RTE', ' ROW', ' RUN', ' SQ', ' ST', ' TER', ' TRCE', ' TRL', \
                                ' VW', ' VLG', ' WAY')):
                addressErrors = errorPtsDict.setdefault('{} | {}'.format(sName, row[2]), [])
                addressErrors.extend(['street type in name?', row[12]])

            if sName.isdigit() and preDir in errorList and sufDir not in errorList:
                continue

            iCursor.insertRow((addSys, utAddId, fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, landmark, building, \
                               unitType, unitID, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                               status, editor, None, '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'Carbon_ErrorPts.shp', 'EXAMPLE', carbonCoAddPts)

    del iCursor
    del sCursor_carbon

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_carbonCo, inputDict)
    addBaseAddress(agrcAddPts_carbonCo)
    deleteDuplicatePts(agrcAddPts_carbonCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def daggettCounty():
    daggettCoAddPts = r'C:\ZBECK\Addressing\Daggett\DaggettCounty.gdb\DaggettAddress2018'
    agrcAddPts_daggettCo = r'C:\ZBECK\Addressing\Daggett\Daggett.gdb\AddressPoints_Daggett'
    cntyFldr = r'C:\ZBECK\Addressing\Daggett'

    daggettCoAddFLDS = ['HouseAddr', 'HouseNum', 'PreDir', 'StreetName', 'StreetType', 'SufDir', 'UnitNumber',\
                        'Parcel_ID', 'Structure','Modified', 'SHAPE@', 'FullAddr']

    aveDict = {'FIRST': '1ST', 'SECOND': '2ND', 'THIRD': '3RD', 'FOURTH': '4TH', 'FIFTH': '5TH', 'SIXTH': '6TH', \
               'SEVENTH': '7TH', 'EIGHTH': '8TH', 'NINTH': '9TH', 'TENTH': '10TH', 'ELEVENTH': '11TH',
               'TWELFTH': '12TH', 'THIRTEENTH': '13TH'}
    aveList = {'1ST', '2ND', '3RD', '4TH', '5TH', '6TH', '7TH', '8TH', '9TH'}

    checkRequiredFields(daggettCoAddPts, daggettCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_daggettCo)

    daggettDirs = ('N', 'S', 'E', 'W', '')

    errorPtsDict = {}

    iCursor = arcpy.da.InsertCursor(agrcAddPts_daggettCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(daggettCoAddPts, daggettCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[1] not in errorList:
                addNum = row[1]
                if addNum.isdigit() == False:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['HouseNum is not a digit', row[10]])
                    continue

                preDir = returnKey(row[2], dirs)
                if row[2].strip() not in daggettDirs:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['Bad SufDir', row[10]])

                sType = returnKey(row[4].upper(), sTypeDir)
                if row[4] == 'BLV':
                    sType = 'BLVD'
                if row[4].strip().upper() not in sTypeList:
                    addressErrors = errorPtsDict.setdefault(row[4], [])
                    addressErrors.extend(['bad street type', row[10]])

                sufDir = returnKey(row[5], dirs)
                if row[5].strip() not in daggettDirs:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['Bad SufDir', row[10]])

                sName = row[3].upper()
                if sName in aveDict:
                    sName = aveDict[sName]
                if row[3][:3] in aveList:
                    sName = sName[:3]
                    sufDir = returnKey(row[3].split()[1], dirs)
                    sType = ''
                if 'HWY' in sName:
                    sType = ''

                if row[3] not in row[0]:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['HouseAddr and StreetName have mixed street names', row[10]])
                if row[3].isalpha() and row[4] == '':
                    print 'missing stype'
                if ' {}'.format(row[3]).endswith(' ' + row[4]):
                    addressErrors = errorPtsDict.setdefault(row[3], [])
                    addressErrors.extend(['StreetType in StreetName', row[10]])

                    sName = row[3].strip(' {}'.format(row[4]))

                unitID = row[6].strip()

                if unitID == '':
                    fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType)
                    fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sufDir, sType, unitID)
                    fullAdd = ' '.join(fullAdd.split())

                parcelID = row[7]
                structure = row[8]
                loadDate = today
                modified = row[9]
                shp = row[10]

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '', \
                                   unitID, '', '', '49009', 'UT', '', '', structure, parcelID, 'DAGGETT COUNTY', \
                                   loadDate, 'COMPLETE', '', modified, '', '', '', shp))


        print errorPtsDict
        createErrorPts(errorPtsDict, cntyFldr, 'Daggett_ErrorPts.shp', daggettCoAddFLDS[0], daggettCoAddPts)

    del iCursor
    del sCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_daggettCo, inputDict)
    addBaseAddress(agrcAddPts_daggettCo)
    deleteDuplicatePts(agrcAddPts_daggettCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def davisCounty():
    davisCoAddPts = r'C:\ZBECK\Addressing\Davis\DavisCounty.gdb\AddressPoints'
    agrcAddPts_davisCo = r'C:\ZBECK\Addressing\Davis\Davis.gdb\AddressPoints_Davis'
    cntyFldr = r'C:\ZBECK\Addressing\Davis'

    davisCoAddFLDS = ['AddressNum', 'AddressN_1', 'UnitType', 'UnitNumber', 'RoadPrefix', 'RoadName', 'RoadNameTy', 'RoadPostDi', \
                      'FullAddres', 'SHAPE@', 'ParcelID']

    checkRequiredFields(davisCoAddPts, davisCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_davisCo)

    noTypeList = ['ANTELOPE ISLAND CAUSEWAY', 'APPLE ACRES', 'ASPEN GROVE', 'BOUNTIFUL MEMORIAL PARK', 'BROADWAY', \
                  'BUFFALO RANCH DEVELOPMENT', 'BURN PLANT', 'CARRIAGE CROSSING', 'CENTERVILLE MEMORIAL PARK', \
                  'CHERRY HILL ENTRANCE', 'CHEVRON REFINERY', 'CHRISTY', 'COMPTONS POINTE', 'DEER CREEK', 'EAST ENTRANCE', \
                  'EAST PROMONTORY', 'EGG ISLAND OVERLOOK', 'FAIRVIEW PASEO', 'FARMINGTON CEMETERY', 'FARMINGTON CROSSING', \
                  'FREEPORT CENTER', 'GARDEN CROSSING PASEO', 'HAWORTH', 'HWY 106', 'HWY 126', 'HWY 193', 'HWY 68', 'HWY 89', \
                  'HWY 93', 'HOLLY HAVEN I', 'HOLLY HAVEN II', 'IBIS CROSSING', 'KAYSVILLE AND LAYTON CEMETERY', \
                  'LLOYDS PARK', 'MOUNTAIN VIEW PASEO', 'NORTH ENTRANCE', 'NORTHEAST ENTRANCE', 'NORTHWEST ENTRANCE', \
                  'POETS REST', 'PRESERVE PASEO', 'SOMERSBY', 'SOUTH CAUSEWAY', 'SOUTH ENTRANCE', 'SOUTHEAST ENTRANCE', \
                  'STATION', 'STONEY BROOK', 'SYRACUSE CEMETERY', 'VALIANT', 'VALLEY VIEW', 'WARD', 'WARWICK', 'WEST PROMONTORY', \
                  'WETLAND POINT', 'WHISPERING PINE', 'WILLOW BEND PASEO', 'WILLOW FARM PASEO', 'WILLOW GARDEN PASEO', \
                  'WILLOW GREEN PASEO', 'WILLOW GROVE PASEO', 'WYNDOM']

    errorPtsDict = {}
    rdSet = createRoadSet('49011')

    iCursor = arcpy.da.InsertCursor(agrcAddPts_davisCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(davisCoAddPts, davisCoAddFLDS) as sCursor_davis:
        for row in sCursor_davis:

            if row[0] == 0 and row[5] != 'Freeport Center':
                continue

            elif row[0] not in errorList or row[5] not in errorList:

                addNum = row[0]
                addNumSuf = formatValues(row[1], addNumSufList)

                unitId = removeBadValues(row[3], errorList).upper()
                preDir = formatValues(row[4], dirs)

                unitType = formatValues(row[2], unitTypeDir).upper()
                if unitType != '' and unitId == '':
                    unitType = ''

                streetName = removeBadValues(row[5], errorList).upper()
                for type in sTypeDir:
                    if streetName != 'FREEPORT CENTER':
                        if streetName.endswith(' ' + type):
                            streetName = streetName.strip(type).strip()
                        elif 'HIGHWAY' in streetName:
                            streetName = streetName.replace('HIGHWAY', 'HWY')

                streetType = parse_address.checkWord(row[6].upper(), parse_address.sTypes)
                streetType = removeBadValues(streetType, errorList)

                sufDir = formatValues(row[7], dirs)

                if streetName.isdigit() == True:
                    if streetType != '':
                        addressErrors = errorPtsDict.setdefault(row[8], [])
                        addressErrors.extend(['Drop street type?', row[9]])
                    streetType = ''
                else:
                    if sufDir != '':
                        addressErrors = errorPtsDict.setdefault(row[8], [])
                        addressErrors.extend(['Drop suffix direction?', row[9]])
                    sufDir = ''

                if streetName == 'FREEPORT CENTER':
                    addNum = '0'
                    fullAdd = '{} {} {} {}'.format(addNum, streetName, unitType, unitId)
                elif addNumSuf in addNumSufList:
                    fullAdd = '{} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, streetName, sufDir, streetType)
                else:
                    #fullAdd = removeDuplicateWords(row[8].split(',')[0].upper())
                    fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, streetName, sufDir, streetType, unitType, unitId)

                fullAdd = ' '.join(fullAdd.split())
                fullAdd = removeDuplicateWords(fullAdd)


                if preDir != '' and preDir == sufDir:
                    addressErrors = errorPtsDict.setdefault(row[8], [])
                    addressErrors.extend(['Prefix = Suffix direction', row[9]])
                if 'HWY' not in streetName and streetName not in row[8].upper():
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[8], streetName), [])
                    addressErrors.extend(['Mixed street names', row[9]])
                if ' {}'.format(row[5]).endswith(' ' + row[6]):
                    addressErrors = errorPtsDict.setdefault(row[8], [])
                    addressErrors.extend(['StreetType in StreetName', row[9]])
                if sufDir != '' and streetType != '':
                    addressErrors = errorPtsDict.setdefault(row[8], [])
                    addressErrors.extend(['Post direction needed?', row[9]])
                if sufDir == '' and streetType == '' and streetName not in noTypeList:
                    print streetName
                    addressErrors = errorPtsDict.setdefault(row[8], [])
                    addressErrors.extend(['Missing Suffix or StreetType?', row[9]])
                if streetName not in row[8].upper() and 'HWY' not in streetName:
                    addressErrors = errorPtsDict.setdefault(row[8], [])
                    addressErrors.extend([streetName + ' not in FullAddress', row[9]])
                if streetName not in rdSet:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[8], streetName), [])
                    addressErrors.extend(['Street name missing in roads data', row[9]])


                addSys = ''
                utAddId = ''
                landmark = ''
                building = ''
                city = ''
                zip = ''
                fips = '49011'
                state = 'UT'
                ptLocation = 'Unknown'
                ptType = 'Unknown'
                structure = 'Unknown'
                addSource = 'DAVIS COUNTY'
                loadDate = today
                status = 'COMPLETE'
                modified = None
                shp = row[9]
                parcelID = row[10]

                iCursor.insertRow((addSys, utAddId, fullAdd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                                   unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcelID, addSource, loadDate, \
                                   status, '', modified, '', '', '', shp))

        print errorPtsDict
        createErrorPts(errorPtsDict, cntyFldr, 'Davis_ErrorPts.shp', davisCoAddFLDS[8], davisCoAddPts)

    del iCursor
    del sCursor_davis

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_davisCo, inputDict)
    addBaseAddress(agrcAddPts_davisCo)
    deleteDuplicatePts(agrcAddPts_davisCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def duchesneCounty():
    duchesneCoAddPts = r'C:\ZBECK\Addressing\Duchesne\DuchesneCo_April7th.gdb\DuchesneAddress472017'
    agrcAddPts_duchesneCo = r'C:\ZBECK\Addressing\Duchesne\Duchesne.gdb\AddressPoints_Duchesne'

    duchesneCoAddFLDS = ['HOUSE_N', 'PRE_DIR', 'S_NAME', 'SUF_DIR', 'S_TYPE', 'PARCEL_ID', 'Date_Mod', 'SHAPE@']

    checkRequiredFields(duchesneCoAddPts, duchesneCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_duchesneCo)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_duchesneCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(duchesneCoAddPts, duchesneCoAddFLDS) as sCursor_duchesne:
        for row in sCursor_duchesne:
            if row[0] not in errorList and row[2] not in errorList and len(row[2]) > 1:
                if row[2].isdigit() and row[3].strip() == '':
                    continue
                elif row[2][0] == '#':
                    continue
                else:
                    addNum = str(row[0]).strip('.0')
                    preDir = returnKey(row[1].upper(), dirs2)
                    sufDir = returnKey(row[3].upper(), dirs2)
                    sType = returnKey(row[4].upper(), sTypeDir)

                    sName = str(row[2]).translate(None, '.').strip()
                    if '(' in sName:
                        if sName[0].isdigit():
                            sName = sName.split('(')[1].strip(')')
                            if returnKey(sName.split()[-1], sTypeDir) != '':
                                sType = returnKey(sName.split()[-1], sTypeDir)
                                sName = sName.rsplit(' ', 1)[0]
                        else:
                            sName = sName.split('(')[0].strip('S ').strip('.')
                            sType = returnKey(sName.split()[-1], sTypeDir)
                            sName = sName.rsplit(' ', 1)[0]
                    if 'SR ' in sName:
                        sName = sName.replace('SR ', 'HWY ')
                        sType = ''
                    if 'US ' in sName:
                        sName = 'HWY {}'.format(sName.split()[-1])
                        sType = ''

                    fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType)
                    fullAdd = ' '.join(fullAdd.split())

                    parcelID = row[5]
                    modDate = row[6]
                    loadDate = today
                    shp = row[7]

                    iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '', '', '', '', '49013', \
                                       'UT', '', '', '', parcelID, 'DUCHESNE COUNTY', loadDate, 'COMPLETE', '', modDate, '', '', '', shp))

    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_duchesneCo, inputDict)


def emeryCounty():
    emeryCoAddPts = r'C:\ZBECK\Addressing\Emery\EmeryCounty.gdb\addresses'
    agrcAddPts_emeryCo = r'C:\ZBECK\Addressing\Emery\Emery.gdb\AddressPoints_Emery'
    cntyFldr = r'C:\ZBECK\Addressing\Emery'

    emeryCoAddFLDS = ['AddNum', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 'UnitID', 'LandmarkNa', \
                      'PtLocation', 'PtType', 'Structure', 'ParcelID', 'Modified', 'Building','SHAPE@', 'FullAdd']

    checkRequiredFields(emeryCoAddPts, emeryCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_emeryCo)

    errorPtsDict = {}

    structureDict = {'Yes':['YES', 'yes', 'y'], 'No':['NO', 'no', 'n'], 'Unknown':['UNKNOWN', 'UNK']}

    iCursor = arcpy.da.InsertCursor(agrcAddPts_emeryCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(emeryCoAddPts, emeryCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] not in errorList or row[2] not in errorList:
                addNum = row[0]
                preDir = returnKey(row[1].upper(), dirs)
                sName = row[2].upper()
                if 'STATE ROAD' in sName:
                    sName = sName.replace('STATE ROAD', 'HIGHWAY')
                sufDir = returnKey(row[4].upper(), dirs)
                sType = returnKey(row[3], sTypeDir)
                unitID = removeBadValues(row[5], errorList)
                if unitID != '':
                    unitID_hash = '# ' + unitID
                else:
                    unitID_hash = ''
                landmark = removeBadValues(row[6], errorList)
                if landmark == '':
                    landmark = removeBadValues(row[12], errorList)
                ptLocation = row[7]
                ptType = row[8].title()
                structure = returnKey(row[9], structureDict)
                parcelID = row[10]
                loadDate = today
                modDate = row[11]
                shp = row[13]

                fullAdd = '{} {} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType, unitID_hash)
                fullAdd = ' '.join(fullAdd.split())

                if fullAdd != row[14].upper():
                    print fullAdd + ' | ' + row[14]

    # --------------Create Error Points--------------
                if row[2].upper() not in row[14].upper():
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[14]), [])
                    addressErrors.extend(['mixed street names', row[13]])
                if preDir == sufDir and sType == '':
                    addressErrors = errorPtsDict.setdefault(row[14], [])
                    addressErrors.extend(['prefix = sufix', row[13]])
                if row[3].upper() not in sTypeList:
                    addressErrors = errorPtsDict.setdefault(row[3], [])
                    addressErrors.extend(['bad street type', row[13]])

                if preDir == sufDir and sType == '':
                    continue

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, landmark, '', '',\
                                   unitID, '', '', '49015', 'UT', ptLocation, ptType, structure, parcelID, 'EMERY COUNTY', \
                                   loadDate, 'COMPLETE', '', modDate, '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'Emery_ErrorPts.shp', emeryCoAddFLDS[14], emeryCoAddPts)

    del sCursor
    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_emeryCo, inputDict)
    addBaseAddress(agrcAddPts_emeryCo)
    deleteDuplicatePts(agrcAddPts_emeryCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def garfieldCounty():
    garfieldCoAddPts = r'C:\ZBECK\Addressing\Garfield\GarfieldCounty.gdb\GarfieldCountyPts'
    agrcAddPts_garfieldCo = r'C:\ZBECK\Addressing\Garfield\Garfield.gdb\AddressPoints_Garfield'

    garfieldCoAddFLDS = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', \
                         'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State', \
                         'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'LoadDate', 'Status', 'Editor', \
                         'ModifyDate', 'StreetAlias', 'Notes', 'SHAPE@']

    checkRequiredFields(garfieldCoAddPts, garfieldCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_garfieldCo)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_garfieldCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(garfieldCoAddPts, garfieldCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[3] in errorList or row[6] in errorList:
                continue
            else:
                addNum = row[3]
                if ' ' in addNum:
                    addNum = addNum.split()[0]

                preDir = returnKey(row[5], dirs)

                sName = removeBadValues(row[6], errorList)
                if sName == 'US':
                    sName = 'HWY 89'
                if 'HIGHWAY' in sName:
                    sName = sName.replace('HIGHWAY', 'HWY')

                sType = returnKey(row[7], sTypeDir)
                sufDir = returnKey(row[8], dirs)
                unitId = removeBadValues(row[12], errorList)
                ptLocation = row[17]
                ptType = row[18]
                structure = row[19]
                parcel = row[20]
                mDate = row[25]
                loadDate = today
                shp = row[28]

                if unitId != '':
                    fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sType, sufDir, unitId)
                elif sType == 'HWY':
                    fullAdd = '{} {} {} {}'.format(addNum, preDir, sName, sufDir)
                else:
                    fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir)

                fullAdd = ' '.join(fullAdd.split())

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '',\
                                   unitId, '', '', '49017', 'UT', ptLocation, ptType, structure, parcel, 'GARFIELD COUNTY', \
                                   loadDate, 'COMPLETE', '', mDate, '', '', '', shp))

    del iCursor
    del sCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_garfieldCo, inputDict)
    addBaseAddress(agrcAddPts_garfieldCo)
    deleteDuplicatePts(agrcAddPts_garfieldCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def grandCounty():
    rdSet = createRoadSet('49019')

    grandCoAddPts = r'C:\ZBECK\Addressing\Grand\GrandCounty.gdb\GrandPts'
    agrcAddPts_grandCo = r'C:\ZBECK\Addressing\Grand\Grand.gdb\AddressPoints_Grand'
    cntyFldr = r'C:\ZBECK\Addressing\Grand'

    grandCoAddFLDS = ['FullAdd', 'AddNum', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 'UnitType', 'UnitID', \
                      'City', 'ZipCode', 'PtLocation', 'PtType', 'Structure', 'ParcelID', 'ModifyDate', 'SHAPE@', 'OBJECTID']

    checkRequiredFields(grandCoAddPts, grandCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_grandCo)

    errorPtsDict = {}

    iCursor = arcpy.da.InsertCursor(agrcAddPts_grandCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(grandCoAddPts, grandCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[1] not in errorList:
                addNum = row[1]
                if row[2] not in errorList:
                    preDir = row[2]
                else:
                    if row[0] != None:
                        addressErrors = errorPtsDict.setdefault(row[0], [])
                        addressErrors.extend(['Prefix direction needed?', row[15]])
                    else:
                        addressErrors = errorPtsDict.setdefault(row[16], [])
                        addressErrors.extend(['Prefix direction needed?', row[15]])
                    preDir = ''

                if row[3] in errorList:
                    addressErrors = errorPtsDict.setdefault(row[16], [])
                    addressErrors.extend(['bad street name', row[15]])
                    continue
                sName = removeNone(row[3]).upper()
                sName = sName.replace(u'\xd1', 'N')
                if sName not in rdSet:
                    if row[0] != None:
                        addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[0], row[3]), [])
                        addressErrors.extend(['street name not in roads data', row[15]])
                    else:
                        addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[16], row[3]), [])
                        addressErrors.extend(['street name not in roads data', row[15]])

                sType = returnKey(removeNone(row[4]), sTypeDir)

                sufDir = removeNone(row[5])
                if sufDir == '' and sName[0].isdigit() == True:
                    if row[0] != None:
                        addressErrors = errorPtsDict.setdefault(row[0], [])
                        addressErrors.extend(['suffix direction missing?', row[15]])
                    else:
                        addressErrors = errorPtsDict.setdefault(row[16], [])
                        addressErrors.extend(['suffix direction missing?', row[15]])

                unitId = removeNone(row[7]).strip('#').strip()

                fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir)
                if unitId != '':
                    fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sType, sufDir, unitId)
                fullAdd = ' '.join(fullAdd.split())

                if sType == '' and sName[0].isdigit() == False:
                    if row[0] != None:
                        addressErrors = errorPtsDict.setdefault(row[0], [])
                        addressErrors.extend(['street type missing?', row[15]])
                    else:
                        addressErrors = errorPtsDict.setdefault(fullAdd, [])
                        addressErrors.extend(['street type missing?', row[15]])

                ptLoc = removeNone(row[10])
                ptType = removeNone(row[11])
                structure = removeNone(row[12])
                parcel = removeNone(row[13])
                loadDate = today
                modDate = row[14]
                shp = row[15]

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '', unitId, '', \
                                   '', '49019', 'UT', ptLoc, ptType, structure, parcel, 'GRAND COUNTY', loadDate, \
                                   'COMPLETE', '', modDate, '', '', '', shp))

    createErrorPts(errorPtsDict, cntyFldr, 'Grand_ErrorPts.shp', 'EXAMPLE', grandCoAddPts)
    del sCursor
    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_grandCo, inputDict)
    addBaseAddress(agrcAddPts_grandCo)
    deleteDuplicatePts(agrcAddPts_grandCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def ironCounty():
    ironCoAddPts = r'C:\ZBECK\Addressing\Iron\IronCounty.gdb\IronAddressPts'
    agrcAddPts_ironCo = r'C:\ZBECK\Addressing\Iron\Iron.gdb\AddressPoints_Iron'

    # counties = r'Database Connections\dc_agrc@SGID10.sgid.agrc.utah.gov.sde\SGID10.BOUNDARIES.Counties'
    # sql = """"{}" = '{}'""".format('NAME', 'IRON')
    # def selectByLocation(points, polygon, sql):
    #     ptsFL = arcpy.MakeFeatureLayer_management(points, 'ptsFL')
    #     polyFL = arcpy.MakeFeatureLayer_management(polygon, 'polyFL', sql)
    #     selectFeatures = arcpy.SelectLayerByLocation_management(ptsFL, 'INTERSECT', polyFL)
    #     return selectFeatures
    # ironPtsONLY = selectByLocation(ironCoAddPts, counties, sql)

    ironCoAddFLDS = ['AddrNum', 'AddrPD', 'AddrSN', 'AddrST', 'AddrSD', 'UnitType', 'UnitID', 'Date', 'SHAPE@']

    checkRequiredFields(ironCoAddPts, ironCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_ironCo)

    fakeStreets = ['BETH', 'KARI', 'RAQUEL', 'RHONDA', 'RONI']

    iCursor = arcpy.da.InsertCursor(agrcAddPts_ironCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(ironCoAddPts, ironCoAddFLDS) as sCursor_iron:
        for row in sCursor_iron:
            if row[0] not in errorList:
                addNum = row[0]
            else:
                continue

            sType = returnKey(row[3], sTypeDir)

            if row[2] not in errorList:
                sName = row[2]
                if sName[:2] == 'SR' and sName[2].isdigit():
                    sName = sName.replace('SR', 'HWY ')
                    sType = ''
                if sName == 'SRY':
                    sName = 'TERRY'
                if sName == 'SRACE':
                    sName == 'TERRACE'

            else:
                continue

            preDir = returnKey(row[1], dirs)

            sufDir = returnKey(row[4], dirs)
            landmark = ''
            unitType = returnKey(row[5], unitTypeDir)
            unitID = removeBadValues(row[6], errorList)
            mDate = row[7]
            loadDate = today
            shp = row[8]

            if sName in fakeStreets:
                addNum = '1435'
                preDir = 'W'
                sName = '200'
                sufDir = 'S'
                sType = ''
                unitType = 'TRLR'
                unitID = row[0]
                landmark = 'Foothills RV Park'

            if unitType == '' and unitID != '':
                fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sType, sufDir, unitID)
            elif unitType != '' and unitID != '':
                fullAdd = '{} {} {} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir, unitType, unitID)
            else:
                fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir)

            fullAdd = ' '.join(fullAdd.split())

            iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, landmark, '', unitType, unitID, '', '', '49021', \
                              'UT', '', '', '', '', 'IRON COUNTY', loadDate, 'COMPLETE', '', mDate, '', '', '', shp))

    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_ironCo, inputDict)
    addBaseAddress(agrcAddPts_ironCo)
    deleteDuplicatePts(agrcAddPts_ironCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def juabCounty():
    juabCoAddPts = r'C:\ZBECK\Addressing\Juab\JuabAddressPointUpdates.gdb\JuabUpdates_10122016'
    agrcAddPts_juabCo = r'C:\ZBECK\Addressing\Juab\Juab.gdb\AddressPoints_Juab'

    juabCoAddFLDS = ['FullAdd', 'AddNum', 'AddNumSuff', 'PrefixDir', 'StreetName', 'StreetType', 'LandmarkNa', 'Building', \
                     'UnitType', 'UnitID', 'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'SHAPE@']

    checkRequiredFields(juabCoAddPts, juabCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_juabCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(juabCoAddPts, juabCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] not in errorList:
                address = parse_address.parse(row[0])
                addNum = address.houseNumber.replace('*', '')
                addNumSuf = formatValues(row[2], addNumSufList)
                preDir = address.prefixDirection
                sName = address.streetName
                sufDir = removeBadValues(address.suffixDirection, errorList)

                if address.suffixType != None:
                    sType = address.suffixType
                else:
                    sType = row[5]

                landmark = removeBadValues(row[6], errorList)
                building = removeBadValues(row[7], errorList)
                unitType = removeBadValues(row[8], errorList)
                unitId_hash = formatUnitID(row[9])
                unitId = unitId_hash.strip('# ')
                ptLocation = row[10]
                ptType = row[11]
                structure = row[12]
                parcel = row[13]
                source = 'JUAB COUNTY'
                loadDate = today
                modDate = None

                fulladd = '{} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sufDir, sType, unitId_hash)
                fulladd = ' '.join(fulladd.split())

                shp = row[15]

                iCursor.insertRow(('', '', fulladd, addNum, addNumSuf, preDir, sName, sType, sufDir, landmark, building, \
                                   unitType, unitId, '', '', '49023', 'UT', ptLocation, ptType, structure, parcel, \
                                   source, loadDate, 'COMPLETE', '', modDate, '', shp))

    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_juabCo, inputDict)


def kaneCounty():
    #addressAppPts = r'C:\ZBECK\Addressing\Kane\Kane.gdb\ADDRESSADMIN_AddressPointsBKUP'
    addressAppPts = r'Database Connections\DC_AddressAdmin@AddressPointEditing@itdb104sp.sde\AddressPointEditing.ADDRESSADMIN.AddressPoints'
    countyBoundaries = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde\SGID10.BOUNDARIES.Counties'

    sql = """"{}" = '{}'""".format('NAME', 'KANE')
    kaneBoundaryFL = arcpy.MakeFeatureLayer_management(countyBoundaries, 'kaneBoundaryFL', sql)
    addressAppPtsFL = arcpy.MakeFeatureLayer_management(addressAppPts, 'addressAppPtsFL')

    kaneCoAddPts = arcpy.SelectLayerByLocation_management(addressAppPtsFL, 'WITHIN', kaneBoundaryFL, '', 'NEW_SELECTION')
    agrcAddPts_kaneCo = r'C:\ZBECK\Addressing\Kane\Kane.gdb\AddressPoints_Kane'

    truncateOldCountyPts(agrcAddPts_kaneCo)

    kaneCoAddFLDS = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', \
                     'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State', \
                     'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'LoadDate', 'Status', 'Editor', \
                     'ModifyDate', 'StreetAlias', 'Notes', 'SHAPE@']

    iCursor = arcpy.da.InsertCursor(agrcAddPts_kaneCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(kaneCoAddPts, kaneCoAddFLDS) as sCursor_kane:
        for row in sCursor_kane:

            addNum = row[3]
            streetName = row[6]

            if row[2] not in errorList:
                fullAdd = row[2].replace('#', '# ')
                addNum = row[3]
                preDir = removeBadValues(row[5], errorList)
                streetName = removeBadValues(row[6], errorList)
                streetType = removeBadValues(row[7], errorList)
                sufDir = removeBadValues(row[8], errorList)
                landmark = removeBadValues(row[9], errorList)
                building = removeBadValues(row[10], errorList)
                unitType = removeBadValues(row[11], errorList)
                unitId = removeBadValues(row[12], errorList).strip('#')
                ptLocation = removeBadValues(row[17], errorList)
                ptType = removeBadValues(row[18], errorList)
                structure = removeBadValues(row[19], errorList)
                parcel = removeBadValues(row[20], errorList)

            if addNum and streetName not in errorList:
                addNum = row[3]
                preDir = removeBadValues(row[5], errorList)
                streetName = removeBadValues(row[6], errorList)
                streetType = removeBadValues(row[7], errorList)
                sufDir = removeBadValues(row[8], errorList)
                landmark = removeBadValues(row[9], errorList)
                building = removeBadValues(row[10], errorList)
                unitType = removeBadValues(row[11], errorList)
                unitId = removeBadValues(row[12], errorList).strip('#')
                ptLocation = removeBadValues(row[17], errorList)
                ptType = removeBadValues(row[18], errorList)
                structure = removeBadValues(row[19], errorList)
                parcel = removeBadValues(row[20], errorList)

                if unitType == '' and unitId != '':
                    fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, streetName, sufDir, streetType, unitId)
                    fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = '{} {} {} {} {} {}'.format(addNum, preDir, streetName, sufDir, streetType, unitId)
                    fullAdd = ' '.join(fullAdd.split())

            else:
                continue

            addNumSuf = ''
            addSys = ''
            utAddId = ''
            city = ''
            zip = row[14]
            fips = '49025'
            state = 'UT'
            addSource = 'KANE COUNTY'
            status = 'COMPLETE'
            loadDate = today
            editor = removeBadValues(row[24], errorList)
            shp = row[28]

            iCursor.insertRow((addSys, utAddId, fullAdd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                                unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                                status, editor, None, '', '', '', shp))

    arcpy.Delete_management(addressAppPtsFL)
    arcpy.Delete_management(kaneBoundaryFL)
    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_kaneCo, inputDict)
    addBaseAddress(agrcAddPts_kaneCo)


def millardCounty():
    millardCoAddPts = r'C:\ZBECK\Addressing\Millard\MillardSource.gdb\AddressPoints'
    agrcAddPts_millardCo = r'C:\ZBECK\Addressing\Millard\Millard.gdb\AddressPoints_Millard'
    cntyFldr = r'C:\ZBECK\Addressing\Millard'

    millardCoAddFLDS = ['FULLADDR', 'UNIT_TYPE', 'UNIT_ID', 'ADDRNUM', 'SHAPE@', 'OBJECTID']

    errorPtsDict = {}
    rdSet = createRoadSet('49027')

    checkRequiredFields(millardCoAddPts, millardCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_millardCo)

    replaceDict = {'NORTH ST':'N', 'NORTH RD':'N', 'SOUTH ST':'S', 'SOUTH RD':'S', 'EAST ST':'E', 'WEST ST':'W',\
                   'WEST RD':'W', 'HIGHWAY':'HWY'}
    rdExceptions = ['E NORTH RD', 'W NORTH RD', 'E SOUTH RD']
    def checkExceptions(word, lst):
        for i in lst:
            if i in word:
                return True

    iCursor = arcpy.da.InsertCursor(agrcAddPts_millardCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(millardCoAddPts, millardCoAddFLDS) as sCursor_millardCo:
        for row in sCursor_millardCo:

            if row[0] != '' and row[0][0].isdigit() == True:
                unitType = row[1].strip()
                unitId = row[2].strip()

                modifiedAddress = replaceByDictionary(row[0], replaceDict)
                if unitType not in errorList and unitType in row[0]:
                    #remove unitTypes from address
                    modifiedAddress = replaceByDictionary(row[0].split(row[1])[0].strip(), replaceDict)
                if 'CENTER' in modifiedAddress and ' ST' not in modifiedAddress:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['missing street type', row[4]])
                    modifiedAddress = modifiedAddress + ' ST'

                if '(' in modifiedAddress:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['bad address', row[4]])
                    modifiedAddress = modifiedAddress.split(' (')[0]

                address = parse_address.parse(modifiedAddress)
                addNum = address.houseNumber
                preDir = removeNone(address.prefixDirection)

                sName = address.streetName
                sType = removeNone(address.suffixType)
                if checkExceptions(row[0], rdExceptions) == True:
                    sName = parse_address.parse(row[0]).streetName
                    sType = parse_address.parse(row[0]).suffixType

                if sName not in rdSet and 'HWY' not in sName:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(sName, row[0]), [])
                    addressErrors.extend(['street name not found in roads', row[4]])

                sName = removeDuplicateWords(sName)
                if sName == '':
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['bad address', row[4]])
                    continue

                sufDir = removeNone(address.suffixDirection)
                if sName[0].isdigit() == True and sName[-1].isdigit() != True and sName != '1 MILE POST':
                    print '{} {}'.format(sName, row[5])
                    sufDir = sName[-1]
                    sName = sName[:-1]
                    sType = ''
                if sName[-1].isdigit() == True and sName[0].isdigit() != True and 'HWY' not in sName:
                    preDir = sName[0]
                    sName = sName[1:].strip()
                    sType = ''
                if sName.endswith((' ST', ' ROAD', ' DR', ' DRIVE', ' AVE')):
                    sType = returnKey(sName.split()[1], sTypeDir)
                    sName = sName.split()[0]

                if preDir == sufDir:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['pre and post directions match', row[4]])

                if sufDir == '' and sType == '' and 'HWY' not in sName:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['post dir or street type missing', row[4]])


                fulladd = '{} {} {} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType, unitType, unitId)
                fulladd = ' '.join(fulladd.split())

                shp = row[4]

                iCursor.insertRow(('', '', fulladd, addNum, '', preDir, sName, sType, sufDir, '', '', unitType, unitId,\
                                   '', '', '49027', 'UT', '', '', '', '', 'MILLARD COUNTY', today, 'COMPLETE', '', None,\
                                   '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'MillardCounty_ErrorPts.shp', 'ADDRESS', millardCoAddPts)

    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5']
    }

    addPolyAttributes(sgid10, agrcAddPts_millardCo, inputDict)
    addBaseAddress(agrcAddPts_millardCo)
    deleteDuplicatePts(agrcAddPts_millardCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def morganCounty():
    morganCoAddPts = r'C:\ZBECK\Addressing\Morgan\MorganCountyPts.gdb\AddressPoints'
    agrcAddPts_morganCo = r'C:\ZBECK\Addressing\Morgan\Morgan.gdb\AddressPoints_Morgan'
    cntyFldr = r'C:\ZBECK\Addressing\Morgan'

    morganCoAddFLDS = ['ADDRNUM', 'FULLNAME', 'UNITTYPE', 'UNITID', 'LASTUPDATE', 'SHAPE@', 'FULLADDR']

    checkRequiredFields(morganCoAddPts, morganCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_morganCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49029')

    exp = re.compile(r'(?:^[NSEW]\s)?(?:(.+)(\s[NSEW]$)|(.+$))')

    iCursor = arcpy.da.InsertCursor(agrcAddPts_morganCo, agrcAddFLDS)

    leadingSpaceTypes.extend([' LANE', ' COURT', ' COVE', ' COURT', ' CIRCLE', ' PARKWAY'])

    with arcpy.da.SearchCursor(morganCoAddPts, morganCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] not in errorList and row[1] not in errorList:
                addNum = row[0].strip()
                fullName = row[1].upper()
                fullAddr = row[6].upper()
                sufDir = ''
                unitType = ''

                expMatches = re.findall(exp, fullName)[0]
                if row[1][:2].strip() in dirs:
                    preDir = row[1][:2].strip()
                    sName = row[1][2:].upper()
                    if sName == 'HWY 66':
                        sType = ''
                    if sName.endswith((tuple(leadingSpaceTypes))):
                        sType = returnKey(sName.split()[-1], sTypeDir)
                        sName = ' '.join(sName.split()[:-1])
                        #sName = sName.strip(' {}'.format(sType)).rstrip()
                    if sName[0].isdigit():
                        sufDir = sName[-1]
                        sName = ' '.join(sName.split()[:-1])
                else:
                    sName = row[1].upper()
                    preDir = ''
                    if sName.endswith((tuple(leadingSpaceTypes))):
                        sType = returnKey(sName.split()[-1], sTypeDir)
                        sName = ' '.join(sName.split()[:-1])

                if sName.isdigit() == True:
                    sType = ''
            else:
                continue

            if row[2] not in errorList:
                unitType = returnKey(row[2].upper(), unitTypeDir)

            unitID = removeBadValues(row[3], errorList)

            modDate = row[4]
            loadDate = today

            shp = row[5]

            fullAdd = '{} {} {} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType, unitType, unitID)
            fullAdd = ' '.join(fullAdd.split())

            if fullAddr != fullAdd:
                print fullAddr + '  -  ' + fullAdd
            if 'HWY' not in sName and sName not in rdSet:
                addressErrors = errorPtsDict.setdefault('{} | {}'.format(sName, fullAddr), [])
                addressErrors.extend(['add pts street name not found in roads', row[5]])

            iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', unitType, unitID, '', '', '49029', \
                              'UT', '', '', '', '', 'MORGAN COUNTY', loadDate, 'COMPLETE', '', modDate, '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'Morgan_ErrorPts.shp', 'EXAMPLE', morganCoAddPts)
    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_morganCo, inputDict)
    addBaseAddress(agrcAddPts_morganCo)
    deleteDuplicatePts(agrcAddPts_morganCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def piuteCounty():
    piuteCoAddPts = r'C:\ZBECK\Addressing\Piute\PiuteCounty.gdb\PiutePtsMaster'
    agrcAddPts_piuteCo = r'C:\ZBECK\Addressing\Piute\Piute.gdb\AddressPoints_Piute'

    piuteCoAddFLDS = ['ADDRESS', 'PARCEL__', 'SHAPE@']

    unitList = [' A', ' B', ' C', ' D', ' E', ' 1', ' 2']

    checkRequiredFields(piuteCoAddPts, piuteCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_piuteCo)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_piuteCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(piuteCoAddPts, piuteCoAddFLDS) as sCursor:
        for row in sCursor:
            unitID = ''
            unitType = ''

            address = parse_address.parse(row[0])
            address_noUnit = parse_address.parse(row[0][:-1])

            addNum = address.houseNumber

            preDir = address.prefixDirection
            if preDir == None:
                preDir = ''

            sufDir = address.suffixDirection
            if sufDir == None:
                sufDir = ''

            sType = address.suffixType
            if sType == None:
                sType = ''

            if ' STE ' in row[0]:
                unitType = 'STE'
                unitID = row[0][-1:]

            if ' OLD HWY 89' in row[0]:
                sName = 'OLD HWY 89'
                sType = ''
                sufDir = ''
                if row[0][-2:] in unitList:
                    unitID = row[0][-1:]
            elif row[0].endswith(' OLD US HWY 89'):
                sName = 'HWY 89'
                sType = ''
            elif row[0].endswith(' US HWY 89'):
                sName = 'HWY 89'
                sType = ''
            elif row[0][-2:] in unitList and row[0][-1] != sufDir:
                unitID = row[0][-1:]
                sName = address_noUnit.streetName
            else:
                sName = address.streetName

            if unitType == '' and unitID != '':
                fulladd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sufDir, sType, unitID)
            else:
                fulladd = '{} {} {} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType, unitType, unitID)

            fulladd = ' '.join(fulladd.split())

            parcel = row[1].strip()

            shp = row[2]

            iCursor.insertRow(('', '', fulladd, addNum, '', preDir, sName, sType, sufDir,
                               '', '', unitType, unitID, '', '', '49031', 'UT', '', '', '', parcel,
                               'SEVIER COUNTY', today, 'COMPLETE', '', None, '', '', '', shp))

    del sCursor
    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_piuteCo, inputDict)
    addBaseAddress(agrcAddPts_piuteCo)
    deleteDuplicatePts(agrcAddPts_piuteCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def richCounty():

    richCoAddPts = r'C:\ZBECK\Addressing\Rich\RichCounty.gdb\AddressPoints'
    agrcAddPts_richCo = r'C:\ZBECK\Addressing\Rich\Rich.gdb\AddressPoints_Rich'

    richCoAddFLDS = ['House_Num', 'Prefix_Dir', 'St_Name', 'St_Dir', 'St_Type', 'Unit_Num', 'Modified', 'Parcel_ID', 'SHAPE@', 'OBJECTID_1']

    checkRequiredFields(richCoAddPts, richCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_richCo)

    hwyList = ['HIGHWAY 16', 'HIGHWAY 30', 'HIGHWAY 89', 'STATE ROUTE 30']

    iCursor = arcpy.da.InsertCursor(agrcAddPts_richCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(richCoAddPts, richCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] not in errorList or row[1] not in errorList:
                addNum = row[0]
                preDir = returnKey(row[1].upper(), dirs)
                sufDir = returnKey(row[3].upper(), dirs)

                sType = returnKey(row[4].upper(), sTypeDir)
                if row[4] == 'Wy':
                    sType = 'WAY'

                sName = row[2].upper()
                if sName == 'Lochwood View'.upper():
                    sName = 'LOCHWOOD'
                    sType = 'VIEW'
                if sName[:2].isdigit() and sName.endswith((' NORTH', ' SOUTH', ' EAST', ' WEST', ' S')):
                    sName = sName.split()[0]
                    sufDir = returnKey(row[2].split()[1].upper(), dirs)
                if sName in hwyList:
                    sType = 'HWY'

                if preDir == sufDir and sType == '':
                    #print '{} p = s no type'.format(row[9])
                    continue
                if sName.isdigit() and preDir == '':
                    #print '{} no p'.format(row[9])
                    continue

                if sType == '' and sName[:1].isdigit() == False:
                    #print '{} no type'.format(row[9])
                    continue

                unitId = removeBadValues(row[5], errorList)
                modified = row[6]
                loadDate = today
                parcelID = row[7]
                shp = row[8]

                if unitId != '':
                    fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sType, sufDir, unitId)
                    fullAdd = ' '.join(fullAdd.split())
                elif sType == 'HWY':
                    fullAdd = '{} {} {} {}'.format(addNum, preDir, sName, sufDir)
                    fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir)
                    fullAdd = ' '.join(fullAdd.split())

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '', unitId, '', '', '49033', 'UT', \
                                   'Unknown', 'Unknown', 'Unknown', parcelID, 'RICH COUNTY', loadDate, 'COMPLETE', '', modified, '', '', '', shp))

    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_richCo, inputDict)
    addBaseAddress(agrcAddPts_richCo)
    deleteDuplicatePts(agrcAddPts_richCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def saltLakeCounty():

    slcoAddPts = r'C:\ZBECK\Addressing\SaltLake\SaltLakeCounty.gdb\ADDRESS_POINTS'
    agrcAddPts_SLCO = r'C:\ZBECK\Addressing\SaltLake\SaltLake.gdb\AddressPoints_SaltLake'
    cntyFldr = r'C:\ZBECK\Addressing\SaltLake'

    slcoAddFLDS = ['PARCEL', 'ADDRESS', 'UNIT_DESIG', 'IDENTIFY', 'BLDG_DESIG', 'ADDR_LABEL', 'DEVELOPMENT', 'BUSINESS_NAME', \
                   'ADDR_TYPE', 'UPDATED', 'MODIFIED_DATE', 'ADDR_PD', 'SHAPE@', 'ZIP_CODE', 'ADDR_HN', 'ADDR_SN', 'EXPORT', \
                   'ADDR_PD', 'ADDR_SN', 'ADDR_ST', 'ADDR_SD']

    fixDict = {'SOUTHTEMPLE':'SOUTH TEMPLE', 'NORTHTEMPLE':'NORTH TEMPLE','WESTTEMPLE':'WEST TEMPLE', \
               'EASTCAPITOL':'EAST CAPITOL', 'SOUTHJORDAN':'SOUTH JORDAN', 'SOUTHJRDN':'SOUTH JORDAN', \
               'SOUTHPOINTE':'SOUTH POINTE', 'SOUTHSAMUEL':'SOUTH SAMUEL', 'NORTHBOROUGH':'NORTH BOROUGH', \
               'NORTHUNION':'NORTH UNION', 'PARK PLACENORTH':'PARK', 'PARK PLACESOUTH':'PARK', 'PARK PLACEEAST':'PARK', \
               'PARK PLACEWEST': 'PARK', 'SOUTHCAMPUS':'SOUTH CAMPUS', 'PINNACLETERRACE':'PINNACLE TERRACE', \
               'SOUTHUNION':'SOUTH UNION', 'SOUTHWOODSIDE':'SOUTH WOODSIDE', 'WESTCAPITOL':'WEST CAPITOL', \
               'THREE FTNS':'THREE FOUNTAINS', 'UONE ELEVEN':'HWY 111', 'UTWO O ONE HWY':'HWY 201', \
               'IEIGHTYEAST FWY':'I-80 EB', 'IEIGHTYEAST':'I-80 EB', 'IEIGHTYWEST FWY':'I-80 WB', \
               'SUNRISEPLACE WEST':'SUNRISE', 'SUNRISEPLACE EAST':'SUNRISE', 'SUNRISEPLACE SOUTH':'SUNRISE', \
               'SUNRISEPLACE NORTH':'SUNRISE', 'SWEET BASIL SOUTH':'SWEET BASIL', 'SWEET BASIL NORTH':'SWEET BASIL', \
               'U-201 EB':'HWY 201 EB', 'U-201 WB':'HWY 201 WB', 'UTWO O ONE':'HWY 201', 'U-202':'HWY 202', 'USIXTY FIVE':'HWY 65'}

    aveDict = {'FIRST':'1ST', 'SECOND':'2ND', 'THIRD':'3RD', 'FOURTH':'4TH', 'FIFTH':'5TH', 'SIXTH':'6TH', \
               'SEVENTH':'7TH', 'EIGHTH':'8TH', 'NINTH':'9TH', 'TENTH':'10TH', 'ELEVENTH':'11TH', 'TWELFTH':'12TH', 'THIRTEENTH':'13TH', \
               'FOURTEENTH':'14TH', 'FIFTEENTH':'15TH', 'SIXTEENTH':'16TH', 'SEVENTEENTH':'17TH', 'EIGHTEENTH':'18TH'}

    ptTypeDic = {
        'Other' : ['AIRPORT', 'CEMETERY', 'CHURCH', 'CIVIC', 'COORDINATE', 'FIRE STATION', 'GOLF COURSE', 'HOSPITAL',
                 'JAIL', 'LIBRARY', 'MAILBOX', 'PARK', \
                 'OPEN SPACE', 'PARKING', 'POLICE', 'POOL', 'POST OFFICE', 'PRISON', 'SCHOOL', 'SLCC', 'TEMPLE', 'TRAX',
                 'U CAMPUS', 'WESTMINSTER', 'ZOO'],
        'Residential' : ['RES', 'APT', 'CONDO', 'CONDO APT', 'HOA', 'MOBILEHOME', 'MULTI', 'PUD', 'TOWNHOME'],
        'Commercial' : ['BUS CONDO', 'BUS PUD', 'BUSINESS', 'MORTUARY'],
        'Industrial' : ['UTILITY']
    }

    errorPtsDict = {}

    checkRequiredFields(slcoAddPts, slcoAddFLDS)
    truncateOldCountyPts(agrcAddPts_SLCO)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_SLCO, agrcAddFLDS)

    with arcpy.da.SearchCursor(slcoAddPts, slcoAddFLDS) as sCursor_slco:
        for row in sCursor_slco:
            if row[16] == 1 and row[14] not in errorList:

                if '-' in row[14]:
                    continue

                addNum = row[14]

                if '/' in row[1]:
                    addNumSuf = row[1].split('/')
                    addNumSuf = '{}/{}'.format(addNumSuf[0][-1], addNumSuf[1][0])
                    addNum = addNum.replace('-{}'.format(addNumSuf), '')
                else:
                    addNumSuf = ''
                preDir = returnKey(row[17], dirs)

                streetType = returnKey(row[19], sTypeDir)
                if row[19] == 'WY':
                    streetType = 'WAY'
                if row[19] == 'CNTR':
                    streetType = 'CTR'
                sufDir = returnKey(row[20], dirs)

                streetName = row[18]
                if streetName in fixDict:
                    streetName = fixDict[streetName]
                if streetName in aveDict and zip == '84103':
                    streetName = aveDict[streetName]

                if streetName.startswith('HWY '):
                    streetType = ''

                if streetType == '' and row[19] in dirs:
                    sufDir = row[19]
                if sufDir == '' and row[20] in sTypeDir:
                    streetType = row[20]

                if row[15] in fixDict and streetName == 'PARK':
                    streetType = 'PL'
                    sufDir = returnKey(row[15][10:], dirs)
                if row[15] in fixDict and streetName == 'SUNRISE':
                    streetType = 'PL'
                    sufDir = returnKey(row[15][13:], dirs)
                if row[15] in fixDict and streetName == 'SWEET BASIL':
                    sufDir = returnKey(row[15][12:], dirs)

                if streetName == 'SEGOLILY':
                    streetName = 'SEGO LILY'

        #-------Error Points---------------
                if row[11] == row[20]:
                    addressErrors = errorPtsDict.setdefault(row[1], [])
                    addressErrors.extend(['predir = sufdir', row[12]])
                if row[15] not in row[1]:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[15], row[3]), [])
                    addressErrors.extend(['Mixed street names', row[12]])
                if row[19] not in sTypeList and row[19] not in errorList and row[19] != 'WY':
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[19], row[3]), [])
                    addressErrors.extend(['bad street type', row[12]])
        #-----------------------------------------------------------------------

                if preDir == sufDir:
                    continue

                unitId = removeBadValues(row[2], errorList)

                if row[8] == 'CONDO APT':
                    unitType = 'APT'
                if row[8] == 'MOBILEHOME':
                    unitType = 'TRLR'
                else:
                    unitType = returnKey(row[8], unitTypeDir)

#----Old----------------------------------------------------------------------------------------
            # if row[1] not in errorList or row[14] not in errorList:
            #     address = parse_address.parse(row[1])
            #
            #     if address.houseNumber != '0' and '-' not in address.houseNumber:
            #         addNum = address.houseNumber
            #         streetName = address.streetName
            #
            #         if streetName in fixDict:
            #             streetName = fixDict[streetName]
            #         if streetName in aveDict and zip == '84103':
            #             streetName = aveDict[streetName]
            #
            #         if '/' in row[1]:
            #             addNumSuf = row[1].split('/')
            #             addNumSuf = '{}/{}'.format(addNumSuf[0][-1], addNumSuf[1][0])
            #             addNum = addNum.replace('-{}'.format(addNumSuf), '')
            #         else:
            #             addNumSuf = ''
            #
            #         preDir = address.prefixDirection
            #         if preDir == None:
            #             preDir = ''
            #         streetType = address.suffixType
            #         if streetType == None:
            #             streetType = ''
            #         sufDir = address.suffixDirection
            #         if sufDir == None:
            #             sufDir = ''
            #
            #         if row[15] in fixDict and streetName == 'PARK':
            #             streetType = 'PL'
            #             sufDir = returnKey(row[15][10:], dirs)
            #
            #         if row[2] not in errorList:
            #             unitId = row[2]
            #         else:
            #             unitId = ''
            #
            #         if row[8] == 'CONDO APT':
            #             unitType = 'APT'
            #         if row[8] == 'MOBILEHOME':
            #             unitType = 'TRLR'
            #         else:
            #             unitType = returnKey(row[8], unitTypeDir)

                if unitType != '' and unitId != '':
                    fulladd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, streetName, sufDir, streetType, unitType, unitId)
                elif unitId != '':
                    fulladd = '{} {} {} {} {} {} # {}'.format(addNum, addNumSuf, preDir, streetName, sufDir, streetType, unitId)
                elif row[15] in fixDict and streetName == 'PARK':
                    fulladd = '{} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, streetName, streetType, sufDir, unitId)
                elif row[15] in fixDict and streetName == 'SUNRISE':
                    fulladd = '{} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, streetName, streetType, sufDir, unitId)
                elif streetName.startswith('HWY '):
                    fulladd = '{} {} {} {}'.format(addNum, addNumSuf, preDir, streetName)
                else:
                    fulladd = '{} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, streetName, sufDir, streetType)

                fulladd = ' '.join(fulladd.split())

                ptType = returnKey(row[8], ptTypeDic)

                zip = row[13]
                landmark = removeBadValues(row[6], errorList)
                if landmark == '':
                    landmark = removeBadValues(row[7], errorList)
                building = removeBadValues(row[4], errorList)

                addSys = ''
                utAddId = ''
                city = ''
                fips = '49035'
                state = 'UT'
                ptLocation = 'Unknown'
                structure = 'Unknown'
                parcel = row[0]
                addSource = 'SALT LAKE COUNTY'
                loadDate = today
                status = 'COMPLETE'
                editor = row[9]
                modified = row[10]
                shp = row[12]

                iCursor.insertRow((addSys, utAddId, fulladd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                                   unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                                   status, editor, modified, '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'SLCounty_ErrorPts.shp', 'ADDRESS', slcoAddPts)

    del iCursor
    del sCursor_slco

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_SLCO, inputDict)
    addBaseAddress(agrcAddPts_SLCO)
    deleteDuplicatePts(agrcAddPts_SLCO, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def murrayCity_AddressPts():
    murrayCityAddPts = r'C:\ZBECK\Addressing\SaltLake\MurrayCity\Murray.gdb\LocationMaster_Addresses'
    agrcAddPts_murrayCity = r'C:\ZBECK\Addressing\SaltLake\MurrayCity\Murray.gdb\AddressPoints_MurrayCity'
    cntyFldr = r'C:\ZBECK\Addressing\SaltLake\MurrayCity'

    murrayCityAddFLDS = ['House_Num', 'Address_Dir', 'Street_Nam', 'Street_Suf', 'Unit', 'Address', 'ZIPCode', 'SHAPE@']

    def createCityRoadSet(cityName):
        sgidRds = r'D:\Basemaps\Data\SGID10_WGS.gdb\Roads'
        #sgidRds = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde\SGID10.TRANSPORTATION.Roads'
        rdFlds = ['INCMUNI_L', 'NAME', 'INCMUNI_R']
        rdList = []

        with arcpy.da.SearchCursor(sgidRds, rdFlds) as sCursorRds:
            for rowRd in sCursorRds:
                if rowRd[0] == cityName or rowRd[2] == cityName and rowRd[1] != '':
                    rdList.append(rowRd[1].upper())
        cityRdNameSet = set(rdList)
        return cityRdNameSet

    checkRequiredFields(murrayCityAddPts, murrayCityAddFLDS)
    truncateOldCountyPts(agrcAddPts_murrayCity)

    errorPtsDict = {}
    rdSet = createCityRoadSet('Murray')

    leadingSpaceDirs = []
    for d in dirs:
        leadingSpaceDirs.append(' {}'.format(d))

    iCursor = arcpy.da.InsertCursor(agrcAddPts_murrayCity, agrcAddFLDS)

    with arcpy.da.SearchCursor(murrayCityAddPts, murrayCityAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] not in errorList:
                addNum = row[0]
                preDir = row[1].strip()
                sName = removeNone(row[2]).strip().upper()
                sufDir = ''
                if sName.endswith((tuple(leadingSpaceDirs))):
                    sufDir = sName[-1]
                    sName = sName[:-2]

                sType = returnKey(removeNone(row[3]).upper(), sTypeDir)
                unit = removeNone(row[4]).upper()

                if unit != '':
                    fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sufDir, sType, unit)
                else:
                    fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType)

                fullAdd = ' '.join(fullAdd.split())

                loadDate = today
                shp = row[7]

                murrayZip = row[6]
                murrayFullAdd = row[5].upper().strip()

                if ' WY ' not in murrayFullAdd and murrayFullAdd.strip() != fullAdd:
                    print murrayFullAdd + ' | ' + fullAdd
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[5], fullAdd), [])
                    addressErrors.extend(['address components != Address field', row[7]])
                if sName not in rdSet:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(sName, row[5]), [])
                    addressErrors.extend(['Street name not found in roads', row[7]])

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '',
                                   unit, '', '', '49035', 'UT', murrayZip, '', '', '', 'MURRAY CITY', loadDate, '', '', None,
                                   '', '', '', shp))

    del iCursor
    del sCursor

    inputDict = {
        'AddSystem': ['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
        'ZipCode': ['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
        'USNG': ['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_murrayCity, inputDict)
    deleteDuplicatePts(agrcAddPts_murrayCity, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])

    createErrorPts(errorPtsDict, cntyFldr, 'MurrayCity_ErrorPts.shp', 'EXAMPLE', murrayCityAddPts)


def murrayCity_ParcelPts():
    murrayCityParPts = r'C:\ZBECK\Addressing\SaltLake\MurrayCity\Murray.gdb\ParcelCentroid'
    agrcParPts_murrayCity = r'C:\ZBECK\Addressing\SaltLake\MurrayCity\Murray.gdb\ParcelPoints_MurrayCity'
    cntyFldr = r'C:\ZBECK\Addressing\SaltLake\MurrayCity'

    murrayCityAddFLDS = ['House_Num', 'Address_Dir', 'Street_Name', 'Street_Suf', 'Unit', 'prop_location', 'Zipcode', 'SHAPE@']

    def createCityRoadSet(cityName):
        sgidRds = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde\SGID10.TRANSPORTATION.Roads'
        rdFlds = ['INCMUNI_L', 'NAME', 'INCMUNI_R']
        rdList = []

        with arcpy.da.SearchCursor(sgidRds, rdFlds) as sCursorRds:
            for rowRd in sCursorRds:
                if rowRd[0] == cityName or rowRd[2] == cityName and rowRd[1] != '':
                    rdList.append(rowRd[1].upper())
        cityRdNameSet = set(rdList)
        return cityRdNameSet

    checkRequiredFields(murrayCityParPts, murrayCityAddFLDS)
    truncateOldCountyPts(agrcParPts_murrayCity)

    errorPtsDict = {}
    rdSet = createCityRoadSet('Murray')

    leadingSpaceDirs = []
    for d in dirs:
        leadingSpaceDirs.append(' {}'.format(d))

    iCursor = arcpy.da.InsertCursor(agrcParPts_murrayCity, agrcAddFLDS)

    with arcpy.da.SearchCursor(murrayCityParPts, murrayCityAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] not in errorList:
                addNum = row[0]
                preDir = removeNone(row[1]).strip()
                sName = removeNone(row[2]).strip().upper()
                sufDir = ''
                if sName.endswith((tuple(leadingSpaceDirs))):
                    sufDir = sName[-1]
                    sName = sName[:-2]

                sType = returnKey(removeNone(row[3]).upper(), sTypeDir)
                unit = removeNone(row[4]).upper()

                if unit != '':
                    fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sufDir, sType, unit)
                else:
                    fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType)

                fullAdd = ' '.join(fullAdd.split())

                loadDate = today
                shp = row[7]

                murrayZip = row[6]
                murrayFullAdd = removeNone(row[5]).upper().strip()

                if ' WY' not in murrayFullAdd and murrayFullAdd.strip() != fullAdd:
                    print murrayFullAdd + ' | ' + fullAdd
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[5], fullAdd), [])
                    addressErrors.extend(['address components != Address field', row[7]])
                if sName not in rdSet:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(sName, row[5]), [])
                    addressErrors.extend(['Street name not found in roads', row[7]])

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '',
                                   unit, '', '', '49035', 'UT', murrayZip, '', '', '', 'MURRAY CITY', loadDate, '', '',
                                   None, '', '', '', shp))

    del iCursor
    del sCursor

    inputDict = {
        'AddSystem': ['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
        'ZipCode': ['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
        'USNG': ['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcParPts_murrayCity, inputDict)
    deleteDuplicatePts(agrcParPts_murrayCity, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])

    createErrorPts(errorPtsDict, cntyFldr, 'MurrayCity_ParcelErrorPts.shp', 'EXAMPLE', murrayCityParPts)


def sevierCounty():
    sevierCoAddPts = r'C:\ZBECK\Addressing\Sevier\SevierCounty.gdb\SevierCountyPts'
    agrcAddPts_sevierCo = r'C:\ZBECK\Addressing\Sevier\Sevier.gdb\AddressPoints_Sevier'

    sevierCoAddFLDS = ['HouseNumbe', 'Pre', 'Name', 'Dir', 'Type', 'Unit', 'PARCEL__', 'SHAPE@']

    checkRequiredFields(sevierCoAddPts, sevierCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_sevierCo)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_sevierCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(sevierCoAddPts, sevierCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] not in errorList:
                addNum = row[0]
                preDir = returnKey(row[1], dirs)
                sName = removeBadValues(row[2], errorList)
                sufDir = returnKey(row[3], dirs)
                sType = returnKey(row[4], sTypeDir)

                if sName.isdigit() == False:
                    sufDir = ''
                if sType != '':
                    sufDir = ''

                unitsRaw = row[5].strip()
                unitTuple = splitVals(unitsRaw, unitTypeList)
                unitType, unitID = unitTuple
                unitType = returnKey(unitType, unitTypeDir)


                if unitType == '' and unitID != '':
                    fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sufDir, sType, unitID)
                    fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = '{} {} {} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType, unitType, unitID)
                    fullAdd = ' '.join(fullAdd.split())

                loadDate = today
                parcel = row[6]
                shp = row[7]

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', \
                                   unitType, unitID, '', '', '49041', 'UT', '', '', '', parcel, \
                                   'SEVIER COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))

    del iCursor
    del sCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_sevierCo, inputDict)
    addBaseAddress(agrcAddPts_sevierCo)
    deleteDuplicatePts(agrcAddPts_sevierCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def summitCounty():
    summitCoAddPts = r'C:\ZBECK\Addressing\Summit\SummitCounty.gdb\AddressPoints'
    agrcAddPts_summitCo = r'C:\ZBECK\Addressing\Summit\Summit.gdb\AddressPoints_Summit'

    summitCoAddFLDS = ['ADDRNUM', 'ADDRNUMSUF', 'APARTMENT', 'ROADPREDIR', 'ROADNAME', 'ROADTYPE', 'ROADPOSTDIR',\
                       'FULLADDR', 'PLACENAME', 'POINTTYPE', 'LASTUPDATE', 'USNGCOORD', 'SHAPE@']

    checkRequiredFields(summitCoAddPts, summitCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_summitCo)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_summitCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(summitCoAddPts, summitCoAddFLDS) as sCursor_summit:
        for row in sCursor_summit:

            if row[0] in errorList or row[4] in errorList:
                continue

            addNum = row[0].strip()
            addNumSuf = removeBadValues(row[1], errorList)
            if addNumSuf != '':
                addNum = addNum.replace(addNumSuf, '').strip()
            preDir = checkWord(row[3], dirs)
            sName = removeBadValues(row[4], errorList).upper()
            #sType = removeBadValues(row[5], sTypeDir).upper()
            sType = returnKey(row[5], sTypeDir)
            sufDir = checkWord(row[6], dirs)

            if sName.isdigit() == False:
                if sType != '' and sufDir != '':
                    sufDir = ''

            unitNum = formatUnitID(row[2])

            fullAdd = '{} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sType, sufDir, unitNum)
            fullAdd = ' '.join(fullAdd.split())

            if row[9] == 'Condo or Unit':
                ptType = 'Residential'
            elif row[9] == 'Office or Suite':
                ptType = 'Commercial'
            else:
                ptType = 'Other'

            building = removeBadValues(row[8], errorList)
            modified = row[10]
            parcelID = row[11]
            loadDate = today
            shp = row[12]

            iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', building, \
                              '', unitNum.strip('# '), '', '', '49043', 'UT', '', ptType, '', parcelID, 'SUMMIT COUNTY', loadDate, \
                              'COMPLETE', '', modified, '', '', '', shp))


    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG': ['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_summitCo, inputDict)
    addBaseAddress(agrcAddPts_summitCo)
    deleteDuplicatePts(agrcAddPts_summitCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def tooeleCounty():

    rdSet = createRoadSet('49045')

    def formatRoute(word, d):
        for key, value in d.iteritems():
            if word in value:
                return key
        # if nothing is found
        return word

    def stripType(street, types):
        if len(street.split()) > 1:
            if ' {}'.format(street.split()[-1]) in types:
                type = street.split()[-1]
                return street.rstrip(type).strip()
        return street

    types = [' LOOP', ' ST', ' RD', ' PARKWAY', ' PKWY', ' RD', ' LANE', ' LN', ' CT', ' CIR', ' COVE', ' CR']

    tooeleCoAddPts = r'C:\ZBECK\Addressing\Tooele\TooeleCountyAddressPts.gdb\TC_AddressPts'
    agrcAddPts_tooeleCo = r'C:\ZBECK\Addressing\Tooele\Tooele.gdb\AddressPoints_Tooele'
    cntyFldr = r'C:\ZBECK\Addressing\Tooele'

    tooeleCoAddFLDS = ['HouseAddr', 'FullAddr', 'HouseNum', 'PreDir', 'StreetName', 'StreetType', 'SufDir', \
                       'UnitNumber', 'City', 'Parcel_ID', 'Structure', 'SHAPE@', 'OBJECTID', 'SP_UnitType']

    checkRequiredFields(tooeleCoAddPts, tooeleCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_tooeleCo)

    routeDict = {'HWY 36':['STATE HWY 36', 'STATE RTE 36', 'SR 36', 'SR36', 'SR36 ', 'HGIHWAY 36', 'UTAH STATE HWY-36'], \
                 'HWY 138':['SR-138 HWY', 'STATE HWY 138', 'SR-138'], 'HWY 196':['SR196', 'STATHWY 196'],\
                 'LINCOLN HWY':['LINCOLN HWY RTE 1913', 'LINCOLN HWY RTE 1919'], \
                 'HWY 112':['SR 112', 'STATHWY 112', 'STATE HWY 112'], 'HWY 199':['SR199'], 'HWY 73':['SR73']}

    separatorList = ['/', '-', '&']
    findSeparator = re.compile('|'.join(separatorList))

    errorPtsDict = {}

    unitList = [' APT ', ' BSMT ', ' BLDG ', ' DEPT ', ' FL ', ' FRNT ', ' HNGR ', ' LBBY ', ' OFC ', \
                ' RM ', ' STE ', ' TRLR ', ' UNIT ', ' UPPR ']
    unitSearch = re.compile('|'.join(unitList))

    #find unwanted directions (E 100 N, S 100, 100 W)
    exp = re.compile(r'(?:^[NSEW]\s)?(?:(.+)(\s[NSEW]$)|(.+$))')

    iCursor = arcpy.da.InsertCursor(agrcAddPts_tooeleCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(tooeleCoAddPts, tooeleCoAddFLDS) as sCursor:
        for row in sCursor:
            sufDir = ''
            addNumSuf = ''

            if row[4] not in errorList and row[2] not in errorList:#  row[2][:1].isdigit:
                sNameRAW = row[4].upper().strip()
                preDir = formatValues(row[3], dirs)
                if 'CLOCK' in row[4]:
                    sName = sNameRAW.replace('THRE', '3 ')
                    preDir = 'W'
                elif sNameRAW[0].isdigit() and ' ' in sNameRAW:
                    sName = formatAddressNumber(sNameRAW.split()[0])
                    sufDir = returnKey(sNameRAW.split()[1], dirs2)
                else:
                    sName = formatRoute(sNameRAW, routeDict)

                expMatches = re.findall(exp, sName)[0]
                if len(expMatches[0]) > 0:
                    sName = formatAddressNumber(expMatches[0])
                    if expMatches[1].strip() in dirs:
                        sufDir = expMatches[1].strip()
                else:
                    sName = expMatches[2]

                sName = stripType(sName, types)

                sType = formatValues(row[5], sTypeDir)
                if row[5] == 'WY':
                    sType = 'WAY'
                if sName[0].isdigit() and sName[-1].isdigit():
                    sType = ''

                unitID = removeBadValues((row[7]), errorList).upper()
                unitType = returnKey(row[13], unitTypeDir).upper()
                # findUnit = unitSearch.search(row[0])
                # unitType = ''
                # if row[13] != '':
                #     unitType = returnKey(removeBadValues(row[13], errorList).upper(), unitTypeDir)
                # if findUnit:
                #     unitType = findUnit.group(0).strip()

                city = removeBadValues(row[8], errorList)
                parcelID = removeBadValues(row[9], errorList)
                structure = removeBadValues(row[10], errorList)
                loadDate = today
                shp = row[11]

        #-------Log address errors
                if removeNone(row[4]).lstrip('0').upper() not in removeNone(row[1]):
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[4], row[1]), [])
                    addressErrors.extend(['Mixed street names', row[11]])
                if sName not in rdSet and 'HWY' not in sName:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[4],row[1]), [])
                    addressErrors.extend(['Street name not found in roads', row[11]])
                if row[3] == row[6] and row[3] not in errorList:
                    addressErrors = errorPtsDict.setdefault(row[1], [])
                    addressErrors.extend(['predir = sufdir', row[11]])
                # if removeNone(row[5]) != '' and removeNone(row[5]) not in sTypeDir:
                #     addressErrors = errorPtsDict.setdefault(row[1], [])
                #     addressErrors.extend(['Bad street type', row[11]])
        #----------------------------------------------------------------
                addNumRAW = row[2]

                separator = findSeparator.search(addNumRAW)

                if ' 1/2' in addNumRAW:
                    addNum = addNumRAW.split()[0]
                    addNumSuf = addNumRAW.split()[1]
                    fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sufDir, sType, unitType, unitID)
                    fullAdd = ' '.join(fullAdd.split())
                    iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                       unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                       'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))

                elif separator:
                    addNum = addNumRAW.split(separator.group(0))[0]
                    fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sufDir, sType, unitType, unitID)
                    fullAdd = ' '.join(fullAdd.split())
                    iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                       unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                       'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))

                    addNum = addNumRAW.split(separator.group(0))[1]
                    if addNum[0].isdigit():
                        fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sufDir, sType, unitType, unitID)
                        fullAdd = ' '.join(fullAdd.split())
                        iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                           unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                           'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))
                    else:
                        continue

                else:
                    if '#' in addNumRAW:
                        addNum = addNumRAW.split('#')[0]
                        fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sufDir, sType, unitType, unitID)
                        fullAdd = ' '.join(fullAdd.split())
                        iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                           unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                           'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))

                    elif addNumRAW[0].isdigit() == False:
                        print row[12]
                        continue

                    else:
                        addNum = addNumRAW
                        if sName in routeDict:
                            fullAdd = '{} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sufDir, unitType, unitID)
                            fullAdd = ' '.join(fullAdd.split())
                        elif unitType == '' and unitID.isdigit():
                            fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sufDir, sType, '#', unitID)
                            fullAdd = ' '.join(fullAdd.split())


                        else:
                            fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sufDir, sType, unitType, unitID)
                            fullAdd = ' '.join(fullAdd.split())

                        iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                           unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                           'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))


            else:
                print row[12]
                print 'what to do?'

        createErrorPts(errorPtsDict, cntyFldr, 'Tooele_ErrorPts.shp', 'EXAMPLE', tooeleCoAddPts)

    del iCursor
    del sCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_tooeleCo, inputDict)
    addBaseAddress(agrcAddPts_tooeleCo)
    deleteDuplicatePts(agrcAddPts_tooeleCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def utahCounty():

    utahCoAddPts = r'C:\ZBECK\Addressing\Utah\UtahCounty.gdb\AddressPnt'
    agrcAddPts_utahCo = r'C:\ZBECK\Addressing\Utah\Utah.gdb\AddressPoints_Utah'
    cntyFldr = r'C:\ZBECK\Addressing\Utah'

    sgidRds = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde\SGID10.TRANSPORTATION.Roads'

    utahCoAddFLDS = ['ADDRNUM', 'ROADPREDIR', 'ROADNAME', 'ROADTYPE', 'ROADPOSTDIR', 'ADDRTYPE', \
                     'UNITTYPE', 'UNITID', 'LASTUPDATE', 'SHAPE@', 'LASTEDITOR', 'FULLADDR']

    checkRequiredFields(utahCoAddPts, utahCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_utahCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49049')

    iCursor = arcpy.da.InsertCursor(agrcAddPts_utahCo, agrcAddFLDS)

    badType = {'AV':'AVE', 'LA':'LN', 'PKY':'PKWY', 'WY':'WAY'}
    addType = {'Building':'Rooftop', 'Parcel':'Parcel Centroid', 'Building Entrance':'Primary Structure Entrance', \
              'Driveway Turn-off':'Driveway Entrance', 'Unit, Condo or Suite':'Residential', 'Other':'Other', 'Unknown':'Unknown'}
    dirList = ['NORTH', 'SOUTH', 'EAST', 'WEST']

    with arcpy.da.SearchCursor(utahCoAddPts, utahCoAddFLDS) as sCursor_utah:
        for row in sCursor_utah:

            unitId = ''
            sType = ''
            sufDir = ''

            if row[0] not in errorList and row[2] not in errorList:
                #if row[3] in errorList and row[1] in errorList:
                if row[3] in errorList and row[1] in errorList and not returnKey(row[2].split()[-1], sTypeDir) in sTypeDir:
                    continue
                else:
                    if row[3] in badType:
                        sType =  badType[row[3]]
                    else:
                        sType = returnKey(row[3], sTypeDir)

                addNum = row[0]

                if ' ' in row[2]:
                    street = ' '.join(row[2].split()).upper()

                    if street.split()[0].isdigit() and street.split()[0] != '0':
                        street = street.split()[0]

                        if row[2].split()[-1] in dirList:
                            sufDir = row[2].split()[-1][:1]

                            if street.isdigit() == True:
                                sType = ''

                        else:
                            if row[2].split()[-1][:1] in dirs:
                                sufDir = row[2].split()[-1][:1]
                            else:
                                sufDir = ''

                    elif street.split()[0].isdigit() == False:
                            street = street
                            sufDir = ''

                    if '#' in street:
                        street = street.split()[0]
                        if street == 'STATE':
                            sType = 'ST'
                        unitId = '# ' + row[2].split('#')[-1]
                        unitId = ' '.join(unitId.split())

                else:
                    street = row[2]
                    sufDir = ''
                    if row[3] not in errorList:
                        if row[3] in badType:
                            sType = badType[row[3]]
                        else:
                            sType = returnKey(row[3], sTypeDir)

                # Fix streets with types in street name
                if returnKey(street.split()[-1], sTypeDir) in sTypeDir and sType == '':
                    sType = returnKey(street.split()[-1], sTypeDir)
                    street = ' '.join(street.split()[:1])

                # Add missing ST
                missingStSuf = ['CENTER', 'MAIN', 'STATE']
                if street in missingStSuf and sType == '':
                    sType = 'ST'

                if street.startswith(('SR ', 'US ')):
                    street = 'HWY {}'.format(street[3:])
                    sType = ''

                if row[1] in dirs:
                    preDir = row[1]
                else:
                    preDir = ''

                if row[4] not in errorList:
                    sufDir = row[4]
                    if ' {} '.format(sufDir) not in row[11]:
                        sufDir = ''

                if preDir in errorList and sufDir not in errorList:
                    continue

                if row[5] not in errorList:
                    ptLocation = addType[row[5]]
                else:
                    ptLocation = ''

                if row[6] not in errorList:
                    if returnKey(row[6].upper(), unitTypeDir) != '': # in unitTypeDir:
                        unitType = returnKey(row[6].upper(), unitTypeDir)
                        unitType_Abbrv = row[6].upper()
                    # else:
                    #     unitType = row[6].upper()
                    #     unitType_Abbrv = ''
                else:
                    unitType = ''
                    unitType_Abbrv = ''

                if row[7] not in errorList:
                    unitId = row[7]

                if unitId == '' and unitType != '':
                    unitType = ''

                loadDate = today
                status = 'COMPLETE'

                if row[10] not in errorList:
                    editor = row[10]
                else:
                    editor = ''

                modDate = row[8]

                if unitType == '' and unitId != '':
                    fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, street, sufDir, sType, unitId)
                    fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = '{} {} {} {} {} {} {}'.format(addNum, preDir, street, sufDir, sType, unitType, unitId)
                    fullAdd = ' '.join(fullAdd.split())

                shp = row[9]

                # -------Error Points---------------
                if preDir == sufDir and sType == '':
                    addressErrors = errorPtsDict.setdefault(row[1], [])
                    addressErrors.extend(['predir = sufdir', row[9]])
                if street not in removeNone(row[11]) and 'HWY' not in street and row[11] != None:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(street, row[11]), [])
                    addressErrors.extend(['Mixed street names', row[9]])
                if street not in rdSet and 'HWY' not in street:
                    addressErrors = errorPtsDict.setdefault(row[11], [])
                    addressErrors.extend(['Street name not found in roads', row[9]])
                if row[3] not in sTypeList and row[3] not in errorList and row[3] != 'WY' and row[3] != 'ALLEY':
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[11], row[3]), [])
                    addressErrors.extend(['bad street type', row[9]])
                # ------------------------------------

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, street, sType, sufDir, '', '', unitType, unitId, '', '', '49049', \
                                   'UT', ptLocation, '', '', '', 'UTAH COUNTY', loadDate, status, editor, modDate, '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'Utah_ErrorPts.shp', 'ADDRESS', utahCoAddPts)

    del iCursor
    del sCursor_utah


    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_utahCo, inputDict)
    addBaseAddress(agrcAddPts_utahCo)
    deleteDuplicatePts(agrcAddPts_utahCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def uintahCounty():
    uintahCoAddPts = r'C:\ZBECK\Addressing\Uintah\UintahCounty.gdb\Uintah_MAL_2018'
    agrcAddPts_uintahCo = r'C:\ZBECK\Addressing\Uintah\Uintah.gdb\AddressPoints_Uintah'
    cntyFldr = r'C:\ZBECK\Addressing\Uintah'

    sgidRds = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde\SGID10.TRANSPORTATION.Roads'

    uintahCoAddFLDS = ['HOUSENUMBE', 'STREETNAME', 'APARTMENT', 'ZIP', 'SHAPE@']

    checkRequiredFields(uintahCoAddPts, uintahCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_uintahCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49047')
    loadDate = today

    iCursor = arcpy.da.InsertCursor(agrcAddPts_uintahCo, agrcAddFLDS)


    with arcpy.da.SearchCursor(uintahCoAddPts, uintahCoAddFLDS) as sCursor_uintah:
        for row in sCursor_uintah:

            sufDir = ''
            sType = ''
            addNumSuf = ''

            if row[0] in errorList:
                continue

            addNum = row[0]
            if ' ' in addNum:
                if addNum.split()[1] == '1/2':
                    addNumSuf = '1/2'
                addNum = addNum.split()[0]

            sName = row[1].upper().strip()
            if sName.startswith(('N ', 'E ', 'S ', 'W ')):
                preDir = sName[0]
                sName_strp = sName[2:]
                if sName_strp.endswith((' N', ' E', ' S', ' W')):
                    sufDir = sName_strp[-1]
                    sName_strp = sName_strp[:-2]
                if sName_strp.endswith(tuple(leadingSpaceTypes)):
                    sType = sName_strp.split()[-1]
                    sName_strp = sName_strp.replace(' ' + sType, '')
            else:
                sType = returnKey(sName.split()[-1], sTypeDir)
                sName_strp = sName.replace(' ' + sType, '')

            if sName_strp not in rdSet and 'HWY' not in sName_strp:
                addressErrors = errorPtsDict.setdefault('{} | {}'.format(sName_strp, row[1]), [])
                addressErrors.extend(['Street name not found in roads', row[4]])
            if preDir == sufDir:
                addressErrors = errorPtsDict.setdefault(row[1], [])
                addressErrors.extend(['Pre and post directions are the same', row[4]])

            unitType = (removeNone(returnStart(row[2].upper(), unitTypeDir)))
            unitID = (row[2].upper().lstrip(unitType)).strip()
            if 'SPACE' in row[2].upper():
                unitType = 'SPC'
                unitID = row[2][6:]
            if 'ROOM' in row[2].upper():
                unitType = 'RM'
                unitID = row[2][5:]

            if unitType == '' and unitID != '':
                fullAdd = '{} {} {} {} {} {} # {}'.format(addNum, addNumSuf, preDir, sName_strp, sufDir, sType, unitID)
            else:
                fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName_strp, sufDir, sType, unitType, unitID)

            fullAdd = ' '.join(fullAdd.split())

            shp = row[4]

            iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName_strp, sType, sufDir, '', '', unitType, unitID, \
                               '', '', '49047', 'UT', '', '', '', '', 'UINTAH COUNTY', loadDate, 'COMPLETE', '', \
                               None, '', '', '', shp))

        createErrorPts(errorPtsDict, cntyFldr, 'Uintah_ErrorPts.shp', 'ADDRESS', uintahCoAddPts)

    del iCursor
    del sCursor_uintah

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_uintahCo, inputDict)
    addBaseAddress(agrcAddPts_uintahCo)
    deleteDuplicatePts(agrcAddPts_uintahCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def wasatchCounty():

    wasatchCoAddPts = r'C:\ZBECK\Addressing\Wasatch\WasatchCounty.gdb\WC_AddressPoints'
    agrcAddPts_wasatchCo = r'C:\ZBECK\Addressing\Wasatch\Wasatch.gdb\AddressPoints_Wasatch'
    cntyFldr = r'C:\ZBECK\Addressing\Wasatch'

    # wasatchCoAddFLDS = ['SiteAddID', 'FullAdd', 'AddrNum', 'AddrNumSuf', 'StreetName', 'StreetType', 'SuffixDir', 'Structure', \
    #                     'CreateDate', 'PlaceName', 'SHAPE@', 'FeatureTyp']
    wasatchCoAddFLDS = ['FullName', 'FullAdd', 'Building', 'UnitType', 'UnitID', 'FeatureTyp', 'SHAPE@']

    checkRequiredFields(wasatchCoAddPts, wasatchCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_wasatchCo)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_wasatchCo, agrcAddFLDS)

    wasatchExclude = [None, '', 'MM']

    errorPtsDict = {}

    def nullToEmpty(word):
        if word is None:
            word = ''
        return word

    with arcpy.da.SearchCursor(wasatchCoAddPts, wasatchCoAddFLDS) as sCursor_wasatchCo:
        for row in sCursor_wasatchCo:
            if row[1] not in wasatchExclude and row[5] != 'MM':
                if row[1][0].isdigit():
                    addNum = row[1].split(' ')[0]
                    address = parse_address.parse(row[1])
                    preDir = nullToEmpty(address.prefixDirection)
                    sName = address.streetName
                    if sName == '' or sName == None:
                        errorPtsDict[row[1]] = row[6]
                        continue
                    sName = sName.replace('SR ', 'HWY ').replace('US ', 'HWY ')
                    sufDir = nullToEmpty(address.suffixDirection)
                    sType = nullToEmpty(address.suffixType)

                    if preDir == sufDir and preDir != '':
                        #print 'preDir({}) = sufDir({})'.format(preDir, sufDir)
                        errorPtsDict[row[1]] = row[6]
                        continue

                    unitType = returnKey(row[3], unitTypeDir)
                    unitID = removeBadValues(row[4], errorList)

                    if unitType == '' and unitID != '':
                        fullAdd = '{} {} {} {} {} # {}'.format(addNum, preDir, sName, sType, sufDir, unitID)
                    elif unitType != '' and unitID != '':
                        fullAdd = '{} {} {} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir, unitType, unitID)
                    else:
                        fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir)

                    fullAdd = ' '.join(fullAdd.split())

                    loadDate = today
                    shp = row[6]

                    iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', unitType, unitID, '',
                                       '', '49051', 'UT', '', '', '', '', 'Wasatch County', loadDate, 'COMPLETE',\
                                       '', None, '', '', '', shp))

############# OLD SCHEMA
            # addNum = removeBadValues(row[2], errorList)
            #
            # if addNum in errorList or row[1] in errorList:
            #     continue
            # if row[11] == 'MM':
            #     continue
            # parcel = removeBadValues(row[0], errorList)
            # fullAdd = removeBadValues(row[1], errorList)
            # preDir = removeBadValues(row[3], errorList)
            # sName = removeBadValues(row[4], errorList)
            # sType = removeBadValues(row[5], errorList)
            # sufDir = removeBadValues(row[6], errorList)
            # structure = removeBadValues(row[7], errorList).title()
            # if row[8] != None:
            #     modDate = row[8]
            # else:
            #     modDate = None
            # landmark = removeBadValues(row[9], errorList).upper()
            # loadDate = today
            # shp = row[10]
            #
            # iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, landmark, '', '', '', '', '', '49051', 'UT', '', \
            #                    '', structure, parcel, 'Wasatch County', loadDate, 'COMPLETE', '', modDate, '', '', '', shp))

    print errorPtsDict.keys()
    createErrorPts(errorPtsDict, cntyFldr, 'Wasatch_ErrorPts.shp', wasatchCoAddFLDS[1], wasatchCoAddPts)
    del iCursor
    del sCursor_wasatchCo


    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_wasatchCo, inputDict)
    addBaseAddress(agrcAddPts_wasatchCo)
    deleteDuplicatePts(agrcAddPts_wasatchCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def washingtonCounty():

    washcoAddPts = r'C:\ZBECK\Addressing\Washington\WashingtonCounty.gdb\WashCo_SiteAddressPoint'
    agrcAddPts_washCo = r'C:\ZBECK\Addressing\Washington\Washington.gdb\AddressPoints_Washington'
    cntyFldr = r'C:\ZBECK\Addressing\Washington'

    washcoAddFLDS = ['TAX_ID', 'ADDRNUM', 'PREFIXDIR', 'STREETNAME', 'STREETTYPE', 'UNITTYPE', 'UNITID', 'PLACENAME', \
                     'LASTUPDATE', 'SHAPE@', 'OBJECTID', 'SUFFIXDIR', 'FULLADDR', 'FULLNAME']

    checkRequiredFields(washcoAddPts, washcoAddFLDS)
    truncateOldCountyPts(agrcAddPts_washCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49053')

    dirList = ['N', 'S', 'E', 'W']
    sTypeList = ['ALY', 'ANX', 'AVE', 'BLVD', 'BYP', 'CSWY', 'CIR', 'CT', 'CTR', 'CV', 'XING', 'DR', 'EST', 'ESTS', \
                 'EXPY', 'FWY', 'HWY', 'JCT', 'LNDG', 'LN', 'LOOP', 'PARK', 'PKWY', 'PL', 'RAMP', 'RD', 'RTE', \
                 'ROW', 'SQ', 'ST', 'TER', 'TRWY', 'TRL', 'TUNL', 'TPKE', 'WAY']

    iCursor = arcpy.da.InsertCursor(agrcAddPts_washCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(washcoAddPts, washcoAddFLDS) as sCursor_washco:
        for row in sCursor_washco:

            if row[1] not in errorList and row[1].isdigit() and row[3] not in errorList:
                addNum = formatAddressNumber(row[1])
                preDir = returnKey(row[2], dirs)

                if row[3] not in errorList:
                    if row[3].endswith((' N', ' S', ' E', ' W')):
                        sName = row[3][:-1].strip().upper()
                        sufDir = row[3][-1]
                    else:
                        sName = row[3].upper().strip()
                        sufDir = returnKey(row[11], dirs)
                else:
                    continue

                if sName[0].isdigit():
                    sType = ''
                else:
                    if row[4] == 'RW':
                        sType = 'ROW'
                    elif row[4] != None:
                        sType = returnKey(row[4].upper(), sTypeDir)
                    else:
                        sType = ''

                if sName.startswith('SR-'):
                    sName = sName.replace('-', ' ')

                if sName[0].isdigit() == False:
                    sufDir = ''

                unitType = removeBadValues(row[5], errorList)
                if unitType == 'CONDO':
                    unitType = 'UNIT'
                else:
                    unitType = returnKey(unitType, unitTypeDir)
                    if unitType == 'BLDG':
                        unitType = 'STE'

                unitID = removeBadValues(row[6], errorList)

                parcel = removeBadValues(row[0], errorList)

                if unitType == '' and unitID != '':
                   unitID_hash = '# {}'.format(unitID)
                   fullAdd = '{} {} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir, unitID_hash)
                elif unitType != '' and unitID != '':
                   fullAdd = '{} {} {} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir, unitType, unitID)
                else:
                   fullAdd = '{} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir)

                fullAdd = ' '.join(fullAdd.split())

                landmark = removeBadValues(row[7], errorList)
                date = today
                modDate = row[8]

                shp = row[9]

                if  row[2] == row[11] and preDir != '':
                    addressErrors = errorPtsDict.setdefault(row[12], [])
                    addressErrors.extend(['prefix = suffix', row[9]])
                if row[11] == '' and row[4] == '':
                    addressErrors = errorPtsDict.setdefault(row[12], [])
                    addressErrors.extend(['missing street type?', row[9]])
                if row[3].upper() not in row[12].upper():
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[3], row[12]), [])
                    addressErrors.extend(['mixed street names', row[9]])
                if sName not in rdSet:
                    addressErrors = errorPtsDict.setdefault('{} | {}'.format(sName, row[12]), [])
                    addressErrors.extend(['street name not in roads', row[9]])

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, landmark, '', unitType, unitID, '', '', '49053', 'UT', 'Unknown', \
                                   'Unknown', 'Unknown', parcel, 'WASHINGTON COUNTY', date, 'COMPLETE', '', modDate, '', '', '', shp))

        print errorPtsDict
        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Washington_ErrorPts.shp', washcoAddFLDS[12], washcoAddPts)

    del iCursor
    del sCursor_washco

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_washCo, inputDict)
    addBaseAddress(agrcAddPts_washCo)
    deleteDuplicatePts(agrcAddPts_washCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_washCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Washington_ErrorPts.shp'), errorFlds, dupePts)


def wayneCounty():
    wayneCoAddPts = r'C:\ZBECK\Addressing\Wayne\WayneCounty.gdb\WayneCoPts'
    agrcAddPts_wayneCo = r'C:\ZBECK\Addressing\Wayne\Wayne.gdb\AddressPoints_Wayne'

    wayneCoAddFLDS = ['numb', 'street', 'Address', 'TYPE', 'SHAPE@', 'COMMENT']

    checkRequiredFields(wayneCoAddPts, wayneCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_wayneCo)

    ptTypeDict = {
        'Residential':['HOUSE', 'TRAILER'],
        'Commercial':['BUSINESS', 'MOTEL', 'RENTAL'],
        'Industrial':['GRAVEL PIT'],
        'Other':['AIRPORT', 'BLDG', 'BUILDING', 'CABIN', 'CAMPGRND', 'CELL TOWER', 'CHURCH', 'FAIR/RODEO GROUNDS/PARK', \
                 'FREMONT', 'GOVERNMENT', 'RESTROOM', 'SHED', 'TRAIL', 'TRAILHEAD', 'VACNET LAND', 'WATER TANK']
    }

    iCursor = arcpy.da.InsertCursor(agrcAddPts_wayneCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(wayneCoAddPts, wayneCoAddFLDS) as sCursor:
        for row in sCursor:

            unitType = ''
            unitID = ''

            if row[2] not in errorList:
                address = parse_address.parse(row[2])
                fullAdd = ' '.join(row[2].split())

                addNum = address.houseNumber
                preDir = address.prefixDirection
                if preDir == None:
                    preDir = ''
                sName = address.streetName
                if sName.startswith('SR '):
                    sName = sName.replace('SR ', 'HIGHWAY ')
                    fullAdd = fullAdd.replace('SR ', 'HIGHWAY ')
                sufDir = address.suffixDirection
                if sufDir == None:
                    sufDir = ''
                sType = address.suffixType
                if sType == None:
                    sType = ''
                if ' UNIT ' in row[2]:
                    unitType = 'UNIT'
                    unitID = row[2].split()[-1]
                if 'SUITE ' in row[5]:
                    unitType = 'STE'
                    unitID = row[5].strip('SUITE ')[0]
                    if ' SUITE ' not in row[2]:
                        fullAdd = '{} {}'.format(fullAdd, unitType)
                    fullAdd = '{} {}'.format(fullAdd, unitID).replace('{} {}'.format('SUITE', unitID), 'STE')


                ptType = returnKey(row[3], ptTypeDict)
                modDate = None
                loadDate = today
                source = 'WAYNE COUNTY'
                shp = row[4]

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', unitType, \
                                   unitID, '', '', '49055', 'UT', '', ptType, '', '', 'WAYNE COUNTY', loadDate, 'COMPLETE', \
                                   '', modDate, '', '', '', shp))

        del sCursor
        del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_wayneCo, inputDict)


def weberCounty():

   weberCoAddPts = r'C:\ZBECK\Addressing\Weber\WeberCounty.gdb\WeberAddressPoints'
   agrcAddPts_weberCo = r'C:\ZBECK\Addressing\Weber\Weber.gdb\AddressPoints_Weber'
   cntyFldr = r'C:\ZBECK\Addressing\Weber'

   weberCoAddFLDS = ['ADDR_HN', 'ADDR_PD', 'ADDR_SN', 'ADDR_ST', 'ADDR_SD', 'PT_ADD', 'PLCMT_METH', 'WEBER_DATE', 'ADDRESS_TY', \
                     'ZIP', 'PARCEL_ID', 'EDIT_DATE', 'SHAPE@', 'OBJECTID_1', 'NAME', 'UNIT', 'UNIT_NUM', 'OBJECTID_1']

   ptTypeDict = {'BUS':'Commercial', 'RESTAURANT':'Commercial', 'RES':'Residential'}

   checkRequiredFields(weberCoAddPts, weberCoAddFLDS)
   truncateOldCountyPts(agrcAddPts_weberCo)

   iCursor = arcpy.da.InsertCursor(agrcAddPts_weberCo, agrcAddFLDS)

   errorPtsDict = {}
   rdSet = createRoadSet('49057')

   numberedUnits = ['APT', 'FLR', 'RM', 'STE', 'UNIT']

   badUnits = ['VETERANS UPWARD', 'UPWARD BOUND', 'Units', 'A&B', 'SOCIAL SCIENCE', 'Security gate', 'RESIDENTIAL', 'resident', \
               'RESIDENCE HALL', 'RECEIVING', 'PARKING', 'POLICE', 'PT', 'Private gate', 'PKWY', 'Parking Unit', 'Limited CA', \
               'INFORMATION', 'HURST CENTER', 'FINE ART STUDIO', 'Common Area', 'Commercial', 'ANNEX', '00', '0']
   reUnits = re.compile('|'.join(unitTypeDir))

   with arcpy.da.SearchCursor(weberCoAddPts, weberCoAddFLDS) as sCursor_weber:
       for row in sCursor_weber:

           if row[0] not in errorList and row[2] not in errorList:
               if row[5] not in errorList:
                   address = parse_address.parse(row[5])

               addNum = row[0]
               addNumSuf = ''
               if len(addNum.split()) > 1:
                   addNumSuf = addNum.split()[1]
                   addNum = addNum.split()[0]

               sName = row[2].upper()
               if 'HWY' not in sName and sName not in rdSet:
                   addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[5]), [])
                   addressErrors.extend(['street name not found in roads', row[12]])

               if sName == 'CENTURY MHP':
                   landmark = sName
                   sName = address.streetName
                   addNum = address.houseNumber
               else:
                   landmark = removeBadValues(row[14], errorList)

               preDir = formatValues(row[1], dirs)
               sType = returnKey(row[3], sTypeDir)
               if sType == 'WY':
                   sType = 'WAY'
               if row[4] == 'RD':
                   sType = 'RD'
                   addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[4], row[5]), [])
                   addressErrors.extend(['bad value in ADDR_SD', row[12]])

               sufDir = returnKey(row[4].strip(), dirs)

               # if sName.endswith((tuple(leadingSpaceTypes))) and row[3] != 'ST':
               #     addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[5]), [])
               #     addressErrors.extend(['street type in street name?', row[12]])

               if sName[-1].isdigit():
                   sType = ''
               if sType != '':
                   sufDir = ''
               if 'HWY' in sName:
                   sType = ''
                   sufDir = ''

               if preDir == sufDir and sType == '' and preDir != '':
                   print 'preDir({}) = sufDir({})'.format(preDir, sufDir)
                   addressErrors = errorPtsDict.setdefault('{} {} | {}'.format(row[1], row[4], row[5]), [])
                   addressErrors.extend(['prefix = suffix', row[12]])
                   continue

               unitType = ''
               building = ''
               ptType = ''

               unitTypeRaw = removeBadValues(row[15], badUnits).strip('#').strip()
               unitId = removeBadValues(row[16], badUnits).strip('#')

               unitSearch = re.search(reUnits, unitTypeRaw)
               if unitSearch != None:
                   unitType = unitSearch.group(0)
                   typeRemainder = unitTypeRaw.replace('{}'.format(unitType), '').strip()

                   if unitTypeRaw.strip(unitType) != '':
                       unitId = '{}{}'.format(typeRemainder, unitId).strip()

                   if unitType == 'BLDG':
                       building = unitTypeRaw
                       unitType = ''
                       unitId = ''
                       if ' ' not in building:
                           building = building.replace('BLDG', 'BLDG ').strip()

                   if row[16][:4] == 'STE ':
                       unitType = 'STE'
                       unitId = row[16].replace('STE', '').strip()
                       print unitId

               else:
                   if unitTypeRaw == '1' and unitId == '':
                       unitTypeRaw = ''
                   if unitTypeRaw != unitId:
                       unitId = '{}{}'.format(unitTypeRaw, unitId)

               if unitId == '' and unitType != '':
                   unitType = ''

               # ----v2 Unit Types and Id's----
               # if row[8] not in errorList:
               #     unitsRaw = row[8].upper().strip()
               #     if unitsRaw.startswith('#'):
               #         unitID = str(unitsRaw).translate(None, '# ')
               #     elif unitsRaw[0].isdigit():
               #         unitID = unitsRaw
               #     elif len(unitsRaw.split()) > 1:
               #         print unitsRaw
               #         if unitsRaw.split()[0] in unitTypeDir:
               #             unitType = unitsRaw.split()[0]
               #             unitID = unitsRaw.split()[1]
               #         if unitsRaw.split()[0] == 'BLDG':
               #             building = unitsRaw.split('-')[0]
               #             unitType = 'STE'
               #             unitID = unitsRaw[-1]
               #     elif unitsRaw in ptTypeDict:
               #         ptType = ptTypeDict[unitsRaw]
               #     else:
               #         landmark = unitsRaw

               # ----v1 Unit Types and Id's----
               # if row[8] not in errorList:
               #     if returnKey(row[8].upper().split()[0], unitTypeDir) != '':
               #         unitLong = row[8].upper()
               #         if len(unitLong.split()) > 3:
               #             building = '{} {}'.format(returnKey(unitLong.split()[0], unitTypeDir), unitLong.split()[1])
               #             unitType = returnKey(unitLong.split()[2], unitTypeDir)
               #             unitID = unitLong.split()[3]
               #             if unitType == 'U':
               #                 unitType = 'UNIT'
               #                 unitID = unitLong.split()[3]
               #         elif len(unitLong.split()) > 1:
               #             if returnKey(unitLong.split()[0], unitTypeDir) == 'BLDG':
               #                 if '-' in unitLong:
               #                     unitLong = unitLong.replace('-', ' ')
               #                     building = '{} {}'.format(returnKey(unitLong.split()[0], unitTypeDir), unitLong.split()[1])
               #                     unitType = returnKey(unitLong.split()[2], unitTypeDir)
               #                     unitID = unitLong.split()[3]
               #             else:
               #                 unitType = returnKey(unitLong.split()[0], unitTypeDir)
               #                 unitID = unitLong.split()[1]
               #
               #         else:
               #             unitType = returnKey(unitLong.split()[0], unitTypeDir)
               #             # if unitLong not in unitTypeDir:
               #             #     unitID = unitLong
               #             # else:
               #             #     unitID = ''
               #
               #     elif row[8].startswith('#') or row[8].isdigit():
               #         #unitIDHash = formatUnitID(row[8])
               #         unitID = row[8].strip('#').lstrip(' ')
               #
               #     elif row[8][:3] in unitTypeDir and len(row[8]) <= 7:
               #         unitType = returnKey(row[8][:3], unitTypeDir)
               #         if len(row[8]) > 3:
               #             unitID = row[8][3:]
               #     elif len(row[8]) <= 6 and row[8] != 'SCHOOL':
               #         unitID = row[8].strip(' ').strip('#').lstrip(' ')
               #         if unitID == 'RES':
               #             unitID = ''
               #             ptType = 'Residential'
               #         if unitID == 'BUS':
               #             unitID = ''
               #             ptType = 'Commercial'
               #
               # if unitID == '' and unitType in numberedUnits:
               #     unitType = ''

               if unitType == '' and unitId != '':
                   fullAdd = '{} {} {} {} {} {} {} # {}'.format(addNum, addNumSuf, preDir, sName, sType, sufDir, unitType, unitId)
                   fullAdd = ' '.join(fullAdd.split())
               elif unitType == 'BLDG' and unitId != '':
                   fullAdd = '{} {} {} {} {} {} # {}'.format(addNum, addNumSuf, preDir, sName, sType, sufDir, unitId)
                   fullAdd = ' '.join(fullAdd.split())
               elif unitType == 'BLDG' and unitId == '':
                   fullAdd = '{} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sType, sufDir, unitId)
                   fullAdd = ' '.join(fullAdd.split())
               else:
                   fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sType, sufDir, unitType, unitId)
                   fullAdd = ' '.join(fullAdd.split())

               parcel = row[10]
               loadDate = today
               modDate = row[11]
               shp = row[12]


               if row[3] == '' and row[4] == '':
                   addressErrors = errorPtsDict.setdefault(row[5], [])
                   addressErrors.extend(['missing street type?', row[12]])
               if row[2].upper() not in row[5].upper():
                   addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[2], row[5]), [])
                   addressErrors.extend(['mixed street names', row[12]])

               iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, landmark, building, unitType, \
                                  unitId, '', '', '49057', 'UT', '', ptType, '', parcel, 'WEBER COUNTY', loadDate, 'COMPLETE', \
                                  '', modDate, '', '', '', shp))

       print errorPtsDict
       createErrorPts(errorPtsDict, cntyFldr, 'Weber_ErrorPts.shp', 'Address', weberCoAddPts)

   del iCursor

   polyAttributesDict = {
   'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
   'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
   'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
   'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
   }

   addPolyAttributes(sgid10, agrcAddPts_weberCo, polyAttributesDict)
   addBaseAddress(agrcAddPts_weberCo)
   deleteDuplicatePts(agrcAddPts_weberCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def checkRequiredFields(inCounty, requiredFlds):

    countyFlds = arcpy.ListFields(inCounty)
    countyFldList = []

    for countyFld in countyFlds:
        countyFldList.append(countyFld.name)
    for fld in requiredFlds:
        if fld not in countyFldList and fld != 'SHAPE@':
            sys.exit(fld + ' Is a requided field MISSING from ' + inCounty)

def addPolyAttributes(sgid10, agrcAddPts, polyDict):

    for input in polyDict:

        print 'Starting ' + polyDict[input][0]

        addPtFL = arcpy.MakeFeatureLayer_management(agrcAddPts)

        polyFC = sgid10 + '\\' + polyDict[input][0]
        polyFL = arcpy.MakeFeatureLayer_management(polyFC)
        polyFL = arcpy.SelectLayerByLocation_management(polyFL, 'INTERSECT', addPtFL, '', 'NEW_SELECTION')

        polyFLD = polyDict[input][1]
        ptFLD = [input]

        scursor = arcpy.da.SearchCursor(polyFL, polyFLD)

        for polys in sorted(set(scursor)):
            uniquePoly = ''.join(polys)
            sql = """"{}" = '{}'""".format(polyFLD, uniquePoly)

            arcpy.SelectLayerByAttribute_management(polyFL, "NEW_SELECTION", sql)
            arcpy.SelectLayerByLocation_management(addPtFL, 'WITHIN', polyFL, '', 'NEW_SELECTION')

            ucursor = arcpy.da.UpdateCursor(addPtFL, ptFLD)

            for urow in ucursor:
                urow[0] = uniquePoly

                ucursor.updateRow(urow)

            del ucursor
        del scursor
        del polyFL

    flds = ['AddSystem', 'UTAddPtID', 'FullAdd']
    with arcpy.da.UpdateCursor(agrcAddPts, flds) as uCursor:

        for urow in uCursor:
            urow[1] = urow[0] + ' | ' + urow[2]

            uCursor.updateRow(urow)

        del uCursor



#beaverCounty()   #Complete w/error points
#boxElderCounty()  #Complete w/error points
#cacheCounty()  #Complete w/error points
#carbonCounty() #Complete
#daggettCounty() #Complete w/error points
#davisCounty()  #Complete
#duchesneCounty()
#emeryCounty()  #Complete
#garfieldCounty()  #Complete
#grandCounty()
#ironCounty()   #Complete
#juabCounty()
#kaneCounty()   #Complete
#millardCounty()   #Complete w/error points
#morganCounty()    #Complete
#murrayCity_AddressPts()
#murrayCity_ParcelPts()
#piuteCounty()
#richCounty()    #Complete
#saltLakeCounty() #Complete w/error points
#sevierCounty()
#summitCounty()
#tooeleCounty()    #Complete
#uintahCounty()
#utahCounty() #Complete
#wasatchCounty()  #Complete w/error points
washingtonCounty()  #Complete
#wayneCounty()
#weberCounty()   #Complete

#addPolyAttributes(sgid10, agrcAddPts_SLCO)







