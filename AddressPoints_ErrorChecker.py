import arcpy, agrc
from agrc import parse_address
from pathlib import Path
from checkAddressFields import checkStreetName
from checkAddressFields import createStreetDict
from checkAddressFields import dirCheck
from checkAddressFields import checkStreetType
from checkAddressFields import checkAddNum
from checkAddressFields import flagDuplicates
from checkPtsAgainstPoly import checkInsidePolys
from checkPtsAgainstPoly import checkOutsidePolys
from UpdatePointAttributes import addPolyAttributes


sgid = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde'))
zips = sgid + '\\SGID.BOUNDARIES.ZipCodes'
munis = sgid + '\\SGID10.BOUNDARIES.Municipalities'
addrSys = sgid + '\\SGID10.LOCATION.AddressSystemQuadrants'

fipsDict = {'Beaver': '49001', 'Box Elder': '49003', 'Cache': '49005', 'Carbon': '49007', 'Daggett': '49009', \
           'Davis': '49011', 'Duchesne': '49013', 'Emery': '49015', 'Garfield': '49017', 'Grand': '49019', \
           'Iron': '49021', 'Juab': '49023', 'Kane': '49025', 'Millard': '49027', 'Morgan': '49029', \
           'Piute': '49031', 'Rich': '49033', 'Salt Lake': '49035', 'San Juan': '49037', 'Sanpete': '49039', \
           'Sevier': '49041', 'Summit': '49043', 'Tooele': '49045', 'Uintah': '49047', 'Utah': '49049', \
           'Wasatch': '49051', 'Washington': '49053', 'Wayne': '49055', 'Weber': '49057'}

blankVals = ['', ' ', None]

unitTypeDict = {'APT':'APARTMENT', 'BSMT':'BASEMENT', 'BLDG':'BUILDING', 'DEPT':'DEPARTMENT', 'FL':'FLOOR', \
               'FRNT':'FRONT', 'HNGR':'HANGAR', 'LBBY':'LOBBY', 'OFC':'OFFICE', \
               'PH':'PENTHOUSE', 'PIER':'PIER', 'REAR':'REAR', 'RM':'ROOM', \
               'SPC':'SPACE', 'STE':'SUITE', 'TRLR':'TRAILER', 'UNIT':'UNIT'}

def formatString(word):
    vals = [None, ' ']
    if word in vals:
        word = ''
    return word

def checkFlagField(inFC):
    fldList = arcpy.ListFields(inFC)
    for fld in fldList:
        if fld.name == 'AGRC_FLAG':
            continue
        else:
            arcpy.AddField_management(inFC, 'AGRC_FLAG', 'TEXT', '#', '#', '250')

def add_ugrc_zips(in_county_pts):
    county_flds = arcpy.ListFields(in_county_pts)
    if 'UGRC_ZIPS' not in county_flds:
        arcpy.AddField_management(in_county_pts, 'UGRC_ZIPS', 'TEXT', '#', '#', '10')

    zip_dict = {'UGRC_ZIPS':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', '']}
    addPolyAttributes(sgid, in_county_pts, zip_dict)

in_pts = r'C:\ZBECK\Addressing\Weber\WeberCounty.gdb\address_pts'

add_ugrc_zips(in_pts)


def checkBoxElderPts(addPts, coName):

    addFlds = ['FullAddr', 'HouseNum', 'PreDir', 'StreetName', 'StreetType', 'SufDir', 'UnitNumber', 'City', 'ZipCode',\
               'UnitType', 'AGRC_FLAG', 'OBJECTID']

    citySplitDict = {'PERRY':'-3', 'OGDEN':'-3', 'GROUSE CREEK':'-4', 'HANSEL VALLEY':'-4', 'TREMONTON':'-3', 'ELWOOD':'-3', 'MANTA':'-3', \
                'DEWEYVILLE':'-3', 'LYNN':'-3', 'BOTHWELL':'-3', 'GARLAND':'-3', 'CLEAR CREEK':'-4', 'COLLINSTON':'-3', 'PLYMOUTH':'-3', \
                'HOWELL':'-3', 'SNOWVILLE':'-3', 'STANDROD':'-3', 'FIELDING':'-3', 'WASHAKIE':'-3', 'YOST':'-3', 'ROSETTE':'-3', 'PENROSE':'-3', \
                'GRANTSVILLE':'-3', 'PORTAGE':'-3', 'WILLARD':'-3', 'PARK VALLEY':'-4', 'THATCHER':'-3', 'CORINNE':'-3', 'ETNA':'-3', \
                'RIVERSIDE':'-3', 'BEAVER DAM':'-4', 'LUCIN':'-3', 'SOUTH WILLARD':'-4', 'HONEYVILLE':'-3', 'BEAR RIVER CITY':'-5', \
                'BRIGHAM CITY':'-4', 'MANTUA':'-3'}

    checkFlagField(addPts)
    #createStreetDict(fipsDict[coName])

    with arcpy.da.UpdateCursor(addPts, addFlds) as addPts_uCursor:
        for addRow in addPts_uCursor:
            fullAdd = addRow[0]
            addNum = addRow[1]
            preDir = addRow[2]
            sName = addRow[3]
            sType = addRow[4]
            sufDir = addRow[5]
            unitNum = addRow[6]
            city = addRow[7]
            zip = addRow[8]
            unitType = addRow[9]
            addSys = addRow[10]
            oId = addRow[11]

            addressOnly = fullAdd.split(' ')[:int(citySplitDict[city])]
            addressOnly = ' '.join(addressOnly)

            prs_fullAdd = parse_address.parse(addressOnly)

            prs_addNum = formatString(prs_fullAdd.houseNumber)
            prs_pDir = formatString(prs_fullAdd.prefixDirection)
            prs_sName = formatString(prs_fullAdd.streetName)
            prs_sType = formatString(prs_fullAdd.suffixType)
            prs_sDir = formatString(prs_fullAdd.suffixDirection)

            fullAddFLG = ''

            if prs_addNum != addNum:
                fullAddFLG = '{} {}'.format(fullAddFLG, '[FullAddr <> HouseNum]')
            if preDir.strip() != prs_pDir:
                fullAddFLG = '{} {}'.format(fullAddFLG, '[FullAddr <> PreDir]')
            if unitType in blankVals:
                if sName != prs_sName:
                    fullAddFLG = '{} {}'.format(fullAddFLG, '[FullAddr <> StreetName]')
            if sType.strip() != prs_sType:
                fullAddFLG = '{} {}'.format(fullAddFLG, '[FullAddr <> StreetType]')

            for unit in unitTypeDict:
                if ' ' + unit in fullAdd and unit != unitType:
                    fullAddFLG = '{} {}'.format(fullAddFLG, '[FullAddr <> UnitType]')

            # if sufDir.strip() != prs_sDir:
            #     fullAddFLG = '{} {}'.format(fullAddFLG, '[FullAddr <> SufDir]')
            #     #print '{} [{}] [{}]'.format(oId, sufDir, prs_sDir)


            # sNameFLG = checkStreetName(sName, zip)
            preDirFLG = dirCheck(preDir)
            sufDirFLG = dirCheck(sufDir)
            sTypeFLG = checkStreetType(sType)
            addNumFLG = checkAddNum(addNum)

            addRow[10] = '{} {} {} {} {}'.format(fullAddFLG, preDirFLG, sufDirFLG, sTypeFLG, addNumFLG)
            addRow[10] = ' '.join(addRow[10].split())


            addPts_uCursor.updateRow(addRow)

    # checkInsidePolys(munis, 'NAME', addPts, ['City', 'AGRC_FLAG'])
    # checkInsidePolys(zips, 'ZIP5', addPts, ['ZipCode', 'AGRC_FLAG'])
    # checkInsidePolys(addrSys, 'GRID_NAME', addPts, ['ADDSYS_AGR', 'AGRC_FLAG'])

    # checkOutsidePolys(munis, 'NAME', addPts, ['City', 'AGRC_FLAG'], coName)
    # checkOutsidePolys(addrSys, 'GRID_NAME', addPts, ['ADDSYS_AGR', 'AGRC_FLAG'], coName)


def checkCachePts(addPts, coName):

    addFlds = ['objectid', 'addsystem', 'fulladd', 'addnum', 'addnumsuffix', 'prefixdir', 'streetname', 'aliasstreetname', \
               'streettype', 'suffixdir', 'city', 'zipcode', 'AGRC_FLAG']

    checkFlagField(addPts)
    createStreetDict(fipsDict[coName])

    with arcpy.da.UpdateCursor(addPts, addFlds) as addPts_uCursor:
        for addRow in addPts_uCursor:

            oID = addRow[0]
            addSys = addRow[1]
            fullAdd = addRow[2]
            addNum = addRow[3]
            addNumSuf = addRow[4]
            preDir = addRow[5]
            sName = addRow[6]
            asName = addRow[7]
            sType = addRow[8]
            sufDir = addRow[9]
            city = addRow[10]
            zip = addRow[11]
            agrcFlag = addRow[12]

            if fullAdd not in blankVals:

                padd = parse_address.parse(fullAdd)
                parsed_sName = padd.streetName
                parsed_pdir = padd.prefixDirection

                if parsed_sName != sName:
                    mixedStreetsFlag = '[fulladd <> streetname]'
                else:
                    mixedStreetsFlag = ''

                sNameFLG = checkStreetName(sName, addSys)
                preDirFLG = dirCheck(preDir)
                sufDirFLG = dirCheck(sufDir)
                sTypeFLG = checkStreetType(sType)
                addNumFLG = checkAddNum(addNum)

                addRow[12] = '{} {} {} {} {} {}'.format(sNameFLG, preDirFLG, sufDirFLG, sTypeFLG, addNumFLG, mixedStreetsFlag)
                addRow[12] = ' '.join(addRow[12].split())

                addPts_uCursor.updateRow(addRow)

            elif fullAdd in blankVals:
                addRow[12] = '[no address]'
                addPts_uCursor.updateRow(addRow)



    flagDuplicates(addPts, 'objectid', 'addsystem', 'fulladd', 'AGRC_FLAG')
    # checkInsidePolys(munis, 'NAME', addPts, ['city', 'AGRC_FLAG'])
    # checkInsidePolys(zips, 'ZIP5', addPts, ['zipcode', 'AGRC_FLAG'])


def checkMillardPts(addPts, coName):
    addFlds = ['OBJECTID_1', 'PREFIX', 'ROAD_NAME', 'ROAD_TYPE', 'HOUSE_NO', 'COMMUNITY', 'AGRC_FLAG']
    typeList = ['AVE', 'BLVD', 'CIR', 'CT', 'DR', 'HWY', 'JCT', 'LN', 'PKWY', 'PL', 'RD', 'ST', 'TRL', 'HIGHWAY']

    checkFlagField(addPts)

    with arcpy.da.UpdateCursor(addPts, addFlds) as addPts_uCursor:
        for row in addPts_uCursor:
            sufFLG = ''
            nameFLG = ''
            addNumFLG = checkAddNum(row[4])
            pDirFLG = dirCheck(row[1])
            sTypeFLG = checkStreetType(row[3])

            if row[2] not in blankVals:
                if ' ' not in row[2]:
                    if row[2][0].isdigit() and row[2][-1].isdigit() == False:
                        sufFLG = '[Bad Suffix]'
                if ' ' in row[2] and row[2].split()[-1] in typeList:
                    nameFLG = '[Street type in name]'
                if row[2][0].isdigit() == False and not row[2].startswith('HIGHWAY') and row[3] == ' ':
                    sTypeFLG = '[Missing street type]'
                if row[2][0].isdigit() and row[1] == ' ':
                    print(row[2])
                    pDirFLG = '[Missing prefix]'

            row[6] = '{}{}{}{}{}'.format(sufFLG, nameFLG, addNumFLG, pDirFLG, sTypeFLG)

            addPts_uCursor.updateRow(row)






    #flagDuplicates(addPts, 'OBJECTID', 'COMMUNITY', 'fulladd', 'AGRC_FLAG')







#checkCachePts(r'C:\ZBECK\Addressing\Cache\cache_MAL.gdb\cache_MAL_7_6_2016', 'Cache')
#checkBoxElderPts(r'C:\ZBECK\Addressing\BoxElder\MonthlyUpdates\BECO_ADDRESS_POINT_UPDATE_AUG_2016.shp', 'Box Elder')
#checkMillardPts(r'C:\ZBECK\Addressing\Millard\MillardSource.gdb\Addresses_Rooftops', 'Millard')


