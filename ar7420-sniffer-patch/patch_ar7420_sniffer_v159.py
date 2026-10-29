#!/usr/bin/env python3
"""Patch the official TP-Link TL-PA4010P V2 firmware (1.1.0.844) into the pyPLC ISO15118 sniffer build
AR7420-SNIFFER-v159. Runs offline with the Python standard library only; touches no hardware and contains no Qualcomm or
TP-Link firmware bytes -- only the bytes this project changed (offset + new bytes) plus this script.

You provide the stock firmware yourself (you must have a lawful copy):
  TP-Link package : https://static.tp-link.com/resources/software/TL-PA4010PKIT_V2_130807.zip
  file inside zip : MAC-7420-v1.1.0-01-X-FINAL.nvm  (SHA-256 398f29834eaa51b0bac2ba660c74da83b6274f1ffef1400ace1c59b00f7f8d27)
This script writes a patched .nvm with the same SHA-256 as the bench-validated build (af67828a2b223a8da0dc6561399f8a827280c5b8e0a9940a7ba605cfc64c476b).

Flash it over Ethernet with YOUR OWN modem config (PIB) -- no PIB is shipped:
  1. back up:  plctool -i <iface> -p my.pib <modem-mac>
  2. flash:    plctool -i <iface> -P my.pib -N ar7420_sniffer_v159.nvm -R <modem-mac>
  3. rollback: re-flash the stock MAC-7420-v1.1.0-01-X-FINAL.nvm the same way.

!!! WARNING -- read before flashing !!!
 * Flashing firmware can brick the modem. Recovery may need SPI access (open the case / solder). Only you are
   responsible. There is no warranty.
 * This build is a SNIFFER: it joins foreign HomePlug-AV networks it overhears and forwards other parties'
   SLAC / SDP / V2G traffic to its host. Use it only on networks and vehicles you are authorised to monitor.
 * Tested only on TP-Link TL-PA4010P V2 (AR7420, firmware 1.1.0.844) with Python 3.x on Windows 10 / Raspberry Pi OS (measure WSL before release).

Usage:  python patch_ar7420_sniffer_v159.py <stock-1.1.0.844.nvm> [-o ar7420_sniffer_v159.nvm]
"""
import argparse, base64, hashlib, lzma, struct, sys

STOCK_SHA = "398f29834eaa51b0bac2ba660c74da83b6274f1ffef1400ace1c59b00f7f8d27"
BUILD_SHA = "af67828a2b223a8da0dc6561399f8a827280c5b8e0a9940a7ba605cfc64c476b"
LOAD = 0x208400
DEC = [{"id": lzma.FILTER_LZMA1, "dict_size": 4096, "lc": 3, "lp": 0, "pb": 2}]
ENC = [{"id": lzma.FILTER_LZMA1, "dict_size": 4096, "lc": 3, "lp": 0, "pb": 2, "mf": lzma.MF_BT2, "nice_len": 273}]
RECORDS = [(a, base64.b64decode(b)) for a, b in [
    (0x20cc98, 'IPDu/Q=='),
    (0x217d54, '6sQi'),
    (0x217ec4, '6sQi'),
    (0x217f04, '6sQi'),
    (0x2189a8, '6sQi'),
    (0x219004, '6sQi'),
    (0x2192b0, '6sQi'),
    (0x21f1f0, '6sQi'),
    (0x2249a4, 'AAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x2249b8, 'AAAAAAAA'),
    (0x2249bf, 'AAAAAAAAAA=='),
    (0x2249c7, 'AAAAAAAAAAAAAAAAAAA='),
    (0x2249d7, 'AAAAAAA='),
    (0x2249dd, 'AAAAAAAAAAAAAA=='),
    (0x2249e8, 'AAAA'),
    (0x2249ec, 'AAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x2249ff, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x224a17, 'AAAAAAA='),
    (0x224a1d, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x224a35, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x224a4f, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x224a71, 'AAAAAAAAAAAAAAAAAA=='),
    (0x224a7f, 'AAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x224a93, 'AAAA'),
    (0x224a97, 'AAAAAAAA'),
    (0x224a9e, 'AAAAAA=='),
    (0x224aa3, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x224abf, 'AAAA'),
    (0x224ac3, 'AAAAAAAAAAAAAA=='),
    (0x224ace, 'AA=='),
    (0x224ad0, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x224aef, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x224b16, 'AAAAAAAA'),
    (0x224b1d, 'AA=='),
    (0x224b1f, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x224b3a, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x224b56, 'AAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x224b69, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x224b82, 'AAAAAAAAAAAAAAA='),
    (0x224b8e, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x224ba9, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x224bc0, 'AAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x224bd5, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x224bfb, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x224c40, 'AAA='),
    (0x224c44, 'AAA='),
    (0x224c48, 'AAAA'),
    (0x224c4c, 'AAAA'),
    (0x224c50, 'AAAA'),
    (0x224c54, 'AA=='),
    (0x224c56, 'AA=='),
    (0x224c58, 'AAAA'),
    (0x224c5d, 'AAA='),
    (0x224c60, 'AAAA'),
    (0x224c64, 'AAAA'),
    (0x224c68, 'AAAA'),
    (0x224c6c, 'AAA='),
    (0x224c70, 'AAA='),
    (0x224c74, 'AAAA'),
    (0x224c78, 'AAAA'),
    (0x2263c2, 'NvCF/A=='),
    (0x226c84, '6sQi'),
    (0x228ece, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e'),
    (0x228f94, 'M/Ds/Q=='),
    (0x229c54, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x22a0c8, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x22ab8c, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e'),
    (0x22abc9, '3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e'),
    (0x22ac94, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e'),
    (0x22afea, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x22b10c, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x22c068, '/t7+3v7e/t4PSBBJAmiKQhnRAnwAKhbQDUkJeA8pCdAMSQl4kUIO0EN8mUIL0IN8mUII0AAhAXRBdIF0LDDBcEF5ATFBcXBH7MQiACCswVr8vQgA7L0IAARKEYgBMRGAwWiJiVGAAkkIR8BG6MIiAIHR'),
    (0x22c0db, 'AP7e/t7+3v7e/t7+3v7e/t7wtTtMO0kiaIpCDNA='),
    (0x22c0f9, 'IiFgYmCiYGJhomHiYSJiImHiYiJjASIic2JoATJiYCJ7ACpc0DFPOXgAKVjQRWqpDVXRAC1T0EFtQylQ0yl7hilN0Wl73SlK0Sl9BikQ0BEpRdEwNal7ASlB0el7/ik+0Sl8kCk70Wl8ASk42E4cCuCpfAkC6nwRQzA1qnwSCZIAiRos3QMmY3wAKwbRAPDd/gEoAtACKB/QIeAifGN8AS4E0TtwoWkBMaFhFeACLgTROnDhaQEx4WEO4GFpATFhYTl4kUIE0KGOATGhhjpwA+BhjgExYYY7cKFoATGhYPC9wEbsxCI='),
    (0x22c1e0, 'IKzBWuy9CA=='),
    (0x22c1e8, '/t7+3v7e/t7wtYKwJnynfAAjAJMBkxBNASKQAChYACgR0MBoACgO0LJCDNC6QgrQAZkBMQGRgGgAKwLQAJlBGgHdEwAAkAEy/irm2QGZ4XQYAAKw8L3ARkDyCAD+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t51RgxMACaPXadVATYQLvrbCUwAJo9dp1UBNhAu+tsHTAAml12nVQE2By762wAgrkZwRwAAMLoIACQEIADouwgAAAAAAAAAAAAAAAAAAA=='),
    (0x22c2b6, 'AAAA'),
    (0x22c2ba, 'AAAAAAAAAAAAAAAAAAAAAA=='),
    (0x22c2cb, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x22c2e8, 'AAA='),
    (0x22c2ec, 'AAA='),
    (0x22c2f0, 'AAAA'),
    (0x22c2f4, 'AAA='),
    (0x22c2f8, '/t7+3g=='),
    (0x22c3e0, 'AfC2+Q=='),
    (0x22c4ec, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x22c508, 'AAAAAAAAAAAAAA=='),
    (0x22c513, 'AAA='),
    (0x22c516, 'AAAAAA=='),
    (0x22c51b, 'AAAAAAAAAAA='),
    (0x22c524, '8LVBTEFJImiKQgzQACIhYGJgomBiYaJh4mEiYiJ0YnSidAEiInNiaAEyYmAiewAqaNA3Tzl4AClk0CJ8Y3wAKgPQkUIc0JlCGtAyTjZ4Dy5Y0DFOMngAKlTQ/ypS0IpCUNAGI5saWxpM3YtCStCTQkjQInRjdKF0OnAhagExIWJFaqkNPtEALTzQRm1DLjnTKXuGKTbRaXvdKTPRKX0GKRrQESk='),
    (0x22c5c9, '0TA1qXsBKSrR6Xv+KSfRKXyQKSTRaXwAKQTRO3ChaQExoWEZ4AEpGtE6cOFpATHhYRLgqXwJAu58MUMwNa58Ngm2AIkbC91haQExYWE5eJFCAdA6cADgO3ChaAExoWDwvQAA7MQiACCswVrsvQgA/L0IAPM='),
    (0x22c63e, 'CAAoAF0wCUkAIoNcj1y7QgnRATIQKvjbBkhBagExQWIFSIZGcEcESCkAcEcAADC6CADsxCIAXdkiAOjbJwDQtSBMIEkiaIpCDNAAIiFgYmCiYGJhomHiYSJi'),
    (0x22c699, 'dGJ0onQBIiJzInsAKinQF085eAApJdAifGN8ACoD0JFCH9CZQh3QEk42eA8uGdARTjJ4ACoV0P8qE9CKQhHQBiObGlsaDd2LQgvQk0IJ0CJ0Y3ShdDpwIWoBMSFioWoBMaFi0L0AAOzEIgAgrMFa7L0IAPw='),
    (0x22c70e, 'CADzvQgAELUg8JP9BAAh8Nj8IAAQvQAAAA=='),
    (0x22c728, 'AAAA'),
    (0x22c72c, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x22c749, 'AA=='),
    (0x22c74b, 'AA=='),
    (0x22c74d, 'AAAAAAAAAAAAAA=='),
    (0x22c759, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x22c77b, 'AAAAAAAAAAAAAAAAAAAAAAA='),
    (0x22c78d, 'AAAAAAAAAAAAAAAAAAAAAAA='),
    (0x22c79f, 'AAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x22c7b4, 'AAAAAAAAAA=='),
    (0x22c7bc, 'AAAAAAAAAAAAAA=='),
    (0x22c7c8, 'AAA='),
    (0x22c7cc, 'AAAA'),
    (0x22c7d0, 'AAAA'),
    (0x22c7d4, 'AAAA'),
    (0x22c7d8, 'AAAA'),
    (0x22c7dc, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x22c7fb, 'AAAAAAA='),
    (0x22c801, 'AA=='),
    (0x22c803, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x22c819, 'AAAAAAAAAAAA'),
    (0x22c823, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x22c83a, 'AAAAAAAAAAAAAAAAAAAAAAA='),
    (0x22c84c, 'AAAA'),
    (0x22c850, 'AAAA'),
    (0x22c854, 'AAAA'),
    (0x22c858, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x22c87d, 'AAAAAAA='),
    (0x22c883, 'AA=='),
    (0x22c885, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='),
    (0x22c89c, 'AAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x22c8b1, 'AAA='),
    (0x22c8b4, 'AAAAAA=='),
    (0x22c8b9, 'AAAAAAAAAAA='),
    (0x22c8c2, 'AAAA'),
    (0x22c8c6, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
    (0x22c8f7, 'AAAAAAAAAAAAAA=='),
    (0x22c902, 'AAAAAAAAAAAAAAAAAAA='),
    (0x22c911, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x22c929, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='),
    (0x22c94a, 'AAAAAAAAAAAAAAAAAAAAAAA='),
    (0x22c95c, 'AAAA'),
    (0x22c960, 'AAA='),
    (0x22c964, 'AAA='),
    (0x22c968, 'AAAA'),
    (0x22c96c, 'AAAA'),
    (0x22c970, 'AAAA'),
    (0x22ce80, '6sQi'),
    (0x22cf40, '/t7+3vC1JQAsNQEuEdDpeA=='),
    (0x22cf51, 'KTA='),
    (0x22cf54, '//dM+QAoA9EpeQExKXEo4GB0ACHpcKl4ATGpcB/gEkkKeAAqHdD/KhvQOXiKQhjQInShdCFqATEhYv/3L/kAKATQYHQpeA=='),
    (0x22cf9b, 'MSlw'),
    (0x22cf9f, '4A=='),
    (0x22cfa1, 'IelwaXgBMWlwInw6cAIg8L0BIPC9ACDwvcBG870IAKF/DykF0QAh4WAhYWFhoWFwR+FoACkC0eBg6WlhYyFpACkD0Sl8ACkA0CBhcEfARv7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x22d678, '6sQi'),
    (0x22d70c, '/t7+3uE='),
    (0x22d712, 'ACkO0GFpACkD0Wl8ACkA0GBhoWkAKQTR6Wlia5FCANCgYXBHwEb+3v7e/t7+3g=='),
    (0x22d750, 'IQADIEACCRgJawMxAA=='),
    (0x22d75e, 'Xvg0SIJCDNA0SIJCC9AzSIJCDdAzSIJCH9AySIJCJtA94DFJP+AEMQ=='),
    (0x22d787, '8En4EQA64AQxAPBE+BAABDELeAExCngCcA=='),
    (0x22d7a1, 'KwfQSg=='),
    (0x22d7a6, 'QnACKwPQiniCcMp4wnABACXgBDEA8C/4I0gRACNKEfAn+CFJG+AEMQDwJfgfS1pgBDEA8CD4HEuaYBo='),
    (0x22d7e2, 'G0tZaJpoEfDm+BdIGEtZaBo='),
    (0x22d7f4, 'EfAP+BVJA+D0GRVJ/vfw/fQZIGsGMBAiC3gDcAExATABOvnR/vdM/gp4S3gbAhpDi3gbBBpDy3gbBhpDcEcAAEdTVDFSRE0xV1JNMVNXUjFTV1cxaNgiANgWCQBY2CIAfEYmAAAAAAAAAAAAAAAAAAAA'),
    (0x22d867, 'ADI2MTAxOC1WMTU5LTA4NDQAJSkAATEJAgQx4GkEIhHwl/g='),
    (0x22d88b, 'NQYt9NvgaVAhCSIR8I/4BbDwvf7e8LUHRuL16PsGRn1qLEg='),
    (0x22d8b0, 'SgEQMhIYFmBXYJVge2vTYAAjE2FTYZNh02GrDQnRAC0H0Ct7E3Rre1N0q3uTdOt703RJHBYpANsAIQFgQ2hbHENgqw0y0QAtMNAre4grLdFre+ErKtHre30rJ9ErfGAr'),
    (0x22d911, '0RRMFEsjYGNoWxxjYHtto2DlYCkAVTEgABAwACKLXINUUhwYKvrb/veC/l0xKgBVMgEjgrAAJwCXBCcBl/73i/wCsKNqATOjYuBiMEbwvaRJIgDsyCIAEazBWujbJwAwtQQA//eU/wU='),
    (0x22d97a, 'IA=='),
    (0x22d97c, 'KfCM/ygAML3+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x22daac, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7wtf73sfoYTBhNGUggYBlIYGDgawEw4GPV9Q74oGAGABVJCHggd8h5YHcIfKB3E0kIeOB3KGkgYuhqYGIojiCFD0kIiGCFaI6ghaiO4IVoaCBjqGkgh+hpYIcwAP/3LPr/99L98L3ARqjCIgDsxCIARUJTMQFQnwDsvQgAuL0I'),
    (0x22db88, 'PPYI'),
    (0x22db8c, '/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x22fa38, '/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x22fb34, '/t7+3v7e/t7+3v7e/t4='),
    (0x232e74, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x233084, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x233408, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x2336a4, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e'),
    (0x237bc8, '6sQi'),
    (0x23ef8c, 'HfBI/g=='),
    (0x23f0d4, '6sQi'),
    (0x23f240, '6sQi'),
    (0x23f434, '6sQi'),
    (0x23f4d0, '6sQi'),
    (0x23f540, '6sQi'),
    (0x23f668, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x2400a0, '6sQi'),
    (0x2406a4, '6sQi'),
    (0x240a64, '6sQi'),
    (0x240b10, '6sQi'),
    (0x240ca4, '6sQi'),
    (0x240da8, '6sQi'),
    (0x2410d6, 'G/Bh/Q=='),
    (0x2418dc, '6sQi'),
    (0x241b18, '6sQi'),
    (0x241c08, '6sQi'),
    (0x241e4c, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x2422ce, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x242b47, '4A=='),
    (0x242be0, '/t7+3g=='),
    (0x242c31, '4A=='),
    (0x242c56, '/t7+3g=='),
    (0x2456ac, '6sQi'),
    (0x245b4c, '6sQi'),
    (0x245f1a, 'FvDv/g=='),
    (0x24cf4e, '3/e3+A=='),
    (0x24cf6e, '3/en+A=='),
    (0x24cfc8, '3/d6+A=='),
    (0x24d028, '3/dK+A=='),
    (0x24d032, '3/dF+A=='),
    (0x24d04e, '3/c3+A=='),
    (0x24d058, '3/cy+A=='),
    (0x24d06a, '3/cp+A=='),
    (0x24d090, '3/cW+A=='),
    (0x24d0f4, '3vfk/w=='),
    (0x24d0fe, '3vff/w=='),
    (0x24d108, '3vfa/w=='),
    (0x24d130, '3vfG/w=='),
    (0x24d144, '3ve8/w=='),
    (0x24d14e, '3ve3/w=='),
    (0x24d158, '3vey/w=='),
    (0x24dd4c, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x24e038, '8A=='),
    (0x24e03a, 'JQAsNQEuFNDpeAApPNDe'),
    (0x24e04a, '0vgAKAM='),
    (0x24e050, 'KXkBMSlxNOBgdAAh6XCpeAExqXAZSwIhGXAo4BdLASEZcRVJCngAKiPQ/yoh0Dl4ikIe0CJ0oXQhagExIWLe96/4ACgH0GB0KXgBMSlwC0sBIRlwC+ABIelwaXgBMWlwIXsBKQXRInw6cAIg8L0BIPC9ACDwvcBG870I'),
    (0x24e0cc, '7MIiAPC13/cZ/UtMS0kiaIpCEtFKTUtPJgAsNnF5SkoSeA8qAtAqepFCB9ApcgAhKXBpcClxqXHpcfC9OXgAKfvQoHwAKPjQYHwAKB0='),
    (0x24e11a, 'P0oSeAAq8dD/Ku/Qo3yaQuzQInTe91/4'),
    (0x24e133, 'KAHRqHEz4Kl5/ykB0AExqXEeKSzTYHQAIfFwaXADISlwJeAiewIqItDe90j4ACge0GF8iEIF0Wl4BDkA1QAhaXAV4Op5kEIC0OhxACFpcGk='),
    (0x24e184, 'ATFpcB4pCtNifDt4k0IA0ThwYHQAIWlwaXkBMWlxOXijfCJ7anIBKhbQAioN0wMqC9hgfAAoCNACKgLQIHwAKAPQgUIa0DhwGOCZQhbQO3DpeAEx6XAR4JlCD9FifAAqDNAifAAqCdAoeQAoAtEoeAMoA9E6cKk='),
    (0x24e1fc, 'ATGpcPC9wEbsxCIAIKzBWuzCIgDsvQgA/L0IAPO9CAD+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x24e77c, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e'),
    (0x2539cc, '2A=='),
    (0x2539ce, 'ov4='),
    (0x253d4c, 'BA=='),
    (0x25454a, 'CPDt+w=='),
    (0x2562e4, '6sQi'),
    (0x2564d4, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x256d41, '4P7e/t7+3v7e'),
    (0x257018, '6sQi'),
    (0x2573c0, '6sQi'),
    (0x2573cc, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x2574f0, 'BfBq+w=='),
    (0x257898, '8A=='),
    (0x25789a, 'QUxBSSJoikIM0AAiIWBiYKJgYmGiYeJhImIiYeJiImMBIiJzYmgBMmJgOE8='),
    (0x2578c7, 'eAApCNBifAAqBdEiACwy0ngAKgDRoXQyTzl4AClb0EVqqQ1Y0QAtVtBBbUMpU9Mpe4YpUNFpe90pTdEpfQYpENARKUjRMDWpewEpRNHpe/4pQdEpfJApPtFpfAEpO9hOHArgqXwJAup8EUMwNap8EgmSAIkaL90DJmN8ACsG0fb3d/sBKALQAigi0CTgInsBKiHRInxjfAEuBNE7cKFpATE='),
    (0x257969, 'YRXgAi4E0Tpw4WkBMeFhDuBhaQExYWE5'),
    (0x257982, 'kUIE0KGOATGhhjpwA+BhjgExYYY7cKFoATGhYPC97MQiACCswVrsvQgA/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x258040, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x2583d4, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e'),
    (0x2584ac, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x258778, '6sQi'),
    (0x258a20, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x25943c, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x2594b7, '3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x2594c9, '3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x2594db, '3v7e/t7+3v7e/t7+3v7e'),
    (0x2594eb, '3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e'),
    (0x259a60, '6sQi'),
    (0x259fa4, '6sQi'),
    (0x25a1c6, 'AvAV/Q=='),
    (0x25a7d4, '6sQi'),
    (0x25cb20, 'UlhEMgEAAQABAAEAAQABAAEAAQABAAEAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP7e/t4MtAhK02k='),
    (0x25cb77, 'M9NhE3kBKwLQBNgBfQPgBEsZeA=='),
    (0x25cb8b, '4FF5DLyxQnBHIMslAP7EIgA='),
    (0x25cb9d, 'tAhIA2oBMwNig3kBKwLQBNgKfQPgBEsa'),
    (0x25cbb6, 'AODCeQm8ApJwRyDLJQD+xCIADLQISlNqATNTYhN6ASsC0ATYOX0D4ARLGXgA4FF6DLwhcnBHIMslAP7EIgAMtAhKk2oBM5Nik3o='),
    (0x25cc01, 'KwLQBNghfQPgBEsZeADg0XoMvKlycEcgyyUA/sQiAAa0CEnKagEyymIKewEqAtAE2A=='),
    (0x25cc33, 'fQPgBEoQeADgSHsGvKhCcEcgyyUA/sQiAAy0CEoTawEzE2OTewErAg=='),
    (0x25cc5c, 'BNgIfQPgBEsYeADg0HsMvLBCcEcgyyUA/sQiAAa0CElKawEySmMKfAEqAtAE2AB9A+AEShB4AOBIfAa8sA=='),
    (0x25cc9a, 'cEcgyyUA/sQiAAO0CEiBawExgWOBfAEpAtAE2BN9A+AESQt4AODDfAO8o0JwRyDLJQD+xCIABrQIScpr'),
    (0x25ccd7, 'MspjCn0BKgLQBNgwfQPgBEoQeADgSH0GvCBxcEcgyyUA/sQiACi0CEsdbAE1HWSdfQEtAtAE2A=='),
    (0x25cd0f, 'fQPgBE0qeADg2n0ovAF6cEcgyyUA/sQiAAO0CEhBbAExQWQBfgEpAtAE2BJ9A+AESQp4AOBCfgO8ASdwRyDLJQD+xCIA/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x25dc74, '6sQi'),
    (0x25de0c, '6sQi'),
    (0x25de44, '/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3g=='),
    (0x25de9d, '3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t7+3v7e/t4='),
    (0x25f014, '6sQi'),
    (0x263c26, 'Bw=='),
    (0x263c46, 'Bw=='),
    (0x263c76, 'Bw=='),
    (0x263ca6, 'Bw=='),
    (0x263cc6, 'Bw=='),
    (0x263cd6, 'Bw=='),
    (0x263cf6, 'Bw=='),
    (0x26cf78, '6sQi'),
    (0x26de84, 'WfJs/w=='),
    (0x26df74, 'WfIK/w=='),
    (0x27b190, 'gA=='),
    (0x27b196, 'gA=='),
    (0x27b87e, 'TPKb+g=='),
    (0x27bb64, '6sQi'),
    (0x27bcb8, '6sQi'),
    (0x27ce84, 'G/L+/Q=='),
    (0x27d69c, '6sQi')
]]

def cks(b):
    c = 0
    for (w,) in struct.iter_unpack("<I", b[: len(b)//4*4]): c ^= w
    return (~c) & 0xFFFFFFFF

def walk(data, base):
    chain, off = [], 0
    while True:
        h = dict(image_len=struct.unpack_from("<I", data, base+off+0x10)[0],
                 addr=struct.unpack_from("<I", data, base+off+0xc)[0],
                 nxt=struct.unpack_from("<I", data, base+off+0x1c)[0],
                 typ=struct.unpack_from("<I", data, base+off+0x24)[0],
                 file_off=base+off, img_off=base+off+0x60)
        chain.append(h)
        if h["nxt"] in (0, 0xFFFFFFFF) or len(chain) > 64: return chain
        off = h["nxt"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stock"); ap.add_argument("-o", "--out", default="ar7420_sniffer_v159.nvm")
    a = ap.parse_args()
    data = bytearray(open(a.stock, "rb").read())
    got = hashlib.sha256(data).hexdigest()
    if got != STOCK_SHA:
        sys.exit("input is not the expected stock 1.1.0.844 firmware\n  expected SHA-256 %s\n  got      %s\n"
                 "Download %s and use %s from it." % (STOCK_SHA, got, "https://static.tp-link.com/resources/software/TL-PA4010PKIT_V2_130807.zip", "MAC-7420-v1.1.0-01-X-FINAL.nvm"))
    outer = walk(data, 0)
    if outer[-1]["typ"] != 4 and len(data) > 0x10000: outer = walk(data, 0x10000)
    fw = outer[-1]; assert fw["typ"] == 4
    rt = walk(data, fw["img_off"])[-1]; assert rt["addr"] == LOAD
    p = rt["img_off"]; clen, dlen = struct.unpack_from("<II", data, p+0x88)
    img = bytearray(lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=DEC).decompress(data[p+0x90:p+0x90+clen], dlen))
    assert len(img) == dlen
    for addr, b in RECORDS: img[addr-LOAD:addr-LOAD+len(b)] = b
    c = lzma.LZMACompressor(format=lzma.FORMAT_RAW, filters=ENC); comp = c.compress(bytes(img)) + c.flush()
    budget = rt["image_len"] - 0x90
    if len(comp) > budget: sys.exit("patched stream overflows by %d B (unexpected)" % (len(comp)-budget))
    true_len = len(comp); comp += b"\x00" * (budget - len(comp))
    sub = bytearray(data[p:p+0x90])
    struct.pack_into("<I", sub, 0x88, true_len); struct.pack_into("<I", sub, 0x8c, len(img))
    struct.pack_into("<I", sub, 0x18, (0x90 + true_len) - 0x80); struct.pack_into("<I", sub, 0x7c, cks(bytes(sub[:0x7c])))
    data[p:p+rt["image_len"]] = bytes(sub) + comp
    for hdr in (rt, fw):
        image = bytes(data[hdr["img_off"]:hdr["img_off"]+hdr["image_len"]]); ho = hdr["file_off"]
        struct.pack_into("<I", data, ho+0x10, len(image)); struct.pack_into("<I", data, ho+0x14, cks(image))
        struct.pack_into("<I", data, ho+0x5c, 0); struct.pack_into("<I", data, ho+0x5c, cks(bytes(data[ho:ho+0x5c])))
    out = hashlib.sha256(data).hexdigest()
    if out != BUILD_SHA:
        sys.exit("internal error: patched output SHA-256 %s != expected %s (LZMA/platform mismatch? report it)"
                 % (out, BUILD_SHA))
    open(a.out, "wb").write(data)
    print("wrote %s (SHA-256 %s) -- the %s sniffer build. Back up your PIB, then flash per the header." %
          (a.out, out, "AR7420-SNIFFER-v159"))

if __name__ == "__main__":
    main()
