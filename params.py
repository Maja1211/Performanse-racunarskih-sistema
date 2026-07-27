#Broj korisnickih diskova
K_VALUES = [2, 3, 4, 5]

#Vrijednosti opterecenja
R_VALUES = [0.30, 0.55, 0.80, 1.00]


#Srednja vremena obrade u sekundama

CPU_TIME = 0.004

SYSTEM_DISK_1_TIME = 0.010
SYSTEM_DISK_2_TIME = 0.015
SYSTEM_DISK_3_TIME = 0.015

USER_DISK_TIME = 0.025


#Vjerovatnoce poslije procesora

CPU_TO_CPU = 0.15
CPU_TO_SYSTEM_DISK_1 = 0.20
CPU_TO_SYSTEM_DISK_2 = 0.15
CPU_TO_SYSTEM_DISK_3 = 0.10
CPU_TO_USER_DISKS = 0.40


#Vjerovatnoce poslije sistemskog diska

SYSTEM_DISK_TO_CPU = 0.35
SYSTEM_DISK_TO_SAME_DISK = 0.25
SYSTEM_DISK_TO_USER_DISKS = 0.40


#Trajanje jedne simulacije
#30 minuta = 1800 sekundi

SIMULATION_TIME = 60 * 30


# Broj ponavljanja simulacije

NUMBER_OF_SIMULATIONS = 100


# Folder u koji se upisuju rezultati

RESULTS_FOLDER = "results"


# Mala vrijednost za poredjenje decimalnih brojeva

EPS = 0.000000001