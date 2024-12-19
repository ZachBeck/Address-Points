from dataclasses import _MISSING_TYPE
import arcpy
import datetime, time
import json
from pathlib import Path
import sys
import re
import os
import agrc
import CreateApartmentDuplicates

from arcpy import env
import arcgis
from arcgis.gis import GIS
from types import SimpleNamespace
from agrc import parse_address
from CreateApartmentDuplicates import addBaseAddress
from DeletePoints import deleteDuplicatePts
from DeletePoints import delete_by_query
from CreateErrorPts import createErrorPts
from ReturnDuplicateAddresses import returnDuplicateAddresses
from ReturnDuplicateAddresses import updateErrorPts
from compareSGIDpts import findMissingPts
from UpdatePointAttributes import addPolyAttributes
from UpdatePointAttributes import updateAddPtID
from UpdatePointAttributes import updateField
from PointTypeUpdater import UpdatePropertyTypeLIR, ptTypeUpdates_SaltLake
from PointTypeUpdater import addPolyAttributesLIR
from sweeper.address_parser import Address

global sgid, agrcAddFLDS, errorList

sgid = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde'))

today = str(datetime.datetime.today().strftime("%m/%d/%Y"))

agrcAddFLDS = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType',
               'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State',
               'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'LoadDate', 'Status', 'Editor',
               'ModifyDate', 'StreetAlias', 'Notes', 'USNG', 'SHAPE@']

dirs = {'N': ['N', 'NORTH', 'NO'], 'S': ['S', 'SOUTH', 'SO'], 'E': ['E', 'EAST', 'EA'], 'W': ['W', 'WEST', 'WE']}
dirs2 = {'N':'NORTH', 'S':'SOUTH', 'E':'EAST', 'W':'WEST'}
longDirs = ['NORTH', 'SOUTH', 'EAST', 'WEST']

sTypeDir = {'ALY':'ALLEY', 'AVE':'AVENUE', 'BAY':'BAY', 'BND':'BEND', 'BLVD':'BOULEVARD', 'CYN':'CANYON',
            'CTR':'CENTER', 'CIR':['CR', 'CIRCLE'], 'COR':'CORNER', 'CT':'COURT', 'CV':'COVE', 'CRK':'CREEK',
            'CRES':'CRESCENT', 'XING':'CROSSING', 'DR':'DRIVE', 'EST':'ESTATE', 'ESTS':'ESTATES',
            'EXPY':'EXPRESSWAY', 'FLT':'FLAT', 'FRK':'FORK', 'FWY':'FREEWAY', 'GLN':'GLEN', 'GRV':'GROVE',
            'HTS':'HEIGHTS','HWY':'HIGHWAY', 'HL':'HILL', 'HOLW':'HOLLOW', 'JCT':'JUNCTION', 'LN':'LANE',
            'LNDG':'LANDING', 'LOOP':'LOOP', 'MNR':'MANOR','MDW':'MEADOW', 'MDWS':'MEADOWS', 'PARK':'PARK', 'PKWY':'PARKWAY',
            'PASS':'PASS', 'PL':'PLACE', 'PLZ':'PLAZA', 'PT':['POINT', 'POINTE'], 'RAMP':'RAMP', 'RNCH':'RANCH', 'RDG':'RIDGE',
            'RD':'ROAD', 'RST':'REST', 'RTE':'ROUTE', 'ROW':'ROW', 'RUN':'RUN', 'SQ':'SQUARE', 'ST':'STREET',
            'TER':'TERRACE', 'TRCE':'TRACE', 'TRL':'TRAIL', 'VW':'VIEW', 'VLG':'VILLAGE', 'WAY':['WY','WAY']}

sTypeList = ['ALY', 'AVE', 'BAY', 'BND', 'BLVD', 'CYN', 'CTR', 'CIR', 'COR', 'CT', 'CV', 'CRK', 'CRES', 'XING',
             'DR', 'EST', 'ESTS', 'EXPY', 'FLT', 'FRK', 'FWY', 'GLN', 'GRV', 'HTS','HWY', 'HL', 'HOLW', 'JCT',
             'LN', 'LNDG', 'LOOP', 'MNR','MDW', 'MDWS', 'PARK', 'PKWY', 'PASS', 'PL', 'PLZ', 'PT', 'RAMP', 'RNCH',
             'RDG', 'RD', 'RTE', 'ROW', 'RUN', 'SQ', 'ST', 'TER', 'TRCE', 'TRL', 'VW', 'VLG', 'WAY']

addNumSufList = ['1/8', '1/4', '1/3', '1/2', '2/3', '3/4', 'A', 'B', 'C', 'D', 'E', 'F']

unitTypeDir = {'APT':'APARTMENT', 'BSMT':'BASEMENT', 'BLDG':'BUILDING', 'DEPT':'DEPARTMENT', 'FL':['FLOOR', 'FLR'],
               'FRNT':'FRONT', 'HNGR':'HANGAR', 'KEY':'KEY', 'LBBY':'LOBBY', 'LOT':'LOT', 'LOWR':'LOWER', 'OFC':'OFFICE',
               'PH':'PENTHOUSE', 'PIER':'PIER', 'REAR':'REAR', 'RM':'ROOM', 'SIDE':'SIDE', 'SLIP':'SLIP',
               'SPC':['SP', 'SPACE'], 'STOP':'STOP', 'STE':'SUITE', 'TRLR':['TRAILER', 'TRL'], 'UNIT':'UNIT', 'UPPR':'UPPER'}

unitTypeList = ['APT', 'APARTMENT', 'BSMT', 'BASEMENT', 'BLDG', 'BUILDING', 'DEPT', 'DEPARTMENT', 'FL', 'FLOOR', 'FLR',
               'FRNT', 'FRONT', 'HNGR', 'HANGAR', 'KEY', 'LBBY', 'LOBBY', 'LOT', 'LOWR', 'LOWER', 'OFC', 'OFFICE',
               'PH', 'PENTHOUSE', 'PIER', 'REAR', 'RM', 'ROOM', 'SIDE', 'SLIP', 'SPC', 'SP', 'SPACE', 'STOP', 'STE',
               'SUITE', 'TRLR', 'TRAILER', 'TRL', 'UNIT', 'UPPR']

noUnitIds = ['BSMT', 'FRNT', 'LBBY', 'LOWR', 'OFC', 'PH', 'REAR', 'SIDE', 'UPPR']

errorList = [None, False, 'None', '<Null>', 'NULL', '', ' ', '#', '####', '--', '.', '~', '-?', '--?', '?', '09-0000-01',
             '0', '00', '000', '??0', '0 STREET', '*', '(Future )', '(FUTURE )', 'Unknown', 'UNKNOWN', '09-0000-01',
             ',ILLER', '+', 0]

leadingSpaceTypes = []
for t in sTypeDir:
    leadingSpaceTypes.append(f' {t}')
    leadingSpaceTypes.append(' STREET')

class clean_street_name:
    def __init__(self, words):

        directions = ['N', 'S', 'E', 'W', 'NORTH', 'SOUTH', 'EAST', 'WEST']

        self.name = ' '.join(words.split()[:-1])
        
        if words.split()[-1] in directions:
          self.direction = returnKey(words[-1], dirs)
          self.type = ''
        else:
          self.type = returnKey(words.split()[-1], sTypeDir)
          self.direction = ''

    def fix_road_name(road_name):
        return clean_street_name(road_name)

def checkWord(word, d):
    for key, value in d.items():
        if word in value:
            return key
    # if nothing is found
    return ''

def returnKey(word, d):
    if word == None:
        word = ''
    word = word.upper()
    for key, value in d.items():
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

def returnKey_noCase(word, d):
    if word == None:
        word = ''
    for key, value in d.items():
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

def formatAddressNumber(addNum):
    removeBadValues(addNum, errorList)
    addNum.strip()
    if addNum.startswith('0'):
        addNum = addNum.lstrip('0')
    return addNum

def removeDuplicateWords(words):
    slist = words.split()
    return ' '.join(sorted(set(slist), key=slist.index))

def truncateOldCountyPts(inPts):
    pointCount = int(arcpy.GetCount_management(inPts).getOutput(0))
    if pointCount > 0:
        arcpy.TruncateTable_management(inPts)
        print (f'Deleted {pointCount} points in {inPts}')
    else:
        print ('No points to delete')

def splitVals(word, list):
    if word == None:
        return ('', '')
    srch = re.compile('|'.join(list))
    match = re.match(srch, word)

    if match != None:
        v1 = match.group()
        v2 = word.replace(v1, '').strip()
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
    sgidRds = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde', 'SGID.TRANSPORTATION.Roads'))
    rdFlds = ['COUNTY_L', 'NAME', 'POSTTYPE']
    rdList = []

    with arcpy.da.SearchCursor(sgidRds, rdFlds) as sCursorRds:
        for rowRd in sCursorRds:
            if rowRd[0] == countyNumber and rowRd[1] != '':
                rdList.append(rowRd[1].upper())
    RoadNameSet = set(rdList)
    return RoadNameSet

def createRoadSet_County(road_fc, road_flds, county_name):
    # road_flds needs to be ordered [RoadName, County]
    # county_name needs to be the same as in the county roads data
    road_list = []

    with arcpy.da.SearchCursor(road_fc, road_flds) as scursor:
        for row in scursor:
            if row[1] in [county_name, None, ''] and row[0] != '' and row[0] != None:
                if row[0][0].isdigit() and row[0].strip().endswith((' NORTH', ' SOUTH', ' EAST', ' WEST')):
                    road_list.append(row[0].split()[0])
                else:
                    road_list.append(row[0].upper())
    RoadNameSet_County = set(road_list)
    return RoadNameSet_County
    
def archive_last_month(archive_pts):
    with arcpy.da.SearchCursor(archive_pts, 'LoadDate') as icursor:
        load_date = str(next(icursor)[0]).split()[0].replace('-', '')
        
    out_archive = f'{archive_pts}{load_date}'
    arcpy.management.CopyFeatures(archive_pts, out_archive)

def agol_to_fgdb(county, fs_url):

    county_fgdb = f'..\{county}\{county}County.gdb'
    with arcpy.EnvManager(workspace=county_fgdb):
        arcpy.env.overwriteOutput = True
        fc = f'{county}_agol_pts'
        arcpy.conversion.ExportFeatures(fs_url, fc)
        print(f'Exported {county} AGOL points to {county_fgdb}')


def beaverCounty():
    beaverCoAddPts = r'..\Beaver\BeaverCounty.gdb\Address_pts'
    agrcAddPts_beaverCo = r'..\Beaver\Beaver.gdb\AddressPoints_Beaver'
    cntyFldr = r'..\Beaver'

    beaverCoAddFLDS = ['Address', 'Prefix', 'St_Name', 'Dir_Type', 'Unit_Num', 'Grid', 'SHAPE@', 'OBJECTID', 'Parcel_ID']

    fix_dict = {'NORTHCREEK':'NORTH CREEK', 'ELK MEADOW':'ELK MEADOWS', 'NORTH CREE':'NORTH CREEK'}
    remove_type = ['MAIN ST', 'PINE LN', 'MT BELKNAP PLACE']

    rdSet = createRoadSet('49001')

    checkRequiredFields(beaverCoAddPts, beaverCoAddFLDS)
    archive_last_month(agrcAddPts_beaverCo)
    truncateOldCountyPts(agrcAddPts_beaverCo)

    errorPtsDict = {}

    with arcpy.da.SearchCursor(beaverCoAddPts, beaverCoAddFLDS) as sCursor, \
        arcpy.da.InsertCursor(agrcAddPts_beaverCo, agrcAddFLDS) as iCursor:
        for row in sCursor:
            if row[0] not in errorList and row[2] not in errorList:
                addNum = row[0]
                preDir = formatValues(row[1], dirs)
                sufDir = formatValues(row[3].upper(), dirs)
                sType = returnKey(row[3].upper(), sTypeDir)

                sName = row[2].upper().replace('HIGHWAY', 'HWY')
                if sName.endswith((' N', ' S', ' E', ' W')):
                    sufDir = sName.split()[1]
                    sType = ''
                    sName = sName.split()[0]
                if sName[1].isdigit() and sName.endswith(tuple([' ' + dir for dir in longDirs])):
                    sufDir = sName.split()[1][0]
                    sName = sName.split()[0]

                if sName.endswith(' ROAD'):
                    sType = 'RD'
                    sName = sName[:-5].strip()

                if sName == 'NORTH CREEK' and sType == '':
                    sType = 'RD'

                if 'HWY' not in sName and sName not in rdSet:
                    addressErrors = errorPtsDict.setdefault(f'OID {row[7]} | {row[2]}', [])
                    addressErrors.extend(['street name not in roads', row[6]])

                if sName in fix_dict:
                    sName = fix_dict[sName]

                if sName in remove_type:
                    sType = returnKey(sName.split()[-1], sTypeDir)
                    sName = ' '.join(sName.split()[:-1])

                if row[3].upper() == 'TR':
                    sType = 'TRL'

                unitID = removeBadValues(row[4], errorList)
                if unitID != '':
                    unitID_hash = '# ' + unitID
                else:
                    unitID_hash = ''

                addSys = row[5].upper()

                parcel_id = removeNone(row[8])

                shp = row[6]

                fullAdd = f'{addNum} {preDir} {sName} {sufDir} {sType} {unitID_hash}'
                fullAdd = ' '.join(fullAdd.split())

                utPtID = f'{addSys} | {fullAdd}'

                if sufDir == '' and sType == '' and 'HWY' not in sName:
                    addressErrors = errorPtsDict.setdefault(fullAdd, [])
                    addressErrors.extend(['missing street type', row[6]])
                if preDir != '' and preDir == sufDir:
                    addressErrors = errorPtsDict.setdefault(fullAdd, [])
                    addressErrors.extend(['predir = sufdir', row[6]])

                iCursor.insertRow((addSys, utPtID, fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '',\
                                   '', unitID, '', '', '49001', 'UT', '', '', '', parcel_id, 'BEAVER COUNTY', today,\
                                   'COMPLETE', '', None, '', '', '', shp))

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Beaver_ErrorPts.shp', beaverCoAddFLDS[1], beaverCoAddPts)

    del iCursor

    intersectPolyDict = {'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
                         'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
                         'USNG': ['SGID.INDICES.NationalGrid', 'USNG', '']}

    addPolyAttributes(sgid, agrcAddPts_beaverCo, intersectPolyDict)
    updateAddPtID(agrcAddPts_beaverCo)
    addBaseAddress(agrcAddPts_beaverCo)
    deleteDuplicatePts(agrcAddPts_beaverCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_beaverCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Beaver_ErrorPts.shp'), errorFlds, dupePts)


def boxElderCounty():
    boxelderCoAddPts = r'..\BoxElder\BoxElderCounty.gdb\BECO_Address_Points'
    agrcAddPts_boxelderCo = r'..\BoxElder\BoxElder.gdb\AddressPoints_BoxElder'
    cntyFldr = r'..\BoxElder'

    boxelderCoAddFLDS = ['FullAddr', 'HouseNum', 'PreDir', 'StreetName', 'StreetType', 'SufDir', 'UnitNumber', 'UnitType', 'City', \
                         'ZipCode', 'Parcel_ID', 'Structure', 'COMPLEX_NA', 'Use_Classi', 'last_edi_1', 'SHAPE@', 'STREET_ALI']

    # useDict = {'AGR':'Agricultural', 'COM':'Commercial', 'EDU':'Education', 'GOV':'Government', 'MED':'Other', 'RES':'Residential',\
    #           'MHU':'Residential', 'MOB':'Residential', 'REL':'Other', 'VAC':'Vacant'}

    ptTypeDict = {'Agricultural':'AGR', 'Commercial':['COM'], 'Residential':['Residential', 'RES', 'MOB', 'MHU'],
                  'Other':['EDU', 'GOV', 'Med', 'OTH', 'REL'], 'Vacant':'VAC', 'Unknown':''}


    excludeUnit = ['UPSTAIRS', 'UP', 'MANAGER', 'DOWNSTAIRS', 'DOWN', 'CLUB', 'BASEMENT']

    #sTypeTuple = tuple(sTypeList)

    checkRequiredFields(boxelderCoAddPts, boxelderCoAddFLDS)
    #archive_last_month(agrcAddPts_boxelderCo)
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
                sName = row[3].strip()

                if row[4] in errorList:
                    sType = ''
                else:
                    sType = returnKey(row[4].strip(), sTypeDir)

                if sName.endswith((' RD', ' DR', ' ST', ' AVE')):
                    sType = sName[-2:]
                    sName = sName[:-2].strip()
                if sName.endswith((' DRIVE', ' LANE', ' ROAD')):
                    sType = returnKey(sName.split()[-1], sTypeDir)
                    sName = sName.rsplit(' ', 1)[0]
                    sufDir = ''
                    print(sName)
                if sName[0].isdigit() == True and sName.endswith((' N', ' S', ' E', ' W')):
                    sufDir = sName[-1]
                    sName = sName.replace(sName[-2:], '')

                if sName.startswith(('HIGHWAY ')):
                    sName = sName.replace('HIGHWAY', 'HWY')

                sufDir = removeBadValues(row[5], errorList)
                if sType != '':
                    sufDir = ''

                if sName == '1200' and row[15] == 'ROCKET ROAD':
                    sName = 'ROCKET'
                    sType = 'RD'
                    sufDir = ''

                if sName[0].isdigit() == False:
                    sufDir = ''

                if sName == 'SADDLEBACK':
                    sType = 'RD'

                sName = sName.upper()

                if row[6] not in errorList:
                    unitNum = row[6].strip('#').strip().upper()
                else:
                    unitNum = ''

                unitType = returnKey(row[7].upper(), unitTypeDir)
                

                city = ''
                zip = row[9]
                parcelID = row[10]
                structure = removeBadValues(row[11], errorList)
                building = removeBadValues(row[12], errorList)

                ptType = returnKey_noCase(removeNone(row[13]), ptTypeDict)

                addSource = 'BOX ELDER COUNTY'
                modDate = row[14]
                loadDate = today
                shp = row[15]

                if unitType == '' and unitNum != '':
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} # {unitNum}'
                else:
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} {unitType} {unitNum}'
                fullAdd = ' '.join(fullAdd.split())

    #-----------Create Error Points-----------
                if preDir == sufDir and sType == '':
                    addressErrors = errorPtsDict.setdefault(fullAdd, [])
                    addressErrors.extend(['predir = sufdir', row[15]])
                if row[3] != None and row[0] != None:
                    if row[3] not in row[0]:
                        addressErrors = errorPtsDict.setdefault(f'{row[3]} | {row[0]}', [])
                        addressErrors.extend(['StreetName not in FullAddr', row[15]])

                iCursor.insertRow((addSys, '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', building, unitType,\
                                   unitNum, city, zip, '49003', 'UT', '', ptType, structure, parcelID, addSource, loadDate, \
                                   'COMPLETE', '', modDate, '', '', '', shp))

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'BoxElder_ErrorPts.shp', 'Address', boxelderCoAddPts)


    del iCursor
    del sCursor


    inputDict = {'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
                 'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
                 'City': ['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],}

    addPolyAttributes(sgid, agrcAddPts_boxelderCo, inputDict)
    updateAddPtID(agrcAddPts_boxelderCo)
    addBaseAddress(agrcAddPts_boxelderCo)
    deleteDuplicatePts(agrcAddPts_boxelderCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_boxelderCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'BoxElder_ErrorPts.shp'), errorFlds, dupePts)


def cacheCounty():
    cacheCoAddPts = r'..\Cache\CacheCounty.gdb\CacheAddressPoints'
    agrcAddPts_cacheCo = r'..\Cache\Cache.gdb\AddressPoints_Cache'
    cntyFldr = r'..\Cache'

    cacheCoAddFLDS = ['addsystem', 'fulladd', 'addnum', 'addnumsuffix', 'prefixdir', 'streetname', 'streettype', 'suffixdir',
                      'landmarkname', 'building', 'unittype', 'unitid', 'ptlocation', 'pttype', 'structure', 'parcelid',
                      'addsource', 'last_edited_date', 'SHAPE@', 'OBJECTID']

    flrDict = {'BSMT':['FLR BSMT','FLR BMST', 'FLR BSMT EAST', 'FLR BSMT RIGHT', 'FLR BSMT S', 'FLR DWNSTRS'],
               'REAR':['FLR REAR'], 'UPPR':['FLR UPPER', 'FLR UPSTRS', 'FLR UPSTRS; APT 1', 'UPSTRS'],
               'FRNT':['FR', 'FRONT'], 'OFC':['OFFICE'], 'RM':['ROOM']}

    cacheTypesDict = {'ALY':'ALLEY', 'AVE':'AVENUE', 'BAY':'BAY', 'BND':'BEND', 'BLVD':'BOULEVARD', 'CYN':'CANYON',
            'CTR':'CENTER', 'CIR':'CIRCLE', 'COR':'CORNER', 'CT':'COURT', 'CV':'COVE', 'CRK':'CREEK',
            'CRES':'CRESCENT', 'XING':'CROSSING', 'DR':'DRIVE', 'EST':'ESTATE', 'ESTS':'ESTATES',
            'EXPY':'EXPRESSWAY', 'FLT':'FLAT', 'FRK':'FORK', 'FWY':'FREEWAY', 'GLN':'GLEN', 'GRV':'GROVE',
            'HTS':'HEIGHTS','HWY':'HIGHWAY', 'HL':'HILL', 'HOLW':'HOLLOW', 'JCT':'JUNCTION', 'LN':'LANE',
            'LNDG':'LANDING', 'LOOP':['LP', 'LOOP'], 'MNR':'MANOR','MDW':'MEADOW', 'MDWS':'MEADOWS', 'PARK':'PARK',
            'PKWY':'PARKWAY', 'PASS':'PASS', 'PL':'PLACE', 'PLZ':'PLAZA', 'PT':'POINT', 'RAMP':'RAMP', 'RNCH':'RANCH',
            'RDG':'RIDGE', 'RD':'ROAD', 'RTE':'ROUTE', 'ROW':'ROW', 'RUN':'RUN', 'SQ':'SQUARE', 'ST':'STREET',
            'TER':'TERRACE', 'TRCE':'TRACE', 'TRL':'TRAIL', 'VW':'VIEW', 'VLG':'VILLAGE', 'WAY':'WAY'}

    hwy_dict = {'SR 101':'HWY 101', 'SR 142':'HWY 142', 'SR 165':'HWY 165', 'SR 23':'HWY 23', '23 SR':'HWY 23',
                'SR 30':'HWY 30', 'US 89':'HWY 89', 'US 89/91':'HWY 89/91', 'HWY 89-91':'HWY 89/91',
                'US 91':'HWY 91'}

    ptTypeDict = {'Agricultural':['LAND AGRICULTURE', 'LAND GREENBELT'], 'Commercial':['LAND COMMERCIAL'],
                  'Residential':['LAND RESIDENTIAL', 'LAND SECONDARY'], 'Vacant':['LAND VACANT']}

    checkRequiredFields(cacheCoAddPts, cacheCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_cacheCo).getOutput(0))
    archive_last_month(agrcAddPts_cacheCo)
    truncateOldCountyPts(agrcAddPts_cacheCo)

    errorPtsDict = {}
    #rdSet = createRoadSet('49005')

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
                        if f' {a}' in addnum:
                            addnumsuf = a
                            suf_form = int(f'-{len(addnumsuf)}')
                            addnum = addnum[:suf_form]
                            print(f'{row[19]} {addnum}')

                            if '-' in addnum:
                                if addnum.split('-')[1] == row[9]:
                                    addnumsuf = ''
                                    building = f'BLDG {row[9]}'
                                addnum = addnum.split('-')[0]
                        if '.5' in addnum:
                            addnumsuf = '1/2'
                            addnum = addnum.split('.')[0]

                modTypes = removeNone(row[6])
                sType = returnKey(modTypes.strip(), cacheTypesDict)
                sufdir = formatValues(row[7], dirs)

                if sName in hwy_dict:
                    sName = hwy_dict[sName]

                if sName.isdigit() == False:
                    sufdir = ''
                if sName.isdigit() == True:
                    sType = ''

                if sName == 'LYNNWOOD':
                    predir = 'E'


                if predir == sType and sName != 'BOULEVARD':
                    continue

                landName = removeBadValues(row[8], errorList)

                unitType = returnKey(row[10], unitTypeDir)
                unitId_src = removeBadValues(row[11], errorList)
                unitId_src = re.sub('[()#]', '', unitId_src).strip()
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

                if sName == '200 E MEMORY':
                    addnum = 200
                    sName = 'MEMORY'
                    predir = 'E'
                    sType = 'LN'
                    unitId = row[2]

                parcelId = removeBadValues(row[15], errorList)
                addSrc = removeBadValues(row[16], errorList)
                modDate = row[17]
                loadDate = today
                editor = ''
                shp = row[18]

                if sName == 'BOULEVARD':
                    sType = 'ST'

                if unitType != '' and unitId == '':
                    unitType = ''

                if unitType == '' and unitId != '' and unitId not in flrDict:
                    fullAdd = f'{addnum} {addnumsuf} {predir} {sName} {sType} {sufdir} {building} {unitType} # {unitId}'
                    fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = f'{addnum} {addnumsuf} {predir} {sName} {sType} {sufdir} {building} {unitType} {unitId}'
                    fullAdd = ' '.join(fullAdd.split())

    #--------------Create Error Points--------------
                # if sName != '' and sName[0].isdigit() == True and sName[-1].isdigit() == False:
                #     addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[1],row[5]), [])
                #     addressErrors.extend(['bad street name', row[18]])
                # if 'HWY' not in sName and sName not in rdSet:
                #     addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[1],row[5]), [])
                #     addressErrors.extend(['street name not in roads', row[18]])
                # if sName not in row[1].strip():
                #     addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[1], row[5]), [])
                #     addressErrors.extend(['mixed street names', row[18]])
                if predir == sufdir and sType == '':
                    addressErrors = errorPtsDict.setdefault(f'{row[1]} | {row[4]} | {row[7]}', [])
                    addressErrors.extend(['predir = sufdir', row[18]])
                # if row[6] != 'LP' and removeNone(row[6]).strip() not in cacheTypesDict and row[6] not in errorList:
                #     addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[1], row[6]), [])
                #     addressErrors.extend(['bad street type', row[18]])


                iCursor.insertRow(('', '', fullAdd, addnum, addnumsuf, predir, sName, sType, sufdir, landName, building, unitType, unitId, '',\
                                   '', '49005', 'UT', '', '', '', parcelId, 'CACHE COUNTY', loadDate, 'COMPLETE', editor, modDate, '', '', '', shp))

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Cache_ErrorPts.shp', cacheCoAddFLDS[1], cacheCoAddPts)

    del sCursor
    del iCursor

    remapLIR = {'Agricultural': ['Agricultural', 'Greenbelt', 'LAND AGRICULTURE', 'LAND GREENBELT'],
                'Commercial': ['LAND COMMERCIAL', 'Commercial',  'Commercial - Office Space', 'Commercial - Retail'],
                'Residential': ['LAND RESIDENTIAL', 'LAND SECONDARY'], 'Vacant': ['LAND VACANT']}

    inputDict = {
        'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
        'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
        'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
        'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
        'PtType': ['SGID.CADASTRE.Parcels_Cache_LIR', 'PROP_CLASS', remapLIR]
    }

    addPolyAttributes(sgid, agrcAddPts_cacheCo, inputDict)
    updateAddPtID(agrcAddPts_cacheCo)
    addBaseAddress(agrcAddPts_cacheCo)
    deleteDuplicatePts(agrcAddPts_cacheCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_cacheCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Cache_ErrorPts.shp'), errorFlds, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_cacheCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def carbonCounty():
    carbon_agol_pts = 'https://maps.carbon.utah.gov/arcgis/rest/services/CountyGeneralMap/Addressing_Ownership/MapServer/0'
    carbonCoAddPts = r'..\Carbon\CarbonCounty.gdb\Carbon_agol_pts'
    #carbonCoAddPts = r'..\Carbon\CarbonCounty.gdb\AddressPoints'
    agrcAddPts_carbonCo = r'..\Carbon\Carbon.gdb\AddressPoints_Carbon'
    cntyFldr = r'..\Carbon'

    agol_to_fgdb('Carbon', carbon_agol_pts)

    # carbonCoAddFLDS = ['NAME', 'BUILD_TYPE', 'WHOLE_ADD', 'INDIC_ADDR', 'PRE_DIR', 'ST_NAME', 'ST_TYPE', 'SUF_DIR', 'UNIT_NUM', \
    #                    'BLDG_NUM', 'PARCEL_NUM', 'GPS_DATE', 'SHAPE@', 'OBJECTID']

    carbonCoAddFLDS = ['LandmaName', 'PtType', 'FullAdd', 'AddNum', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 'UnitID', \
                       'Building', 'ParcelID', 'ModifyDate', 'SHAPE@', 'OBJECTID', 'UnitType']

    checkRequiredFields(carbonCoAddPts, carbonCoAddFLDS)
    archive_last_month(agrcAddPts_carbonCo)
    truncateOldCountyPts(agrcAddPts_carbonCo)
    rdSet = createRoadSet('49007')

    errorPtsDict = {}

    ptTypeDict = {
    'Other' : ['AGRICULTURAL', 'GOVERMENT', 'EDUCATIONAL', 'FIRE HYDRANT', 'MISSING', 'OTHER', 'OUTBUILDING', 'OUT BUILDING', 'PUBLIC',
               'PUBLIC WATER TANK', 'RELIGIOUS', 'STREET SIGN', 'TRAIN', 'WATER TANK'],
    'Residential' : ['RESIDENTIAL', 'RESIDEENTIAL', 'RESIDENTIAL/COMMERCI'],
    'Commercial' : ['COMMERCIAL', 'GARAGE', 'HELPER GUN CLUB'],
    'Industrial': ['UTILITY'],
    'Unknown':''
    }

    units = {'APT' : ['APT.', 'APARTMENT'], 'HNGR':'HNGR', 'STE' : ['STE.', 'SUITE'], 'TRLR':['TRAILER'],
             'UNIT':'UNIT', 'UPPER':['UPPER', 'UPPR']}
    sNameSuffs = [' N', ' S', ' E', ' W']
    stripTypes = [' AVE', ' DR', ' LN', ' RD', ' ST', ' WAY']
    fix_types = ['WOOD HILL ROAD', 'WESTWOOD BLVD', 'SPRING GLEN ROAD', 'SPRING CANYON ROAD', 'SHELBY LANE', 'AIRPORT ROAD',
                 'RICHELMAN LANE', 'NORTH COAL CREEK ROAD', 'CONSUMERS ROAD', 'DRY VALLEY ROAD', 'FORD RIDGE ROAD']


    iCursor = arcpy.da.InsertCursor(agrcAddPts_carbonCo, agrcAddFLDS)

    unitID = ''

    with arcpy.da.SearchCursor(carbonCoAddPts, carbonCoAddFLDS) as sCursor_carbon:
        for row in sCursor_carbon:

            #------- Errror Pts --------
            if row[4] not in dirs and row[4] not in longDirs and row[4] not in errorList:
                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[4]}', [])
                addressErrors.extend(['bad pre dir', row[12]])
            if row[5].endswith((' N', ' S', ' E', ' W')):
                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[5]}', [])
                addressErrors.extend(['suf dir in street name', row[12]])
            if row[5].isdigit() and row[4] == row[7] and row[4] not in errorList:
                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[4]} | {row[7]}', [])
                addressErrors.extend(['pre dir = suf dir', row[12]])
            if row[7] not in dirs and row[7] not in longDirs and row[7] not in errorList:
                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[7]}', [])
                addressErrors.extend(['bad suf dir', row[12]])
            if row[5] not in row[2] and row[5] not in errorList and  row[2] not in errorList:
                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[5]}', [])
                addressErrors.extend(['street name not in FullAdd', row[12]])
            if row[5].endswith((tuple(leadingSpaceTypes))):
                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[5]}', [])
                addressErrors.extend(['street type in street name', row[12]])
            if row[3].startswith('#') or row[3].endswith(('W', 'TH', 'ST', 'E', 'N', '350? OR 39', '4099 N HWY', '?')) \
                or row[3] in ('CEMETARY R', 'GUN CLUB R', 'JANET', 'WILSON ST'):
                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[3]}', [])
                addressErrors.extend(['bad address number', row[12]])
            #---------------------------


            if row[3] not in errorList and row[5] not in errorList:

                if row[3].startswith('#') or row[2][0] == '#':
                    continue
                elif '#' in row[3]:
                    addNum = row[3].split()[0]
                    unitID = row[3].split()
                elif len(row[3]) <= 5:
                    if row[3].isalpha():
                        continue
                    if row[3][-1] == 'E':
                        continue
                    addNum = row[3].strip('W').strip()
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
                sName = row[5].upper().strip()

                sType = checkWord(row[6], parse_address.sTypes)
                sufDir = returnKey(row[7], dirs)
                if sufDir != '' and sType != '':
                    sType = ''

                if sName[-2:] in sNameSuffs:
                    sName = sName[:-2]
                    if sName.isdigit() == True:
                        sufDir = row[5][-1:]
                        print (sufDir)
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

                if sName == '1777 S HWY 10':
                    sName = 'HWY 10'
                if sName == 'HIGHWAY':
                    sName = 'HWY 6'
                    sType = ''

                if sName in fix_types:
                    sType = returnKey(sName.split()[-1], sTypeDir)
                    sName = sName.strip(sName.split()[-1]).strip()

                if sType == '' and sName.isdigit() == False and sName[0].isdigit() == False:
                    sType = returnKey(row[6], sTypeDir)
                    sufDir = ''

                if sName == 'SCENIC VIEW':
                    sType = ''

                if 'HIGHWAY 6' in row[2]:
                    sName = 'HWY 6'
                    if sType != '':
                        addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[6]}', [])
                        addressErrors.extend(['street type not needed', row[12]])
                    sType = ''
                if 'HWY' in sName:
                    sName = sName.lstrip('U S ')
                    if sType != '':
                        addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[6]}', [])
                        addressErrors.extend(['street type not needed', row[12]])
                    sType = ''
                hwyNumbers = ['6', '10', '96', '122', '123', '124', '157', '191', '264']
                if row[5] in hwyNumbers and row[6] == 'HWY':
                    sName = f'HWY {row[5]}'
                    sType = ''

                if row[6] != '' and row[6] != ' ' and row[6] != None and row[6] not in sTypeDir:
                    addressErrors = errorPtsDict.setdefault(f'{row[6]} | {row[2]}', [])
                    addressErrors.extend(['bad or missing street type', row[12]])

                if row[9] not in errorList and row[9] != 'OFFICE':
                    building = str(row[9]).replace('.', '').strip()
                else:
                    building = ''

                unitType = returnKey(row[14], units)
                if row[8] not in errorList:
                    unitID = row[8].strip('#')
                    if unitID.startswith(('STE', 'SUITE')):
                        unitType = 'STE'
                        unitID = row[8].split()[1].strip('#')
                else:
                    unitID = ''
                
                if unitType == 'UPPER':
                    unitType = ''
                    unitID = 'UPPR'
                    
                # cntyUnits = removeBadValues(str(row[8]).translate('.#'), errorList)
                # if len(cntyUnits.split()) > 1:
                #     unitType = returnKey(cntyUnits.split()[0], units)
                #     unitID = cntyUnits.split()[1].replace('#', '')
                # else:
                #     unitID = cntyUnits.replace('#', '')
                #     unitType = ''

                if unitType == '' and unitID != '':
                   unitID_hash = f'# {unitID}'
                   fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} {unitType} {unitID_hash}'
                   fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} {unitType} {unitID}'
                    fullAdd = ' '.join(fullAdd.split())

            elif row[2] != '' and row[2][0].isdigit() and len(row[2]) > 7:
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
                if sName == 'HIGHWAY 6':
                    sName = 'HWY 6'
                sufDir = address.suffixDirection
                if sufDir == None:
                    sufDir = ''
                if sName == 'CENTRAL MILLER':
                    sName = 'CENTRAL MILLER CREEK'
                    sType = 'RD'
                fullAdd = row[2].upper().replace('HIGHWAY 6', 'HWY 6')
                fullAdd = ' '.join(fullAdd.split())
            else:
                continue

            ptType = returnKey(row[1], ptTypeDict)

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
            mod_date = row[11]
            shp = row[12]

            if row[5].upper() not in rdSet and row[5] != '' and 'HWY' not in sName:
                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[5]}', [])
                addressErrors.extend(['street name not found in roads', row[12]])
            if sName.endswith((' ALY', ' AVE', ' BAY', ' BND', ' BLVD', ' CYN', ' CTR', ' CIR', ' COR', ' CT', ' CV', \
                                ' CRK', ' CRES', ' XING', ' DR', ' EST', ' ESTS', ' EXPY', ' FLT', ' FRK', ' FWY', \
                                ' GLN', 'GRV', ' HTS', ' HWY', ' HL', ' HOLW', ' JCT', ' LN', ' LNDG', ' LOOP', \
                                ' MNR', ' MDW', ' MDWS', ' PARK', ' PKWY', ' PASS', ' PL', ' PLZ', ' PT', ' RAMP', \
                                ' RNCH', ' RDG', ' RD', ' RTE', ' ROW', ' RUN', ' SQ', ' ST', ' TER', ' TRCE', ' TRL', \
                                ' VW', ' VLG', ' WAY')):
                addressErrors = errorPtsDict.setdefault(f'{sName} | {row[2]}', [])
                addressErrors.extend(['street type in name?', row[12]])

            if sName.isdigit() and preDir in errorList and sufDir not in errorList:
                continue

            iCursor.insertRow((addSys, utAddId, fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, landmark, building, \
                               unitType, unitID, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                               status, editor, mod_date, '', '', '', shp))

        #createErrorPts(errorPtsDict, cntyFldr, 'Carbon_ErrorPts.shp', 'EXAMPLE', carbonCoAddPts)
        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Carbon_ErrorPts.shp', 'EXAMPLE', carbonCoAddPts)

    del iCursor
    del sCursor_carbon

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_carbonCo, inputDict)
    updateAddPtID(agrcAddPts_carbonCo)
    addBaseAddress(agrcAddPts_carbonCo)
    deleteDuplicatePts(agrcAddPts_carbonCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_carbonCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Carbon_ErrorPts.shp'), errorFlds, dupePts)


def daggettCounty():
    daggettCoAddPts = r'..\Daggett\DaggettCounty.gdb\DaggettAddress2021'
    agrcAddPts_daggettCo = r'..\Daggett\Daggett.gdb\AddressPoints_Daggett'
    cntyFldr = r'..\Daggett'

    daggettCoAddFLDS = ['HouseAddr', 'HouseNum', 'PreDir', 'StreetName', 'StreetType', 'SufDir', 'UnitNumber',\
                        'Parcel_ID', 'Structure','Modified', 'SHAPE@', 'FullAddr']

    aveDict = {'FIRST': '1ST', 'SECOND': '2ND', 'THIRD': '3RD', 'FOURTH': '4TH', 'FIFTH': '5TH', 'SIXTH': '6TH', \
               'SEVENTH': '7TH', 'EIGHTH': '8TH', 'NINTH': '9TH', 'TENTH': '10TH', 'ELEVENTH': '11TH',
               'TWELFTH': '12TH', 'THIRTEENTH': '13TH'}
    aveList = {'1ST', '2ND', '3RD', '4TH', '5TH', '6TH', '7TH', '8TH', '9TH'}

    checkRequiredFields(daggettCoAddPts, daggettCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_daggettCo)

    daggettDirs = ('N', 'S', 'E', 'W', '')

    fix_name = {'UTCH JOHN MTN':'DUTCH JOHN MTN', 'VALLEY VEW':'VALLEY VIEW'}
    remove_type = ('LINWOOD LN', 'STATELINE RD')

    errorPtsDict = {}
    rdSet = createRoadSet('49009')

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
                if removeNone(row[2]).strip() not in daggettDirs:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['Bad SufDir', row[10]])

                sType = returnKey(removeNone(row[4]).upper(), sTypeDir)
                if row[4] == 'BLV':
                    sType = 'BLVD'
                if removeNone(row[4]).strip().upper() not in sTypeList:
                    addressErrors = errorPtsDict.setdefault(row[4], [])
                    addressErrors.extend(['bad street type', row[10]])

                sufDir = returnKey(row[5], dirs)
                if removeNone(row[5]).strip() not in daggettDirs:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['Bad SufDir', row[10]])

                sName = row[3].upper().strip()
                if sName in aveDict:
                    sName = aveDict[sName]
                if row[3][:3] in aveList:
                    sName = sName[:3].strip()
                    sufDir = returnKey(row[3].split()[1], dirs)
                    sType = ''
                if 'HWY' in sName:
                    sType = ''
                if sName.isdigit() == True:
                    sType = ''
                if sName.isdigit() == False and len(sName) > 3:
                    sufDir = ''

                if row[3] not in row[0]:
                    addressErrors = errorPtsDict.setdefault(row[0], [])
                    addressErrors.extend(['HouseAddr and StreetName have mixed street names', row[10]])
                if row[3].isalpha() and row[4] == '':
                    print ('missing stype')
                if f' {removeNone(row[3])}'.endswith(' ' + removeNone(row[4])):
                    addressErrors = errorPtsDict.setdefault(row[3], [])
                    addressErrors.extend(['StreetType in StreetName', row[10]])

                    sName = row[3].strip(f' {row[4]}')

                if sName in fix_name:
                    sName = fix_name[sName]

                if sName in remove_type:
                    sType = sName[-3:].strip()
                    sName = sName.split()[0]

                unitID = removeNone(row[6]).strip()

                if unitID == '':
                    fullAdd = f'{addNum} {preDir} {sName} {sufDir} {sType}'
                    fullAdd = ' '.join(fullAdd.split())
                else:
                    fullAdd = f'{addNum} {preDir} {sName} {sufDir} {sType} # {unitID}'
                    fullAdd = ' '.join(fullAdd.split())

                parcelID = row[7]
                structure = row[8]
                loadDate = today
                modified = row[9]
                shp = row[10]

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '', \
                                   unitID, '', '', '49009', 'UT', '', '', structure, parcelID, 'DAGGETT COUNTY', \
                                   loadDate, 'COMPLETE', '', modified, '', '', '', shp))


        print (errorPtsDict)
        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Daggett_ErrorPts.shp', daggettCoAddFLDS[0], daggettCoAddPts)
        #createErrorPts(errorPtsDict, cntyFldr, 'Daggett_ErrorPts.shp', daggettCoAddFLDS[0], daggettCoAddPts)

    del iCursor
    del sCursor

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_daggettCo, inputDict)
    updateAddPtID(agrcAddPts_daggettCo)
    addBaseAddress(agrcAddPts_daggettCo)
    deleteDuplicatePts(agrcAddPts_daggettCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_daggettCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Daggett_ErrorPts.shp'), errorFlds, dupePts)


def davisCounty():
    davisCoAddPts = r'..\Davis\DavisCounty.gdb\DavisAddress'
    agrcAddPts_davisCo = r'..\Davis\Davis.gdb\AddressPoints_Davis'
    cntyFldr = r'..\Davis'

    # davisCoAddFLDS = ['AddressNum', 'AddressN_1', 'UnitType', 'UnitNumber', 'RoadPrefix', 'RoadName', 'RoadNameTy', 'RoadPostDi',
    #                   'FullAddres', 'SHAPE@', 'PrimaryAdd', 'MunicipalN']
    davisCoAddFLDS = ['AddressNumber', 'AddressNumberSuffix', 'UnitType', 'UnitNumber', 'RoadPrefixDirection', 'RoadName', 'RoadNameType',
                      'RoadPostDirection', 'FullAddress', 'SHAPE@', 'PrimaryAddress', 'MunicipalName', 'LastUpdate']

    checkRequiredFields(davisCoAddPts, davisCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_davisCo).getOutput(0))
    archive_last_month(agrcAddPts_davisCo)
    truncateOldCountyPts(agrcAddPts_davisCo)

    noTypeList = ['ANTELOPE ISLAND CAUSEWAY', 'APPLE ACRES', 'ASPEN GROVE', 'BOUNTIFUL MEMORIAL PARK', 'BROADWAY',
                  'BUFFALO RANCH DEVELOPMENT', 'BURN PLANT', 'CARRIAGE CROSSING', 'CENTERVILLE MEMORIAL PARK',
                  'CHERRY HILL ENTRANCE', 'CHEVRON REFINERY', 'CHRISTY', 'COMPTONS POINTE', 'DEER CREEK', 'EAST ENTRANCE',
                  'EAST PROMONTORY', 'EGG ISLAND OVERLOOK', 'FAIRVIEW PASEO', 'FARMINGTON CEMETERY', 'FARMINGTON CROSSING',
                  'FREEPORT CENTER', 'GARDEN CROSSING PASEO', 'HAWORTH', 'HWY 106', 'HWY 126', 'HWY 193', 'HWY 68', 'HWY 89',
                  'HWY 93', 'HOLLY HAVEN I', 'HOLLY HAVEN II', 'IBIS CROSSING', 'KAYSVILLE AND LAYTON CEMETERY',
                  'LLOYDS PARK', 'MOUNTAIN VIEW PASEO', 'NORTH ENTRANCE', 'NORTHEAST ENTRANCE', 'NORTHWEST ENTRANCE',
                  'POETS REST', 'PRESERVE PASEO', 'SOMERSBY', 'SOUTH CAUSEWAY', 'SOUTH ENTRANCE', 'SOUTHEAST ENTRANCE',
                  'STATION', 'STONEY BROOK', 'SYRACUSE CEMETERY', 'VALIANT', 'VALLEY VIEW', 'WARD', 'WARWICK', 'WEST PROMONTORY',
                  'WETLAND POINT', 'WHISPERING PINE', 'WILLOW BEND PASEO', 'WILLOW FARM PASEO', 'WILLOW GARDEN PASEO',
                  'WILLOW GREEN PASEO', 'WILLOW GROVE PASEO', 'WYNDOM']

    remove_stypes = ['STONEY BROOK CIR', 'ANGEL ST', 'BROWNING LN', 'CHARLENE WAY', 'COUNTRY WAY', 'EAGLES LNDG', 'GRANTS LN',
                     'SAGE DR']

    hwy_dict = {'SR 37':'HWY 37', 'SR 193':'HWY 193'}

    errorPtsDict = {}
    rdSet = createRoadSet('49011')


    with arcpy.da.SearchCursor(davisCoAddPts, davisCoAddFLDS) as sCursor_davis, \
        arcpy.da.InsertCursor(agrcAddPts_davisCo, agrcAddFLDS) as iCursor:

        for row in sCursor_davis:
            if row[10] == 'P':
                if row[0] == 0 and row[5] != 'Freeport Center':
                    continue
                if row[11] in ['Ogden', 'Roy', 'Uintah', 'Washington Terrace']:
                    continue   

                elif row[0] not in errorList and row[5] not in errorList:

                    addNum = row[0]
                    addNumSuf = formatValues(row[1], addNumSufList)

                    unitId = removeBadValues(row[3], errorList).upper()
                    preDir = formatValues(row[4], dirs)

                    unitType = formatValues(row[2], unitTypeDir).upper()
                    if unitType != '' and unitId == '':
                        unitType = ''

                    streetName = removeBadValues(row[5], errorList).upper()

                    streetType = returnKey(removeNone(row[6]).upper(), sTypeDir)

                    if streetName.startswith('BEVERLY'):
                        streetName = 'BEVERLY'
                        streetType = 'WAY'
                    if streetName in remove_stypes:
                        long_sname = clean_street_name(streetName)
                        streetName = long_sname.name
                        streetType = long_sname.type
                        print(streetName)

                    if 'HIGHWAY' in streetName:
                        streetName = streetName.replace('HIGHWAY', 'HWY')

                    sufDir = formatValues(row[7], dirs)

                    if streetName in hwy_dict:
                        streetName = hwy_dict[streetName]
                        streetType = ''
                        sufDir = ''


                    if streetName == 'FREEPORT CENTER':
                        addNum = ''
                        fullAdd = f'{addNum} {streetName} {unitType} {unitId}'
                    if unitId != '' and unitType != '':
                        fullAdd = f'{addNum} {addNumSuf} {preDir} {streetName} {sufDir} {streetType} {unitType} {unitId}'
                    else:
                        fullAdd = f'{addNum} {addNumSuf} {preDir} {streetName} {sufDir} {streetType} {unitType} {unitId}'
                    fullAdd = ' '.join(fullAdd.split())


                    if preDir != '' and preDir == sufDir:
                        addressErrors = errorPtsDict.setdefault(row[8], [])
                        addressErrors.extend(['Prefix = Suffix direction', row[9]])
                    if 'HWY' not in streetName and streetName not in row[8].upper():
                        addressErrors = errorPtsDict.setdefault(f'{row[8]} | {streetName}', [])
                        addressErrors.extend(['Mixed street names', row[9]])
                    # if ' {}'.format(row[5]).endswith(' ' + row[6]):
                    #     addressErrors = errorPtsDict.setdefault(row[8], [])
                    #     addressErrors.extend(['StreetType in StreetName', row[9]])
                    # if sufDir != '' and streetType != '':
                    #     addressErrors = errorPtsDict.setdefault(row[8], [])
                    #     addressErrors.extend(['Post direction needed?', row[9]])
                    if sufDir == '' and streetType == '' and streetName not in noTypeList:
                        print (streetName)
                        addressErrors = errorPtsDict.setdefault(row[8], [])
                        addressErrors.extend(['Missing Suffix or StreetType?', row[9]])
                    # if streetName not in row[8].upper() and 'HWY' not in streetName:
                    #     addressErrors = errorPtsDict.setdefault(row[8], [])
                    #     addressErrors.extend([streetName + ' not in FullAddress', row[9]])
                    if streetName not in rdSet:
                        addressErrors = errorPtsDict.setdefault(f'{row[8]} | {streetName}', [])
                        addressErrors.extend(['Street name missing in roads data', row[9]])
                    # if streetName.isdigit() == True:
                    #     if streetType != '':
                    #         addressErrors = errorPtsDict.setdefault(row[8], [])
                    #         addressErrors.extend(['Drop street type?', row[9]])
                    #     streetType = ''
                    # else:
                    #     if sufDir != '':
                    #         addressErrors = errorPtsDict.setdefault(row[8], [])
                    #         addressErrors.extend(['Drop suffix direction?', row[9]])
                    #     sufDir = ''


                    addSys = ''
                    utAddId = ''
                    landmark = ''
                    building = ''
                    city = ''
                    zip = ''
                    fips = '49011'
                    state = 'UT'
                    ptLocation = 'Unknown'
                    ptType = ''
                    structure = 'Unknown'
                    addSource = 'DAVIS COUNTY'
                    loadDate = today
                    status = 'COMPLETE'
                    modified = row[12]
                    shp = row[9]
                    parcelID = ''
                    #parcelID = row[10]

                    iCursor.insertRow((addSys, utAddId, fullAdd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                                    unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcelID, addSource, loadDate, \
                                    status, '', modified, '', '', '', shp))

        # hill_afb_pts = r'..\Davis\Davis.gdb\AddressPoints_HillAFB'
        # arcpy.Append_management([hill_afb_pts], agrcAddPts_davisCo)

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Davis_ErrorPts.shp', 'FullAdd', davisCoAddPts)


    # dictLIR = {'Commercial':'Commercial', 'Residential':'Residential', 'Vacant':'Vacant Land', 'Unknown':['', ' ']}
    # davisLIR = {'PtType': ['SGID.CADASTRE.Parcels_Davis_LIR', 'PROP_CLASS']}
    
    remapLIR = {'Agricultural': ['LAND AGRICULTURE', 'LAND GREENBELT'], 'Commercial': ['LAND COMMERCIAL', 'Commercial'],
                'Residential': ['LAND RESIDENTIAL', 'LAND SECONDARY', 'Residential'], 'Other': ['LAND VACANT', 'Vacant Land', 'Vacant'],
                'Unknown':['Unknown', None, '']}

    inputDict = {
        'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
        'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
        'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
        'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
        'CountyID':['SGID.BOUNDARIES.Counties', 'FIPS_STR', ''],
        'PtType': ['SGID.CADASTRE.Parcels_Davis_LIR', 'PROP_CLASS', remapLIR],
        'ParcelID':['SGID.CADASTRE.Parcels_Davis', 'PARCEL_ID', '']
    }

    #fix_residential_type = {'PtType': ['SGID.CADASTRE.Parcels_Davis_LIR', 'PRIMARY_RES']}
    fix_residential_type = {'PtType': ['PLANNING.HousingUnitInventory', 'COUNTY']}
    remap_residential = {'Residential':'Davis'}

    addPolyAttributes(sgid, agrcAddPts_davisCo, inputDict)
    #addPolyAttributesLIR(sgid, agrcAddPts_davisCo, davisLIR, remapLIR)
    addPolyAttributesLIR(sgid, agrcAddPts_davisCo, fix_residential_type, remap_residential)
    #UpdatePropertyTypeLIR(sgid, agrcAddPts_davisCo, fix_residential_type, remap_residential)
    updateAddPtID(agrcAddPts_davisCo)
    addBaseAddress(agrcAddPts_davisCo)
    deleteDuplicatePts(agrcAddPts_davisCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_davisCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Davis_ErrorPts.shp'), errorFlds, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_davisCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def davisCounty_alias():
    davisCoAddPts = r'..\Davis\DavisCounty.gdb\DavisAddress'
    agrcAddPts_AliasDavisCo = r'..\Davis\Davis.gdb\AliasAddressPoints_Davis'
    out_county_fgdb = r'..\Davis\Davis.gdb'

    # davisCoAddFLDS = ['AddressNum', 'AddressN_1', 'UnitType', 'UnitNumber', 'RoadPrefix', 'RoadName', 'RoadNameTy', 'RoadPostDi',
    #                   'FullAddres', 'SHAPE@', 'PrimaryAdd', 'MunicipalN']
    davisCoAddFLDS = ['AddressNumber', 'AddressNumberSuffix', 'UnitType', 'UnitNumber', 'RoadPrefixDirection', 'RoadName', 'RoadNameType',
                      'RoadPostDirection', 'FullAddress', 'SHAPE@', 'PrimaryAddress', 'MunicipalName']
    
    alias_flds = ['AddSystem', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir',
                  'ZipCode', 'UnitType', 'UnitID', 'City', 'CountyID', 'UTAddPtID', 'SHAPE@']
        

    checkRequiredFields(davisCoAddPts, davisCoAddFLDS)
    #archive_last_month(agrcAddPts_AliasDavisCo)
    truncateOldCountyPts(agrcAddPts_AliasDavisCo)

    noTypeList = ['ANTELOPE ISLAND CAUSEWAY', 'APPLE ACRES', 'ASPEN GROVE', 'BOUNTIFUL MEMORIAL PARK', 'BROADWAY',
                  'BUFFALO RANCH DEVELOPMENT', 'BURN PLANT', 'CARRIAGE CROSSING', 'CENTERVILLE MEMORIAL PARK',
                  'CHERRY HILL ENTRANCE', 'CHEVRON REFINERY', 'CHRISTY', 'COMPTONS POINTE', 'DEER CREEK', 'EAST ENTRANCE',
                  'EAST PROMONTORY', 'EGG ISLAND OVERLOOK', 'FAIRVIEW PASEO', 'FARMINGTON CEMETERY', 'FARMINGTON CROSSING',
                  'FREEPORT CENTER', 'GARDEN CROSSING PASEO', 'HAWORTH', 'HWY 106', 'HWY 126', 'HWY 193', 'HWY 68', 'HWY 89',
                  'HWY 93', 'HOLLY HAVEN I', 'HOLLY HAVEN II', 'IBIS CROSSING', 'KAYSVILLE AND LAYTON CEMETERY',
                  'LLOYDS PARK', 'MOUNTAIN VIEW PASEO', 'NORTH ENTRANCE', 'NORTHEAST ENTRANCE', 'NORTHWEST ENTRANCE',
                  'POETS REST', 'PRESERVE PASEO', 'SOMERSBY', 'SOUTH CAUSEWAY', 'SOUTH ENTRANCE', 'SOUTHEAST ENTRANCE',
                  'STATION', 'STONEY BROOK', 'SYRACUSE CEMETERY', 'VALIANT', 'VALLEY VIEW', 'WARD', 'WARWICK', 'WEST PROMONTORY',
                  'WETLAND POINT', 'WHISPERING PINE', 'WILLOW BEND PASEO', 'WILLOW FARM PASEO', 'WILLOW GARDEN PASEO',
                  'WILLOW GREEN PASEO', 'WILLOW GROVE PASEO', 'WYNDOM']

    remove_stypes = ['STONEY BROOK CIR', 'ANGEL ST', 'BROWNING LN', 'CHARLENE WAY', 'COUNTRY WAY', 'EAGLES LNDG', 'GRANTS LN',
                     'SAGE DR']

    hwy_dict = {'SR 37':'HWY 37', 'SR 193':'HWY 193'}


    with arcpy.da.SearchCursor(davisCoAddPts, davisCoAddFLDS) as sCursor_davis, \
        arcpy.da.InsertCursor(agrcAddPts_AliasDavisCo, alias_flds) as iCursor:

        for row in sCursor_davis:
            if row[10] == 'A':
                if row[0] == 0 and row[5] != 'Freeport Center':
                    continue
                if row[11] in ['Ogden', 'Roy', 'Uintah', 'Washington Terrace']:
                    continue   

                elif row[0] not in errorList and row[5] not in errorList:

                    addNum = row[0]
                    addNumSuf = formatValues(row[1], addNumSufList)

                    unitId = removeBadValues(row[3], errorList).upper()
                    preDir = formatValues(row[4], dirs)

                    unitType = formatValues(row[2], unitTypeDir).upper()
                    if unitType != '' and unitId == '':
                        unitType = ''

                    streetName = removeBadValues(row[5], errorList).upper()

                    streetType = returnKey(removeNone(row[6]).upper(), sTypeDir)

                    if streetName.startswith('BEVERLY'):
                        streetName = 'BEVERLY'
                        streetType = 'WAY'
                    if streetName in remove_stypes:
                        long_sname = clean_street_name(streetName)
                        streetName = long_sname.name
                        streetType = long_sname.type
                        print(streetName)

                    if 'HIGHWAY' in streetName:
                        streetName = streetName.replace('HIGHWAY', 'HWY')

                    sufDir = formatValues(row[7], dirs)

                    if streetName in hwy_dict:
                        streetName = hwy_dict[streetName]
                        streetType = ''
                        sufDir = ''

                    if streetName == 'FREEPORT CENTER':
                        addNum = ''

                    addSys = ''
                    utAddId = ''
                    city = ''
                    zip = ''
                    fips = '49011'
                    shp = row[9]

                    iCursor.insertRow((addSys, addNum, addNumSuf, preDir, streetName, streetType, sufDir, 
                                       unitType, unitId, city, zip, fips, utAddId, shp))
                    
    inputDict = {
        'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
        'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
        'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', '']
        }

    alias_pts = {
        'UTAddPtID':['AddressPoints_Davis', 'UTAddPtID', '']
        }


    addPolyAttributes(sgid, agrcAddPts_AliasDavisCo, inputDict)
    addPolyAttributes(out_county_fgdb, agrcAddPts_AliasDavisCo, alias_pts)


def duchesneCounty():
    duchesneCoAddPts = r'..\Duchesne\DuchesneCounty.gdb\DuchesneAddressPoints'
    agrcAddPts_duchesneCo = r'..\Duchesne\Duchesne.gdb\AddressPoints_Duchesne'
    cntyFldr = r'..\Duchesne'

    duchesneCoAddFLDS = ['HOUSE_N', 'PRE_DIR', 'S_NAME', 'SUF_DIR', 'S_TYPE', 'PARCEL_ID', 'SHAPE@']

    checkRequiredFields(duchesneCoAddPts, duchesneCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_duchesneCo).getOutput(0))
    #archive_last_month(agrcAddPts_duchesneCo)
    truncateOldCountyPts(agrcAddPts_duchesneCo)

    highways = ['35', '40', '87', '121']
    county_rds = ['29', '6', '#6']
    sNameFix = {'1000 S (SUMMERALL LANE)':'1000 S', '12000 S (PLEASANT VALLEY ROAD)':'PLEASANT VALLEY ROAD',
                '31750 W (ELKHORN CIRCLE)':'ELKHORN CIRCLE', '34700 W (LAKE FORK AVE)':'LAKE FORK AVE',
                '35240 W COYOTE':'COYOTE', '6375  (SADDLEBACK ROAD)':'SADDLEBACK ROAD', 
                '6375 S (SADDLEBAC ROAD)':'SADDLEBACK ROAD', '800 N (CASEY COURT)':'800 N', '8000 S SUNSET':'SUNSET',
                '8375 S (BOULDER DRIVE)':'BOULDER DRIVE', '8375 S BOULDER':'BOULDER DRIVE',
                '8430 S (DIAMOND FORK DR)':'DIAMOND FORK DR', '8430 S (DIAMOND FORK DRIVE)':'DIAMOND FORK DR',
                '8430 S DIAMOND FORK':'DIAMOND FORK DR', '8485 S DIXIE':'DIXIE', '8820 S (LASAL RD)':'LASAL RD',
                '8875 S (TINTIC LN)':'TINTIC LN', '9030 S (BONANZA ROAD)':'BONANZA ROAD',
                '9140 S OPHIR':'OPHIR', '9200 S EUREKA':'EUREKA', 'BIG BUCKK RUN':'BIG BUCK RUN', 'BLUBELL':'BLUEBELL',
                'E RIVER':'EAST RIVER', 'EDYTHE MARRET':'EDYTHE MARETT', 'GEORGE MARET':'GEORGE MARETT',
                'HIGHWAY 40':'HWY 40', 'HIGHWAY 87':'HWY 87', 'KING ARTHUR':'KING ARTHURS', 'MT. TABBY':'MT TABBY',
                'N POCO':'NORTH POCO', 'N':'CENTER', 'PARKRIDGE':'PARK RIDGE', 'POLE LINE RD. (2000 S)':'2000 S',
                'RABBIT GULCH RAOD':'RABBIT GULCH ROAD', 'S MYTON':'SOUTH MYTON',
                'S MYTON ROAD (4000 WEST)':'SOUTH MYTON', 'SR 121':'HWY 121', 'SR 35':'HWY 35', 'SR 87':'HWY 87',
                'STATE STREET (0 EAST)':'STATE STREET', 'TITANIC':'TINTIC', 'TINTIC LANE (8875 S)':'TINTIC LANE',
                'U.S. HIGHWAY 40':'HWY 40', 'US 406':'HWY 40', 'VISTA POINTE (750 NORTH)':'VISTA POINTE'}

    errorPtsDict = {}
    rdSet = createRoadSet('49013')

    iCursor = arcpy.da.InsertCursor(agrcAddPts_duchesneCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(duchesneCoAddPts, duchesneCoAddFLDS) as sCursor_duchesne:
        for row in sCursor_duchesne:
            if row[0] not in errorList and row[2] not in errorList: # and len(row[2]) > 1:
                if row[2].isdigit() and row[3].strip() == '' and row[2] not in highways and row[2] not in county_rds:
                    continue
                else:
                    addNum = str(row[0]).replace('.0', '')
                    sName = (row[2]).strip().strip('.').upper()
                    sType = returnKey(row[4].upper().strip(), sTypeDir)
                    preDir = returnKey(row[1].upper(), dirs2)
                    if row[4] == 'Center':
                        preDir = row[2]
                        sName = 'CENTER'
                        sType = 'ST'
                    sufDir = returnKey(row[3].upper(), dirs2)

                    if sName in sNameFix:
                        sName = sNameFix[sName]

                    if sName in highways:
                        sName = f'HWY {sName}'
                        sType = ''
                    if sName in county_rds:
                        sName = sName.strip('#')
                        sName = f'COUNTY RD {sName}'
                        sType = ''
                    if sName.endswith((' N', ' S', ' E', ' W', ' NORTH', ' SOUTH', ' EAST', ' WEST')) and sName[0].isdigit() == True:
                        sufDir = returnKey(sName.split()[-1], dirs)
                        sName = sName.split()[0]
                        print(sName)
                        print(sufDir)
                        sType = ''
                    if sName.endswith((' AVE', ' AVENUE', ' CIR', ' CIRCLE', ' DR', ' DRIVE', ' RD', ' ROAD')):
                        sType = returnKey(sName.split()[-1], sTypeDir)
                        sName = ' '.join(sName.split()[:-1]).strip()

                    if sName in ['MAIN', 'STATE']:
                        sType = 'ST'
                    if sName[0].isdigit() == True:
                        sType = ''
                    if sName[0].isdigit() == False:
                        sufDir = ''

                    if preDir != '' and sufDir != '' and preDir == sufDir:
                        addressErrors = errorPtsDict.setdefault(f'{preDir} {sName} {sufDir}', [])

                        addressErrors.extend(['Prefix = Suffix direction', row[6]])

                    fullAdd = f'{addNum} {preDir} {sName} {sufDir} {sType}'
                    fullAdd = ' '.join(fullAdd.split())

                    parcelID = row[5]
                    modDate = None
                    loadDate = today
                    shp = row[6]

                    iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '', '', '', '', '49013', \
                                       'UT', '', '', '', parcelID, 'DUCHESNE COUNTY', loadDate, 'COMPLETE', '', modDate, '', '', '', shp))

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Duchesne_ErrorPts.shp', 'ADDRESS', duchesneCoAddPts)

    del iCursor

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_duchesneCo, inputDict)
    dupePts = returnDuplicateAddresses(agrcAddPts_duchesneCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Duchesne_ErrorPts.shp'), errorFlds, dupePts)
    updateAddPtID(agrcAddPts_duchesneCo)
    deleteDuplicatePts(agrcAddPts_duchesneCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    #findMissingPts('Duchesne', agrcAddPts_duchesneCo)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_duchesneCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def emeryCounty():
    emeryCoAddPts = r'..\Emery\EmeryCounty.gdb\addresses'
    agrcAddPts_emeryCo = r'..\Emery\Emery.gdb\AddressPoints_Emery'
    cntyFldr = r'..\Emery'

    emeryCoAddFLDS = ['AddNum', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 'UnitID', 'LandmarkNa', 'PtLocation',
                      'PtType', 'Structure', 'ParcelID', 'Modified', 'Building','SHAPE@', 'FullAdd', 'HouseAddr', 'OBJECTID']

    checkRequiredFields(emeryCoAddPts, emeryCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_emeryCo)

    rdSet = createRoadSet('49015')
    errorPtsDict = {}

    fix_dict = {'GREENRIVER':'GREEN RIVER', 'SOUTHFLAT':'SOUTH FLAT'}

    structureDict = {'Yes':['YES', 'yes', 'y'], 'No':['NO', 'no', 'n'], 'Unknown':['UNKNOWN', 'UNK']}
    county_list = ['Grand Co', 'Sevier Co']

    iCursor = arcpy.da.InsertCursor(agrcAddPts_emeryCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(emeryCoAddPts, emeryCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[10] not in county_list:
                if row[0] not in errorList or row[2] not in errorList:
                    address = parse_address.parse(row[14])
                    
                    addNum = row[0]
                    preDir = returnKey(row[1].upper(), dirs)
                    sName = row[2].upper()
                    if 'STATE ROAD' in sName:
                        sName = sName.replace('STATE ROAD', 'HWY')

                    if sName not in rdSet and 'HWY' not in sName:
                        addressErrors = errorPtsDict.setdefault(f'{row[14]} | {sName}', [])
                        addressErrors.extend(['Street name not in roads data', row[13]])

                    sufDir = returnKey(row[4].upper(), dirs)
                    sType = returnKey(row[3], sTypeDir)

                    if sName[1].isdigit() and sName.endswith(tuple([' ' + dir for dir in longDirs])):
                        sufDir = sName.split()[1][0]
                        sName = sName.split()[0]
                    if sName in fix_dict:
                        sName = fix_dict[sName]

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

                    fullAdd = f'{addNum} {preDir} {sName} {sufDir} {sType} {unitID_hash}'
                    fullAdd = ' '.join(fullAdd.split())

                    # if fullAdd != row[14].upper():
                    #     print (fullAdd + ' | ' + row[14])

        # --------------Create Error Points--------------
                    if row[2].upper() not in row[14].upper():
                        addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[14]}', [])
                        addressErrors.extend(['mixed street names', row[13]])
                    if preDir == sufDir and sType == '':
                        addressErrors = errorPtsDict.setdefault(row[14], [])
                        addressErrors.extend(['prefix = sufix', row[13]])
                    if row[3].upper() not in sTypeList:
                        addressErrors = errorPtsDict.setdefault(row[3], [])
                        addressErrors.extend(['bad street type', row[13]])

                    if preDir == sufDir and sType == '':
                        if preDir != address.prefixDirection:
                            preDir = address.prefixDirection
                        else:
                            continue

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, landmark, '', '',\
                                   unitID, '', '', '49015', 'UT', ptLocation, ptType, structure, parcelID, 'EMERY COUNTY', \
                                   loadDate, 'COMPLETE', '', modDate, '', '', '', shp))

        errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Emery_ErrorPts.shp', emeryCoAddFLDS[14], emeryCoAddPts)

    del sCursor
    del iCursor

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_emeryCo, inputDict)
    updateAddPtID(agrcAddPts_emeryCo)
    dupePts = returnDuplicateAddresses(agrcAddPts_emeryCo, ['UTAddPtID', 'SHAPE@'])
    addBaseAddress(agrcAddPts_emeryCo)
    updateErrorPts(os.path.join(cntyFldr, 'Emery_ErrorPts.shp'), errorPts, dupePts)
    deleteDuplicatePts(agrcAddPts_emeryCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def garfieldCounty():
    garfieldCoAddPts = r'..\Garfield\GarfieldCounty.gdb\AddressPoints_GarfieldCounty'
    agrcAddPts_garfieldCo = r'..\Garfield\Garfield.gdb\AddressPoints_Garfield'
    cntyFldr = r'..\Garfield'

    garfieldCoAddFLDS = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType',
                         'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State',
                         'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'LoadDate', 'Status', 'Editor',
                         'ModifyDate', 'StreetAlias', 'Notes', 'SHAPE@']

    checkRequiredFields(garfieldCoAddPts, garfieldCoAddFLDS)
    archive_last_month(agrcAddPts_garfieldCo)
    truncateOldCountyPts(agrcAddPts_garfieldCo)

    errorPtsDict = {}

    fix_name = {'ANTELPOE':'ANTELOPE', 'BRINGHAM YOUNG':'BRIGHAM YOUNG', 'BROKER BRANCH':'BROKEN BRANCH',
                'CHAFFIN\'S':'CHAFFINS', 'DD HOLOW':'DD HOLLOW', 'EGALE RIDGE':'EAGLE RIDGE', 'EPHRIAM\'S CAMP':'EPHRIAMS',
                'HELL\'S BACKBONE':'HELLS BACKBONE', 'HELL\'S BACK BONE':'HELLS BACKBONE', 'HELLS BACK BONE':'HELLS BACKBONE',
                'HOMESTEADE':'HOMESTEAD', 'HOMESTAED':'HOMESTEAD', 'KINGSS RANCH':'KINGS RANCH', 'KODACHOME':'KODACHROME',
                'LEFEVER':'LEFEVRE', 'MONKIA':'MONIKA', 'NORTH C0RRAL':'NORTH CORRAL', 'NOTH RUSSEL':'RUSSEL',
                'PANSAUGUNT C;LIFFS':'PAUNSAUGUNT CLIFFS', 'PINION BRANCH NORTH DRIVE':'PINION BRANCH NORTH',
                'PONDERPSA':'PONDEROSA', 'PONDEROSE':'PONDEROSA', 'PONDEROSE TRAILS':'PONDEROSA TRAILS',
                'RESERVIOR':'RESERVOIR', 'SHANGRA':'SHANGRA LA', 'S0UTHVIEW':'SOUTHVIEW', 'SKOTTS CREEK':'SKOOTS CREEK',
                'STATE HIGHWAY 276':'HWY 276', 'STATE HWY 276':'HWY 276', 'STATE HWY 12':'HWY 12', 'SQAUW BERRY':'SQUAW BERRY',
                'TROUT STREET':'TROUT', 'UHIGHWAY 89':'HWY 89', 'UHWY 89':'HWY 89', 'US':'HWY 89', 'US HIGHWAY 89':'HWY 89',
                'UTAH STATE':'HWY 12', 'WOOKCHUCK':'WOODCHUCK'}

    full_name_rds = ['BRYCE MEADOW LN', 'CENTER ST', 'CORN CREEK ROAD' , 'MILLER LANE', 'POINT VIEW DR' , 'ATKINS ROAD']

    with arcpy.da.SearchCursor(garfieldCoAddPts, garfieldCoAddFLDS) as sCursor, \
        arcpy.da.InsertCursor(agrcAddPts_garfieldCo, agrcAddFLDS) as iCursor:
        for row in sCursor:
            if row[3] in errorList or row[6] in errorList:
                continue
            else:
                addNum = row[3]
                if ' ' in addNum:
                    addNum = addNum.split()[0]

                preDir = returnKey(row[5], dirs)

                sName = removeBadValues(row[6], errorList)
                if 'HIGHWAY' in sName:
                    sName = sName.replace('HIGHWAY', 'HWY')

                sName = sName.replace("'", "")
                if sName in fix_name:
                    sName = fix_name[sName]
                
                if sName in full_name_rds:
                    long_sname = clean_street_name(sName)
                    sName = long_sname.name
                    sType = long_sname.type

                sType = returnKey(row[7], sTypeDir)
                if 'HWY' in sName:
                    sType = ''
                sufDir = returnKey(row[8], dirs)
                unitId = removeBadValues(row[12], errorList)
                ptLocation = row[17]
                ptType = row[18]
                structure = row[19]
                parcel = removeNone(row[20])
                if len(parcel) < 5:
                    parcel = ''
                mDate = row[25]
                loadDate = today
                shp = row[28]

                if unitId != '':
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} # {unitId}'
                elif sType == 'HWY':
                    fullAdd = f'{addNum} {preDir} {sName} {sufDir}'
                else:
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir}'

                fullAdd = ' '.join(fullAdd.split())

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '',\
                                   unitId, '', '', '49017', 'UT', ptLocation, ptType, structure, parcel, 'GARFIELD COUNTY', \
                                   loadDate, 'COMPLETE', '', mDate, '', '', '', shp))


    errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Garfield_ErrorPts.shp', 'EXAMPLE', garfieldCoAddPts)

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_garfieldCo, inputDict)
    updateAddPtID(agrcAddPts_garfieldCo)
    addBaseAddress(agrcAddPts_garfieldCo)
    dupePts = returnDuplicateAddresses(agrcAddPts_garfieldCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Garfield_ErrorPts.shp'), errorPts, dupePts)
    deleteDuplicatePts(agrcAddPts_garfieldCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def grandCounty():
    rdSet = createRoadSet('49019')

    grandCoAddPts = r'..\Grand\GrandCounty.gdb\GrandPts'
    agrcAddPts_grandCo = r'..\Grand\Grand.gdb\AddressPoints_Grand'
    cntyFldr = r'..\Grand'

    grandCoAddFLDS = ['FullAdd', 'AddNum', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 'UnitType', 'UnitID', \
                      'City', 'ZipCode', 'PtLocation', 'PtType', 'Structure', 'ParcelID', 'ModifyDate', 'SHAPE@', 'OBJECTID']

    checkRequiredFields(grandCoAddPts, grandCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_grandCo).getOutput(0))
    archive_last_month(agrcAddPts_grandCo)
    truncateOldCountyPts(agrcAddPts_grandCo)

    errorPtsDict = {}

    fix_name = {'BAGDERS':'BADGERS', 'BUCCHANAN':'BUCHANAN', 'DRE':'DREAM', 'HASTING':'HASTINGS', 'HIGHWAY 128':'HWY 128',
                'HIGHWAY 191':'HWY 191', 'HUNTCREEK':'HUNT CREEK', 'ICEHOUSE PLACE':'ICEHOUSE', 'KANE CREEL':'KANE CREEK',
                'KANE PRINGS':'KANE SPRINGS', 'MAIN RUBISON':'MAIN RUBICON', 'MOUNTAINVIEW':'MOUNTAIN VIEW', 'MULBERRY': 'MULLBERRY', 'S HWY':'HWY 191',
                'SR 279':'HWY 279', 'SR 313':'HWY 313', 'SR 94':'HWY 94', 'RIM SHADOW':'RIMSHADOW', 'S HWY 191':'HWY 191',
                'SUNNY DALE':'SUNNYDALE', 'VAKKEY VIEW':'VALLEY VIEW', 'ZIMMERMZN':'ZIMMERMAN'}
    
    add_type = {'MAIN':'ST', 'CERMAK':'ST', 'PACE':'LN', 'RIMSHADOW':'LN', 'TIERRA DEL SOL':'DR'}
    
    long_names = ['100 N', '400 N', 'CASTLE VALLEY DR']

    with arcpy.da.SearchCursor(grandCoAddPts, grandCoAddFLDS) as sCursor, \
        arcpy.da.InsertCursor(agrcAddPts_grandCo, agrcAddFLDS) as iCursor:
        for row in sCursor:
            if row[1] not in errorList:
                addNum = row[1]
                preDir = returnKey(row[2], dirs)

                if row[3] in errorList:
                    addressErrors = errorPtsDict.setdefault(row[16], [])
                    addressErrors.extend(['bad street name', row[15]])
                    continue
                sName = row[3].upper()
                sName = sName.replace(u'\xd1', 'N')
                if sName not in rdSet:
                    if row[0] != None:
                        addressErrors = errorPtsDict.setdefault(f'{row[0]} | {row[3]}', [])
                        addressErrors.extend(['street name not in roads data', row[15]])
                    else:
                        addressErrors = errorPtsDict.setdefault(f'{row[16]} | {row[3]}', [])
                        addressErrors.extend(['street name not in roads data', row[15]])

                if sName in fix_name:
                    sName = fix_name[sName]

                sType = returnKey(removeNone(row[4]), sTypeDir)

                sufDir = returnKey(row[5], dirs)
                if sufDir == '' and sName[0].isdigit() == True:
                    if row[0] != None:
                        addressErrors = errorPtsDict.setdefault(row[0], [])
                        addressErrors.extend(['suffix direction missing?', row[15]])
                    else:
                        addressErrors = errorPtsDict.setdefault(row[16], [])
                        addressErrors.extend(['suffix direction missing?', row[15]])

                if sName in long_names:
                    fix_long_name = clean_street_name(sName)
                    sName = fix_long_name.name
                    sufDir = fix_long_name.direction
                    sType = fix_long_name.type

                if 'HWY ' in sName:
                    sType = ''
                if sName[1].isdigit() == False:
                    sufDir = ''

                if sName in add_type and sType == '':
                    sType = add_type[sName]

                unitId = removeNone(row[7]).strip('#').strip()

                fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir}'
                if unitId != '':
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} # {unitId}'
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

    errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Grand_ErrorPts.shp', 'EXAMPLE', grandCoAddPts)

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_grandCo, inputDict)
    updateAddPtID(agrcAddPts_grandCo)
    addBaseAddress(agrcAddPts_grandCo)
    dupePts = returnDuplicateAddresses(agrcAddPts_grandCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Grand_ErrorPts.shp'), errorPts, dupePts)
    deleteDuplicatePts(agrcAddPts_grandCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_grandCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def ironCounty():
    iron_agol_pts = 'https://services.arcgis.com/xGNWaeXY0POVazgT/arcgis/rest/services/Addressing_WFL1/FeatureServer/19'
    ironCoAddPts = r'..\Iron\IronCounty.gdb\iron_agol_pts'
    #ironCoAddPts = r'..\Iron\IronCounty.gdb\IronAddressPts'
    agrcAddPts_ironCo = r'..\Iron\Iron.gdb\AddressPoints_Iron'
    cntyFldr = r'..\Iron'

    agol_to_fgdb('Iron', iron_agol_pts)

    #ironCoAddFLDS = ['AddNum', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 'UnitType', 'UnitID', 'EditDate', 'SHAPE@', 'FullAdd']
    ironCoAddFLDS = ['AddrNum', 'AddrPD', 'AddrSN', 'AddrST', 'AddrSD', 'UnitType', 'UnitID', 'Date', 'SHAPE@', 'FullAddr']
    #ironCoAddFLDS = ['AddNum', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 'UnitType', 'UnitID', 'LoadDate', 'SHAPE@', 'FullAdd']

    checkRequiredFields(ironCoAddPts, ironCoAddFLDS)
    archive_last_month(agrcAddPts_ironCo)
    truncateOldCountyPts(agrcAddPts_ironCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49021')
    fixStreets = {'AAROTIPPETS':'AARON TIPPETS', 'APPLBLOSSOM':'APPLE BLOSSOM', 'AHSDOWFOREST':'ASHDOWN FOREST', 'ASHDOWFOREST':'ASHDOWN FOREST',
                  'ANTELOPSPRINGS':'ANTELOPE SPRINGS', 'APPLALOSA':'APPALOOSA', 'APPLALOOSA':'APPALOOSA', 'APPLEBLOSSOM':'APPLE BLOSSOM',
                  'ASPERIDGE':'ASPEN RIDGE', 'AVIATON':'AVIATION', 'BEACOHL':'BEACON','CANYORANCH':'CANYON RANCH', 'BLUJAY':'BLUE JAY', 'BUCKSKIVALLEY':'BUCKSKIN VALLEY',
                  'BUMBLEBESPRING':'BUMBLEBEE SPRING', 'CANYOBREEZE':'CANYON BREEZE', 'CEDAR KNOLLSOUTH':'CEDAR KNOLLS SOUTH',
                  'COMMERCCENTER':'COMMERCE CENTER', 'COVCANYON':'COVE CANYON', 'COVVIEW':'COVE VIEW', 'COVEREDAGON':'COVERED WAGON',
                  'COVHEIGHTS':'COVE HEIGHTS', 'CROSHOLLOW': 'CROSS HOLLOW', 'DOUBLTREE':'DOUBLE TREE', 'EAGLEROOST':'EAGLES ROOST',
                  'EAGLRIDGE':'EAGLE RIDGE', 'GEORGBERRY':'GEORGE BERRY', 'GLECANYON':'GLEN CANYON', 'GOLDELEAF':'GOLDEN LEAF',
                  'GREENLAKE':'GREENS LAKE', 'GUIDELIGHT':'GUIDE LIGHT', 'HALFCLE':'HALF CIRCLE', 'HERITAGHILLS':'HERITAGE HILLS', 
                  'HIDDEHILLS':'HIDDEN HILLS', 'HIDDELAKE':'HIDDEN LAKE', 'HIGH MOUNTAIVIEW':'HIGH MOUNTAIN VIEW', 'HOUSROCK':'HOUSE ROCK',
                  'IROTOWLOOKOUT':'IRON TOWN LOOKOUT', 'JACKSOPOINT':'JACKSON POINT', 'JAMES':'ST JAMES', 'LITTLPINTO CREEK':'LITTLE PINTO CREEK',
                  'LITTLCREEK CANYON':'LITTLE CREEK CANYON', 'LITTLSALT LAKE':'LITTLE SALT LAKE', 'LODGLAKE':'LODGE LAKE',
                  'LUMDERJACK':'LUMBERJACK', 'KIMBERLEY':'KIMBERLY', 'MAPLCANYON':'MAPLE CANYON', 'MARBLCANYON':'MARBLE CANYON',
                  'MARSHALL':'MARSHAL', 'MEADOLAKE':'MEADOW LAKE', 'MEADOLANE':'MEADOW LANE', 'MEADOLARK':'MEADOW LARK',
                  'MOUNTAIVALLEY':'MOUNTAIN VALLEY', 'MOUNTAIVIEW':'MOUNTAIN VIEW', 'MOUNTIAVIEW':'MOUNTAIN VIEW', 'MT VIEW':'MOUNTAIN VIEW',
                  'MULTRIAN':'MULE TRAIN', 'MULETRAIN':'MULE TRAIN', 'MULTRAIN':'MULE TRAIN', 'NIFTWOOD':'DRIFT WOOD', 'NY LAKES':'DRY LAKES',
                  'OLD HWY91':'OLD HWY 91', 'OLD HWY144':'OLD HWY 144', 'OLD IROTOWN':'OLD IRONTOWN', 'OLDIROTOWN':'IRONTOWN',
                  'PAINTBRUST':'PAINTBRUSH', 'PARADISCANYON':'PARADISE CANYON', 'PARK-U PINE WALK':'PARK-U-PINE WALK', 'PINCANYON':'PINE CANYON',
                  'PINHURST':'PINEHURST', 'PROVIDENC CENTER':'PROVIDENCE CENTER', 'PROVIDENCCENTER':'PROVIDENCE CENTER',
                  'PROVIDENICE CENTER':'PROVIDENCE CENTER', 'RIDGVIEW':'RIDGE VIEW','ROBBERROOST':'ROBBERS ROOST', 'RUJOLLEY':'RUE JOLLEY',
                  'SADDLBACK':'SADDLE BACK', 'SCLEWAY':'CIRCLEWAY', 'SIFTWOOD DR':'DRIFTWOOD', 'SILVERSPUR':'SILVER SPUR', 'SUISE':'SUNRISE',
                  'SHOOTINGAR':'SHOOTING STAR', 'SNOSHOE':'SNOW SHOE', 'SOUTHERVIEW':'SOUTHERN VIEW', 'SPLINTERWOOD':'SPLINTER WOOD',
                  'TIMBERNEST':'TIMBERCREST', 'TOBAGGAN':'TOBOGGAN', 'TRIPLDUECE':'TRIPLE DUECE', 'VAQUERO WAYM':'VAQUERO WAY', 'VASLES':'VASELS',
                  'VASSELS':'VASELS', '4100 N SYCAMORE RD':'4100'}

    fullname_roads = ['5300 N', 'ANTELOPE RD', 'CEDAR BLUFF DR', 'GAP RD', 'GRAND VW', 'GRIMSHAW LN', 'IRON SPRINGS RD', 'LUND HWY',
                      'MAVERICK WAY', 'MIDVALLEY RD', 'MINERSVILLE HWY', 'SKI VIEW DR', 'TIPPLE RD', 'VAQUERO WAY',  'WECCO RD']

    iCursor = arcpy.da.InsertCursor(agrcAddPts_ironCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(ironCoAddPts, ironCoAddFLDS) as sCursor_iron:
        for row in sCursor_iron:
            if row[0] not in errorList:
                addNum = row[0]
            else:
                continue

            if row[3] == 'TR':
                sType = 'TRL'
            else:
                sType = returnKey(row[3], sTypeDir)

            if row[2] not in errorList:
                sName = row[2].upper().strip()

                if sName[:2] == 'SR' and sName[2].isdigit():
                    sName = sName.replace('SR', 'HWY ')
                    sType = ''
                if sName == 'SRY':
                    sName = 'TERRY'
                if sName == 'SRACE':
                    sName == 'TERRACE'

            else:
                continue

            if row[2] not in rdSet:
                addressErrors = errorPtsDict.setdefault(f'{row[9]} | {row[2]}', [])
                addressErrors.extend(['Street name missing in roads data', row[8]])

            if sName in fixStreets:
                print(f'fixed {sName}')
                sName = fixStreets[sName]

            preDir = returnKey(row[1], dirs)

            sufDir = returnKey(row[4], dirs)

            if sName in fullname_roads:
                long_sname = clean_street_name(sName)
                sName = long_sname.name
                sType = long_sname.type
                if sName.isdigit() == True:
                    sType = ''
                    sufDir = long_sname.sdir

            if sName == 'COVERED WAGON':
                sType = 'DR'
                sufDir = ''
            if sName == 'NATURE VIEW' and sType == '':
                sType = 'DR'
            if sName == '1020' and preDir == 'W' and sufDir == '':
                sufDir = 'S'
            if sName == '2175' and preDir == 'N' and sufDir == '':
                sufDir = 'W'
            if sName == '2925' and preDir == 'S' and sufDir == '':
                sufDir = 'W'
            if sName == '2925' and sType == 'ST':
                sType = ''
            if sName == '300' and preDir == 'W' and sufDir == 'W':
                sufDir = 'N'

            landmark = ''
            unitType = returnKey(row[5], unitTypeDir)
            unitID = removeBadValues(row[6], errorList)
            mDate = None
            loadDate = today
            shp = row[8]

            if unitType == '' and unitID != '':
                fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} # {unitID}'
            elif unitType != '' and unitID != '':
                fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} {unitType} {unitID}'
            else:
                fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir}'

            fullAdd = ' '.join(fullAdd.split())

            if preDir == sufDir and preDir != '':
                print('dir = dir')
                addressErrors = errorPtsDict.setdefault(fullAdd, [])
                addressErrors.extend(['predir = sufdir', row[8]])

            iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, landmark, '', unitType, unitID, '', '', '49021', \
                               'UT', '', '', '', '', 'IRON COUNTY', loadDate, 'COMPLETE', '', mDate, '', '', '', shp))

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Iron_ErrorPts.shp', ironCoAddFLDS[9], ironCoAddPts)


    del iCursor

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    iron_parcelsLIR = {'PtType': ['SGID.CADASTRE.Parcels_Iron_LIR', 'PROP_CLASS']}

    iron_remapLIR = {'Agricultural':['Agricultural', 'Greenbelt'],
                     'Residential':['Residential', 'Commercial - Apartment & Condo'],
                     'Commercial':['Commercial',  'Commercial - Office Space', 'Commercial - Retail'], 
                     'Mixed Use':['Mixed Use'],
                     'Unknown': [None, 'Unknown', ''],
                     'Other':['Tax Exempt', 'Tax Exempt - Charitable Organization or Religious',
                              'Tax Exempt - Government', 'Undevelopable', 'Vacant', 'Privilege Tax', 'Personal Property']}
    

    addPolyAttributes(sgid, agrcAddPts_ironCo, inputDict)
    updateAddPtID(agrcAddPts_ironCo)
    addPolyAttributesLIR(sgid, agrcAddPts_ironCo, iron_parcelsLIR, iron_remapLIR)
    addBaseAddress(agrcAddPts_ironCo)
    deleteDuplicatePts(agrcAddPts_ironCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_ironCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Iron_ErrorPts.shp'), errorFlds, dupePts)


def juabCounty():
    juabCoAddPts = r'..\Juab\JuabCounty.gdb\Juab_addpts_20220728_UGRC_edits'
    agrcAddPts_juabCo = r'..\Juab\Juab.gdb\AddressPoints_Juab'

    juabCoAddFLDS = ['FullAdd', 'AddNum', 'AddNumSuff', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 
                     'LandmarkNa', 'Building', 'UnitType', 'UnitID', 'PtLocation', 'PtType', 'Structure', 'ParcelID',
                     'AddSource', 'SHAPE@']
    
    remap_pt_location = {'Water Tank':'Other', 'Well':'Other'}
    remap_hwy = {'HIGHWAY 78':'HWY 78', 'HIGHWAY 132':'HWY 132'}

    checkRequiredFields(juabCoAddPts, juabCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_juabCo)

    with arcpy.da.SearchCursor(juabCoAddPts, juabCoAddFLDS) as scursor, \
        arcpy.da.InsertCursor(agrcAddPts_juabCo, agrcAddFLDS) as icursor:

        for row in scursor:
            if row[1] and row[4] not in errorList:
                add_num = row[1].strip()
                pre_dir = row[3].strip()
                street_name = row[4].strip()
                street_type = row[5].strip()

                if street_name == 'SHEEPLANE':
                    street_name = 'SHEEP'
                    street_type = 'LN'
                if street_name in remap_hwy:
                    street_name = remap_hwy[street_name]
                if street_name.startswith('HWY'):
                    street_type = ''

                suf_dir = row[6].strip()
                landmark = row[7].upper().strip()
                unit_type = ''
                unit_id = row[10].strip()

                pt_location = row[11].strip()
                if pt_location in remap_pt_location:
                    pt_location = remap_pt_location[pt_location]

                pt_type = row[12].strip()
                structure = row[13].strip()
                load_date = today

                if unit_id != '':
                    full_add = f'{add_num} {pre_dir} {street_name} {suf_dir} {street_type} # {unit_id}'
                else:
                    full_add = f'{add_num} {pre_dir} {street_name} {suf_dir} {street_type}'

                full_add = ' '.join(full_add.split())

                shp = row[16]

                icursor.insertRow(('', '', full_add, add_num, '', pre_dir, street_name, street_type, suf_dir, landmark, '',
                                   unit_type, unit_id, '', '', '49023', 'UT', pt_location, pt_type, structure, '',
                                   'JUAB COUNTY', load_date, 'COMPLETE', '', None, '', '', '', shp))

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
    'ParcelID':['SGID.CADASTRE.Parcels_Juab', 'PARCEL_ID', '']
    }

    addPolyAttributes(sgid, agrcAddPts_juabCo, inputDict)
    addBaseAddress(agrcAddPts_juabCo)
    updateAddPtID(agrcAddPts_juabCo)
    deleteDuplicatePts(agrcAddPts_juabCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def kaneCounty():
    kaneCoAddPts = r'..\Kane\KaneCounty.gdb\ADDRESS_POINTS'
    agrcAddPts_kaneCo = r'..\Kane\Kane.gdb\AddressPoints_Kane'
    cntyFldr = r'..\Kane'

    kaneCoAddFLDS = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuff', 'PrefixDir', 'StreetName', 'StreetType',
                     'SuffixDir', 'LandmarkNa', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State',
                     'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'SHAPE@', 'OBJECTID']

    checkRequiredFields(kaneCoAddPts, kaneCoAddFLDS)
    #archive_last_month(agrcAddPts_kaneCo)
    truncateOldCountyPts(agrcAddPts_kaneCo)

    errorPtsDict = {}

    fix_rds = {'8 MILE GAP':'EIGHT MILE GAP','AARON BURR SUITE D':'AARON BURR', 'JOHNSON CAYON':'JOHNSON CANYON',
               'JOHNSONCANYON':'JOHNSON CANYON', 'UNINTAH':'UINTAH'}


    with arcpy.da.SearchCursor(kaneCoAddPts, kaneCoAddFLDS) as sCursor_kane, \
        arcpy.da.InsertCursor(agrcAddPts_kaneCo, agrcAddFLDS) as iCursor:

        for row in sCursor_kane:

            if row[3] not in errorList and row[6] not in ['725 E KANEPLEX DR']:
                addNum = row[3]
                preDir = returnKey(removeBadValues(row[5], errorList), dirs)
                streetName = removeBadValues(row[6], errorList)
                if row[7] == '100':
                    streetName = '100'
                streetType = returnKey(removeBadValues(row[7], errorList), sTypeDir)
                sufDir = returnKey(removeBadValues(row[8], errorList), dirs)
                landmark = removeBadValues(row[9], errorList)
                building = removeBadValues(row[10], errorList)
                unitType = removeBadValues(row[11], errorList)
                unitId = removeBadValues(row[12], errorList).strip('#')
                ptLocation = removeBadValues(row[17], errorList)
                ptType = removeBadValues(row[18], errorList)
                structure = removeBadValues(row[19], errorList)
                parcel = removeBadValues(row[20], errorList)

            elif row[2] not in errorList and row[2] not in ['KANAB', 'KANAB UTAH', 'S HOUSE ROCK VALLEY ROAD', 'WHITE HOUSE TRAILHEAD RD']:
                address = parse_address.parse(row[2])
                addNum = address.houseNumber
                preDir = removeNone(address.prefixDirection)
                streetName = address.streetName
                streetType = removeNone(address.suffixType)
                sufDir = removeNone(address.suffixDirection)
                landmark = removeBadValues(row[9], errorList)
                building = removeBadValues(row[10], errorList)
                unitType = removeBadValues(row[11], errorList)
                unitId = removeBadValues(row[12], errorList).strip('#')
                ptLocation = removeBadValues(row[17], errorList)
                ptType = removeBadValues(row[18].title(), errorList)
                structure = removeBadValues(row[19], errorList)
                parcel = removeBadValues(row[20], errorList)

            else:
                continue

            if streetName in fix_rds:
                streetName = fix_rds[streetName]

                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[6]}', [])
                addressErrors.extend(['bad street name', row[22]])
            
            if streetName not in errorList and streetName[0].isdigit() == True and streetName.endswith((' N', ' S', ' E', ' W')):
                sufDir = streetName[-1]
                streetName = streetName.replace(streetName[-2:], '')

                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[6]}', [])
                addressErrors.extend(['suffix dir in street name', row[22]])

            if streetName.endswith((' LN', ' DR', ' ST', ' TL')):
                streetType = streetName[-2:]
                if streetType == 'TL':
                    streetType = 'TRL'
                streetName = streetName[:-3]

                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[6]}', [])
                addressErrors.extend(['street type in street name', row[22]])
                
            if streetName.startswith('HIGHWAY'):
                streetName = streetName.replace('HIGHWAY', 'HWY').rstrip('HWY')

            if streetType in ['N', 'S', 'E', 'W']:
                sufDir = streetType
                streetType = ''

                addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[7]}', [])
                addressErrors.extend(['suffix dir in street street type', row[22]])

            if unitType == '' and unitId != '':
                fullAdd = f'{addNum} {preDir} {streetName} {sufDir} {streetType} # {unitId}'
            else:
                fullAdd = f'{addNum} {preDir} {streetName} {sufDir} {streetType} {unitType} {unitId}'

            fullAdd = ' '.join(fullAdd.split())

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
            editor = ''
            shp = row[22]

            iCursor.insertRow((addSys, utAddId, fullAdd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                                unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                                status, editor, None, '', '', '', shp))

    errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Kane_ErrorPts.shp', 'EXAMPLE', kaneCoAddPts)

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_kaneCo, inputDict)
    updateAddPtID(agrcAddPts_kaneCo)
    addBaseAddress(agrcAddPts_kaneCo)
    deleteDuplicatePts(agrcAddPts_kaneCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_kaneCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Kane_ErrorPts.shp'), errorPts, dupePts)


def millardCounty():
    millardCoAddPts = r'..\Millard\MillardCounty.gdb\Millard_Addresses'
    agrcAddPts_millardCo = r'..\Millard\Millard.gdb\AddressPoints_Millard'
    cntyFldr = r'..\Millard'

    millardCoAddFLDS = ['HOUSENUM1', 'PREDIR', 'STREETNAME', 'STREETTYPE', 'UNIT_TYPE', 'UNIT_ID', 'SHAPE@']

    name_types = (' AVE', ' DR', ' LANE', ' LN', ' RD', ' WAY')
    fix_names = {'8430 SOUTH (SANDHILLS RD)':'SANDHILLS RD', 'BIRCH DR (450 SOUTH)':'BIRCH DR',
                 'OLDFIELD':'OLD FIELD', 'US HIGHWAY 50':'HWY 50', 'TAMERIX':'TAMARIX',
                 'CRYSTAL PEAKS SPUR':'CRYSTAL PEAK SPUR'}

    errorPtsDict = {}
    rdSet = createRoadSet('49027')

    checkRequiredFields(millardCoAddPts, millardCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_millardCo).getOutput(0))
    archive_last_month(agrcAddPts_millardCo)
    truncateOldCountyPts(agrcAddPts_millardCo)

    with arcpy.da.SearchCursor(millardCoAddPts, millardCoAddFLDS) as sCursor_millardCo, \
        arcpy.da.InsertCursor(agrcAddPts_millardCo, agrcAddFLDS) as iCursor:

        for row in sCursor_millardCo:
            if row[0] not in errorList and row[2] not in errorList:

                if ' ' in row[0]:
                    add_num = row[0].split()[0]
                else:
                    add_num = row[0]
                
                stype = returnKey(row[3], sTypeDir)
                predir = row[1].upper().strip()
                unit_type = returnKey(row[4].strip(), unitTypeDir)
                unit_id = row[5].strip()

                if row[2][1].isdigit() == True and row[2] not in fix_names:
                    sname = row[2].split()[0]
                    sufdir = returnKey(row[2].split()[1], dirs)
                    stype = ''
                else:
                    sname = row[2].upper()
                    stype = returnKey(row[3], sTypeDir)
                    sufdir = ''

                if sname in fix_names:
                    sname = fix_names[sname]
                
                if sname.startswith('HIGHWAY'):
                    sname = sname.replace('HIGHWAY', 'HWY')
                if sname.endswith('HIGHWAY'):
                    stype = 'HWY'
                    sname = sname[:-8]
                if sname.startswith('HWY'):
                    stype = ''
                if sname.endswith((name_types)):
                    stype = returnKey(sname.split()[-1], sTypeDir)
                    sname = ' '.join(sname.split()[:-1]).strip()
                if 'NOTTINGHAM' in sname:
                    sname = 'NOTTINGHAM'
                    stype = 'DR'

                if 'O' in add_num:
                    add_num = add_num.replace('O', '0')
                add_num = re.sub('[^0-9]', '', add_num)

                if unit_type == '' and unit_id != '':
                    fulladd = f'{add_num} {predir} {sname} {sufdir} {stype} # {unit_id}'
                else:
                    fulladd = f'{add_num} {predir} {sname} {sufdir} {stype} {unit_type} {unit_id}'

                fulladd = ' '.join(fulladd.split())
 
                shp = row[6]

                iCursor.insertRow(('', '', fulladd, add_num, '', predir, sname, stype, sufdir, '', '', unit_type, unit_id,\
                                   '', '', '49027', 'UT', 'Unknown', 'Unknown', 'Unknown', '', 'MILLARD COUNTY', today,\
                                   'COMPLETE', '', None, '', '', '', shp))

                if predir == sufdir:
                    addressErrors = errorPtsDict.setdefault(fulladd, [])
                    addressErrors.extend(['pre and post directions match', row[6]])
                if 'HWY' not in sname and sname not in rdSet:
                    addressErrors = errorPtsDict.setdefault(f'{row[2]} | {fulladd}', [])
                    addressErrors.extend(['street name not found in roads', row[6]])
                if predir == '' and sufdir != '':
                    addressErrors = errorPtsDict.setdefault(f'NSEW | {fulladd}'.format(fulladd, row[0]), [])
                    addressErrors.extend(['prefix direction is missing', row[6]])


        error_pts = createErrorPts(errorPtsDict, cntyFldr, 'Millard_ErrorPts.shp', 'ADDRESS', millardCoAddPts)

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'ParcelID':['SGID.CADASTRE.Parcels_Millard_LIR', 'PARCEL_ID', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_millardCo, inputDict)
    updateAddPtID(agrcAddPts_millardCo)
    addBaseAddress(agrcAddPts_millardCo)
    deleteDuplicatePts(agrcAddPts_millardCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_millardCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Millard_ErrorPts.shp'), error_pts, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_millardCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def morganCounty():
    #morgan_agol_pts = 'https://services5.arcgis.com/9zdKz4c9IFXMrlCe/ArcGIS/rest/services/AddressPoints/FeatureServer/0'
    #morganCoAddPts = r'..\Morgan\MorganCounty.gdb\Morgan_agol_pts'
    morganCoAddPts = r'..\Morgan\MorganCounty.gdb\AddressPoints'
    
    agrcAddPts_morganCo = r'..\Morgan\Morgan.gdb\AddressPoints_Morgan'
    cntyFldr = r'..\Morgan'

    #agol_to_fgdb('Morgan', morgan_agol_pts)

    morganCoAddFLDS = ['ADDRNUM', 'FULLNAME', 'UNITTYPE', 'UNITID', 'LASTUPDATE', 'SHAPE@', 'FULLADDR', 'SERIAL']
    #morganCoAddFLDS = ['addrnum', 'fullname', 'unittype', 'unitid', 'last_edited_date', 'SHAPE@', 'fulladdr', 'Serial']

    checkRequiredFields(morganCoAddPts, morganCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_morganCo).getOutput(0))
    #archive_last_month(agrcAddPts_morganCo)
    truncateOldCountyPts(agrcAddPts_morganCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49029')

    exp = re.compile(r'(?:^[NSEW]\s)?(?:(.+)(\s[NSEW]$)|(.+$))')

    leadingSpaceTypes.extend([' LANE', ' COURT', ' COVE', ' CIRCLE', ' PARKWAY'])
                                       
    with arcpy.da.SearchCursor(morganCoAddPts, morganCoAddFLDS) as sCursor, \
        arcpy.da.InsertCursor(agrcAddPts_morganCo, agrcAddFLDS) as iCursor:

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

            if sName == '5800' and addNum > '4399':
                sName = 'POWDER HORN'
                sType = 'DR'
                sufDir = ''
            sName = sName.replace('POWDERHORN', 'POWDER HORN')

            if row[2] not in errorList:
                unitType = returnKey(row[2].upper(), unitTypeDir)

            unitID = removeBadValues(row[3], errorList).strip('#')

            modDate = row[4]
            loadDate = today
            parcel = removeNone(row[7])

            shp = row[5]

            if unitType == '' and unitID != '':
                fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} # {unitID}'
            else:
                fullAdd = f'{addNum} {preDir} {sName} {sufDir} {sType} {unitType} {unitID}'

            fullAdd = ' '.join(fullAdd.split())

            if fullAddr != fullAdd:
                print(fullAddr + '  -  ' + fullAdd)
            if 'HWY' not in sName and sName not in rdSet:
                addressErrors = errorPtsDict.setdefault(f'{sName} | {fullAddr}', [])
                addressErrors.extend(['add pts street name not found in roads', row[5]])

            iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', unitType, unitID, '', '', '49029', \
                              'UT', '', '', '', parcel, 'MORGAN COUNTY', loadDate, 'COMPLETE', '', modDate, '', '', '', shp))

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Morgan_ErrorPts.shp', morganCoAddFLDS[6], morganCoAddPts)
    del iCursor

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    morgan_parcelsLIR = {'PtType': ['SGID.CADASTRE.Parcels_Morgan_LIR', 'PROP_CLASS']}

    morgan_remapLIR = {'Agricultural':['Agricultural', 'Greenbelt'],
                      'Commercial':['Commercial',  'Commercial - Office Space', 'Commercial - Retail'],
                      'Industrial':['Industrial', 'Commercial - Industrial'],
                      'Mixed Use':['Mixed Use'],
                      'Other':['Tax Exempt', 'Tax Exempt - Charitable Organization or Religious',
                               'Tax Exempt - Government', 'Undevelopable', 'Vacant', 'Privilege Tax', 'Personal Property'],
                      'Residential':['Residential', 'Commercial - Apartment & Condo'],
                      'Unknown':[None, '', 'Unknown']}

    addPolyAttributes(sgid, agrcAddPts_morganCo, inputDict)
    addPolyAttributesLIR(sgid, agrcAddPts_morganCo, morgan_parcelsLIR, morgan_remapLIR)
    updateAddPtID(agrcAddPts_morganCo)
    addBaseAddress(agrcAddPts_morganCo)
    deleteDuplicatePts(agrcAddPts_morganCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_morganCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Morgan_ErrorPts.shp'), errorFlds, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_morganCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def piuteCounty():
    piuteCoAddPts = r'..\Piute\PiuteCounty.gdb\PiuteAddressPoints'
    agrcAddPts_piuteCo = r'..\Piute\Piute.gdb\AddressPoints_Piute'
    cntyFldr = r'..\Piute'

    # piuteCoAddFLDS = ['ADDRESS', 'PARCEL__', 'SHAPE@', 'OBJECTID']
    # piuteCoAddFLDS = ['HouseNumbe', 'Pre', 'Name', 'Type', 'Dir', 'Unit', 'ADDRESS', 'SHAPE@', 'OBJECTID',
    #                   'PARCEL__', 'COUNTY', 'AddSysName']
    piuteCoAddFLDS = ['AddNum', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 'UnitID', 'FullAdd',
                      'SHAPE@', 'OBJECTID', 'ParcelID', 'CountyID', 'AddSystem']

    old_point_count = int(arcpy.GetCount_management(agrcAddPts_piuteCo).getOutput(0))
    #archive_last_month(agrcAddPts_piuteCo)
    checkRequiredFields(piuteCoAddPts, piuteCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_piuteCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49031')

    unitList = [' A', ' B', ' C', ' D', ' E', ' 1', ' 2']
    hwy_exceptions = ['22', '25', '62', '153', '89']
    fix_name = {'DEER MILL':'DEER TRAIL MILL', 'DEER MINE':'DEER TRAIL MINE', 'HOOVER CIR':'HOOVER',
                'MARSCHALL':'MARSHALL','SR 22':'HWY 22', 'SR 25':'HWY 25', 'SR 62':'HWY 62',
                'SR 153':'HWY 153', 'US HWY 89':'HWY 89'}
    no_sType_rds = {'BEAVER':'BEAVER CREEK', 'ANDERSON':'ANDERSON HILL', 'GOLD DUST':'GOLD DUST TRAIL',
                    'HWY 89':'HWY 89', 'OLD HWY 89':'OLD HWY 89'}



    # with arcpy.da.SearchCursor(piuteCoAddPts, piuteCoAddFLDS) as scursor, \
    #     arcpy.da.InsertCursor(agrcAddPts_piuteCo, agrcAddFLDS) as icursor:
    #         for row in scursor:
    #             unitID = ''
    #             unitType = ''

    #             address = parse_address.parse(row[0])

    #             addNum = address.houseNumber
    #             preDir = removeNone(address.prefixDirection)
    #             sufDir = removeNone(address.suffixDirection)
    #             sType = removeNone(address.suffixType)

    #             sName = address.streetName
    #             if sName in fix_name:
    #                 sName = fix_name[sName]
    #             if sName in no_sType_rds:
    #                 sName = no_sType_rds[sName]
    #                 sType = ''

    #             if row[0].split()[-2] in ['STE', 'UNIT']:
    #                 unitType = row[0].split()[-2]
    #                 unitID = row[0].split()[-1]

    #             if row[0].endswith((' A', ' B', ' C', ' D', ' E', ' 1', ' 2')) and sName.isdigit() == False:
    #                 unitID = row[0][-1]

    #             if unitType == '' and unitID != '':
    #                 fulladd = f'{addNum} {preDir} {sName} {sufDir} {sType} # {unitID}'
    #             else:
    #                 fulladd = f'{addNum} {preDir} {sName} {sufDir} {sType} {unitType} {unitID}'

    #             fulladd = ' '.join(fulladd.split())

    #             parcel = row[1].strip()

    #             shp = row[2]

    #             if fulladd != row[0]:
    #                 print(f'{row[3]} {row[0]} - {fulladd}')

    #             icursor.insertRow(('', '', fulladd, addNum, '', preDir, sName, sType, sufDir,
    #                                '', '', unitType, unitID, '', '', '49031', 'UT', '', '', '', parcel,
    #                                'PIUTE COUNTY', today, 'COMPLETE', '', None, '', '', '', shp))
    with arcpy.da.SearchCursor(piuteCoAddPts, piuteCoAddFLDS) as scursor, \
    arcpy.da.InsertCursor(agrcAddPts_piuteCo, agrcAddFLDS) as icursor:
        for row in scursor:
            if row[0] != '' and row[10] != 'PIUTEGARF' and row[11] != 'GARFIELD CTY':
                addNum = row[0].strip(' NSEW')
                preDir = removeNone(row[1])
                sName = removeNone(row[2]).upper()
                sType = removeNone(row[3]).strip()
                sufDir = removeNone(row[4])
                unitID = removeNone(row[5]).strip()
                unitType = ''
                
                if sName.isdigit() == True:
                    sType = ''
                else:
                    sufDir = ''
                if sName in fix_name:
                    sName = fix_name[sName]

                if unitID != '':
                    fulladd = f'{addNum} {preDir} {sName} {sufDir} {sType} # {unitID}'
                else:
                    fulladd = f'{addNum} {preDir} {sName} {sufDir} {sType} {unitType} {unitID}'
                fulladd = ' '.join(fulladd.split())

                parcel = removeNone(row[9]).strip()
                shp = row[7]

                if fulladd != row[6]:
                    print(f'{row[8]} {row[6]} - {fulladd}')

                icursor.insertRow(('', '', fulladd, addNum, '', preDir, sName, sType, sufDir,
                                   '', '', unitType, unitID, '', '', '49031', 'UT', '', '', '', parcel,
                                   'PIUTE COUNTY', today, 'COMPLETE', '', None, '', '', '', shp))

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Piute_ErrorPts.shp', piuteCoAddFLDS[0],
                                   piuteCoAddPts)

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    piute_parcelsLIR = {'PtType': ['SGID.CADASTRE.Parcels_Washington_LIR', 'PROP_CLASS']}

    piute_remapLIR = {'Agricultural':['Agricultural', 'Greenbelt'],
                      'Commercial':['Commercial',  'Commercial - Office Space', 'Commercial - Retail'],
                      'Industrial':['Industrial', 'Commercial - Industrial'],
                      'Mixed Use':['Mixed Use'],
                      'Other':['Tax Exempt', 'Tax Exempt - Charitable Organization or Religious',
                               'Tax Exempt - Government', 'Undevelopable', 'Vacant', 'Privilege Tax', 'Personal Property'],
                      'Residential':['Residential', 'Commercial - Apartment & Condo'],
                      'Unknown':[None, '', 'Unknown']}

    addPolyAttributes(sgid, agrcAddPts_piuteCo, inputDict)
    addPolyAttributesLIR(sgid, agrcAddPts_piuteCo, piute_parcelsLIR, piute_remapLIR)
    updateAddPtID(agrcAddPts_piuteCo)
    addBaseAddress(agrcAddPts_piuteCo)
    deleteDuplicatePts(agrcAddPts_piuteCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_piuteCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Piute_ErrorPts.shp'), errorFlds, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_piuteCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def richCounty():

    richCoAddPts = r'..\Rich\RichCounty.gdb\AddressPoints'
    agrcAddPts_richCo = r'..\Rich\Rich.gdb\AddressPoints_Rich'
    cntyFldr = r'..\Rich'

    #richCoAddFLDS = ['House_Num', 'Prefix_Dir', 'St_Name', 'St_Dir', 'St_Type', 'Unit_Num', 'Modified', 'Parcel_ID', 'SHAPE@', 'OBJECTID_1']
    richCoAddFLDS = ['HouseNumbe', 'Pre', 'Name', 'Dir', 'Type', 'Unit', 'LastModifi', 'Parcel_ID', 'SHAPE@', 'OBJECTID_1']

    checkRequiredFields(richCoAddPts, richCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_richCo)

    errorPtsDict = {}

    hwyDict = {'HIGHWAY 16':'HWY 16', 'HIGHWAY 30':'HWY 30', 'HIGHWAY 89':'HWY 89', 'STATE ROUTE 30':'HWY 30'}
    fix_streets = {'150 SOUJTH':'150 SOUTH', 'ARROWLEAFF':'ARROWLEAF', 'CEMETARY':'CEMETERY', 'CRAWFORD VEIW':'CRAWFORD VIEW',
                   'MONTEISTO':'MONTE CRISTO', 'MOUNTIAN VIEW':'MOUNTAIN VIEW', 'CHOKE CHERRY':'CHOKECHERRY'}
    skipAdd = ['AR111']

    with arcpy.da.SearchCursor(richCoAddPts, richCoAddFLDS) as sCursor, \
        arcpy.da.InsertCursor(agrcAddPts_richCo, agrcAddFLDS) as iCursor:

        for row in sCursor:
            if row[0] not in errorList or row[1] not in errorList and row[2] not in errorList:
                addNum = row[0].strip()
                preDir = returnKey(row[1].upper(), dirs)
                sufDir = returnKey(row[3].upper(), dirs)

                sType = returnKey(row[4].upper(), sTypeDir)
                if row[4] == 'Wy':
                    sType = 'WAY'

                sName = row[2].upper().strip()
                if sName in fix_streets:
                    sName = fix_streets[sName]

                if sName[:2].isdigit() and sName.endswith((' NORTH', ' SOUTH', ' EAST', ' WEST', ' S', ' E', ' N', ' W')):

                    addressErrors = errorPtsDict.setdefault(f'{row[9]} | {sName}', [])
                    addressErrors.extend(['Direction in street name', row[8]])

                    sName = sName.split()[0]
                    sufDir = returnKey(row[2].split()[1].upper(), dirs)
                    sType = ''
                if sName in hwyDict:
                    sName = hwyDict[sName]
                    sType = ''

                if sName.isdigit() == False and sType != '':
                    sufDir = ''
                if sName.isdigit() == True and sType != '':
                    sType = ''

                if preDir == sufDir and sType == '':
                    addressErrors = errorPtsDict.setdefault(f'{sName} | {preDir} {sufDir}', [])
                    addressErrors.extend(['prefix = suffix direction', row[8]])
                    print (f'{row[9]} p = s no type')
                    continue
                if sName.isdigit() and preDir == '':
                    addressErrors = errorPtsDict.setdefault(f'{sName} | {preDir} {sufDir}', [])
                    addressErrors.extend(['prefix direction is missing', row[8]])
                    print (f'{row[9]} no p')
                    continue
                if sName in skipAdd:
                    continue

                unitId = removeBadValues(row[5], errorList)
                modified = row[6]
                loadDate = today
                parcelID = row[7]
                shp = row[8]


                if sName.isdigit() and sufDir == '':
                    addressErrors = errorPtsDict.setdefault(f'{row[9]} | {sName} no dir', [])
                    addressErrors.extend(['No suffix direction in Dir field', row[8]])
                if sName.isdigit() == False and sName.startswith('HWY ') == False and sType == '':
                    addressErrors = errorPtsDict.setdefault(f'{row[9]} | {sName} no type', [])
                    addressErrors.extend(['No street type', row[8]])


                if unitId != '':
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} # {unitId}'
                elif sType == 'HWY':
                    fullAdd = f'{addNum} {preDir} {sName} {sufDir}'
                else:
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir}'

                fullAdd = ' '.join(fullAdd.split())

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '', unitId, '', '', '49033', 'UT', \
                                   'Unknown', 'Unknown', 'Unknown', parcelID, 'RICH COUNTY', loadDate, 'COMPLETE', '', modified, '', '', '', shp))


    errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Rich_ErrorPts.shp', 'ADDRESS', richCoAddPts)
    
    remap_lir = {
        'Agricultural':['Agricultural Building', 'Agricultural Real Estate'],
        'Commercial':['Commercial Building', 'Commercial Real Estate', 'Commercial Real Estate FF'],
        'Residential':['Accessory Bldg.', 'Detached Garage', 'Residential Building', 'Residential Real Estate', 
                       'Residential Real Estate - FF', 'Secondary Building', 'Secondary House Trailer', 
                        'Secondary Real Estate', 'Secondary Real Estate - FF', 'Tennis Court'],
        'Other':['Exempt Real Estate', 'Green Belt Real Estate', 'Greenbelt Real Estate - FF', 
                 'Undeveloped Land', 'Undeveloped Land - FF', 'Utilities'],
        'Unknown': [None, '', ' ']
    }


    #     address point field name:[SGID FC, SGID field name, remap dictionary]

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
    'PtType':['SGID.CADASTRE.Parcels_Rich_LIR', 'PROP_CLASS', remap_lir]
    }

    addPolyAttributes(sgid, agrcAddPts_richCo, inputDict)
    updateAddPtID(agrcAddPts_richCo)
    addBaseAddress(agrcAddPts_richCo)
    deleteDuplicatePts(agrcAddPts_richCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_richCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Rich_ErrorPts.shp'), errorPts, dupePts)


def saltLakeCounty():

    slcoAddPts = r'..\SaltLake\SaltLakeCounty.gdb\ADDRESS_POINTS'
    agrcAddPts_SLCO = r'..\SaltLake\SaltLake.gdb\AddressPoints_SaltLake'
    cntyFldr = r'..\SaltLake'

    slcoAddFLDS = ['PARCEL', 'ADDRESS', 'UNIT_DESIG', 'IDENTIFY', 'BLDG_DESIG', 'ADDR_LABEL', 'DEVELOPMENT', 'BUSINESS_NAME',
                   'ADDR_TYPE', 'ADDR_PD', 'SHAPE@', 'ZIP_CODE', 'ADDR_HN', 'ADDR_SN', 'EXPORT', 'ADDR_PD', 'ADDR_SN',
                   'ADDR_ST', 'ADDR_SD', 'PRIMARY_ADDRESS', 'CORNER_ADDRESS', 'ADDR_CLASS', 'last_edited_date']
    
    checkRequiredFields(slcoAddPts, slcoAddFLDS)
    archive_last_month(agrcAddPts_SLCO)
    truncateOldCountyPts(agrcAddPts_SLCO)

    errorPtsDict = {}
    rdSet = createRoadSet('49035')

    fixDict = {'ANN DEL': 'ANN DELL', 'BIATHLON': 'BIATHALON', 'BROUGHTYFERRY': 'BROUGHTY FERRY', 'CENTRAL POINT': 'CENTRAL POINTE',
               'CHURCHILL': 'CHURCH HILL', 'COPPERCREEK': 'COPPER CREEK', 'COVEPOINT': 'COVE POINT', 'EASTCAPITOL': 'EAST CAPITOL',
               'EMERALDSPRING': 'EMERALD SPRING', 'FOURB': 'FOUR B', 'FOX BRIDGE': 'FOXBRIDGE', 'GLENOAKS': 'GLEN OAKS',
               'IEIGHTYEAST': 'I-80 EB', 'IEIGHTYEAST FWYNDE': 'MONTE GRANDE', 'MONTEHERMOSA': 'MONTE HERMOSA',
               'MOUNT LOGAN': 'MT LOGAN', 'MTN VIEW CORID': 'MOUNTAIN VIEW HWY', 'NORTHBONNEVILLE': 'NORTH BONNEVILLE',
               'NORTHBOROUGH': 'NORTH BOROUGH', 'NORTHFORK': 'NORTH FORK', 'NORTHHILLS': 'NORTH HILLS',
               'NORTHSANDRUN': 'NORTH SANDRUN', 'NORTHTEMPLE': 'NORTH TEMPLE', 'NORTHUNION': 'NORTH UNION',
               'NORTHWOODSIDE': 'NORTH WOODSIDE', 'PARK PLACEEAST': 'PARK', 'PARK PLACENORTH': 'PARK', 'PARK PLACESOUTH': 'PARK',
               'PARK PLACEWEST': 'PARK', 'PARKGREEN': 'PARK GREEN', 'PETTERSENBLUFF': 'PETTERSEN BLUFF',
               'PHEASANTRIDGE': 'PHEASANT RIDGE', 'PINNACLETERRACE': 'PINNACLE TERRACE', 'POINT RIDGE': 'POINTE RIDGE',
               'POULOS PLACE': 'POULOS', 'PUTTER': 'PUTTERS', 'ROPEKEY': 'ROPE KEY', 'SECRET': 'CECRET', 'SEGOLILY': 'SEGO LILY',
               'SILT STONE': 'SILTSTONE', 'SOUTHCAMPUS': 'SOUTH CAMPUS', 'SOUTHCREST': 'SOUTH CREST', 'SOUTHJORDAN': 'SOUTH JORDAN',
               'SOUTHJRDN': 'SOUTH JORDAN', 'SOUTHMEADOW': 'SOUTH MEADOW', 'SOUTHPOINTE': 'SOUTH POINTE',
               'SOUTHSAMUEL': 'SOUTH SAMUEL', 'SOUTHSANDRUN': 'SOUTH SANDRUN', 'SOUTHTEMPLE': 'SOUTH TEMPLE',
               'SOUTHUNION': 'SOUTH UNION', 'SOUTHWILLOW': 'SOUTH WILLOW', 'SOUTHWOODSIDE': 'SOUTH WOODSIDE',
               'ST MORITZ': 'SAINT MORITZ', 'STELLER JAY': 'STELLAR JAY', 'SUNRISEPLACE EAST': 'SUNRISE',
               'SUNRISEPLACE NORTH': 'SUNRISE', 'SUNRISEPLACE SOUTH': 'SUNRISE', 'SUNRISEPLACE WEST': 'SUNRISE',
               'SWEET BASIL N': 'SWEET BASIL NORTH', 'SWEET BASIL S': 'SWEET BASIL SOUTH', 'THREE FTNS': 'THREE FOUNTAINS',
               'U-201 EB': 'HWY 201 EB', 'U-201 WB': 'HWY 201 WB', 'U-202': 'HWY 202', 'UEIGHTYFIVE NB': 'HWY 85 NB',
               'UEIGHTYFIVE SB': 'HWY 85 SB', 'UONE ELEVEN': 'HWY 111', 'USIXTY FIVE': 'HWY 65', 'UTWO O ONE': 'HWY 201',
               'UTWO O ONE HWY': 'HWY 201', 'VALDOWN': 'VAL DOWN', 'WELL SPRING': 'WELLSPRING', 'WESTCAPITOL': 'WEST CAPITOL',
               'WESTLILAC': 'WEST LILAC', 'WESTTEMPLE': 'WEST TEMPLE', 'WHITECHERRY': 'WHITE CHERRY', 'WILLOW BANK': 'WILLOWBANK',
               'WOLF GROVE': 'WOLFE GROVE'}

    typeNames = ['APPLE HILL', 'BALDWIN PARK', 'BELL RIDGE', 'BEN DAVIS PARK', 'DAWN HILL', 'GRAVENSTEIN PARK', 'HICKORY HILL', \
                 'HOLLYHOCK HILL', 'PEPPERWOOD POINTE', 'ROME BEAUTY PARK', 'SOLITUDE RIDGE', 'STRAWBERRY LOOP', \
                 'WASHINGTON LOOP']

    sufNames = {'6100 SOUTH', '6160 SOUTH'}

    aveDict = {'FIRST':'1ST', 'SECOND':'2ND', 'THIRD':'3RD', 'FOURTH':'4TH', 'FIFTH':'5TH', 'SIXTH':'6TH', \
               'SEVENTH':'7TH', 'EIGHTH':'8TH', 'NINTH':'9TH', 'TENTH':'10TH', 'ELEVENTH':'11TH', 'TWELFTH':'12TH', 'THIRTEENTH':'13TH', \
               'FOURTEENTH':'14TH', 'FIFTEENTH':'15TH', 'SIXTEENTH':'16TH', 'SEVENTEENTH':'17TH', 'EIGHTEENTH':'18TH'}

    ptTypeDic = {
        'Other' : ['CEMETERY', 'CHURCH', 'CIVIC', 'COORDINATE', 'FIRE STATION', 'GOLF COURSE', 'HOSPITAL',
                   'JAIL', 'LIBRARY', 'MAILBOX', 'PARK', 'OPEN SPACE', 'PARKING', 'POLICE', 'POOL', 'POST OFFICE',
                   'PRISON', 'SCHOOL', 'SLCC', 'TEMPLE', 'TRAX', 'U CAMPUS', 'WESTMINSTER', 'ZOO', 'OTHER'],
        'Residential' : ['RES', 'RESIDENTIAL', 'APT', 'CONDO', 'CONDO APT', 'HOA', 'MOBILEHOME', 'MULTI', 'PUD', 'TOWNHOME'],
        'Commercial' : ['AIRPORT', 'BUS CONDO', 'BUS PUD', 'BUSINESS', 'COMMERCIAL', 'MORTUARY'],
        'Industrial' : ['UTILITY']
    }

    unitDict = {'APARTMENT':'APT', 'MOBILEHOME':'TRLR'}

    class strip_street_type:
        def __init__(self, words):
            self.name = ' '.join(words.split()[:-1])
            directions = ['N', 'S', 'E', 'W', 'NORTH', 'SOUTH', 'EAST', 'WEST']
            if words.split()[:-1] in directions:
                self.direction = ''
            self.type = words.split()[-1]
    def fix_road_name(road_name):
        return strip_street_type(road_name)

    with arcpy.da.SearchCursor(slcoAddPts, slcoAddFLDS) as sCursor_slco, \
        arcpy.da.InsertCursor(agrcAddPts_SLCO, agrcAddFLDS) as iCursor:
        for row in sCursor_slco:
            if row[14] == 1 and row[12] not in errorList and row[16] not in errorList:

                if row[20] != '' and row[1] != row[20] and row[19] == 0:
                    continue

                if '-' in row[12]:
                    continue

                addNum = row[12]

                if '/' in row[1]:
                    addNumSuf = row[1].split('/')
                    addNumSuf = f'{addNumSuf[0][-1]}/{addNumSuf[1][0]}'
                    addNum = addNum.replace(f'-{addNumSuf}', '')
                else:
                    addNumSuf = ''
                preDir = returnKey(row[15], dirs)

                streetType = returnKey(row[17], sTypeDir)
                if row[17] == 'WY':
                    streetType = 'WAY'
                if row[17] == 'CNTR':
                    streetType = 'CTR'
                sufDir = returnKey(row[18], dirs)

                zip = row[11]

                streetName = row[16]
                if streetName in fixDict:
                    streetName = fixDict[streetName]
                if streetName in aveDict and zip in ['84103', '84047', '84111']:
                    streetName = aveDict[streetName]

                if streetName.startswith('HWY '):
                    streetType = ''
                if streetName == 'MOUNTAIN VIEW HWY':
                    streetType = ''

                if streetType == '' and row[17] in dirs:
                    sufDir = row[17]
                if sufDir == '' and row[18] in sTypeDir:
                    streetType = row[18]

                if row[13] in fixDict and streetName == 'PARK':
                    streetType = 'PL'
                    sufDir = returnKey(row[13][10:], dirs)
                if row[13] in fixDict and streetName == 'SUNRISE':
                    streetType = 'PL'
                    sufDir = returnKey(row[13][13:], dirs)
                if row[13] in fixDict and streetName == 'SWEET BASIL':
                    sufDir = returnKey(row[13][12:], dirs)

                if streetName in typeNames:
                    fixName = fix_road_name(streetName)
                    streetName = fixName.name
                    print(streetName)
                    streetType = returnKey(fixName.type, sTypeDir)
                    print(streetType)

                if streetName in sufNames:
                    sufDir = streetName.split()[1][0]
                    streetName = streetName.split()[0]
                    streetType = ''


        #-------Error Points---------------
                if row[9] == row[18] and row[9] != '':
                    addressErrors = errorPtsDict.setdefault(row[1], [])
                    addressErrors.extend(['predir = sufdir', row[10]])
                if row[13] not in row[1]:
                    addressErrors = errorPtsDict.setdefault(f'{row[13]} | {row[3]}', [])
                    addressErrors.extend(['Mixed street names', row[10]])
                if row[17] not in sTypeList and row[17] not in errorList and row[17] != 'WY' and row[17] != 'CNTR':
                    addressErrors = errorPtsDict.setdefault(f'{row[17]} | {row[3]}', [])
                    addressErrors.extend(['bad street type', row[10]])
        #-----------------------------------------------------------------------

                if preDir == sufDir:
                    continue

                #unitId = removeBadValues(row[2], errorList)
                unitId = ''
                if '#' in removeBadValues(row[3], errorList):
                    unitId = row[3].split('#')[1].strip()
                if unitId == '' and row[2] not in errorList:
                    unitId = row[2]

                unitType = ''
                if row[21] in unitDict and unitId != '':
                    unitType = unitDict[row[21]]

                if unitType != '' and unitId != '':
                    fulladd = f'{addNum} {addNumSuf} {preDir} {streetName} {sufDir} {streetType} {unitType} {unitId}'
                elif unitId != '':
                    fulladd = f'{addNum} {addNumSuf} {preDir} {streetName} {sufDir} {streetType} # {unitId}'
                elif row[13] in fixDict and streetName == 'PARK':
                    fulladd = f'{addNum} {addNumSuf} {preDir} {streetName} {streetType} {sufDir} {unitId}'
                elif row[13] in fixDict and streetName == 'SUNRISE':
                    fulladd = f'{addNum} {addNumSuf} {preDir} {streetName} {streetType} {sufDir} {unitId}'
                elif streetName.startswith('HWY '):
                    fulladd = f'{addNum} {addNumSuf} {preDir} {streetName}'
                else:
                    fulladd = f'{addNum} {addNumSuf} {preDir} {streetName} {sufDir} {streetType}'

                fulladd = ' '.join(fulladd.split())

                if fulladd in ['1379 E 9090 S', '1381 E 9090 S']:
                    zip = '84093'
                if zip == None and streetName in ['GLACIAL PEAK', 'RAVINE ROCK', 'SNOWY PEAK', 'SNOW CAP']:
                    zip = '84020'

                #-------------Error Points Part II----------------
                if streetName not in fixDict and 'HWY' not in streetName and streetName not in rdSet:
                    addressErrors = errorPtsDict.setdefault(f'{streetName} | {fulladd}', [])
                    addressErrors.extend(['add pts street name not found in roads', row[10]])
                #--------------------------------------------------

                ptType = returnKey(row[8], ptTypeDic)

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
                editor = '' #row[9]
                modified = row[22]
                shp = row[10]

                iCursor.insertRow((addSys, utAddId, fulladd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                                   unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                                   status, editor, modified, '', '', '', shp))

            if row[13] == 'MILLCREEK CANYON' and row[14] == 0 and row[8] in ['RESIDENTIAL']:
                addNum = row[12]
                preDir = returnKey(row[15], dirs)
                streetName = row[16]
                streetType = returnKey(row[17], sTypeDir)

                unitId = ''
                if '#' in removeBadValues(row[3], errorList):
                    unitId = row[3].split('#')[1].strip()

                if unitId != '':
                    fulladd = f'{addNum} {preDir} {streetName} {streetType} # {unitId}'
                else:
                    fulladd = f'{addNum} {preDir} {streetName} {streetType}'

                fulladd = ' '.join(fulladd.split())

                landmark = removeBadValues(row[7], errorList)
                ptType = returnKey(row[8], ptTypeDic)
                addSys = ''
                utAddId = ''
                zip = row[11]
                city = ''
                fips = '49035'
                state = 'UT'
                ptLocation = 'Unknown'
                structure = 'Unknown'
                parcel = row[0]
                addSource = 'SALT LAKE COUNTY'
                loadDate = today
                status = 'COMPLETE'
                editor = '' #row[9]
                modified = None #row[9]
                shp = row[10]

                iCursor.insertRow((addSys, utAddId, fulladd, addNum, '', preDir, streetName, streetType, '', landmark, '', \
                                   '', unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                                   status, editor, modified, '', '', '', shp))

    errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'SaltLake_ErrorPts.shp', 'ADDRESS', slcoAddPts)


    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    sl_parcelsLIR = {'PtType':['SGID.CADASTRE.Parcels_SaltLake_LIR', 'PROP_CLASS']}

    sl_remapLIR = {'Agricultural':['Agricultural', 'Greenbelt'],
                   'Commercial':['Commercial',  'Commercial - Office Space', 'Commercial - Retail'],
                   'Industrial':['Industrial', 'Commercial - Industrial'],
                   'Mixed Use':['Mixed Use'],
                   'Other':['Tax Exempt', 'Tax Exempt - Charitable Organization or Religious', 
                            'Tax Exempt - Government', 'Undevelopable', 'Vacant', 'Privilege Tax', 'Personal Property'],
                   'Residential':['Residential', 'Commercial - Apartment & Condo'],
                   'Unknown':[None, '', 'Unknown']}

    addPolyAttributes(sgid, agrcAddPts_SLCO, inputDict)
    updateAddPtID(agrcAddPts_SLCO)
    #ptTypeUpdates_SaltLake(sgid, agrcAddPts_SLCO, slco_lirDict, lir_codes)      #Use for census group quarters
    addPolyAttributesLIR(sgid, agrcAddPts_SLCO, sl_parcelsLIR, sl_remapLIR)
    addBaseAddress(agrcAddPts_SLCO)
    deleteDuplicatePts(agrcAddPts_SLCO, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    #sweep(agrcAddPts_SLCO)
    dupePts = returnDuplicateAddresses(agrcAddPts_SLCO, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'SaltLake_ErrorPts.shp'), errorFlds, dupePts)


def SanJuanCounty():
    sde_file = Path(__file__).resolve().parents[3].joinpath('sde', 'AddressAdmin@AddressPointEditing@agrc.utah.gov.sde')
    sanjuanCoAddPts = str(Path.joinpath(sde_file, 'AddressPointEditing.ADDRESSADMIN.AddressPoints'))
    agrcAddPts_sanjuanCo = r'..\SanJuan\SanJuan.gdb\AddressPoints_SanJuan'

    cntyFldr = r'..\SanJuan'

    truncateOldCountyPts(agrcAddPts_sanjuanCo)

    errorPtsDict = {}

    sanjuan_fields = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', \
                      'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State', \
                      'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'LoadDate', 'Status', 'Editor', \
                      'ModifyDate', 'StreetAlias', 'Notes', 'SHAPE@']

    fix_hwy = {'HIGHWAY 191':'HWY 191', 'HIGHWAY 46':'HWY 46', 'HIGHWAY 491':'HWY 191', 'SR 211':'HWY 211',
               'SR 46':'HWY 46', 'SR 95':'HWY 95', 'US 191':'HWY 191'}

    sql = f'"CountyID" = \'49037\''
    with arcpy.da.SearchCursor(sanjuanCoAddPts, sanjuan_fields, sql) as scursor,\
        arcpy.da.InsertCursor(agrcAddPts_sanjuanCo, agrcAddFLDS) as icursor:
        for row in scursor:
            if row[3] not in errorList:
                add_num = row[3]
                add_num_suf = removeNone(row[4])
                pre_dir = row[5]
                street_name = row[6].upper()
                street_type = removeNone(row[7])

                if street_name in fix_hwy:
                    street_name = fix_hwy[street_name]
                    street_type = ''

                suf_dir = removeNone(row[8])
                unit_type = removeNone(row[11]).replace(' ', '')
                unit_id = removeNone(row[12]).strip()
                pt_location = removeNone(row[17])
                pt_type = removeNone(row[18])
                structure = removeNone(row[19])
                parcel_id = removeNone(row[20])
                pts_source = removeNone(row[21]).upper()
                load_date = today
                mod_date = row[25]
                shp = row[28]

                if unit_type != '':
                    full_address = f'{add_num} {add_num_suf} {pre_dir} {street_name} {street_type} {suf_dir} {unit_type} {unit_id}'
                elif unit_id != '':
                    full_address = f'{add_num} {add_num_suf} {pre_dir} {street_name} {street_type} {suf_dir} # {unit_id}'
                else:
                    full_address = f'{add_num} {add_num_suf} {pre_dir} {street_name} {street_type} {suf_dir}'

                full_address = ' '.join(full_address.split())

                icursor.insertRow(('', '', full_address, add_num, add_num_suf, pre_dir, street_name, street_type, suf_dir,
                                   '', '', unit_type, unit_id, '', '', '49037', 'UT', pt_location, pt_type, structure, parcel_id,
                                   pts_source, load_date, 'COMPLETE', '', mod_date, '', '', '', shp))
                
        errorPts = createErrorPts(errorPtsDict, cntyFldr, 'SanJuan_ErrorPts.shp', 'ADDRESS', agrcAddPts_sanjuanCo)

    inputDict = {
        'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
        'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
        'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
        'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
        'ParcelID':['SGID.CADASTRE.Parcels_SanJuan', 'PARCEL_ID', '']
        }

    addPolyAttributes(sgid, agrcAddPts_sanjuanCo, inputDict)
    updateAddPtID(agrcAddPts_sanjuanCo)
    addBaseAddress(agrcAddPts_sanjuanCo)
    dupePts = returnDuplicateAddresses(agrcAddPts_sanjuanCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'SanJuan_ErrorPts.shp'), errorPts, dupePts)
    deleteDuplicatePts(agrcAddPts_sanjuanCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def sanpeteCounty():
    sanpeteCoAddPts = r'..\Sanpete\SanpeteCounty.gdb\SanpeteAddressPts_07212021'
    agrcAddPts_sanpeteCo = r'..\Sanpete\Sanpete.gdb\AddressPoints_Sanpete'

    sanpete_fields = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', \
                      'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State', \
                      'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'LoadDate', 'Status', 'Editor', \
                      'ModifyDate', 'StreetAlias', 'Notes', 'SHAPE@']

    truncateOldCountyPts(agrcAddPts_sanpeteCo)

    with arcpy.da.SearchCursor(sanpeteCoAddPts, sanpete_fields) as scursor, \
        arcpy.da.InsertCursor(agrcAddPts_sanpeteCo, agrcAddFLDS) as icursor:
        for row in scursor:
            if row[3] not in errorList and row[6] not in errorList:
                add_num = row[3]
                pre_dir = returnKey(row[5], dirs)
                street_name = row[6].upper()
                street_type = removeNone(returnKey(row[7], sTypeDir)).upper()
                suf_dir = returnKey(row[8], dirs)

                if street_name.isdigit() == True:
                    street_type = ''
                else:
                    suf_dir = ''

                if street_name.startswith('HIGHWAY') or street_name.startswith('HWY'):
                    street_name = street_name.replace('HIGHWAY', 'HWY')
                    street_type = ''
                
                landmark = removeNone(row[9]).upper()
                building = removeNone(row[10]).upper()
                unit_type = returnKey(removeNone(row[11]), unitTypeDir)
                unit_id = removeNone(row[12]).upper()

                if unit_type == '' and unit_id != '':
                    full_address = f'{add_num} {pre_dir} {street_name} {suf_dir} {street_type} # {unit_id}'
                else:
                    full_address = f'{add_num} {pre_dir} {street_name} {suf_dir} {street_type} {unit_type} {unit_id}'

                full_address = ' '.join(full_address.split())

                pt_location = removeNone(row[17])
                pt_type = removeNone(row[18])
                structure = removeNone(row[19])
                parcel = removeNone(row[20])
                load_date = today
                status = 'COMPLETE'
                editor = row[24]
                mod_date = row[25]
                alias = removeNone(row[26]).upper()
                notes = row[26]
                shp = row[28]

                icursor.insertRow(('', '', full_address, add_num, '', pre_dir, street_name, street_type, suf_dir, landmark, building, \
                                   unit_type, unit_id, '', '', '49039', 'UT', pt_location, pt_type, structure, parcel, \
                                   'SANPETE COUNTY', load_date, status, editor, mod_date, alias, notes, '', shp))

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_sanpeteCo, inputDict)
    updateAddPtID(agrcAddPts_sanpeteCo)
    addBaseAddress(agrcAddPts_sanpeteCo)
    deleteDuplicatePts(agrcAddPts_sanpeteCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def sevierCounty():
    sevierCoAddPts = r'..\Sevier\SevierCounty.gdb\SC911AddressPts'
    agrcAddPts_sevierCo = r'..\Sevier\Sevier.gdb\AddressPoints_Sevier'

    sevierCoAddFLDS = ['NUMBER', 'Pre', 'Name', 'Dir', 'Type', 'Unit', 'PARCEL__', 'SHAPE@', 'ADDRESS']

    cntyFldr = r'..\Sevier'

    errorPtsDict = {}

    checkRequiredFields(sevierCoAddPts, sevierCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_sevierCo).getOutput(0))
    archive_last_month(agrcAddPts_sevierCo)
    truncateOldCountyPts(agrcAddPts_sevierCo)

    hwyDict = {'SR 118':'HWY 118', 'SR 119':'HWY 119', 'SR 24':'HWY 24', 'SR 25':'HWY 25', 'SR 256':'HWY 256',
               'SR 258':'HWY 258', 'SR 260':'HWY 260', 'SR 50':'HWY 50', 'SR 62':'HWY 62', 'SR 72':'HWY 72',
               'SR 76':'HWY 76', 'US HWY 89':'HWY 89'}
    
    rds_with_types = ['ASPEN TERRACE RD', 'VACA LN', 'DRY CREEK RD']

    with arcpy.da.SearchCursor(sevierCoAddPts, sevierCoAddFLDS) as sCursor, \
        arcpy.da.InsertCursor(agrcAddPts_sevierCo, agrcAddFLDS) as iCursor:
        for row in sCursor:
            #if row[2] not in errorList:
            addNum = row[0]
            preDir = returnKey(row[1], dirs)
            sName = row[2].strip(' ?')
            sufDir = returnKey(row[3], dirs)
            sType = returnKey(row[4], sTypeDir)

            if sName == '' and row[8] != '':
                address = parse_address.parse(row[8])
                addNum = address.houseNumber
                sName = address.streetName
                preDir = address.prefixDirection
                sType = removeNone(address.suffixType)
                sufDir = removeNone(address.suffixDirection)

            if sName.isdigit() == False:
                sufDir = ''
            if sType != '':
                sufDir = ''
            if sName[0].isdigit() == True and sName.endswith((' N', ' S', ' E', ' W')):
                sufDir = sName[-1]
                sName = sName[:-2]
            if sName in hwyDict:
                sName = hwyDict[sName]

            if sName in rds_with_types:
                sName = sName.rsplit(' ', 1)[0]

            unitsRaw = row[5].strip()
            unitTuple = splitVals(unitsRaw, unitTypeList)
            unitType, unitID = unitTuple
            unitType = returnKey(unitType, unitTypeDir)

            if unitType == '' and unitID != '':
                fullAdd = f'{addNum} {preDir} {sName} {sufDir} {sType} # {unitID}'
            else:
                fullAdd = f'{addNum} {preDir} {sName} {sufDir} {sType} {unitType} {unitID}'

            fullAdd = ' '.join(fullAdd.split())

            loadDate = today
            parcel = row[6]
            shp = row[7]

            iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', \
                                unitType, unitID, '', '', '49041', 'UT', '', '', '', parcel, \
                                'SEVIER COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))

    errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Sevier_ErrorPts.shp', sevierCoAddFLDS[1], sevierCoAddPts)

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
    'CountyID': ['SGID.BOUNDARIES.Counties', 'FIPS_STR', '']
    }

    addPolyAttributes(sgid, agrcAddPts_sevierCo, inputDict)
    updateAddPtID(agrcAddPts_sevierCo)
    addBaseAddress(agrcAddPts_sevierCo)
    deleteDuplicatePts(agrcAddPts_sevierCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_sevierCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Sevier_ErrorPts.shp'), errorPts, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_sevierCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def summitCounty():
    #summit_agol_pts = 'https://services2.arcgis.com/gyfpgFh2Wj2gglYD/ArcGIS/rest/services/Address_Points/FeatureServer/0'
    #summit_agol_pts = 'https://services2.arcgis.com/gyfpgFh2Wj2gglYD/ArcGIS/rest/services/AddressPoints_24_12/FeatureServer/0'
    summitCoAddPts = r'..\Summit\SummitCounty.gdb\AddressPoints'
    #summitCoAddPts = r'..\Summit\SummitCounty.gdb\Summit_agol_pts'
    #agrcAddPts_PC = r'..\Summit\Summit.gdb\AddressPoints_ParkCity'

    agrcAddPts_summitCo = r'..\Summit\Summit.gdb\AddressPoints_Summit'

    #agol_to_fgdb('Summit', summit_agol_pts)

    cntyFldr = r'..\Summit'

    errorPtsDict = {}
    rdSet = createRoadSet('49043')

    summitCoAddFLDS = ['ADDRNUM', 'APARTMENT', 'ROADPREDIR', 'ROADNAME', 'ROADTYPE', 'ROADPOSTDIR',
                       'FULLADDR', 'PLACENAME', 'POINTTYPE', 'LASTUPDATE', 'USNGCOORD', 'SHAPE@',
                       'STATUS', 'ADDRNUMSUF']
    # summitCoAddFLDS = ['addrnum', 'addrnumsuf', 'unittype', 'unitid', 'fullname', 'fulladdr', 'SHAPE@']

    checkRequiredFields(summitCoAddPts, summitCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_summitCo).getOutput(0))
    archive_last_month(agrcAddPts_summitCo)
    truncateOldCountyPts(agrcAddPts_summitCo)

    fix_sName = {'CLAIMJUMPER': 'CLAIM JUMPER', 'DEAR VALLEY':'DEER VALLEY', 'DEER VALL': 'DEER VALLEY',
                 'DEER VALL DR': 'DEER VALLEY', 'DEER VALLY': 'DEER VALLEY', 'DEER VALEY': 'DEER VALLEY',
                 'DEER VALLEY DR':'DEER VALLEY', 'EQUESTRAIN': 'EQUESTRIAN',
                 'FAIRWAY VILLIAGE': 'FAIRWAY VILLAGE', 'FENSHURCH': 'FENCHURCH', 'FOXGLEN': 'FOX GLEN',
                 'IRONHORSE': 'IRON HORSE', 'LOWER IRONHORSE LOOP':'LOWER IRON HORSE LOOP',
                 'PADDINTON': 'PADDINGTON', 'PERSERVERANCE': 'PERSEVERANCE', 'PROSPECTOR AVEUNE':'PROSPECTOR',
                 'PROSPECTOR AVENEUE':'PROSPECTOR', 'ROYAL ST': 'ROYAL', 'SADDLEVIEW':'SADDLE VIEW',
                 'SPY GLASS': 'SPYGLASS', 'SR 224': 'HWY 224', 'SR224':'HWY 224', 'SR 248':'HWY 248',
                 'SR 302': 'HWY 302', 'SR 32': 'HWY 32', 'SR 35': 'HWY 35', 'APRIL MOUNTIAN':'APRIL MOUNTAIN'}

    fix_sType = {'AVEUNE':'AVE', 'AVENEUE':'AVE', 'DRIE':'DR', 'Spur':'SPUR', 'Trn':'LN'}
    
    parse_crasher = ['OLD SMITH AND MOREHOUSE RD', 'SMITH AND MOREHOUSE RD']

    # with arcpy.da.SearchCursor(summitCoAddPts, summitCoAddFLDS) as scursor_summit, \
    # arcpy.da.InsertCursor(agrcAddPts_summitCo, agrcAddFLDS) as icursor:
    #     for row in scursor_summit:

    #         if row[0] in errorList or row[4] in errorList or row[5].startswith('?'):
    #             continue

    #         else:
    #             if row[4].upper() in parse_crasher:
    #                 add_num = row[0]
    #                 add_num_suf = ''
    #                 pre_dir = ''
    #                 street_name = row[4].rsplit(' ', 1)[0].upper()
    #                 street_type = row[4].split()[-1].upper()
    #                 suf_dir = ''
    #                 unit_id = ''
    #             else:
    #                 fulladdr = Address(row[5].upper())
    #                 add_num = fulladdr.address_number
    #                 add_num_suf = removeNone(row[1])
    #                 pre_dir = removeNone(fulladdr.prefix_direction)
    #                 street_name = fulladdr.street_name
    #                 street_type = removeNone(fulladdr.street_type)
    #                 suf_dir = removeNone(fulladdr.street_direction)
    #                 unit_id = removeNone(row[3]).strip('#')

    #             if unit_id != '':
    #                 full_address = f'{add_num} {add_num_suf} {pre_dir} {street_name} {street_type} {suf_dir} #{unit_id}'
    #             else:
    #                 full_address = f'{add_num} {add_num_suf} {pre_dir} {street_name} {street_type} {suf_dir}'
    #             full_address = ' '.join(full_address.split())

    #             if full_address != row[5].upper():
    #                 print(f'{full_address}  -  {row[5].upper()}')


                
            # if ['A', 'B', 'C', 'D'] in row[0]:
            #     add_num = row[0].strip(row[1])
            # elif '1/2' in row[0]:
            #     add_num = row[0].split()[0]
            # else:
            #     add_num = row[0].strip()

            # if row[4].startswith(('N ', 'S ', 'E ', 'W ')):
            #     pre_dir = row[4].split()[0]

            # if row[4].endsswith((' N', ' S', ' E', ' W')):
            #     suf_dir = row[4].split()[-1]

    with arcpy.da.SearchCursor(summitCoAddPts, summitCoAddFLDS) as sCursor_summit, \
            arcpy.da.InsertCursor(agrcAddPts_summitCo, agrcAddFLDS) as iCursor:
        for row in sCursor_summit:

            if row[0] in errorList or row[3] in errorList or row[12] == 'Retired':
                continue

            addNum = row[0].strip()
            addNumSuf = removeBadValues(row[13], errorList)
            # if addNumSuf != '':
            #     addNum = addNum.replace(addNumSuf, '').strip()
            preDir = checkWord(row[2], dirs)
            sName = removeBadValues(row[3], errorList).upper()
            #sType = removeBadValues(row[5], sTypeDir).upper()
            if row[4] in fix_sType:
                sType = fix_sType[row[4]]
            else:
                sType = returnKey(row[4], sTypeDir)
            
            sufDir = returnKey(row[5], dirs)

            if sName.isdigit() == False:
                if sType != '' and sufDir != '':
                    sufDir = ''

            if sName == 'DEER VALLEY':
                sufDir = removeNone(row[5]).strip()
            
            if sName in fix_sName:
                sName = fix_sName[sName]
            if sufDir == None:
                sufDir = ''
            if sName == 'ECHO' and sType == '':
                sType = 'SPUR'
            if sName == 'SILVER CLOUD' and sType == '':
                sType = 'DR'
            if sName == '500 W':
                sName = '500'
                sufDir = 'W'

            unitNum = removeNone(row[1]).strip('#').strip()

            if sName.isdigit() == True:
                if unitNum != '':
                    fullAdd = f'{addNum} {preDir} {sName} {sufDir} # {unitNum}'
                else:
                    fullAdd = f'{addNum} {preDir} {sName} {sufDir}'
            else:
                if unitNum != '':
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} # {unitNum}'
                else:
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir}'
                    
            fullAdd = ' '.join(fullAdd.split())

            if row[8] == 'Condo or Unit':
                ptType = 'Residential'
            elif row[8] == 'Office or Suite':
                ptType = 'Commercial'
            else:
                ptType = 'Other'

            building = removeBadValues(row[8], errorList)
            modified = row[9]
            loadDate = today
            shp = row[11]

            # -------Error Points---------------
            if preDir == sufDir and sType == '' and preDir != '':
                addressErrors = errorPtsDict.setdefault(row[6], [])
                addressErrors.extend(['predir = sufdir', row[11]])
            if sName not in rdSet and removeNone(row[3]).startswith('SR') == False:
                addressErrors = errorPtsDict.setdefault(row[3], [])
                addressErrors.extend(['Street name not found in roads', row[11]])
            # ------------------------------------

            iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', building, \
                              '', unitNum, '', '', '49043', 'UT', '', ptType, '', '', 'SUMMIT COUNTY', \
                               loadDate, 'COMPLETE', '', modified, '', '', '', shp))

        errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Summit_ErrorPts.shp', 'ADDRESS', summitCoAddPts)

    del iCursor

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG': ['SGID.INDICES.NationalGrid', 'USNG', ''],
    'ParcelID':['SGID.CADASTRE.Parcels_Summit', 'PARCEL_ID', '']
    }

    addPolyAttributes(sgid, agrcAddPts_summitCo, inputDict)
    updateAddPtID(agrcAddPts_summitCo)
    addBaseAddress(agrcAddPts_summitCo)
    deleteDuplicatePts(agrcAddPts_summitCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_summitCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Summit_ErrorPts.shp'), errorPts, dupePts)

    sql = f'"City" = \'PARK CITY (WASATCH CO)\''
    delete_by_query(agrcAddPts_summitCo, sql) #delete PC points in Wasatch County

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_summitCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


    
    # updateErrorPts(os.path.join(cntyFldr, 'Summit_ErrorPts.shp'), errorPts, dupePts)

    # def ParkCity():
    #     PCandCounty_points = r'..\Summit\SummitCounty.gdb\SummitCoAddrs'
    #     agrcAddPts_PC = r'..\Summit\Summit.gdb\AddressPoints_ParkCity'

    #     truncateOldCountyPts(agrcAddPts_PC)

    #     PCandCounty_FLDS = ['ADDR_HN', 'ADDR_PD', 'ADDR_PT', 'ADDR_SN', 'ADDR_ST', 'ADDR_SD', 'SERIAL', 'CITY', 'Unit', \
    #                         'SHAPE@', 'ZIP', 'CODE']

    #     fix_sName = {'CLAIMJUMPER': 'CLAIM JUMPER', 'DEER VALL': 'DEER VALLEY', 'DEER VALL DR': 'DEER VALLEY',
    #                  'DEER VALLY': 'DEER VALLEY', 'DEER VALEY': 'DEER VALLEY', 'EQUESTRAIN': 'EQUESTRIAN',
    #                  'FAIRWAY VILLIAGE': 'FAIRWAY VILLAGE', 'FENSHURCH': 'FENCHURCH', 'FOXGLEN': 'FOX GLEN',
    #                  'IRONHORSE': 'IRON HORSE', 'PADDINTON': 'PADDINGTON', 'PERSERVERANCE': 'PERSEVERANCE',
    #                  'ROYAL ST': 'ROYAL', 'SADDLEVIEW': 'SADDLE VIEW', 'SPY GLASS': 'SPYGLASS', 'SR 224': 'HWY 224',
    #                  'SR 248': 'HWY 248', 'SR 302': 'HWY 302', 'SR 32': 'HWY 32', 'SR 35': 'HWY 35'}

    #     pcDict = {
    #         'SERIAL': ['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    #         'CITY': ['SGID.BOUNDARIES.Municipalities', 'NAME'],
    #         'ZIP': ['SGID.BOUNDARIES.ZipCodes', 'ZIP5'],
    #         'CODE': ['SGID.INDICES.NationalGrid', 'USNG']
    #     }

    #     addPolyAttributes(sgid, PCandCounty_points, pcDict)
    #     print('updated Park City polygon attributes')

    #     hwyList = ['STATE ROAD', 'STATE RD', 'STATE HWY', 'STATE  RD', 'STATE   RD', 'STATE   HWY', 'SR', 'HWY',
    #                'HIGHWAY']

    #     badRow = ['', ' ', None]

    #     with arcpy.da.SearchCursor(PCandCounty_points, PCandCounty_FLDS) as sCursor, \
    #         arcpy.da.InsertCursor(agrcAddPts_PC, agrcAddFLDS) as iCursor:
    #         for row in sCursor:
    #             if row[7] == 'Park City' and row[0] not in badRow:
    #                 addNum = row[0]
    #                 if row[2] not in hwyList:
    #                     pre_street = ' '.join(row[2].split())
    #                 else:
    #                     pre_street = 'HWY'

    #                 preDir = returnKey(row[1], dirs)

    #                 sName = f'{pre_street} {row[3]}'.strip().upper()
    #                 if sName.startswith('1/2'):
    #                     sName = sName.strip('1/2 ')
    #                     addNumSuf = '1/2'
    #                 else:
    #                     addNumSuf = ''

    #                 if ' ' in row[4] and len(row[4]) > 2:
    #                     sName = f'{sName} {row[4].split()[1]}'
    #                     sType = returnKey(row[4].split()[0], sTypeDir)
    #                 else:
    #                     sType = returnKey(row[4], sTypeDir)

    #                 sufDir = returnKey(row[5], dirs)

    #                 if sName in fix_sName:
    #                     sName = fix_sName[sName]
    #                     if sufDir == None:
    #                         sufDir = ''

    #                 unitID = row[8].strip()

    #                 if unitID != '':
    #                     fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} # {unitID}'
    #                 else:
    #                     fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir}'

    #                 fullAdd = ' '.join(fullAdd.split())

    #                 addSys = row[6]
    #                 utahAddID = f'{addSys} | {fullAdd}'
    #                 zip = row[10]
    #                 usng = row[11]
    #                 parcelID = removeBadValues(row[6], errorList)
    #                 loadDate = None
    #                 shp = row[9]

    #                 iCursor.insertRow((addSys, utahAddID, fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, \
    #                                    '', '', '', unitID, 'PARK CITY (SUMMIT CO)', zip, '49043', 'UT', '', '', '', \
    #                                    parcelID, 'PARK CITY', loadDate, 'COMPLETE', '', None, '', '', usng, shp))

    #     addBaseAddress(agrcAddPts_PC)

    # #ParkCity()

    # def updateSummit(summitPts, pcPts):
    #     pcPts_dict = {}
    #     with arcpy.da.SearchCursor(pcPts, agrcAddFLDS) as sCursor:
    #         for row in sCursor:
    #             if row[1] not in pcPts_dict:
    #                 pcPts_dict[row[1]] = row

    #     with arcpy.da.SearchCursor(summitPts, agrcAddFLDS) as sCursor:
    #         for row in sCursor:
    #             if row[1] in pcPts_dict:
    #                 pcPts_dict.pop(row[1], None)
    #                 print(f'{row[1]} REMOVED')

    #     with arcpy.da.InsertCursor(summitPts, agrcAddFLDS) as iCursor:
    #         for k in pcPts_dict:
    #             print(k)
    #             iCursor.insertRow((pcPts_dict[k]))

    # #updateSummit(agrcAddPts_summitCo, agrcAddPts_PC)


def tooeleCounty():

    rdSet = createRoadSet('49045')

    def formatRoute(word, d):
        for key, value in d.items():
            if word in value:
                return key
        # if nothing is found
        return word

    def stripType(street, types):
        if len(street.split()) > 1:
            if f' {street.split()[-1]}' in types:
                type = street.split()[-1]
                return street.rstrip(type).strip()
        return street

    types = [' LOOP', ' ST', ' RD', ' PARKWAY', ' PKWY', ' RD', ' LANE', ' LN', ' CT', ' CIR', ' COVE', ' CR', ' DR']
    add_type = {'1ST':'ST', '2ND':'ST', '3RD':'ST', '4TH':'ST', '5TH':'ST', '6TH':'ST', '7TH':'ST',
                '8TH':'ST', '9TH':'ST', 'BOWERY':'ST', 'BROOK':'AVE', 'CENTER':'ST', 'CHURCH':'ST',
                'CLARK':'ST', 'COLEMAN':'ST', 'COOLEY':'ST', 'DAVIS':'LN', 'GARDEN':'ST', 'GREYSTONE':'WAY',
                'GYPSUM':'DR', 'HIDDEN RIVER':'TRL', 'MAIN':'ST', 'MAPLE':'ST', 'NELSON':'AVE', 'OPAL':'LN',
                'PINE':'ST', 'PINYON':'DR', 'ROCKWOOD':'WAY', 'SEVERE':'ST', 'SHEEP ROCK':'TRL', 'SHERMAN':'ST',
                'SNIVELY':'CT', 'TAHOE':'ST', 'VIA LA COSTA':'ST', }


    tooeleCoAddPts = r'..\Tooele\TooeleCounty.gdb\TCAddressPoints'
    agrcAddPts_tooeleCo = r'..\Tooele\Tooele.gdb\AddressPoints_Tooele'
    cntyFldr = r'..\Tooele'

    tooeleCoAddFLDS = ['HouseAddr', 'FullAddr', 'HouseNum', 'PreDir', 'StreetName', 'StreetType', 'SufDir', 
                       'UnitNumber', 'City', 'Parcel_ID', 'Structure', 'SHAPE@', 'OBJECTID', 'SP_UnitType']

    checkRequiredFields(tooeleCoAddPts, tooeleCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_tooeleCo).getOutput(0))
    archive_last_month(agrcAddPts_tooeleCo)
    truncateOldCountyPts(agrcAddPts_tooeleCo)

    routeDict = {'HWY 36':['STATE HWY 36', 'SR36 HWY', 'STATE RTE 36', 'SR 36', 'SR36', 'SR36 ', 'HGIHWAY 36', 'UTAH STATE HWY-36',
                 'N UTAH STATE HWY-36'],
                 'HWY 138':['SR-138 HWY', 'STATE HWY 138', 'SR-138', 'SR 138', 'SR138', 'SR38', 'STATE ROUTE 138', 'STATE ROUTE138'],
                 'HWY 196':['SR196', 'STATHWY 196'],
                 'LINCOLN HWY':['LINCOLN HWY RTE 1913', 'LINCOLN HWY RTE 1919'],
                 'HWY 112':['SR 112', 'SR-112', 'SR112', 'STATHWY 112', 'STATE HWY 112'],
                 'HWY 199':['SR199'], 'HWY 73':['SR73']}

    separatorList = ['/', '-', '&', '\(', '\?', ' T']
    findSeparator = re.compile('|'.join(separatorList))

    errorPtsDict = {}

    unitList = [' APT ', ' BSMT ', ' BLDG ', ' DEPT ', ' FL ', ' FRNT ', ' HNGR ', ' LBBY ', ' OFC ', \
                ' RM ', ' STE ', ' TRLR ', ' UNIT ', ' UPPR ']
    unitSearch = re.compile('|'.join(unitList))

    fixNames = {'PRATTACE':'PRATT', 'ANNCLE':'ANN', 'CHIMES VIEW':'CHIMESVIEW', 'CLEAR WATERCLE':'CLEAR WATER',
                'CLUB HOUSE':'CLUBHOUSE', 'DIAMANT':'DIAMONT', 'GENTLEBREEZE':'GENTLE BREEZE', 'HOMTOWNE':'HOME TOWNE',
                'JULIANN':'JULIE ANN', 'NEWADDLE':'NEW SADDLE', 'OAK HILL':'OAKHILL', 'SAGHILL':'SAGE HILL',
                'SCARLET HORIZOST':'SCARLET HORIZON', 'SHEPHERD':'SHEPARD', 'STREAMSDGE':'STREAMS EDGE',
                'SUNSET RIDGCT':'SUNSET RIDGE', 'TIMPE':'TIMPIE', 'TRIPLCROWN':'TRIPLE CROWN', 'BENCHVIEW':'BENCH VIEW',
                'COWDERY':'COWDREY', 'MIDDLE CYN':'MIDDLE CANYON', 'CORNER VIEW DRIVE':'CORNER VIEW',
                'CANYON MEADWOS':'CANYON MEADOWS', 'BOWRY':'BOWERY', 'BUZIANIWAY':'BUZIANIS', 'BUZIANIWY':'BUZIANIS',
                'ERIKSON':'ERICSON', 'HALORAN':'HALLORAN', 'HOLLORAN':'HALLORAN', 'LAEKSHORE':'LAKESHORE',
                'MOIUNTAIN VIEW':'MOUNTAIN VIEW', 'MORAH':'MORIAH', 'TIPPCANOE':'TIPPECANOE', 'WILCAT':'WILDCAT',
                'WIILDCAT':'WILDCAT', 'CAROLES WAY BUILDING':'CAROLE\'S', 'CAROLES WAY BUILDING F':'CAROLE\'S',
                'CAROLES WAY BUIDLING F':'CAROLE\'S', 'BLUEMOON':'BLUE MOON', 'COLLETTE':'COLETTE', 'DAVILN':'DAVIS',
                'DOALN':'DOLAN', 'GRANT AVENUE':'GRANT', 'HANDICART':'HANDCART', 'HIGHWAY 36':'HWY 36', 'RIDGON':'RIGDON',
                'SILVER AVE':'SILVER', 'BIRCHWOOD':'BIRCH WOOD', 'MORMAN TRAIL':'MORMON TRAIL', 'N':'NORTH',
                'OLD COUNTRY':'OLD COUNTY', 'SHERIDAST':'SHERIDAN'}

    yes_no = {'Y':'YES', 'N':'NO'}
                                                                           
    #find unwanted directions (E 100 N, S 100, 100 W)
    exp = re.compile(r'(?:^[NSEW]\s)?(?:(.+)(\s[NSEW]$)|(.+$))')

    with arcpy.da.SearchCursor(tooeleCoAddPts, tooeleCoAddFLDS) as sCursor, \
        arcpy.da.InsertCursor(agrcAddPts_tooeleCo, agrcAddFLDS) as iCursor:
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
                    if sNameRAW == '7 C':
                        sName = sNameRAW
                    else:
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

                if sName != 'JANELLE COVE':
                    sName = stripType(sName, types)

                sType = formatValues(row[5], sTypeDir)
                if row[5] == 'WY':
                    sType = 'WAY'
                if sName[0].isdigit() and sName[-1].isdigit():
                    sType = ''
                if sName == 'BOGGS':
                    sName = '80'
                    sufDir = 'E'
                    sType = ''
                if sName == 'TIEBREAKER' and sType == '':
                    sType = 'CIR'
                if sName == 'PREAKNESS WAY':
                    sName = 'PREAKNESS'
                    sType = 'WAY'

                if sName in fixNames:
                    sName = fixNames[sName]
                if sName in add_type and sType == '':
                    sType = add_type[sName]
                if sName == 'CAROLE\'S':
                    sType = 'WAY'
                    sufDir = ''

                unitID = removeBadValues((row[7]), errorList).upper().strip('#').strip('(').strip(')')
                unitType = returnKey(row[13], unitTypeDir).upper()
                # findUnit = unitSearch.search(row[0])
                # unitType = ''
                # if row[13] != '':
                #     unitType = returnKey(removeBadValues(row[13], errorList).upper(), unitTypeDir)
                # if findUnit:
                #     unitType = findUnit.group(0).strip()

                city = ''
                parcelID = removeBadValues(row[9], errorList)
                structure = removeBadValues(removeNone(row[10]).upper(), errorList)
                if structure in yes_no:
                    structure = yes_no[structure]
                if structure == '':
                    structure = 'UNKNOWN'
                loadDate = today
                shp = row[11]

        #-------Log address errors
                if removeNone(row[4]).lstrip('0').upper() not in removeNone(row[1]):
                    addressErrors = errorPtsDict.setdefault(f'{row[4]} | {row[1]}', [])
                    addressErrors.extend(['Mixed street names', row[11]])
                if sName not in rdSet and 'HWY' not in sName:
                    addressErrors = errorPtsDict.setdefault(f'{row[4]} | {row[1]}', [])
                    addressErrors.extend(['Street name not found in roads', row[11]])
                if row[3] == row[6] and row[3] not in errorList:
                    addressErrors = errorPtsDict.setdefault(row[1], [])
                    addressErrors.extend(['predir = sufdir', row[11]])
        #----------------------------------------------------------------
                addNumRAW = row[2]

                separator = findSeparator.search(addNumRAW)

                if ' 1/2' in addNumRAW:
                    addNum = addNumRAW.split()[0]
                    addNumSuf = addNumRAW.split()[1]
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} {unitType} {unitID}'
                    fullAdd = ' '.join(fullAdd.split())
                    iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                       unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                       'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))

                elif separator:
                    addNum = addNumRAW.split(separator.group(0))[0].strip()
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} {unitType} {unitID}'
                    fullAdd = ' '.join(fullAdd.split())
                    iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                       unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                       'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))

                else:
                    if '#' in addNumRAW:
                        addNum = addNumRAW.strip('#')
                        if unitType == '' and unitID != '':
                            fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} # {unitID}'
                            fullAdd = ' '.join(fullAdd.split())
                        else:
                            fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} {unitType} {unitID}'
                            fullAdd = ' '.join(fullAdd.split())

                        iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                           unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                           'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))

                    elif addNumRAW[0].isdigit() == False:
                        print (f'{row[0]} {row[2]}   FIX ME')
                        if addNumRAW[1].isdigit() == True:
                            address = parse_address.parse(row[0])
                            addNum = address.houseNumber
                            preDir = address.prefixDirection
                            sName = address.streetName
                            sufDir = address.suffixDirection
                            unitID = row[7]
                            shp = row[11]
                            fullAdd = f'{addNum} {preDir} {sName} {sufDir} # {unitID}'
                            print(f'{fullAdd}   FIXED')
                            iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                           unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                           'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))
                        else:
                            continue

                    else:
                        addNum = addNumRAW.strip()
                        if sName in routeDict:
                            fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {unitType} {unitID}'
                            fullAdd = ' '.join(fullAdd.split())
                            if unitType == '' and unitID != '':
                                fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} # {unitID}'
                                fullAdd = ' '.join(fullAdd.split())

                        elif unitType == '' and unitID != '':
                            fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} # {unitID}'
                            fullAdd = ' '.join(fullAdd.split())
                        else:
                            fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} {unitType} {unitID}'
                            fullAdd = ' '.join(fullAdd.split())


                        iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                                           unitType, unitID, city, '', '49045', 'UT', '', '', structure, parcelID, \
                                           'TOOELE COUNTY', loadDate, 'COMPLETE', '', None, '', '', '', shp))

                # if unitType == '' and unitID != '':
                #             fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sufDir} {sType} # {unitID}'
                #             fullAdd = ' '.join(fullAdd.split())

            else:
                print (row[12])
                print ('what to do?')

        errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Tooele_ErrorPts.shp', 'ADDRESS', tooeleCoAddPts)

    del iCursor
    del sCursor

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    tooele_parcelsLIR = {'PtType': ['SGID.CADASTRE.Parcels_Tooele_LIR', 'PROP_CLASS']}

    tooele_remapLIR = {'Agricultural':['Agricultural', 'Greenbelt'],
                       'Commercial':['Commercial',  'Commercial - Office Space', 'Commercial - Retail'],
                       'Industrial':['Industrial', 'Commercial - Industrial'],
                       'Mixed Use':['Mixed Use'],
                       'Other':['Tax Exempt', 'Tax Exempt - Charitable Organization or Religious',
                                'Tax Exempt - Government', 'Undevelopable', 'Vacant', 'Privilege Tax', 'Personal Property'],
                       'Residential':['Residential', 'Commercial - Apartment & Condo'],
                       'Unknown':[None, '', 'Unknown']}

    addPolyAttributes(sgid, agrcAddPts_tooeleCo, inputDict)
    updateAddPtID(agrcAddPts_tooeleCo)
    addPolyAttributesLIR(sgid, agrcAddPts_tooeleCo, tooele_parcelsLIR, tooele_remapLIR)
    addBaseAddress(agrcAddPts_tooeleCo)
    deleteDuplicatePts(agrcAddPts_tooeleCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_tooeleCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Tooele_ErrorPts.shp'), errorPts, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_tooeleCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')
    

def utahCounty():

    utahCoAddPts = r'..\Utah\Address.gdb\AddressPnt'
    #utahCoAddPts = r'..\Utah\UtahCounty.gdb\AddressPnt'
    agrcAddPts_utahCo = r'..\Utah\Utah.gdb\AddressPoints_Utah'
    cntyFldr = r'..\Utah'

    sgidRds = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde', 'SGID.TRANSPORTATION.Roads'))

    utahCoAddFLDS = ['ADDRNUM', 'ROADPREDIR', 'ROADNAME', 'ROADTYPE', 'ROADPOSTDIR', 'ADDRTYPE',
                     'UNITTYPE', 'UNITID', 'LASTUPDATE', 'SHAPE@', 'LASTEDITOR', 'FULLADDR', 'ZIPCODE',
                     'OBJECTID', 'LAST_EDITED_DATE', 'CITY', 'ALTUNITTYPE', 'ALTUNITID']
    
    # utahCoAddFLDS = ['ADDRNUM', 'ROADPREDIR', 'ROADNAME', 'ROADTYPE', 'ROADPOSTDI', 'ADDRTYPE',
    #                 'UNITTYPE', 'UNITID', 'LASTUPDATE', 'SHAPE@', 'LASTEDITOR', 'FULLADDR', 'ZIPCODE',
    #                 'OBJECTID', 'LAST_EDI_1', 'CITY', 'ALTUNITTYP', 'ALTUNITID']


    checkRequiredFields(utahCoAddPts, utahCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_utahCo).getOutput(0))
    #archive_last_month(agrcAddPts_utahCo)
    truncateOldCountyPts(agrcAddPts_utahCo)

    errorPtsDict = {}
    countyRds_Ldrive = r'..\Utah\Roads.gdb\RoadCenterline'
    rdSet = createRoadSet('49049')
    #rdSet_county = createRoadSet_County(countyRds_Ldrive, ['ROADNAME', 'COUNTYNAME'], 'Utah')

    badType = {'AV':'AVE', 'LA':'LN', 'PKY':'PKWY', 'WY':'WAY'}
    addType = {'Building':'Rooftop', 'Parcel':'Parcel Centroid', 'Building Entrance':'Primary Structure Entrance', \
              'Driveway Turn-off':'Driveway Entrance', 'Unit, Condo or Suite':'Residential', 'Other':'Other', 'Unknown':'Unknown'}
    dirList = ['NORTH', 'SOUTH', 'EAST', 'WEST']
    stExceptions = ['2720 WEST', 'WILD HORSE POINT', 'RED TAILED CRESCENT', 'CENTER', 'WEMBLY PARK']
    remove_type = ['HASKELL LANDING']
    fix_name = {'GAMBOL OAK':'GAMBEL OAK'}

    with arcpy.da.SearchCursor(utahCoAddPts, utahCoAddFLDS) as sCursor_utah, \
        arcpy.da.InsertCursor(agrcAddPts_utahCo, agrcAddFLDS) as iCursor:

        for row in sCursor_utah:

            unitId = ''
            sType = ''
            sufDir = ''

            if row[0] not in errorList and row[2] not in errorList:
                if row[3] in errorList and row[1] in errorList and not returnKey(row[2].split()[-1], sTypeDir) in sTypeDir:
                    #print(f'{row[13]} - {row[11]}')
                    continue
                else:
                    if row[3] in badType:
                        sType =  badType[row[3]]
                    else:
                        sType = returnKey(row[3], sTypeDir)

                addNum = row[0].strip()

                if ' ' in row[2]:
                    street = ' '.join(row[2].split()).upper()

                    if street.split()[0].isdigit() and street.split()[0] != '0':
                        street = street.split()[0]

                        if row[2].split()[-1] in dirList and row[2] not in stExceptions:
                            sufDir = row[2].split()[-1][:1]

                            if street.isdigit() == True:
                                sType = ''

                        else:
                            if row[2].split()[-1][:1] in dirs: # and row[2]:
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
                if returnKey(street.split()[-1], sTypeDir) in sTypeDir and sType == '' and street not in stExceptions:
                    sType = returnKey(street.split()[-1], sTypeDir)
                    street = ' '.join(street.split()[:-1])
                if street.endswith(' DR'):
                    street = street.replace(' DR', '')
                if street in remove_type:
                    sType = returnKey(street.split()[-1], sTypeDir)
                    street = street.strip(street.split()[-1]).strip()

                # Add missing ST
                missingStSuf = ['CENTER', 'MAIN', 'STATE']
                if street in missingStSuf and sType == '':
                    sType = 'ST'

                if street.startswith(('SR ', 'US ')):
                    street = f'HWY {street[3:]}'
                    sType = ''

                if row[1] in dirs:
                    preDir = row[1]
                else:
                    preDir = ''

                if row[4] not in errorList:
                    sufDir = row[4]
                    if f' {sufDir} ' not in row[11]:
                        sufDir = ''

                if preDir in errorList and sufDir not in errorList:
                    continue

                if row[5] in addType:
                    ptLocation = addType[row[5]]
                else:
                    ptLocation = ''

                if row[6] not in errorList:
                    if returnKey(row[6].upper(), unitTypeDir) != '': # in unitTypeDir:
                        unitType = returnKey(row[6].upper(), unitTypeDir)
                        unitType_Abbrv = row[6].upper()
                else:
                    unitType = ''
                    unitType_Abbrv = ''

                if row[7] not in errorList:
                    unitId = row[7]

                if unitId == '' and unitType != '':
                    unitType = ''

                if row[16] in ['BLDG', 'Building'] and row[17] not in [None, 'Creekside']:
                    building = row[17]
                else:
                    building = ''

                loadDate = today
                status = 'COMPLETE'

                if row[10] not in errorList:
                    editor = row[10]
                else:
                    editor = ''

                modDate = row[8]
                if modDate != None and row[14] != None and modDate < row[14]:
                    modDate = row[14]

                if building != '':
                    fullAdd = f'{addNum} {preDir} {street} {sufDir} {sType} BLDG {building} {unitType} {unitId}'

                elif unitType == '' and unitId != '':
                    fullAdd = f'{addNum} {preDir} {street} {sufDir} {sType} # {unitId}'
                else:
                    fullAdd = f'{addNum} {preDir} {street} {sufDir} {sType} {unitType} {unitId}'

                fullAdd = ' '.join(fullAdd.split())

                zip = ''
                shp = row[9]

                # -------Error Points---------------
                if preDir == sufDir and preDir != '':
                    print('dir = dir')
                    addressErrors = errorPtsDict.setdefault(f'{row[15]} | {fullAdd}', [])
                    addressErrors.extend(['predir = sufdir', row[9]])
                # if street not in removeNone(row[11]) and 'HWY' not in street and row[11] != None:
                #     addressErrors = errorPtsDict.setdefault('{street} | {row[11]}', [])
                #     addressErrors.extend(['Mixed street names', row[9]])
                # if street not in rdSet and 'HWY' not in street:
                # #if street not in rdSet_county and 'HWY' not in street:
                #     addressErrors = errorPtsDict.setdefault(row[11], [])
                #     addressErrors.extend(['Street name not found in roads', row[9]])
                # if row[3] not in sTypeList and row[3] not in errorList and row[3] != 'WY' and row[3] != 'ALLEY':
                #     addressErrors = errorPtsDict.setdefault('{} | {}'.format(row[11], row[3]), [])
                #     addressErrors.extend(['bad street type', row[9]])
                # ------------------------------------

                iCursor.insertRow(('PROVO', '', fullAdd, addNum, '', preDir, street, sType, sufDir, '', building, unitType, unitId, '', zip, '49049', \
                                   'UT', ptLocation, '', '', '', 'UTAH COUNTY', loadDate, status, editor, modDate, '', '', '', shp))

    errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Utah_ErrorPts.shp', 'ADDRESS', utahCoAddPts)

    del iCursor
    del sCursor_utah

    inputDict = {
            'AddSystem':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
            'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
            'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
            'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
            'ParcelID':['SGID.CADASTRE.Parcels_Utah', 'PARCEL_ID', '']
            }

    utah_parcelsLIR = {'PtType': ['SGID.CADASTRE.Parcels_Utah_LIR', 'PROP_CLASS']}

    utah_remapLIR = {'Agricultural':['Agricultural', 'Greenbelt'],
                     'Commercial':['Commercial',  'Commercial - Office Space', 'Commercial - Retail'],
                     'Industrial':['Industrial', 'Commercial - Industrial'],
                     'Mixed Use':['Mixed Use'],
                     'Other':['Tax Exempt', 'Tax Exempt - Charitable Organization or Religious',
                              'Tax Exempt - Government', 'Undevelopable', 'Vacant', 'Privilege Tax', 'Personal Property'],
                     'Residential':['Residential', 'Commercial - Apartment & Condo'],
                     'Unknown':[None, '', 'Unknown']}

    update_grid = {'BLUFFDALE (UTAH CO)':'SALT LAKE CITY', 'CEDAR HILLS':'PROVO', 'HIGHLAND':'PROVO',
                   'DRAPER CITY (UTAH CO)':'SALT LAKE CITY', 'SANTAQUIN CITY (UTAH CO)':'SANTAQUIN'}

    addPolyAttributes(sgid, agrcAddPts_utahCo, inputDict)
    updateField(agrcAddPts_utahCo, 'AddSystem', update_grid)
    updateAddPtID(agrcAddPts_utahCo)
    addPolyAttributesLIR(sgid, agrcAddPts_utahCo, utah_parcelsLIR, utah_remapLIR)
    addBaseAddress(agrcAddPts_utahCo)
    deleteDuplicatePts(agrcAddPts_utahCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_utahCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Utah_ErrorPts.shp'), errorPts, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_utahCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def uintahCounty_oldSchema():
    uintahCoAddPts = r'..\Uintah\UintahCounty.gdb\Uintah_MAL_2022'
    agrcAddPts_uintahCo = r'..\Uintah\Uintah.gdb\AddressPoints_Uintah'
    cntyFldr = r'..\Uintah'

    sgidRds = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde', 'SGID.TRANSPORTATION.Roads'))

    uintahCoAddFLDS = ['HOUSENUMBE', 'STREETNAME', 'APARTMENT', 'ZIP', 'SHAPE@', 'Add_Type']

    checkRequiredFields(uintahCoAddPts, uintahCoAddFLDS)
    truncateOldCountyPts(agrcAddPts_uintahCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49047')
    loadDate = today

    fix_name = {'US 40':'HWY 40', 'US 88':'HWY 88', 'SR 149':'HWY 149', 'BONANZA HWY 45':'HWY 45'}
    bad_unitId = ['HOUSE', 'HOUSE-OLD']
    map_ptType = {'Residential':'Residential', 'Resident':'Residential', 'EDUCATION':'Other', 'RELIGION':'Other',
                  ' ':'Unknown'}

    with arcpy.da.SearchCursor(uintahCoAddPts, uintahCoAddFLDS) as sCursor_uintah, \
        arcpy.da.InsertCursor(agrcAddPts_uintahCo, agrcAddFLDS) as iCursor:

        for row in sCursor_uintah:

            sufDir = ''
            sType = ''
            addNumSuf = ''

            if row[0] in errorList:
                continue

            addNum = row[0].strip()
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
                preDir = ''

            if sName_strp in fix_name:
                sName_strp = fix_name[sName_strp]

            sName_strp = sName_strp.strip()

            if sName_strp not in rdSet and sName_strp[:4] != 'HWY ':
                addressErrors = errorPtsDict.setdefault(f'{sName_strp} | {row[1]}', [])
                addressErrors.extend(['Street name not found in roads', row[4]])
            if preDir == sufDir:
                addressErrors = errorPtsDict.setdefault(row[1], [])
                addressErrors.extend(['Pre and post directions are the same', row[4]])

            unitType = (removeNone(returnStart(row[2].upper(), unitTypeDir)))
            unitID = (row[2].upper().lstrip(unitType)).strip().strip('#')
            if 'SPACE' in row[2].upper():
                unitType = 'SPC'
                unitID = row[2][6:]
            if 'ROOM' in row[2].upper():
                unitType = 'RM'
                unitID = row[2][5:]
            if unitID in bad_unitId:
                unitID = ''
            if unitType not in ['', 'BSMT', 'FRNT'] and unitID == '':
                unitType = ''

            if unitType == '' and unitID != '':
                fullAdd = f'{addNum} {addNumSuf} {preDir} {sName_strp} {sufDir} {sType} # {unitID}'
            else:
                fullAdd = f'{addNum} {addNumSuf} {preDir} {sName_strp} {sufDir} {sType} {unitType} {unitID}'

            if row[5] in map_ptType:
                pt_Type = map_ptType[row[5]]

            fullAdd = ' '.join(fullAdd.split())

            shp = row[4]

            iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName_strp, sType, sufDir, '', '', unitType, unitID, \
                               '', '', '49047', 'UT', '', pt_Type, '', '', 'UINTAH COUNTY', loadDate, 'COMPLETE', '', \
                               None, '', '', '', shp))

        errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Uintah_ErrorPts.shp', 'ADDRESS', uintahCoAddPts)

    del iCursor
    del sCursor_uintah

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_uintahCo, inputDict)
    updateAddPtID(agrcAddPts_uintahCo)
    addBaseAddress(agrcAddPts_uintahCo)
    deleteDuplicatePts(agrcAddPts_uintahCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_uintahCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Uintah_ErrorPts.shp'), errorPts, dupePts)


def uintahCounty():
        
    fs_url = 'https://apps.uintah.utah.gov/arcgis/rest/services/UintahMAL/MapServer/0'
    agol_to_fgdb('Uintah', fs_url)

    uintahCoAddPts = r'..\Uintah\UintahCounty.gdb\Uintah_agol_pts'
    #uintahCoAddPts = r'..\Uintah\UintahCounty.gdb\Uintah_MAL_2022'
    agrcAddPts_uintahCo = r'..\Uintah\Uintah.gdb\AddressPoints_Uintah'
    cntyFldr = r'..\Uintah'

    sgidRds = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde', 'SGID.TRANSPORTATION.Roads'))

    uintahCoAddFLDS = ['FullAdd', 'AddNum', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir', 'LandmarkNa',
                       'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'PtLocation', 'PtType', 'Structure',
                       'ParcelID', 'EDIT_DATE', 'SHAPE@']

    fix_name = {'19500 (THE LANE)':'THE LANE RD', 'DIAMOND MTN LANE':'THE LANE RD', 'DRY FORK CEMETARY':'DRY FORK CEMETERY',
                'HIGHWAY 191':'HWY 191', 'HIGWAY 40':'HWY 40', 'HIWY 40':'HWY 40', 'HW 40':'HWY 40', 'HWY 40 STE A-B':'HWY 40',
                'HORESHOE BEND':'HORSESHOE BEND', 'NDIAN TRAIL RANCH':'INDIAN TRAIL RANCH', 'US':'HWY 40', 'US 149':'HWY 149',
                'WARRENDRAW':'WARREN DRAW'}

    checkRequiredFields(uintahCoAddPts, uintahCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_uintahCo).getOutput(0))
    #archive_last_month(agrcAddPts_uintahCo)
    truncateOldCountyPts(agrcAddPts_uintahCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49047')

    with arcpy.da.SearchCursor(uintahCoAddPts, uintahCoAddFLDS) as scursor, \
        arcpy.da.InsertCursor(agrcAddPts_uintahCo, agrcAddFLDS) as icursor:
        for row in scursor:
            if row[1] not in errorList and row[3] not in errorList:
                add_num = row[1]
                pre_dir = returnKey(row[2], dirs)
                street_name = row[3].strip()
                street_type = returnKey(row[4], sTypeDir)
                suf_dir = row[5].strip()

                if street_name in fix_name:
                    street_name = fix_name[street_name]

                if street_name.endswith((' AVE', ' BLVD', ' CIR', ' DR', ' DRIVE', ' RD', ' ROAD', ' ST', ' WAY')):
                    street_type = returnKey(street_name.split()[-1], sTypeDir)
                    street_name = ' '.join(street_name.split()[:-1])

                if street_name == 'THE LANE':
                    street_type = 'RD'

                unit_id = row[9].strip()
                if row[8].isdigit() == False:
                    unit_type = returnKey(row[8], unitTypeDir)
                else:
                    unit_type = ''
                    unit_id = row[8].strip()
  
            elif row[0] not in errorList:
                address = parse_address.parse(row[0])
                add_num = address.houseNumber
                pre_dir = removeNone(address.prefixDirection)
                street_name = address.streetName
                street_type = removeNone(address.suffixType)
                suf_dir = removeNone(address.suffixDirection).strip()

                if street_name == 'MAIN ST' or street_name == 'MAIN':
                    street_name = 'MAIN'
                    street_type = 'ST'

                if street_name in fix_name:
                    street_name = fix_name[street_name]

                unit_id = row[9].strip()
                if row[8].isdigit() == False:
                    unit_type = returnKey(row[8], unitTypeDir)
                else:
                    unit_type = ''
                    unit_id = row[8].strip()

                if unit_type == '' and unit_id != '':
                    full_add = f'{add_num} {pre_dir} {street_name} {street_type} {suf_dir} # {unit_id}'
                else:
                    full_add = f'{add_num} {pre_dir} {street_name} {street_type} {suf_dir} {unit_type} {unit_id}'
                full_add = ' '.join(full_add.split())

            else:
                continue

            if unit_type == '' and unit_id != '':
                    full_add = f'{add_num} {pre_dir} {street_name} {street_type} {suf_dir} # {unit_id}'
            else:
                full_add = f'{add_num} {pre_dir} {street_name} {street_type} {suf_dir} {unit_type} {unit_id}'
                full_add = ' '.join(full_add.split())

            pt_type = row[13]
            load_date = today
            mod_date = row[16]
            shp = row[17]

            icursor.insertRow(('', '', full_add, add_num, '', pre_dir, street_name, street_type, suf_dir, '', '', unit_type, unit_id, '',
                                '', '49047', 'UT', '', pt_type, '', '', 'UINTAH COUNTY', load_date, 'COMPLETE', '', mod_date, '', '', '', shp))

        errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Uintah_ErrorPts.shp', 'ADDRESS', uintahCoAddPts)

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'ParcelID':['SGID.CADASTRE.Parcels_Uintah', 'PARCEL_ID', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']      
    }

    addPolyAttributes(sgid, agrcAddPts_uintahCo, inputDict)
    updateAddPtID(agrcAddPts_uintahCo)
    addBaseAddress(agrcAddPts_uintahCo)
    deleteDuplicatePts(agrcAddPts_uintahCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_uintahCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Uintah_ErrorPts.shp'), errorPts, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_uintahCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def wasatchCounty():

    fs_url = 'https://maps.wasatch.utah.gov/arcgis/rest/services/Maps/Basic_Map_Layer/MapServer/3'
    agol_to_fgdb('Wasatch', fs_url)

    rdSet = createRoadSet('49051')
   
    wasatchCoAddPts = r'..\Wasatch\WasatchCounty.gdb\Wasatch_agol_pts'

    #wasatchCoAddPts = r'..\Wasatch\WasatchCounty.gdb\WC_ADDRESS'
    agrcAddPts_wasatchCo = r'..\Wasatch\Wasatch.gdb\AddressPoints_Wasatch'
    cntyFldr = r'..\Wasatch'

    # wasatchCoAddFLDS = ['FullName', 'FullAdd', 'AddrNum', 'AddrNumSuf', 'StreetName', 'StreetType', 'SuffixDir', \
    #                     'Building', 'UnitType', 'UnitID', 'FeatureTyp', 'SiteAddID', 'PointType', 'SHAPE@']
    # wasatchCoAddFLDS = ['FullAdd', 'AddrNum', 'AddrNumSuffix', 'StreetName', 'StreetType', 'SuffixDir',
    #                     'Building', 'UnitType', 'UnitID', 'LandmarkName', 'ParcelID', 'PointType', 'SHAPE@', 'Structure']
    # wasatchCoAddFLDS = ['FullAdd', 'AddrNum', 'AddrNumSuffix', 'StreetName', 'StreetType', 'SuffixDir',
    #                     'UnitType', 'UnitID', 'LandmarkName', 'ParcelID', 'PointType', 'SHAPE@']
    wasatchCoAddFLDS = ['FullAdd', 'AddrNum', 'AddrNumSuf', 'StreetName', 'StreetType', 'SuffixDir',
                        'UnitType', 'UnitID', 'Subdivision', 'SiteAddID', 'PointType', 'SHAPE@']

    checkRequiredFields(wasatchCoAddPts, wasatchCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_wasatchCo).getOutput(0))
    archive_last_month(agrcAddPts_wasatchCo)
    truncateOldCountyPts(agrcAddPts_wasatchCo)

    wasatchExclude = ['MM', 'Mile Marker']
    fixDict = {'1080 ALPENHOF':'ALPENHOF', '1080 ALPNEHOF':'ALPENHOF', '3000 SNAKE CREEK':'SNAKE CREEK', '1050 BURGI':'BURGI',
               'BAXTOR':'BAXTER', 'VALLEYHILLS':'VALLEY HILLS', 'COUNTRY SIDE':'COUNTRYSIDE', 'AGUSTA':'AUGUSTA',
               'SOUTH FORK':'FORK', 'STILL WATER':'STILLWATER', 'EDENBURGH':'EDINBURGH', 'COUNTRY MEADOWS':'COUNTRY MEADOW',
               'COUNTRY MEADOWS ESTATES':'COUNTRY MEADOW ESTATES', 'AGUSTA':'AUGUSTA', 'SOARING VIEW':'APPENZELL',
               'HAMLET CIR W':'HAMLET', 'HAMLET CIR N':'HAMLET', 'HAMLET CIR S':'HAMLET', 'DANIEL':'DANIELS',
               'BOULDER POINTE':'BOULDER POINT', 'CALAWAY':'CALLAWAY', 'EIGER POINTE':'EIGER POINT', 'LUSANNE':'LAUSANNE',
               'TABION':'TOBIANO', 'TABIANO':'TOBIANO', 'EAGLE REST':'EAGLES REST'}

    fix_stype = {'BUCK HORN TRAIL':'TRL', 'HILLSIDE DR':'DR', 'WILLOW CIR':'CIR', 'TUHAYE HOLLOW':'HOLLOW'}

    errorPtsDict = {}

    with arcpy.da.SearchCursor(wasatchCoAddPts, wasatchCoAddFLDS) as sCursor_wasatchCo, \
        arcpy.da.InsertCursor(agrcAddPts_wasatchCo, agrcAddFLDS) as iCursor:
        for row in sCursor_wasatchCo:
            # if row[12] == 'PARCEL':
            #     continue
            if removeNone(row[9]).startswith('SR '):
                continue

            if row[1] in errorList:
                continue

            if row[1].isdigit():
                addNum = row[1]
                preDir = removeNone(row[2])
                sName = row[3]
                if sName == '' or sName == None:
                    #errorPtsDict[row[1]] = row[13]
                    continue

                sName = sName.replace('SR ', 'HWY ').replace('US ', 'HWY ')
                if 'HWY' not in sName and sName not in rdSet:
                    addressErrors = errorPtsDict.setdefault(f'{sName} | {row[1]}', [])
                    addressErrors.extend(['add pts street name not found in roads', row[11]])

                sufDir = removeNone(row[5])
                sType = removeNone(row[4])
                if sType != '' and sufDir in dirs:
                    sufDir = ''

                if sName.endswith(f' {sType}'):
                    sName = sName.replace(f' {sType}', '')
                if sName in fixDict:
                    sName = fixDict[sName]
                if sName == 'HAMLET':
                    sType = 'CIR'
                    sufDir = returnKey(row[3][-1], dirs)
                    # if row[3] != 'HAMLET':
                    #     sufDir = row[4][-1]
                if sName == 'APPENZELL':
                    sType = 'LN'
                if sName in fix_stype:
                    sType = returnKey(fix_stype[sName], sTypeDir)
                    sName = sName.replace(sName.split()[-1], '').strip()
                    if sName.endswith('TRAIL'):
                        sName = sName.replace('TRAIL', '').strip()


                if preDir == sufDir and preDir != '':
                    addressErrors = errorPtsDict.setdefault(row[1], [])
                    addressErrors.extend(['predir = sufdir', row[11]])
                    continue

                unitType = returnKey(row[6], unitTypeDir)
                unitID = removeBadValues(row[7], errorList)

                if unitType == '' and unitID != '':
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} # {unitID}'
                elif unitType != '' and unitID != '':
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} {unitType} {unitID}'
                else:
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir}'

                fullAdd = ' '.join(fullAdd.split())

                parcelID = removeBadValues(row[10], errorList)
                loadDate = today
                #structure = removeNone(row[13])
                shp = row[11]

                iCursor.insertRow(
                    ('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', unitType, unitID, '',
                     '', '49051', 'UT', '', '', '', parcelID, 'WASATCH COUNTY', loadDate, 'COMPLETE', \
                     '', None, '', '', '', shp))

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Wasatch_ErrorPts.shp', wasatchCoAddFLDS[1], wasatchCoAddPts)

    #print (errorPtsDict.keys())
    createErrorPts(errorPtsDict, cntyFldr, 'Wasatch_ErrorPts.shp', wasatchCoAddFLDS[1], wasatchCoAddPts)
    del iCursor
    del sCursor_wasatchCo


    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_wasatchCo, inputDict)
    updateAddPtID(agrcAddPts_wasatchCo)
    addBaseAddress(agrcAddPts_wasatchCo)
    deleteDuplicatePts(agrcAddPts_wasatchCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_wasatchCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Wasatch_ErrorPts.shp'), errorFlds, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_wasatchCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def washingtonCounty():

    def _get_secrets():
        secret_folder = Path('secrets')
        return json.loads((secret_folder / 'secrets.json').read_text(encoding='utf-8'))
    secrets = SimpleNamespace(**_get_secrets())
    
    arcgis.gis.GIS(secrets.AGOL_ORG, secrets.AGOL_USER, secrets.AGOL_PASSWORD)
    
    agrcAddPts_washCo = r'..\Washington\Washington.gdb\AddressPoints_Washington'
    cntyFldr = r'..\Washington'

    fs_url = 'https://agisprodvm.washco.utah.gov/arcgis/rest/services/Share/FeatureServer/1'
    agol_to_fgdb('Washington', fs_url)

    washcoAddPts = r'..\Washington\WashingtonCounty.gdb\Washington_agol_pts'

    washcoAddFLDS = ['TAX_ID', 'ADDRNUM', 'PREFIXDIR', 'STREETNAME', 'STREETTYPE', 'UNITTYPE', 'UNITID', 'PLACENAME', \
                     'LASTUPDATE', 'SHAPE@', 'OBJECTID', 'SUFFIXDIR', 'FULLADDR', 'FULLNAME', 'POST_DIR']

    checkRequiredFields(washcoAddPts, washcoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_washCo).getOutput(0))
    archive_last_month(agrcAddPts_washCo)
    truncateOldCountyPts(agrcAddPts_washCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49053')

    dirList = ['N', 'S', 'E', 'W']
    sTypeList = ['ALY', 'ANX', 'AVE', 'BLVD', 'BYP', 'CSWY', 'CIR', 'CT', 'CTR', 'CV', 'XING', 'DR', 'EST', 'ESTS', \
                 'EXPY', 'FWY', 'HWY', 'JCT', 'LNDG', 'LN', 'LOOP', 'PARK', 'PKWY', 'PL', 'RAMP', 'RD', 'RTE', \
                 'ROW', 'SQ', 'ST', 'TER', 'TRWY', 'TRL', 'TUNL', 'TPKE', 'WAY']
    fix_name = {'BIRKIN':'BIRKEN', 'MOLINERO':'MOLINARO', 'NORTHSTAR':'NORTH STAR'}

    iCursor = arcpy.da.InsertCursor(agrcAddPts_washCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(washcoAddPts, washcoAddFLDS) as sCursor_washco, \
        arcpy.da.InsertCursor(agrcAddPts_washCo, agrcAddFLDS) as iCursor:

        for row in sCursor_washco:

            if row[1] not in errorList and row[1].isdigit() and row[3] not in errorList:
                addNum = formatAddressNumber(row[1])
                preDir = returnKey(row[2], dirs)

                if row[3] not in errorList:
                    if row[3].endswith((' N', ' S', ' E', ' W')):
                        sName = row[3][:-1].strip().upper()
                        sufDir = row[3][-1].strip()
                    else:
                        sName = row[3].upper().strip()
                        sufDir = returnKey(row[11], dirs).strip()

                    if sufDir == '' and row[14] != None:
                        sufDir = removeNone(row[14]).strip()

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

                if sName.startswith(('SR-', 'HIGHWAY')):
                    sName = sName.replace('SR-', 'HWY ').replace('HIGHWAY', 'HWY ')
                    sName = ' '.join(sName.split())

                # if sName[0].isdigit() == False:
                #     sufDir = ''

                if sName in fix_name:
                    sName = fix_name[sName]

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
                   unitID_hash = f'# {unitID}'
                   fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} {unitID_hash}'
                elif unitType != '' and unitID != '':
                   fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} {unitType} {unitID}'
                else:
                   fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir}'

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
                if removeNone(row[3]).upper() not in removeNone(row[12]).upper():
                    addressErrors = errorPtsDict.setdefault(f'{row[3]} | {row[12]}', [])
                    addressErrors.extend(['mixed street names', row[9]])
                if 'HWY ' not in sName and sName not in rdSet:
                    addressErrors = errorPtsDict.setdefault(f'{sName} | {row[12]}', [])
                    addressErrors.extend(['street name not in roads', row[9]])

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, landmark, '', unitType, unitID, '', '', '49053', 'UT', 'Unknown', \
                                   'Unknown', 'Unknown', parcel, 'WASHINGTON COUNTY', date, 'COMPLETE', '', modDate, '', '', '', shp))

        errorFlds = createErrorPts(errorPtsDict, cntyFldr, 'Washington_ErrorPts.shp', washcoAddFLDS[12], washcoAddPts)

    del iCursor
    del sCursor_washco

    inputDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
    'ParcelID':['SGID.CADASTRE.Parcels_Washington', 'PARCEL_ID', '']
    }

    washington_parcelsLIR = {'PtType': ['SGID.CADASTRE.Parcels_Washington_LIR', 'PROP_CLASS']}

    washington_remapLIR = {'Agricultural':['Agricultural', 'Greenbelt'],
                           'Commercial':['Commercial',  'Commercial - Office Space', 'Commercial - Retail'],
                           'Industrial':['Industrial', 'Commercial - Industrial'],
                           'Mixed Use':['Mixed Use'],
                           'Other':['Tax Exempt', 'Tax Exempt - Charitable Organization or Religious',
                                    'Tax Exempt - Government', 'Undevelopable', 'Vacant', 'Privilege Tax', 'Personal Property'],
                           'Residential':['Residential', 'Commercial - Apartment & Condo'],
                           'Unknown':[None, '', 'Unknown']}


    addPolyAttributes(sgid, agrcAddPts_washCo, inputDict)
    addPolyAttributesLIR(sgid, agrcAddPts_washCo, washington_parcelsLIR, washington_remapLIR)
    updateAddPtID(agrcAddPts_washCo)
    addBaseAddress(agrcAddPts_washCo)
    deleteDuplicatePts(agrcAddPts_washCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_washCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Washington_ErrorPts.shp'), errorFlds, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_washCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def wayneCounty():
    wayneCoAddPts = r'..\Wayne\WayneCounty.gdb\WayneCoPts'
    agrcAddPts_wayneCo = r'..\Wayne\Wayne.gdb\AddressPoints_Wayne'

    cntyFldr = r'..\Wayne'
    wayneCoAddFLDS = ['HouseNumbe', 'Pre', 'Name', 'Type', 'Dir', 'Unit', 'SHAPE@', 'OBJECTID']

    checkRequiredFields(wayneCoAddPts, wayneCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_wayneCo).getOutput(0))
    archive_last_month(agrcAddPts_wayneCo)
    truncateOldCountyPts(agrcAddPts_wayneCo)

    ptTypeDict = {
        'Residential':['HOUSE', 'TRAILER'],
        'Commercial':['BUSINESS', 'MOTEL', 'RENTAL'],
        'Industrial':['GRAVEL PIT'],
        'Other':['AIRPORT', 'BLDG', 'BUILDING', 'CABIN', 'CAMPGRND', 'CELL TOWER', 'CHURCH', 'FAIR/RODEO GROUNDS/PARK', \
                 'FREMONT', 'GOVERNMENT', 'RESTROOM', 'SHED', 'TRAIL', 'TRAILHEAD', 'VACNET LAND', 'WATER TANK']
    }

    errorPtsDict = {}
    rdSet = createRoadSet('49055')

    with arcpy.da.SearchCursor(wayneCoAddPts, wayneCoAddFLDS) as sCursor,\
        arcpy.da.InsertCursor(agrcAddPts_wayneCo, agrcAddFLDS) as iCursor:
        for row in sCursor:
            if row[0] not in errorList and row[0].isdigit() == True:
                addNum = row[0]
                preDir = row[1]
                sName = row[2]
                if sName.startswith('SR '):
                    sName = sName.replace('SR', 'HWY')
                sType = returnKey(row[3], sTypeDir)
                if sType == '' and row[3].strip() != '':
                    print(f'OID {row[7]} BAD STREET TYPE')
                sufDir = row[4]
                unitID = row[5].strip()

                if sName[0].isdigit() == False:
                    sufDir = ''
                if sName[0].isdigit() == True:
                    sType = ''
                    if sName[-1].isdigit() == False:
                        sName = sName[:-1].strip()
                if sName.endswith((' ST', ' RD')):
                    sType = sName[-2:]
                    sName = sName[:-3]


                if sName.startswith('HWY ') == False and sName not in rdSet:
                    addressErrors = errorPtsDict.setdefault(f'{row[7]} | {sName}', [])
                    addressErrors.extend(['street name not found in roads', row[6]])


                if unitID == '':
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir}'
                else:
                    fullAdd = f'{addNum} {preDir} {sName} {sType} {sufDir} # {unitID}'

                fullAdd = ' '.join(fullAdd.split())

                loadDate = today
                modDate = None
                source = 'WAYNE COUNTY'

                shp = row[6]

                iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '', '', unitID,
                                   '', '', '49055', 'UT', '', '', '', '', source, loadDate, 'COMPLETE', '', modDate,
                                   '', '', '', shp))


    errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Wayne_ErrorPts.shp', 'Address', wayneCoAddPts)

    polyAttributesDict = {
    'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
    'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
    'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
    'USNG':['SGID.INDICES.NationalGrid', 'USNG', '']
    }

    addPolyAttributes(sgid, agrcAddPts_wayneCo, polyAttributesDict)
    updateAddPtID(agrcAddPts_wayneCo)
    addBaseAddress(agrcAddPts_wayneCo)
    deleteDuplicatePts(agrcAddPts_wayneCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_wayneCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Wayne_ErrorPts.shp'), errorPts, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_wayneCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def weberCounty():

    weberCoAddPts = r'..\Weber\WeberCounty.gdb\address_pts'
    agrcAddPts_weberCo = r'..\Weber\Weber.gdb\AddressPoints_Weber'
    cntyFldr = r'..\Weber'

    weberCoAddFLDS = ['ADDR_HN', 'ADDR_PD', 'ADDR_SN', 'ADDR_ST', 'ADDR_SD', 'PT_ADD', 'PLCMT_METH', 'WEBER_DATE', 'ADDRES_TYP', 
                      'ZIP', 'PARCEL_ID', 'EDIT_DATE', 'SHAPE@', 'OBJECTID_1', 'NAME', 'UNIT', 'UNIT_NUM', 'OBJECTID_1']

    ptTypeDict = {'Residential':['0', '1', '3'], 'Commercial':['2'], 'Other':['4', '5', '6', '7']}

    checkRequiredFields(weberCoAddPts, weberCoAddFLDS)
    old_point_count = int(arcpy.GetCount_management(agrcAddPts_weberCo).getOutput(0))
    archive_last_month(agrcAddPts_weberCo)
    truncateOldCountyPts(agrcAddPts_weberCo)

    errorPtsDict = {}
    rdSet = createRoadSet('49057')

    numberedUnits = ['APT', 'FLR', 'RM', 'STE', 'UNIT']

    badUnits = ['.', '-', ' ', 'VETERANS UPWARD', 'UPWARD BOUND', 'UNITS', 'A&B', 'SOCIAL SCIENCE', 'SECURITY GATE', 'RESIDENTIAL', 'RESIDENT',
                'RESIDENCE HALL', 'RECEIVING', 'PARKING', 'POLICE', 'PT', 'PRIVATE GATE', 'PKWY', 'PARKING UNIT', 'LIMITED CA',
                'INFORMATION', 'HURST CENTER', 'FINE ART STUDIO', 'COMMON AREA', 'COMMERCIAL', 'ANNEX', '00', '0', '-EVENT SITE',
                '2200-2600 ROAD EVENT', 'ATTN:', 'EVENT SITE -', 'EVENTS 100-300 25TH', 'EVENTS 100-400 25TH', 'CELL TOWER',
                'ELECTRICAL ENCLOSURE', 'COMM VAULT', 'INTERSECTION', 'LEASING OFFICE', 'LOTLOT', 'OUTDOOR SALES', 'RESTAURANT', 'PT',
                'RESTROOMS & PAVILION', 'SEASONAL OUTDOOR SALES', 'UTILITY POLE', 'UTILITY VAULT', 'WATER PUMP HOUSE', 'WATER VAULT',
                'FLEET', 'FLEET FUEL ISLAND', 'FACILITIES & COMM', 'FOOD CART PAD', 'PAD', 'PARKING AWNING EAST', 'PARKING AWNING WEST',
                'PARTS SHED', 'ROADBASE SHED', 'SALT DOME', 'SALT WASH', 'WASH BAY', 'TERMINAL BLDG', 'TSA', 'UTILITY BOX', 'SEWER & REFUSE',
                'SHOP', 'REFUSE', 'PARKING GARAGE', 'PLAYGROUND', 'POOLHOUSE', 'POOL HOUSE', 'PARK', 'OUT SALES', 'GREENHOUSE', 'FIELD HOUSE',
                'EVENT SITE', '<Null>', '<NULL>']

    reUnits = re.compile('|'.join(unitTypeList))

    fix_name = {'ADAMS AVENUE':'ADAMS AVE', 'HWY38':'HWY 39', 'IROQUOI':'IROQUOIS', 'CARBIOU':'CARIBOU'}

    stype_names = ['AIRPORT RD']

    with arcpy.da.SearchCursor(weberCoAddPts, weberCoAddFLDS) as sCursor_weber, \
        arcpy.da.InsertCursor(agrcAddPts_weberCo, agrcAddFLDS) as iCursor:
        for row in sCursor_weber:

            if removeNone(row[0]).strip().isdigit() == True and row[0] not in errorList and row[2] not in errorList or row[14] == 'West Haven Cove':
                if row[5] not in errorList:
                    address = parse_address.parse(row[5])

                addNum = row[0].strip()
                if addNum == '':
                    addNum = address.houseNumber
                
                addNumSuf = ''
                if len(addNum.split()) > 1:
                    addNumSuf = addNum.split()[1]
                    addNum = addNum.split()[0]

                sName = row[2].upper()
                if sName == 'MALLORY LOOP':
                    sName = 'MALLORY'
                if 'HWY' not in sName and sName not in rdSet:
                    addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[5]}', [])
                    addressErrors.extend(['street name not found in roads', row[12]])

                if sName == 'CENTURY MHP':
                    landmark = sName
                    sName = address.streetName
                    addNum = address.houseNumber
                else:
                    landmark = removeBadValues(row[14], errorList)

                preDir = returnKey(row[1], dirs)
                sType = returnKey(row[3], sTypeDir)
                if sType == 'WY':
                    sType = 'WAY'
                if row[4] == 'RD':
                    sType = 'RD'
                    addressErrors = errorPtsDict.setdefault(f'{row[4]} | {row[5]}', [])
                    addressErrors.extend(['bad value in ADDR_SD', row[12]])

                if sName == 'HORIZON RUN':
                    sType = 'RD'

                if sName.endswith((' N', ' S', ' E', ' W')):
                    sName = sName[:-2]

                sufDir = returnKey(removeNone(row[4]).strip(), dirs)

                # if preDir != '' and sufDir != '':
                #     sType = ''

                if sName[-1].isdigit() and sufDir == '':
                    sufDir = removeNone(address.suffixDirection)

                if sName == '1097 W GOODYEAR':
                    addNum = '1121'
                    preDir = 'W'
                    sName = 'GOODYEAR'
                    sType = 'AVE'
                if sName == '29TH ST':
                    sName = '29TH'
                    sType = 'ST'
                if sName == 'RULON WHITE':
                    sufDir = ''
                    sType = 'BLVD'

                if sName[-1].isdigit():
                    sType = ''
                if sType != '':
                    sufDir = ''
                if 'HWY' in sName:
                    sType = ''
                    sufDir = ''
                
                if sName in fix_name:
                    sName = fix_name[sName]
                if sName in stype_names:
                    long_sname = clean_street_name(sName)
                    sName = long_sname.name
                    sType = long_sname.type
                    print(sName)


                if preDir == sufDir and sType == '' and preDir != '':
                    print (f'preDir({preDir}) = sufDir({sufDir})')
                    addressErrors = errorPtsDict.setdefault(f'{row[1]} {row[4]} | {row[5]}', [])
                    addressErrors.extend(['prefix = suffix', row[12]])
                    continue

                unitType = ''
                building = ''
                ptType = returnKey(str(row[8]), ptTypeDict)

                unitTypeRaw = removeBadValues(removeNone(row[15]).upper(), badUnits).strip('#').strip()
                unitId = removeBadValues(removeNone(row[16]).upper(), badUnits).strip('#').strip().replace('BLDG ', '').strip()

                unitSearch = re.search(reUnits, unitTypeRaw)
                if unitSearch != None:
                    unitType = unitSearch.group(0)
                    typeRemainder = unitTypeRaw.replace(f'{unitType}', '').strip()

                    if unitTypeRaw.strip(unitType) != '':
                        unitId = f'{typeRemainder}{unitId}'.strip()

                    if 'BLDG' in unitType:
                        building = ''
                        unitType = ''
                        unitId = row[16]

                    if unitType == 'SUITE':
                        unitType = 'STE'

                else:
                    if unitTypeRaw == '1' and unitId == '':
                        unitTypeRaw = ''
                    if unitTypeRaw != unitId:
                        unitId = f'{unitTypeRaw}{unitId}'.strip()

                if unitId.startswith('BAY'):
                    unitId = f'{unitId[:3]} {unitId[3:].strip()}'

                if len(unitId) > 12:
                    unitId = ''
                if unitId == '' and unitType not in ['BSMT', 'FRNT', 'REAR']:
                    unitType = ''

                # if row[15] == 'BLDG' and ' ' in unitId:
                #     if 'BLDG' in row[16]:
                #         building = row[16]
                #         unitId = ''
                #     else:
                #         building = f'BLDG {row[16].split()[0]}'
                #         unitId = row[16].replace(row[16].split()[0], '').strip()
                #         if 'STE' in row[16]:
                #             unitType = 'STE'
                #             unitId = row[16].split()[-1]
                #         # else:
                #         #     unitType = ''

                unitId = unitId.replace('PKWY ', '').strip()

                if row[15] == 'BLDG' and ' ' not in row[16]:
                    unitType = ''


                if unitId.startswith(('BAY', 'BLDG')):
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} {building} {unitType} {unitId}'

                elif unitType == 'BLDG' and unitId != '':
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} # {unitId}'

                elif unitType in ['FRNT', 'REAR'] and unitId == '':
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} {unitType}'

                elif unitType != '' and unitId != '':
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} {unitType} {unitId}'

                elif unitId != '':
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} # {unitId}'

                else:
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} {unitType} {unitId}'

                fullAdd = ' '.join(fullAdd.split())

                parcel = row[10]
                if parcel in ['0', ' ', 'Point']:
                    parcel = ''
                loadDate = today
                modDate = row[11]
                shp = row[12]


                if row[3] == '' and row[4] == '':
                    addressErrors = errorPtsDict.setdefault(row[5], [])
                    addressErrors.extend(['missing street type?', row[12]])
                if removeNone(row[2]).upper() not in removeNone(row[5]).upper():
                    addressErrors = errorPtsDict.setdefault(f'{row[2]} | {row[5]}', [])
                    addressErrors.extend(['mixed street names', row[12]])

                iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, landmark, building, unitType, \
                                  unitId, '', '', '49057', 'UT', '', ptType, '', parcel, 'WEBER COUNTY', loadDate, 'COMPLETE', \
                                  '', modDate, '', '', '', shp))

    
    errorPts = createErrorPts(errorPtsDict, cntyFldr, 'Weber_ErrorPts.shp', 'Address', weberCoAddPts)

    weber_remapLIR = {'Agricultural':['Agricultural', 'Greenbelt'],
                      'Commercial':['Commercial',  'Commercial - Office Space', 'Commercial - Retail'],
                      'Industrial':['Industrial', 'Commercial - Industrial'],
                      'Mixed Use':['Mixed Use'],
                      'Other':['Tax Exempt', 'Tax Exempt - Charitable Organization or Religious',
                               'Tax Exempt - Government', 'Undevelopable', 'Vacant', 'Privilege Tax', 'Personal Property'],
                      'Residential':['Residential', 'Commercial - Apartment & Condo'],
                      'Unknown':[None, '', 'Unknown']}

    polyAttributesDict = {
                        'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
                        'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
                        'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
                        'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
                        'PtType': ['SGID.CADASTRE.Parcels_Weber_LIR', 'PROP_CLASS', weber_remapLIR]
                        }
    
    weber_parcelsLIR = {'PtType': ['SGID.CADASTRE.Parcels_Weber_LIR', 'PROP_CLASS']}

    addPolyAttributes(sgid, agrcAddPts_weberCo, polyAttributesDict)
    updateAddPtID(agrcAddPts_weberCo)
    addPolyAttributesLIR(sgid, agrcAddPts_weberCo, weber_parcelsLIR, weber_remapLIR)
    addBaseAddress(agrcAddPts_weberCo)
    deleteDuplicatePts(agrcAddPts_weberCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    dupePts = returnDuplicateAddresses(agrcAddPts_weberCo, ['UTAddPtID', 'SHAPE@'])
    updateErrorPts(os.path.join(cntyFldr, 'Weber_ErrorPts.shp'), errorPts, dupePts)

    new_point_count = int(arcpy.GetCount_management(agrcAddPts_weberCo).getOutput(0))
    print (f'Old count {old_point_count}, new count {new_point_count}')


def dabc_pts():
    dabc_pts = r'..\DABC\AddressPointAdditions.gdb\Pt_Additions_20241212'
    agrcAddPts_DABC = r'..\DABC\dabc.gdb\AddressPoints_DABC'
    cntyFldr = r'..\DABC'

    dabc_flds = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType',
                 'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State',
                 'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'USNG', 'SHAPE@']

    checkRequiredFields(dabc_pts, dabc_flds)
    #archive_last_month(agrcAddPts_DABC)
    truncateOldCountyPts(agrcAddPts_DABC)

    with arcpy.da.SearchCursor(dabc_pts, dabc_flds) as sCursor,\
        arcpy.da.InsertCursor(agrcAddPts_DABC, agrcAddFLDS) as iCursor:

        for row in sCursor:
            add_num = removeNone(row[3])
            add_num_suf = ''
            pre_dir = removeNone(row[5])
            st_name = removeNone(row[6])
            st_type = removeNone(row[7])
            suf_dir = removeNone(row[8])
            unit_type = removeNone(row[11])
            unit_id = removeNone(row[12])
            zip = removeNone(row[14])
            load_date = today
            shp = row[23]

            if st_name.startswith('HWY ') and st_type == 'HWY':
                st_type = ''

            if unit_type != '' and unit_id != '':
                full_add = f'{add_num} {add_num_suf} {pre_dir} {st_name} {st_type} {suf_dir} {unit_type} {unit_id}'

            elif unit_id != '':
                full_add = f'{add_num} {add_num_suf} {pre_dir} {st_name} {st_type} {suf_dir} # {unit_id}'

            else:
                full_add = f'{add_num} {add_num_suf} {pre_dir} {st_name} {st_type} {suf_dir} {unit_type} {unit_id}'

            full_add = ' '.join(full_add.split())

            iCursor.insertRow(('', '', full_add, add_num, '', pre_dir, st_name, st_type, suf_dir, '', '', unit_type,
                               unit_id, '', zip, '', 'UT', '', '', '', '', 'DABC', load_date, 'COMPLETE', '',
                               load_date, '', '', '', shp))

        polyAttributesDict = {
                        'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
                        'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
                        'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
                        'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
                        'CountyID': ['SGID.BOUNDARIES.Counties', 'FIPS_STR', '']
                        }

    addPolyAttributes(sgid, agrcAddPts_DABC, polyAttributesDict)
    updateAddPtID(agrcAddPts_DABC)
    addBaseAddress(agrcAddPts_DABC)


def hill_AFB():
    hill_pts = r'..\Davis\911MTRL_Hill.gdb\HAFB_only'
    agrcAddPts_HillAFB = r'..\Davis\Davis.gdb\AddressPoints_HillAFB'

    hill_flds = ['Add_Number', 'AddNum_Suf', 'St_PreDir', 'StreetName', 'St_PosTyp', 'Unit', 'SHAPE@']

    truncateOldCountyPts(agrcAddPts_HillAFB)

    loadDate = today

    with arcpy.da.SearchCursor(hill_pts, hill_flds) as scursor_hill, \
        arcpy.da.InsertCursor(agrcAddPts_HillAFB, agrcAddFLDS) as icursor:

        for row in scursor_hill:
            add_num = row[0]
            add_num_suf = removeNone(row[1]).upper()
            if row[5] in ['A', 'B']:
                add_num_suf = row[5]
            pre_dir = removeNone(row[2]).upper()
            street_name = row[3].upper()
            street_type = returnKey(removeNone(row[4]).upper(), sTypeDir)
            shp = row[6]

            full_add = f'{add_num} {add_num_suf} {street_name} {street_type}'
            full_add = ' '.join(full_add.split())

            icursor.insertRow(('', '', full_add, add_num, add_num_suf, pre_dir, street_name, street_type, '', '', '', \
                               '', '', '', '', '', 'UT', 'Unknown', 'Unknown', 'Unknown', '', 'HAFB', loadDate, \
                               'COMPLETE', '', None, '', '', '', shp))
            
    inputDict = {
        'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
        'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
        'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
        'USNG':['SGID.INDICES.NationalGrid', 'USNG', ''],
        'CountyID':['SGID.BOUNDARIES.Counties', 'FIPS_STR', '']
    }

    addPolyAttributes(sgid, agrcAddPts_HillAFB, inputDict)
    updateAddPtID(agrcAddPts_HillAFB)
    addBaseAddress(agrcAddPts_HillAFB)
    deleteDuplicatePts(agrcAddPts_HillAFB, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])
    


def checkRequiredFields(inCounty, requiredFlds):

    countyFlds = arcpy.ListFields(inCounty)
    countyFldList = []

    for countyFld in countyFlds:
        countyFldList.append(countyFld.name)
    for fld in requiredFlds:
        if fld not in countyFldList and fld != 'SHAPE@':
            sys.exit(fld + ' Is a requided field MISSING from ' + inCounty)




#beaverCounty()   #Complete w/error points
#boxElderCounty()  #Complete w/error points
#cacheCounty()  #Complete w/error points
#carbonCounty() #Complete
#daggettCounty() #Complete w/error points
#davisCounty()  #Complete
#davisCounty_alias()
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
#SanJuanCounty()
#sanpeteCounty()
#sevierCounty()
#summitCounty()
#tooeleCounty()    #Complete
#uintahCounty()
utahCounty() #Complete
#wasatchCounty()  #Complete w/error points
#washingtonCounty()  #Complete
#wayneCounty()
#weberCounty()   #Complete
#dabc_pts()
#hill_AFB()









