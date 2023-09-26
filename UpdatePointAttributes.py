import arcpy
import os

sgid = r'C:\sde\SGID_internal\SGID_agrc.sde'

def returnKey(word, d):
    if word == None:
        word = ''
    for key, value in d.items():
        # if word == '':
        #     return ''
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

def addPolyAttributes(sgid, in_features, near_layers_dict):

    arcpy.env.workspace = os.path.dirname(in_features)
    arcpy.env.overwriteOutput = True

    nearFLDS = ['IN_FID', 'NEAR_FID', 'NEAR_DIST']

    for lyr in near_layers_dict:

        near_features = sgid + '\\' + near_layers_dict[lyr][0]
        print (near_features)

        near_table = f'{lyr}_nearTbl'

        arcpy.GenerateNearTable_analysis(in_features, near_features, near_table, '1 Meters', 'NO_LOCATION', 'NO_ANGLE', 'CLOSEST')

        feature_to_near_features_dict = {}
        near_features_dict = {}

        near_feature_flds = ['OBJECTID', near_layers_dict[lyr][1]]

        with arcpy.da.SearchCursor(near_table, nearFLDS) as sCursor:
            for row in sCursor:
                feature_to_near_features_dict[row[0]] = row[1]
                near_features_dict.setdefault(row[1])
        with arcpy.da.SearchCursor(near_features, near_feature_flds) as sCursor:
            for row in sCursor:
                if row[0] in near_features_dict:
                    near_features_dict[row[0]] = row[1]

        ucursorFLDS = ['OBJECTID', lyr]
        ucursor = arcpy.da.UpdateCursor(in_features, ucursorFLDS)
        
        for urow in ucursor:
            try:
                if feature_to_near_features_dict[urow[0]] in near_features_dict:
                    if near_layers_dict[lyr][2] == '':
                        urow[1] = near_features_dict[feature_to_near_features_dict[urow[0]]]
                    else:
                        #print(returnKey(near_features_dict[feature_to_near_features_dict[urow[0]]], near_layers_dict[lyr][2]))
                        urow[1] = returnKey(near_features_dict[feature_to_near_features_dict[urow[0]]], near_layers_dict[lyr][2])
                        print(urow[1])
            except:
                continue
                #urow[1] = ''

            ucursor.updateRow(urow)

        arcpy.Delete_management(near_table)


def updateAddPtID(inPts):
    flds = ['AddSystem', 'UTAddPtID', 'FullAdd']
    with arcpy.da.UpdateCursor(inPts, flds) as uCursor:
        for urow in uCursor:
            urow[1] = f'{urow[0]} | {urow[2]}'
            uCursor.updateRow(urow)

    del uCursor

def updateField(inPts, fld, dict):
    # def returnKey(word, dict):
    #     if word == None:
    #         word = ''
    #     for key, value in dict.items():
    #         if word == '':
    #             return ''
    #         if word == key:
    #             return key
    #         if type(value) is str:
    #             if word == value:
    #                 return key
    #         else:
    #             for v in value:
    #                 if word == v:
    #                     return key
    #     return ''

    with arcpy.da.UpdateCursor(inPts, fld) as uCursor:
        for urow in uCursor:
            if urow[0] in dict:
                print(f'Changed {urow[0]} to {dict[urow[0]]}')
                urow[0] = dict[urow[0]]
            # urow[0] = returnKey(urow[0], dict)
                uCursor.updateRow(urow)
                

    del uCursor