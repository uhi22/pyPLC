
# Hyundai Ioniq (2018) investigations

## What PLC chip is used?

QCA7005.
The software version is MAC-QCA7005-1.1.0.730-04-20140815-CS (found by sending GetSwVersion).

## Which module contains the PLC interface, and where is it located?
`
In the Kona, there is a CCM (Charge Control Module)
https://parts.hyundaicanada.com/p/Hyundai_2021_Kona-ELECTRIC-GL-STD-5P/CHARGE-CONTROL-MODULE-PLC/125385163/91950K4510.html
Part Number: 91950K4510. In the picture this is 91950Q 

For the Ioniq we find
https://www.ebay.de/itm/394528814451?_trkparms=amclksrc%3DITM%26aid%3D1110006%26algo%3DHOMESPLICE.SIM%26ao%3D1%26asc%3D20201210111314%26meid%3Dd4a895de93cc438da026c4488e103aac%26pid%3D101195%26rk%3D3%26rkt%3D12%26sd%3D155444727217%26itm%3D394528814451%26pmt%3D1%26noa%3D0%26pg%3D2047675%26algv%3DSimplAMLv11WebTrimmedV3MskuWithLambda85KnnRecallV1V4V6ItemNrtInQueryAndCassiniVisualRankerAndBertRecall&_trksid=p2047675.c101195.m1851&amdata=cksum%3A394528814451d4a895de93cc438da026c4488e103aac%7Cenc%3AAQAIAAABQA2rugFlOq3qu1cLac%252F%252Fk6Vp0Oa0HaJIqoXKeIiOR%252BTUgsSvHaeyPxKYu6UqHqq7GaGyKVqHQnjeiiXcQpMGw2t3aB%252BssGfjtIWOBj8wExc7oYYP7xGMyQCrHDyDaSaWjB1CueI3A94n0yxXX5dx5gDO4pgNGYOGnz%252BnDlP61rIVr1Utg%252B1XyXIRruqox9MiB0wwnlIyoFSPB8wRYRZrLIzMxrPqwAj0dT%252FCbYeEsaCM46Xhbt%252BZssKJD2DuF1cyqXaYHd3QCKHQpwIVLe51hi%252B9vriq8dHlSRhB1xCOULlON4DO4I5C62jCqCT%252BVILcAv0JbaNXT81CXee8ym0PSIIaz5QEm1bhRyrfz2Nj6cFvyFRHnSasf8HUuqPyt3CNY1zORaJc4AzorOsluSFm1oSeH5KOKHEsYZPKm5LShPjI%7Campid%3APL_CLK%7Cclp%3A2047675

Fotos of the Kona controller: https://openinverter.org/forum/viewtopic.php?t=1195

For the Ioniq face lift:
91950-G7300
Hyundai Ioniq EV Ladesteuermodul ECU 91950-G7300 2021 RHD 17709538
https://www.hyundaipartsdeal.com/genuine/hyundai-charge-control-module-plc~91950-g7300.html

For the Ioniq vFL:
https://www.ebay.com/itm/304610337175
OEM Charging Control Module PLC Hyundai Ioniq electric 2017-2019 / 91950-G7200
https://www.hyundaipartsdeal.com/genuine/hyundai-charge-control-module-plc~91950-g7200.html

In https://www.hyundaipartsdeal.com/genuine/hyundai-charge-control-module-plc~91950-g7200.html?vin=&make=Hyundai&model=Ioniq&year=2018&submodel=Electric&extra1=&extra2=&filter=() it looks like this module is in or below the fuse box in the engine compartment.

In
https://autotechnician.co.uk/hyundai-ioniq-electric-ae-ev-2016-present/
they write: A Charge Control Module is located under the front passenger seat. It converts the PLC communication from the external charging post into CAN that can be understood by the rest of the car. 
But: Under the passenger seat, there is the seat control unit:  Hyundai Ioniq Steuergerät Sitz 88196G2200. No other control unit found there.

In
https://openinverter.org/forum/viewtopic.php?p=19675&sid=b0b1e32820cf0af9227c684f17bb82b5#p19675
there is the discussion, that the PCB is nearly the same between Kona and Ioniq.

In
https://openinverter.org/forum/viewtopic.php?p=20110#p20110 there is the Kona wiring diagram with pinout.

And for the Ioniq: https://openinverter.org/forum/viewtopic.php?p=20118#p20118. The CP of the CCM connects via a green wire to connector P111.8 (male).
Also CP is pin7 of the OBC, with a green wire links to pin11 of P52.

In https://openinverter.org/forum/viewtopic.php?p=20132#p20132 there is a foto which shows the unit under the DRIVER seat, below the left guiding rail, screwed on the floor pan.





