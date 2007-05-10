""" Module with physical constants for use with ipython, profile
"physics".

Definition of Fundamental Physical Constants, CODATA Recommended Values

Source, Peter J. Mohr and Barry N. Taylor,  
CODATA Recommended Values of the Fundamental
Physical Constants, 1998                    
                                            
Website: physics.nist.gov/constants         
"""
# License: BSD-like
# Copyright: Gael Varoquaux (gael.varoquaux@normalesup.org)

# inspired by maxima's physconst.mac by Cliff Yapp

#from math import * # math MUST be imported BEFORE PhysicalQInteractive 
from IPython.Extensions.PhysicalQInteractive import PhysicalQuantityInteractive

# Math constants:

# Pi mathematical constants
pi = 3.141592653589793238462643383279502884197169399375105820974944592

# Universal Constants
#-------------------------------------------------------------------------

c = PhysicalQuantityInteractive(299792458 , 'm/s')
c.__doc__ = """speed of light in vacuum"""
c.__doc__ = "speed of light in vacuum"

u_0 = PhysicalQuantityInteractive(4*pi*1E-7 , 'N/(A**2)')
u_0.__doc__ = """magnetic constant"""
mu_0 = PhysicalQuantityInteractive(4*pi*1E-7 , 'N/(A**2)')

epsilon_0 = PhysicalQuantityInteractive(8.854187817E-12 , 'F/m')
epsilon_0.__doc__ = """electric constant """

Z_0 = PhysicalQuantityInteractive(376.730313461 , 'ohm')
Z_0.__doc__ = """characteristic impedance of vacuum """

G = PhysicalQuantityInteractive(6.673E-11 , 'm**3/(kg*s**2)')
G.__doc__ = """Newtonian constant of gravitation    """


h = PhysicalQuantityInteractive(6.62606876E-34 , 'J*s')
h.__doc__ = """Planck constant    """


h_eV = PhysicalQuantityInteractive(4.13566727E-15 , 'eV*s')
h_eV.__doc__ = """Planck constant in eVs  """


h_bar = PhysicalQuantityInteractive(1.054571596E-34 , 'J*s')
h_bar.__doc__ = """Hbar"""


h_bar_eV = PhysicalQuantityInteractive(6.58211889E-16 , 'eV*s')
h_bar_eV.__doc__ = """Hbar in eV"""


P_m = PhysicalQuantityInteractive(2.1767E-8 , 'kg')
P_m.__doc__ = """Planck mass"""


P_l = PhysicalQuantityInteractive(1.6160E-35 , 'm')
P_l.__doc__ = """Planck length  """


P_t = PhysicalQuantityInteractive(5.3906E-44 , 's')
P_t.__doc__ = """Planck time """

# Electromagnetic Constants
#------------------------------------------------------------------------

_e = PhysicalQuantityInteractive(1.602176462E-19 , 'C')
_e.__doc__ = """elementary charge"""
q = _e


capitalphi_0 = PhysicalQuantityInteractive(2.067833636E-15 , 'Wb')
capitalphi_0.__doc__ = """magnetic flux quantum """
mfq_0 = PhysicalQuantityInteractive(2.067833636E-15 , 'Wb')


G_0 = PhysicalQuantityInteractive(7.748091696E-5 , 'S')
G_0.__doc__ = """conductance quantum """


K_J = PhysicalQuantityInteractive(483597.898E9 , 'Hz/V')
K_J.__doc__ = """Josephson constant"""


R_K = PhysicalQuantityInteractive(25812.807572 , 'ohm')
R_K.__doc__ = """von Klitzing constant"""


u_B = PhysicalQuantityInteractive(927.400899E-26 , 'J/T')
u_B.__doc__ = """Bohr magneton"""

ueVT_B = PhysicalQuantityInteractive(5.788381749E-5 , 'eV/T')
ueVT_B.__doc__ = """Bohr magneton in eV T-1"""


u_N = PhysicalQuantityInteractive(5.05078317E-27 , 'J/T')
u_N.__doc__ = """nuclear magneton """

ueVT_N = PhysicalQuantityInteractive(3.152451238E-8 , 'eV/T')
ueVT_N.__doc__ = """nuclear magneton in eV T-1      """

# Atomic and Nuclear Constants
# General
#-------------------------------------------------------------------------
# fine-structure constant 
alpha = 7.297352533E-3


Ry = PhysicalQuantityInteractive(10973731.568549 , '1/m')
Ry.__doc__ = """Rydberg constant  """
Ry_INF = PhysicalQuantityInteractive(10973731.568549 , '1/m')


a_0 = PhysicalQuantityInteractive(0.5291772083E-10 , 'm')
a_0.__doc__ = """Bohr radius """


E_h = PhysicalQuantityInteractive(4.35974381E-18 , 'J')
E_h.__doc__ = """Hartree energy """

Eev_h = PhysicalQuantityInteractive(27.2113834 , 'eV')
Eev_h.__doc__ = """Hartree energy in eV    """


qcir2 = PhysicalQuantityInteractive(3.636947516E-4 , 'm**2/s')
qcir2.__doc__ = """quantum of circulation   h/(2me) """

qcir = PhysicalQuantityInteractive(7.273895032E-4 , 'm**2/s')
qcir.__doc__ = """quantum of circulation   h/(me) """

# Electroweak
#-------------------------------------------------------------------------

Fcc = PhysicalQuantityInteractive(1.16639E-5 , '1/GeV**2')
Fcc.__doc__ = """Fermi coupling constant    """
# weak mixing angled  W (on-shell scheme)
wma_W = 0.2224

# Electron, e-
#-------------------------------------------------------------------------

m_e = PhysicalQuantityInteractive(9.10938188E-31 , 'kg')
m_e.__doc__ = """electron mass    """

m_e_u = PhysicalQuantityInteractive(5.485799110E-4 , 'amu')
m_e_u.__doc__ = """electron mass (electron relative atomic mass times amu)"""

me_J = PhysicalQuantityInteractive(8.18710414E-14 , 'J')
me_J.__doc__ = """electron mass - energy equivalent    """

me_MeV = PhysicalQuantityInteractive(0.510998902 , 'MeV')
me_MeV.__doc__ = """electron mass - energy equivalent in MeV"""

# electron-muon mass ratio
memu = 4.83633210E-3

# electron-tau mass ratio    
metau = 2.87555E-4

# electron-proton mass ratio    
memp = 5.446170232E-4

# electron-neutron mass ratio 
memn = 5.438673462E-4

# electron-deuteron mass ratio    
memd = 2.7244371170E-4

# electron to alpha particle mass ratio    
memalpha = 1.3709335611E-4


echargeemass = PhysicalQuantityInteractive(-1.758820174E11 , 'C/kg')
echargeemass.__doc__ = """electron charge to mass quotient    """


Molar_e = PhysicalQuantityInteractive(5.485799110E-7 , 'kg/mol')
Molar_e.__doc__ = """electron molar mass     """


lambdaC = PhysicalQuantityInteractive(2.426310215E-12 , 'm')
lambdaC.__doc__ = """Compton wavelength """


r_e = PhysicalQuantityInteractive(2.817940285E-15 , 'm')
r_e.__doc__ = """classical electron radius  """


sigma_e = PhysicalQuantityInteractive(0.665245854E-28 , 'm**2')
sigma_e.__doc__ = """Thomson cross section """


u_e = PhysicalQuantityInteractive(-928.476362E-26 , 'J/T')
u_e.__doc__ = """electron magnetic moment    """

# electron magnetic moment to Bohr magneton ratio     
ueuB = -1.0011596521869

# electron magnetic moment to nuclear magneton ratio    
ueuN = -1838.2819660

# electron magnetic moment anomaly |ue|/uB - 1    
a_e = 1.1596521869E-3

# electron g-factor 
g_e = -2.0023193043737

# electron-muon magnetic moment ratio   
ueuu = 206.7669720

# electron-proton magnetic moment ratio    
ueup = -658.2106875

# electron to shielded proton magnetic moment ratio  (H2O, sphere, 25  C)
ueusp = -658.2275954

# electron-neutron magnetic moment ratio    
ueun = 960.92050

# electron-deuteron magnetic moment ratio    
ueud = -2143.923498

# electron to shielded helione magnetic moment ratio  (gas, sphere, 25  C)
ueush = 864.058255


gamma_e = PhysicalQuantityInteractive(1.760859794E11 , '1/(s*T)')
gamma_e.__doc__ = """electron gyromagnetic ratio """

# Muon, u-
#-------------------------------------------------------------------------

m_u = PhysicalQuantityInteractive(1.88353109E-28 , 'kg')
m_u.__doc__ = """muon mass    """

mu_u = PhysicalQuantityInteractive(0.1134289168 , 'amu')
mu_u.__doc__ = """muon mass in muon relative atomic mass times amu    """


muc2_J = PhysicalQuantityInteractive(1.69283332E-11 , 'J')
muc2_J.__doc__ = """energy equivalent    """

muc2_MeV = PhysicalQuantityInteractive(105.6583568 , 'MeV')
muc2_MeV.__doc__ = """energy equivalent in MeV """

# muon-electron mass ratio    
mume = 206.7682657

# muon-tau mass ratio
mum = 5.94572E-2

# muon-proton mass ratio
mump = 0.1126095173

# muon-neutron mass ratio 
mumn = 0.1124545079


Molar_u = PhysicalQuantityInteractive(0.1134289168E-3 , 'kg/mol')
Molar_u.__doc__ = """muon molar mass """


lambda_C_u = PhysicalQuantityInteractive(11.73444197E-15 , 'm')
lambda_C_u.__doc__ = """muon Compton wavelength """


uu = PhysicalQuantityInteractive(-4.49044813E-26 , 'J/T')
uu.__doc__ = """muon magnetic moment    """

# ratio of muon magnetic moment to Bohr magneton ratio 
uuuB = -4.84197085E-3

# ratio of muon magnetic moment to nuclear magneton ratio    
uuuN = -8.89059770

# muon magnetic moment anomaly |uu|/(e /2mu) - 1    
a_u = 1.16591602E-3

# muon g-factor -2(1 + au)
g_u = -2.0023318320

# muon-proton magnetic moment ratio    
uuup = -3.18334539

# Tau, tau-
#-------------------------------------------------------------------------

m_tau = PhysicalQuantityInteractive(3.16788E-27 , 'kg')
m_tau.__doc__ = """tau mass    """

mu_tau = PhysicalQuantityInteractive(1.90774 , 'amu')
mu_tau.__doc__ = """tau mass  (tau relative atomic mass times amu)   """


mtauc2_J = PhysicalQuantityInteractive(2.84715E-10 , 'J')
mtauc2_J.__doc__ = """tau mass energy equivalent    """


mtauc2_MeV = PhysicalQuantityInteractive(1777.05 , 'MeV')
mtauc2_MeV.__doc__ = """tau mass energy equivalent in MeV """

# tau-electron mass ratio   
mtaume = 3477.60

# tau-muon mass ratio    
mtaumu = 16.8188

# tau-proton mass ratio    
mtaump = 1.89396

# tau-neutron mass ratio    
mtaumn = 1.89135


Molar_tau = PhysicalQuantityInteractive(1.90774E-3 , 'kg/mol')
Molar_tau.__doc__ = """tau molar mass """


lambda_C_tau = PhysicalQuantityInteractive(0.69770E-15 , 'm')
lambda_C_tau.__doc__ = """tau Compton wavelength    """

# Proton, p
#-------------------------------------------------------------------------

m_p = PhysicalQuantityInteractive(1.67262158E-27 , 'kg')
m_p.__doc__ = """proton mass  """

mu_p = PhysicalQuantityInteractive(1.00727646688 , 'amu')
mu_p.__doc__ = """proton mass (proton relative atomic mass times amu)  """


mpc2_J = PhysicalQuantityInteractive(1.50327731E-10 , 'J')
mpc2_J.__doc__ = """energy equivalent   """

mpc2_MeV = PhysicalQuantityInteractive(938.271998 , 'MeV')
mpc2_MeV.__doc__ = """energy equivalent in MeV  """

# proton-electron mass ratio 
mpme = 1836.1526675

# proton-muon mass ratio
mpmu = 8.88024408

# proton-tau mass ratio 
mpmtau = 0.527994

# proton-neutron mass ratio 
mpmn = 0.99862347855


emp = PhysicalQuantityInteractive(9.57883408E7 , 'C/kg')
emp.__doc__ = """proton charge to mass quotient    """


Molar_p = PhysicalQuantityInteractive(1.00727646688E-3 , 'kg/mol')
Molar_p.__doc__ = """proton molar mass """


lambda_C_p = PhysicalQuantityInteractive(1.321409847E-15 , 'm')
lambda_C_p.__doc__ = """proton Compton wavelength h/mpc  """


up = PhysicalQuantityInteractive(1.410606633E-26 , 'J/T')
up.__doc__ = """proton magnetic moment   """

# proton magnetic moment to Bohr magneton ratio 
upuB = 1.521032203E-3

# proton magnetic moment to nuclear magneton ratio 
upuN = 2.792847337

# proton g-factor 2up/uN  
g_p = 5.585694675

# proton-neutron magnetic moment ratio  
upun = -1.45989805


usp = PhysicalQuantityInteractive(1.410570399E-26 , 'J/T')
usp.__doc__ = """shielded proton magnetic moment  (H2O, sphere, 25  C)"""

# shielded proton magnetic moment to Bohr magneton ratio 
uspuB = 1.520993132E-3

# shielded proton magnetic moment to nuclear magneton ratio 
uspuN = 2.792775597

# proton magnetic shielding correction 1 - u p/up  (H2O, sphere, 25  C)
spc = 25.687E-6


gamma_p = PhysicalQuantityInteractive(2.67522212E8 , '1/(s*T)')
gamma_p.__doc__ = """proton gyromagnetic ratio """


gamma_sp = PhysicalQuantityInteractive(2.67515341E8 , '1/(s*T)')
gamma_sp.__doc__ = """shielded proton gyromagnetic ratio (H2O, sphere, 25  C)"""

# Neutron, n
#-------------------------------------------------------------------------

m_n = PhysicalQuantityInteractive(1.67492716E-27 , 'kg')
m_n.__doc__ = """neutron mass  """

mu_n = PhysicalQuantityInteractive(1.00866491578 , 'amu')
mu_n.__doc__ = """neutron mass (neutron relative atomic mass times amu) """


mnc2_J = PhysicalQuantityInteractive(1.50534946E-10 , 'J')
mnc2_J.__doc__ = """neutron mass energy equivalent  """


mnc2_MeV = PhysicalQuantityInteractive(939.565330 , 'MeV')
mnc2_MeV.__doc__ = """neutron mass energy equivalent  in MeV  """

# neutron-electron mass ratio 
mnme = 1838.6836550

# neutron-muon mass ratio 
mnmu = 8.89248478

# neutron-tau mass ratio 
mnm = 0.528722

# neutron-proton mass ratio 
mnmp = 1.00137841887


Molar_n = PhysicalQuantityInteractive(1.00866491578E-3 , 'kg/mol')
Molar_n.__doc__ = """neutron molar mass  """


lambda_C_n = PhysicalQuantityInteractive(1.319590898E-15 , 'm')
lambda_C_n.__doc__ = """neutron Compton wavelength"""


un = PhysicalQuantityInteractive(-0.96623640E-26 , 'J/T')
un.__doc__ = """neutron magnetic moment """

# neutron magnetic moment to Bohr magneton ratio 
unuB = -1.04187563E-3

# neutron magnetic moment to nuclear magneton ratio 
unuN = -1.91304272

# neutron g-factor 
g_n = -3.82608545

# neutron-electron magnetic moment ratio  
unue = 1.04066882E-3

# neutron-proton magnetic moment ratio 
unup = -0.68497934

# neutron to shielded proton magnetic moment ratio (H2O, sphere, 25  C)
unusp = -0.68499694


gamma_n = PhysicalQuantityInteractive(1.83247188E8 , '1/(s*T)')
gamma_n.__doc__ = """neutron gyromagnetic ratio """

# Deuteron, d
#-------------------------------------------------------------------------

m_d = PhysicalQuantityInteractive(3.34358309E-27 , 'kg')
m_d.__doc__ = """deuteron mass """


mu_d = PhysicalQuantityInteractive(2.01355321271 , 'amu')
mu_d.__doc__ = """deuteron mass (deuteron relative atomic mass times amu)  """


mdc2_J = PhysicalQuantityInteractive(3.00506262E-10 , 'J')
mdc2_J.__doc__ = """deuteron mass energy equivalent """


mdc2_eV = PhysicalQuantityInteractive(1875.612762 , 'MeV')
mdc2_eV.__doc__ = """deuteron mass energy equivalent in MeV  """

# deuteron-electron mass ratio  
mdme = 3670.4829550

# deuteron-proton mass ratio 
mdmp = 1.99900750083


Molar_d = PhysicalQuantityInteractive(2.01355321271E-3 , 'kg/mol')
Molar_d.__doc__ = """deuteron molar mass """


ud = PhysicalQuantityInteractive(0.433073457E-26 , 'J/T')
ud.__doc__ = """deuteron magnetic moment  """

# deuteron magnetic moment to Bohr magneton ratio 
uduB = 0.4669754556E-3

# deuteron magnetic moment to nuclear magneton ratio 
uduN = 0.8574382284

# deuteron-electron magnetic moment ratio 
udue = -4.664345537E-4

# deuteron-proton magnetic moment ratio 
udup = 0.3070122083

# deuteron-neutron magnetic moment ratio 
udun = -0.44820652

# Helion, h
#-------------------------------------------------------------------------

m_h = PhysicalQuantityInteractive(5.00641174E-27 , 'kg')
m_h.__doc__ = """helion mass """


mu_h = PhysicalQuantityInteractive(3.01493223469 , 'amu')
mu_h.__doc__ = """helion mass (helion relative atomic mass times amu)  """


mhc2_J = PhysicalQuantityInteractive(4.49953848E-10 , 'J')
mhc2_J.__doc__ = """helion mass energy equivalent """

mhc2_MeV = PhysicalQuantityInteractive(2808.39132 , 'MeV')
mhc2_MeV.__doc__ = """helion mass energy equivalent in MeV """

# helion-electron mass ratio 
mhme = 5495.885238

# helion-proton mass ratio 
mhmp = 2.99315265850


Molar_h = PhysicalQuantityInteractive(3.01493223469E-3 , 'kg/mol')
Molar_h.__doc__ = """helion molar mass """


ush = PhysicalQuantityInteractive(-1.074552967E-26 , 'J/T')
ush.__doc__ = """shielded helion magnetic moment (gas, sphere, 25  C)"""

# shielded helion magnetic moment to Bohr magneton ratio 
ushuB = -1.158671474E-3

# shielded helion magnetic moment to nuclear magneton ratio  
ushuN = -2.127497718

# shielded helion to proton magnetic moment ratio  (gas, sphere, 25  C)
ushup = -0.761766563

# shielded helion to shielded proton magnetic moment ratio  (gas/H2O, spheres, 25  C)
ushusp = -0.7617861313


gamma_h = PhysicalQuantityInteractive(2.037894764E8 , '1/(s*T)')
gamma_h.__doc__ = """shielded helion gyromagnetic  (gas, sphere, 25  C) """

# Alpha particle, 
#-------------------------------------------------------------------------

m_alpha = PhysicalQuantityInteractive(6.64465598E-27 , 'kg')
m_alpha.__doc__ = """alpha particle mass  """

mu_alpha = PhysicalQuantityInteractive(4.0015061747 , 'amu')
mu_alpha.__doc__ = """alpha particle mass (alpha particle relative atomic mass times amu) """


malphac2_J = PhysicalQuantityInteractive(5.97191897E-10 , 'J')
malphac2_J.__doc__ = """alpha particle mass energy equivalent  """


malphac2_MeV = PhysicalQuantityInteractive(3727.37904 , 'MeV')
malphac2_MeV.__doc__ = """alpha particle mass energy equivalent in MeV  """

# alpha particle to electron mass ratio 
malphame = 7294.299508

# alpha particle to proton mass ratio 
malphamp = 3.9725996846


Molar_alpha = PhysicalQuantityInteractive(4.0015061747E-3 , 'kg/mol')
Molar_alpha.__doc__ = """alpha particle molar mass"""

# PHYSICO-CHEMICAL
#-------------------------------------------------------------------------

N_A = PhysicalQuantityInteractive(6.02214199E23 , '1/mol')
N_A.__doc__ = """Avogadro constant  """
L = PhysicalQuantityInteractive(6.02214199E23 , '1/mol')


m_u = PhysicalQuantityInteractive(1.66053873E-27 , 'kg')
m_u.__doc__ = """atomic mass constant mu = 112m(12C) = 1 u = 10E-3 kg mol-1/NA"""
# atomic mass constant mu = 112m(12C) = 1 u = 10E-3 kg mol-1/NA
amu = m_u


muc2_J = PhysicalQuantityInteractive(1.49241778E-10 , 'J')
muc2_J.__doc__ = """energy equivalent of the atomic mass constant"""


muc2_MeV = PhysicalQuantityInteractive(931.494013 , 'MeV')
muc2_MeV.__doc__ = """energy equivalent of the atomic mass constant in MeV """


F = PhysicalQuantityInteractive(96485.3415 , 'C/mol')
F.__doc__ = """Faraday constant"""


N_Ah = PhysicalQuantityInteractive(3.990312689E-10 , 'J*s/mol')
N_Ah.__doc__ = """molar Planck constant   """


R = PhysicalQuantityInteractive(8.314472 , 'J/(mol*K)')
R.__doc__ = """molar gas constant  """


k_J = PhysicalQuantityInteractive(1.3806503E-23 , 'J/K')
k_J.__doc__ = """Boltzmann constant """


k_eV = PhysicalQuantityInteractive(8.617342E-5 , 'eV/K')
k_eV.__doc__ = """Boltzmann constant in eV """


n_0 = PhysicalQuantityInteractive(2.6867775E25 , '1/m**3')
n_0.__doc__ = """Loschmidt constant  NA/Vm """


Vm_1 = PhysicalQuantityInteractive(22.413996E-3 , 'm**3/mol')
Vm_1.__doc__ = """molar volume of ideal gas RT/p   T = 273.15 K, p = 101.325 kPa """

Vm_2 = PhysicalQuantityInteractive(22.710981E-3 , 'm**3/mol')
Vm_2.__doc__ = """molar volume of ideal gas RT/p   T = 273.15 K, p = 100 kPa  """

# Sackur-Tetrode constant (absolute entropy constant) 52 + ln_(2 mukT1/h2)3/2kT1/p0
# T1 = 1 K, p0 = 100 kPa 
S_0R_1 = -1.1517048
# T1 = 1 K, p0 = 101.325 kPa  
S_0R_2 = -1.1648678


sigma = PhysicalQuantityInteractive(5.670400E-8 , 'W/(m**2*K**4)')
sigma.__doc__ = """Stefan-Boltzmann constant """


c_1 = PhysicalQuantityInteractive(3.74177107E-16 , 'W*m**2')
c_1.__doc__ = """first radiation constant"""


c_1L = PhysicalQuantityInteractive(1.191042722E-16 , 'W*m**2/sr')
c_1L.__doc__ = """first radiation constant for spectral radiance"""


c_2 = PhysicalQuantityInteractive(1.4387752E-2 , 'm*K')
c_2.__doc__ = """second radiation constant"""


b = PhysicalQuantityInteractive(2.8977686E-3 , 'm*K')
b.__doc__ = """Wien displacement law constant b =  maxT = c2/4.965 114231... """

