
from DeleteDuplicatePoints import deleteDuplicatePts


pts = r'C:\ZBECK\Addressing\Utah\Utah.gdb\AddressPoints_Utah'
flds = ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID']
#flds = ['FULLADDR', 'SHAPE@WKT', 'OBJECTID']

deleteDuplicatePts(pts, flds)