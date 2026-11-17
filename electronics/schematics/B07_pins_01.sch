EESchema Schematic File Version 4
LIBS:ZL80_R5-cache
EELAYER 29 0
EELAYER END
$Descr A3 16535 11693
encoding utf-8
Sheet 1 1
Title "ZL80 B07 PIN-NET DRAFT 1"
Date "2026-11-14"
Rev "R5-PDR"
Comp "NOT ROUTED / NO ERC / REVIEW REQUIRED"
$EndDescr
Text Notes 800 650 0 90 ~ 0
PIN-NET REVIEW SHEET - not a manufacturing schematic. Named nets connect globally.
$Comp
L B07_J1 J1
U 1 1 d7b3481c
P 3000 3000
F 0 "J1" H 3000 2450 50 0000 C CNN
F 1 "HEADER_1x4_P1.27" H 3000 3550 40 0000 C CNN
	1 3000 3000
	1 0 0 -1
$EndComp
Wire Wire Line
	2000 2910 1500 2910
Text Label 1500 2910 0 35 ~ 0
5VA
Wire Wire Line
	2000 3090 1500 3090
Text Label 1500 3090 0 35 ~ 0
GND
Wire Wire Line
	4000 2910 4500 2910
Text Label 4000 2910 0 35 ~ 0
SYNC
Wire Wire Line
	4000 3090 4500 3090
Text Label 4000 3090 0 35 ~ 0
GND
$EndSCHEMATC