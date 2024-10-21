ZPL_BT_SMALL = """
^Q20,3
^W30
^H8
^P1
^S3
^AD
^C1
^R0
~Q+0
^O0
^D0
^E18
~R255
^L
Dy2-me-dd
Th:m:s
Dy2-me-dd
Th:m:s
XRB30,30,5,0,33
~1code
AF,30,150,1,1,0,0,date_party
AE,160,90,1,1,0,0,number_party
AE,160,30,1,1,0,0,sequence_number
E

"""

ZPL_MB_BIG = """
^Q20,3
^W30
^H8
^P1
^S3
^AD
^C1
^R0
~Q+0
^O0
^D0
^E18
~R255
^L
Dy2-me-dd
Th:m:s
XRB30,32,5,0,87
~1code
AD,244,195,1,1,0,3E,date_party
AD,300,131,1,1,0,3E,number_party
E

"""

ZPL_LF_BIG = """
^Q20,3
^W30
^H8
^P1
^S3
^AD
^C1
^R0
~Q+0
^O0
^D0
^E18
~R255
^L
Dy2-me-dd
Th:m:s
XRB30,32,5,0,87
~1code
AE,230,218,1,1,0,3E,date_party
AE,288,155,1,1,0,3E,number_party
E

"""

ZPL_ML_BIG = """
^Q20,3
^W30
^H8
^P1
^S3
^AD
^C1
^R0
~Q+0
^O0
^D0
^E18
~R255
^L
Dy2-me-dd
Th:m:s
XRB30,32,5,0,87
~1code
AD,244,195,1,1,0,3E,date_party
AD,300,131,1,1,0,3E,number_party
E

"""