import streamlit as st
import math

st.set_page_config(layout="wide", page_title="ThermoX", page_icon="🔥", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* Custom Dark Theme to match React App */
[data-testid="stAppViewContainer"] {
    background-color: #020617;
    color: #cbd5e1;
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] {
    background-color: #020617;
}
header.stAppHeader {
    border-bottom: 1px solid #1e293b;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(15, 23, 42, 0.5);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid #1e293b;
}
.stTabs [data-baseweb="tab"] {
    height: 40px;
    background-color: transparent;
    border-radius: 8px;
    color: #94a3b8;
    border: none;
    padding: 0 20px;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(14, 165, 233, 0.1) !important;
    color: #38bdf8 !important;
    border: 1px solid rgba(14, 165, 233, 0.2) !important;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}
[data-testid="stMetricLabel"] {
    color: #94a3b8;
    font-size: 0.875rem;
}
[data-testid="stMetricValue"] {
    color: #f8fafc;
    font-size: 1.5rem;
    font-family: monospace;
}

h2, h3 {
    color: #f8fafc !important;
}

p, span, div, li {
    color: #cbd5e1 !important;
}

[data-testid="stMetricValue"] div {
    color: #f8fafc !important;
}

[data-testid="stMetricLabel"] p {
    color: #94a3b8 !important;
}

hr {
    border-color: #1e293b;
}

/* Force light text in Expander contents */
[data-testid="stExpanderDetails"] p, 
[data-testid="stExpanderDetails"] li, 
[data-testid="stExpanderDetails"] span {
    color: #e2e8f0 !important;
}

/* Form Inputs Contrast Fixes */
div[data-baseweb="select"] > div, 
div[data-baseweb="select"] span,
div[data-baseweb="popover"] span,
input {
    color: #f8fafc !important;
}
input {
    background-color: #0f172a !important;
}
</style>
""", unsafe_allow_html=True)

FLUIDS = {
    'water': {'name': 'Água Líquida', 'density': 998, 'cp': 4182, 'k': 0.6, 'mu': 0.001002, 'prandtl': 6.99},
    'air': {'name': 'Ar (Gás Ideial)', 'density': 1.225, 'cp': 1006, 'k': 0.0242, 'mu': 1.78e-5, 'prandtl': 0.73},
    'oil': {'name': 'Óleo Motor', 'density': 888, 'cp': 1880, 'k': 0.145, 'mu': 0.8, 'prandtl': 10400},
    'ethylene': {'name': 'Etilenoglicol', 'density': 1111, 'cp': 2470, 'k': 0.252, 'mu': 0.0157, 'prandtl': 154}
}

MATERIALS = {
    'copper': {'name': 'Cobre', 'density': 8960, 'k': 398},
    'aluminum': {'name': 'Alumínio', 'density': 2719, 'k': 202},
    'steel': {'name': 'Aço Carbono', 'density': 7850, 'k': 54},
    'ss304': {'name': 'Aço Inox 304', 'density': 8000, 'k': 16.2}
}

# --- Properties Logic ---
def interpolate_linear(x, x0, y0, x1, y1):
    if x0 == x1: return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

def get_interpolated_props(T_kelvin, table):
    if T_kelvin <= table[0]['T']: return table[0]
    if T_kelvin >= table[-1]['T']: return table[-1]
    
    for i in range(len(table) - 1):
        if table[i]['T'] <= T_kelvin <= table[i+1]['T']:
            r1 = table[i]
            r2 = table[i+1]
            return {
                'density': interpolate_linear(T_kelvin, r1['T'], r1['density'], r2['T'], r2['density']),
                'cp': interpolate_linear(T_kelvin, r1['T'], r1['cp'], r2['T'], r2['cp']),
                'k': interpolate_linear(T_kelvin, r1['T'], r1['k'], r2['T'], r2['k']),
                'mu': interpolate_linear(T_kelvin, r1['T'], r1['mu'], r2['T'], r2['mu']),
                'prandtl': interpolate_linear(T_kelvin, r1['T'], r1['pr'], r2['T'], r2['pr']),
            }
    return table[0]

air_table = [
    {'T': 250, 'density': 1.4128, 'cp': 1006, 'mu': 159.9e-7, 'k': 22.3e-3, 'pr': 0.720},
    {'T': 300, 'density': 1.1614, 'cp': 1007, 'mu': 184.6e-7, 'k': 26.3e-3, 'pr': 0.707},
    {'T': 350, 'density': 0.9950, 'cp': 1009, 'mu': 208.2e-7, 'k': 30.0e-3, 'pr': 0.700},
    {'T': 400, 'density': 0.8711, 'cp': 1014, 'mu': 230.1e-7, 'k': 33.8e-3, 'pr': 0.690},
    {'T': 450, 'density': 0.7740, 'cp': 1021, 'mu': 250.7e-7, 'k': 37.3e-3, 'pr': 0.686},
    {'T': 500, 'density': 0.6964, 'cp': 1029, 'mu': 270.1e-7, 'k': 40.7e-3, 'pr': 0.684},
    {'T': 600, 'density': 0.5804, 'cp': 1051, 'mu': 305.8e-7, 'k': 46.9e-3, 'pr': 0.685},
    {'T': 800, 'density': 0.4354, 'cp': 1099, 'mu': 371.1e-7, 'k': 57.3e-3, 'pr': 0.709},
    {'T': 1000, 'density': 0.3482, 'cp': 1141, 'mu': 430.3e-7, 'k': 66.7e-3, 'pr': 0.739},
]

water_table = [
    {'T': 273.15, 'density': 999.8, 'cp': 4217, 'mu': 1750e-6, 'k': 0.569, 'pr': 12.99},
    {'T': 280, 'density': 1000.0, 'cp': 4198, 'mu': 1422e-6, 'k': 0.582, 'pr': 10.26},
    {'T': 300, 'density': 997.0, 'cp': 4179, 'mu': 855e-6, 'k': 0.613, 'pr': 5.83},
    {'T': 320, 'density': 989.0, 'cp': 4180, 'mu': 577e-6, 'k': 0.640, 'pr': 3.77},
    {'T': 340, 'density': 979.0, 'cp': 4188, 'mu': 420e-6, 'k': 0.660, 'pr': 2.66},
    {'T': 360, 'density': 967.0, 'cp': 4203, 'mu': 324e-6, 'k': 0.674, 'pr': 2.02},
    {'T': 373.15, 'density': 958.0, 'cp': 4217, 'mu': 279e-6, 'k': 0.680, 'pr': 1.76},
]

def evaluate_fluid_props(fluid_id, T_celcius):
    base_fluid = FLUIDS[fluid_id].copy()
    T_k = T_celcius + 273.15
    if fluid_id == 'air':
        base_fluid.update(get_interpolated_props(T_k, air_table))
    elif fluid_id == 'water':
        base_fluid.update(get_interpolated_props(T_k, water_table))
    return base_fluid

# --- Calculation Logic --- 
def calculate(state):
    steps = []
    warnings = []
    mat = MATERIALS[state['materialId']]

    hotMdot = state['hotMdot']
    coldMdot = state['coldMdot']
    hotOutletT = state['hotTargetOutletT']
    coldOutletT = state['coldTargetOutletT']
    q = 0

    steps.append("## 1. Inicialização e Balanceamento Térmico")
    
    hotF = evaluate_fluid_props(state['hotFluidId'], state['hotInletT'])
    coldF = evaluate_fluid_props(state['coldFluidId'], state['coldInletT'])

    steps.append("- Resolvendo o Balanço de Energia: $Q = \\dot{m} C_p \\Delta T$")

    for iter in range(10):
        if state['solveTarget'] == 'hot_outlet':
            q = coldMdot * coldF['cp'] * (coldOutletT - state['coldInletT'])
            hotOutletT = state['hotInletT'] - (q / (hotMdot * hotF['cp']))
        elif state['solveTarget'] == 'cold_outlet':
            q = hotMdot * hotF['cp'] * (state['hotInletT'] - hotOutletT)
            coldOutletT = state['coldInletT'] + (q / (coldMdot * coldF['cp']))
        elif state['solveTarget'] == 'cold_mdot':
            q = hotMdot * hotF['cp'] * (state['hotInletT'] - hotOutletT)
            cp_dt = coldF['cp'] * (coldOutletT - state['coldInletT'])
            coldMdot = q / cp_dt if cp_dt != 0 else 0.001
        elif state['solveTarget'] == 'hot_mdot':
            q = coldMdot * coldF['cp'] * (coldOutletT - state['coldInletT'])
            cp_dt = hotF['cp'] * (state['hotInletT'] - hotOutletT)
            hotMdot = q / cp_dt if cp_dt != 0 else 0.001
        elif state['solveTarget'] == 'heat_duty':
            q = state['targetHeatDuty']
            hotOutletT = state['hotInletT'] - (q / (hotMdot * hotF['cp']))
            coldOutletT = state['coldInletT'] + (q / (coldMdot * coldF['cp']))

        T_hot_mean = (state['hotInletT'] + hotOutletT) / 2
        T_cold_mean = (state['coldInletT'] + coldOutletT) / 2
        
        hotF = evaluate_fluid_props(state['hotFluidId'], T_hot_mean)
        coldF = evaluate_fluid_props(state['coldFluidId'], T_cold_mean)

    dT1 = state['hotInletT'] - coldOutletT
    dT2 = hotOutletT - state['coldInletT']
    
    lmtd = max(dT1, dT2, 1)
    if abs(dT1 - dT2) > 0.01 and dT1 > 0 and dT2 > 0:
        lmtd = (dT1 - dT2) / math.log(dT1 / dT2)

    F = 1.0
    if state['geometryType'] in ['cross-flow-bank', 'shell-tube']:
        R = abs((state['hotInletT'] - hotOutletT) / (coldOutletT - state['coldInletT'])) if coldOutletT != state['coldInletT'] else 1.0
        P = abs((coldOutletT - state['coldInletT']) / (state['hotInletT'] - state['coldInletT'])) if state['hotInletT'] != state['coldInletT'] else 0.0
        
        if R != 1 and P > 0 and P < 1:
            try:
                num = math.sqrt(R*R + 1) * math.log((1 - P) / (1 - P*R))
                denInner = (2 - P*(R + 1 - math.sqrt(R*R + 1))) / (2 - P*(R + 1 + math.sqrt(R*R + 1)))
                F_calc = num / ((R - 1) * math.log(denInner))
                if not math.isnan(F_calc) and F_calc > 0.4: F = F_calc
            except: pass
        elif R == 1 and P > 0 and P < 1:
            try:
                num = (P / (1 - P)) * math.sqrt(2)
                denInner = (2 - P*(2 - math.sqrt(2))) / (2 - P*(2 + math.sqrt(2)))
                F_calc = num / math.log(denInner)
                if not math.isnan(F_calc) and F_calc > 0.4: F = F_calc
            except: pass
            
        if F < 0.75:
            warnings.append(f"Aviso de Baixa Eficiência Térmica (F = {F:.2f}).")

    if math.isnan(lmtd) or lmtd <= 0: lmtd = 1

    steps.append(f"- Diferença de Temperatura Logarítmica (LMTD) calculada: **{lmtd:.2f} °C**")
    if state['geometryType'] in ['cross-flow-bank', 'shell-tube']:
        steps.append(f"- Fator de Correção $F$: **{F:.2f}**")
        if F < 0.75:
            steps.append("- *Aviso:* Fator F abaixo de 0.75 indica baixa eficiência térmica neste arranjo.")

    steps.append("\\n## 2. Coeficientes de Transferência de Calor (Convecção)")
    
    Do = state['tubeDo'] / 1000
    t = state['tubeThickness'] / 1000
    Di = Do - 2 * t
    Pt = state['tubePitch'] / 1000

    Nt = 20
    U, v_t, v_s, Re_t, Re_s, h_i, h_o = 500, 0, 0, 0, 0, 1000, 1000

    T_surface = ((state['hotInletT'] + hotOutletT)/2 + (state['coldInletT'] + coldOutletT)/2) / 2
    coldF_surface = evaluate_fluid_props(state['coldFluidId'], T_surface)
    w_effective = state['shellDo']

    for i in range(20):
        N_T = max(1, math.floor(state['shellDo'] / Pt))
        w_effective = state['shellDo']

        if state['geometryType'] == 'cross-flow-bank':
            opt_N_T = N_T
            target_v_max = 0.8 if coldF['density'] > 500 else 8.0
            limit_v_t = 2.5 if hotF['density'] > 500 else 20.0
            
            while opt_N_T > 1:
                temp_w = opt_N_T * Pt
                temp_v_app = coldMdot / (coldF['density'] * temp_w * state['tubeLength'])
                temp_v_max = temp_v_app * (Pt / (Pt - Do))
                temp_A_cross_t = opt_N_T * math.pi * (Di**2) / 4
                temp_v_t = hotMdot / (hotF['density'] * temp_A_cross_t)
                
                if temp_v_max < target_v_max and temp_v_t < limit_v_t:
                    opt_N_T -= 1
                else:
                    break
            N_T = opt_N_T
            w_effective = N_T * Pt
            A_cross_t = N_T * math.pi * (Di**2) / 4
        else:
            A_cross_t = (Nt / state.get('tubePasses', 1)) * math.pi * (Di**2) / 4
            
        v_t = hotMdot / (hotF['density'] * max(A_cross_t, 1e-6))
        Re_t = abs(hotF['density'] * v_t * Di / hotF['mu'])
        
        Nu_t = 4.36
        if Re_t >= 10000:
            Nu_t = 0.023 * (Re_t**0.8) * (hotF['prandtl']**0.3)
        elif Re_t > 2300:
            f_pet = (0.79 * math.log(max(Re_t, 2)) - 1.64)**(-2)
            Nu_t = ((f_pet / 8) * (Re_t - 1000) * hotF['prandtl']) / (1 + 12.7 * (f_pet / 8)**0.5 * (hotF['prandtl']**(2/3) - 1))
            
        h_i = Nu_t * hotF['k'] / Di
        
        As = 0
        if state['geometryType'] == 'shell-tube':
            As = (Pt - Do) * state['shellDo'] * state.get('baffleSpacing', 0.5) / Pt
            v_s = coldMdot / (coldF['density'] * max(As, 1e-6))
            D_eq = (4 * ((Pt**2) - (math.pi * (Do**2) / 4))) / (math.pi * Do)
            Re_s = abs(coldF['density'] * v_s * D_eq / coldF['mu'])
            Nu_s = 0.36 * (max(Re_s, 1)**0.55) * (coldF['prandtl']**0.33)
            h_o = Nu_s * coldF['k'] / D_eq
        else:
            w = w_effective
            ST = Pt
            SL = state.get('tubePitchLongitudinal', 25) / 1000
            v_app = coldMdot / (coldF['density'] * w * state['tubeLength'])
            v_max = v_app * (ST / max((ST - Do), 1e-6))
            
            if state.get('bundleAlignment', 'staggered') == 'staggered':
                SD = math.sqrt((ST/2)**2 + SL**2)
                if 2 * (SD - Do) < (ST - Do):
                    v_max = v_app * (ST / max(2 * (SD - Do), 1e-6))
            
            v_s = v_max
            Re_s = abs(coldF['density'] * v_s * Do / coldF['mu'])
            
            # Zhukauskas correl.
            C, m = 0, 0
            if state.get('bundleAlignment', 'staggered') == 'aligned':
                if Re_s < 100: C, m = 0.80, 0.40
                elif Re_s < 1000: C, m = 0.22, 0.63
                elif Re_s < 200000: C, m = 0.27, 0.63
                else: C, m = 0.021, 0.84
            else:
                if Re_s < 100: C, m = 0.90, 0.40
                elif Re_s < 1000: C, m = 0.51, 0.50
                elif Re_s < 200000: C, m = 0.35 * ((ST/max(SL, 0.001))**0.2), 0.60
                else: C, m = 0.022, 0.84
            
            Nu_s = C * (max(Re_s, 1)**m) * (coldF['prandtl']**0.36) * ((coldF['prandtl'] / coldF_surface['prandtl'])**0.25)
            h_o = Nu_s * coldF['k'] / Do

        if i == 19:  # Last iteration, save detailed steps
            steps.append(f"**Lado dos Tubos (Fluido Quente):**")
            steps.append(f"- Número final iterativo de tubos: $N_t = {Nt}$")
            steps.append(f"- $Re_{{tubos}} = {Re_t:.1f}$ (Velocidade média: {v_t:.3f} m/s)")
            steps.append(f"- Correlação (Dittus-Boelter / Gnielinski): $Nu_{{tubos}} = {Nu_t:.2f}$")
            steps.append(f"- Coef. Conv. Interno $h_i = {h_i:.2f} \\; W/m^2K$")
            
            steps.append(f"\\**Lado do Casco / Banco (Fluido Frio):**")
            steps.append(f"- $Re_{{ext}} = {Re_s:.1f}$ (Velocidade máx.: {v_s:.3f} m/s)")
            if state['geometryType'] == 'cross-flow-bank':
                steps.append(f"- Correlação de Zhukauskas aplicada (Arranjo {state.get('bundleAlignment')}, C={C:.3f}, m={m:.2f})")
            else:
                steps.append(f"- Correlação de Kern estimada")
            steps.append(f"- $Nu_{{ext}} = {Nu_s:.2f}$")
            steps.append(f"- Coef. Conv. Externo $h_o = {h_o:.2f} \\; W/m^2K$")

        R_wall = (Do / (2 * mat['k'])) * math.log(Do / Di)
        R_fi = state.get('foulingHot', 0.0001) * (Do / Di)
        R_fo = state.get('foulingCold', 0.0002)
        
        U = 1 / ( (1/h_i)*(Do/Di) + R_wall + R_fi + R_fo + (1/h_o) )
        A_req = q / (U * lmtd * F)
        Nt_new = math.ceil(A_req / (math.pi * Do * state['tubeLength']))
        Nt = math.ceil(0.4 * Nt_new + 0.6 * Nt)
        if Nt < 1: Nt = 1
        if Nt > 2000: Nt = 2000
        
    f_t = (0.79 * math.log(max(Re_t, 2)) - 1.64)**(-2) if Re_t > 2300 else 64/max(Re_t, 1)
    deltaPTube = f_t * (state['tubeLength'] / Di) * (hotF['density'] * (v_t**2) / 2)

    deltaPShell = 0
    if state['geometryType'] == 'shell-tube':
        f_s = 1 if Re_s < 1 else 0.4
        D_eq = 4 * ((Pt**2) - math.pi * (Do**2)/4) / (math.pi * Do)
        numBaffles = math.floor(state['tubeLength'] / state.get('baffleSpacing', 0.5))
        deltaPShell = f_s * (state['shellDo'] / D_eq) * (numBaffles + 1) * (coldF['density'] * (v_s**2) / 2)
    else:
        f_s = 1.0
        N_T_final = max(math.floor(w_effective / Pt), 1)
        N_L = math.ceil(Nt / N_T_final)
        deltaPShell = N_L * f_s * (coldF['density'] * (v_s**2) / 2)
        
    if hotF['density'] > 500 and v_t < 1.0:
        warnings.append(f"Velocidade muito baixa lado tubos ({v_t:.2f} m/s).")

    steps.append("\\n## 3. Coeficiente Global e Queda de Pressão")
    steps.append(f"- Área Total de Troca: $A = {Nt * math.pi * Do * state['tubeLength']:.2f} \\; m^2$")
    steps.append(f"- Coeficiente Global $U = \\cfrac{{1}}{{\\cfrac{{1}}{{h_i}} + R_{{wall}} + R_{{fi}} + R_{{fo}} + \\cfrac{{1}}{{h_o}}}} = {U:.2f} \\; W/m^2K$")
    steps.append(f"- Fator de Atrito Darcy Lado Tubos: $f = {f_t:.4f}$")
    steps.append(f"- Queda de Pressão Lado Tubos: $\\Delta P = {(deltaPTube/1000):.2f} \\; kPa$")
    steps.append(f"- Queda de Pressão Lado Casco: $\\Delta P = {(deltaPShell/1000):.2f} \\; kPa$")

    y_plus = state.get('yPlusTarget', 5.0)
    cf_t = 0.058 * (Re_t**-0.2) if Re_t > 0 else 0
    tau_wall_t = cf_t * hotF['density'] * (v_t**2) / 2
    u_tau_t = math.sqrt(tau_wall_t / hotF['density']) if tau_wall_t > 0 else 0.01
    dy_int = y_plus * hotF['mu'] / (hotF['density'] * u_tau_t) if u_tau_t > 0 else 1e-5

    cf_s = 0.058 * (max(Re_s, 1)**-0.2)
    tau_wall_s = cf_s * coldF['density'] * (v_s**2) / 2
    u_tau_s = math.sqrt(tau_wall_s / coldF['density']) if tau_wall_s > 0 else 0.01
    dy_ext = y_plus * coldF['mu'] / (coldF['density'] * u_tau_s) if u_tau_s > 0 else 1e-5

    courant = state.get('courantNumber', 5.0)
    estimatedTimeStep = courant * 0.01 / max(v_t, v_s, 0.001)

    return {
        'U': U, 'Area': Nt * math.pi * Do * state['tubeLength'],
        'Nt': Nt, 'v_t': v_t, 'v_s': v_s, 'h_i': h_i, 'h_o': h_o,
        'warnings': warnings,
        'q': q, 'lmtd': lmtd, 'F': F, 'hotOutletT': hotOutletT, 'coldOutletT': coldOutletT,
        'Re_t': Re_t, 'Re_s': Re_s, 'deltaPTube': deltaPTube, 'deltaPShell': deltaPShell,
        'steps': steps,
        'dy_int': dy_int, 'dy_ext': dy_ext, 'estimatedTimeStep': estimatedTimeStep
    }

def generate_solidworks_macro(state, results):
    is_cross = state.get('geometryType') == 'cross-flow-bank'
    do_half = state['shellDo'] / 2
    if is_cross:
        draw_base = f"Part.SketchManager.CreateCenterRectangle 0, 0, 0, {do_half:.4f}, {do_half:.4f}, 0"
    else:
        draw_base = f"Part.SketchManager.CreateCircleByRadius2 0, 0, 0, {do_half:.4f}"
        
    return f"""' SW VBA Macro para Geometria de Trocador de Calor
Dim swApp As Object
Dim Part As Object
Dim boolstatus As Boolean
Dim longstatus As Long, longwarnings As Long

Sub main()
    Set swApp = Application.SldWorks
    Set Part = swApp.NewDocument("C:\\ProgramData\\SolidWorks\\SOLIDWORKS 202X\\templates\\Part.prtdot", 0, 0, 0)
    swApp.ActivateDoc2 "Peça1", False, longstatus
    
    Part.Extension.SelectByID2 "Plano frontal", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    Part.SketchManager.InsertSketch True
    {draw_base}
    Part.FeatureManager.FeatureExtrusion3 True, False, False, 0, 0, {state['tubeLength']:.4f}, 0, False, False, False, False, 0, 0, False, False, False, False, True, True, True, 0, 0, False

    ' Padrão para os Tubos (Numero previsto: {results['Nt']})
    Part.Extension.SelectByID2 "Face frontal", "FACE", 0, 0, 0, False, 0, Nothing, 0
    Part.SketchManager.InsertSketch True
    Part.SketchManager.CreateCircleByRadius2 0, 0, 0, {(state['tubeDo']/2000):.4f}
    Part.FeatureManager.FeatureCut4 True, False, False, 1, 0, {state['tubeLength']:.4f}, 0, False, False, False, False, 1.74532925199433E-02, 1.74532925199433E-02, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False
End Sub"""

def generate_fluent_meshing(state, results):
    return f""";; Script ANSYS Fluent Meshing (TUI)
/file/import/cad "TrocadorCalor_Geometria.STEP"
/size-functions/create curvature-size
/size-functions/set-scaling-parameters 1.2
/mesh/prism/controls/grow-prisms geometric
/mesh/prism/controls/number-of-layers 12
/mesh/prism/controls/growth-rate 1.2

/mesh/prism/controls/zone-specific-prisms "tube_walls_internal" yes
/mesh/prism/controls/zone-specific-first-height "tube_walls_internal" {results['dy_int']:.4e}

/mesh/prism/controls/zone-specific-prisms "tube_walls_external" yes
/mesh/prism/controls/zone-specific-first-height "tube_walls_external" {results['dy_ext']:.4e}

/mesh/volume/polyhedra
/mesh/volume/create yes
/mesh/repair/improve-quality
/file/write-mesh "TrocadorCalor_Malha.msh"
"""

def generate_fluent_setup(state, results):
    turbTui = "/define/models/viscous/ke-standard yes" if state.get('turbModel') == 'k-epsilon' else "/define/models/viscous/kw-sst yes"
    is_transient = state.get('simType') == 'transient'
    transientTui = f"/define/models/unsteady-2nd-order yes\n/solve/set/time-step {results['estimatedTimeStep']:.4e}\n/solve/dual-time-iterate {state.get('timeSteps', 100)} {state.get('iterPerStep', 20)}" if is_transient else f"/solve/iterate {state.get('iterSteady', 100)}"
    return f""";; Script ANSYS Fluent Setup & Solve (TUI)
/file/read-case "TrocadorCalor_Malha.msh"
/define/models/energy yes
{turbTui}

/define/boundary-conditions/mass-flow-inlet tube_inlet yes yes {state['hotMdot']} no {state['hotInletT'] + 273.15}
/define/boundary-conditions/mass-flow-inlet shell_inlet yes yes {state['coldMdot']} no {state['coldInletT'] + 273.15}

/solve/monitors/surface/set-monitor "hot-outlet-temp" "mass-avg" "temperature" "tube_outlet" () yes yes "hot_out_t.out"
/solve/monitors/surface/set-monitor "cold-outlet-temp" "mass-avg" "temperature" "shell_outlet" () yes yes "cold_out_t.out"
/solve/monitors/surface/set-monitor "total-heat-flux" "integral" "heat-flux" "tube_walls" () yes yes "heat_flux.out"

/solve/monitors/residual/convergence-criteria {state.get('residualsTarget', 1e-4)} {state.get('residualsTarget', 1e-4)} {state.get('residualsTarget', 1e-4)} {state.get('residualsTarget', 1e-4)} {state.get('residualsTarget', 1e-4)} {state.get('residualsTarget', 1e-4)}

/solve/initialize/hyb-initialization
{transientTui}
/file/write-case-data "TrocadorCalor_Resolvido.cas"
"""



# --- UI ---
st.title("🔥 ThermoX - Trocador de Calor")

tab1, tab2, tab3, tab4 = st.tabs(["Setup", "Cálculos Analíticos", "Desenho 2D", "Scripts CFD/CAD"])

with tab1:
    st.markdown("### 🧮 Balanço Térmico (Variável Desconhecida / Alvo)")
    
    col_bal_1, col_bal_2 = st.columns(2)
    with col_bal_1:
        solve_target = st.selectbox("Calcular:", [
            ('heat_duty', "Definir Fluxo de Calor (Calcular Ambas Saídas)"),
            ('hot_outlet', "Calcular Temperatura de Saída (Quente/Tubo)"),
            ('cold_outlet', "Calcular Temperatura de Saída (Frio/Casco)"),
            ('hot_mdot', "Calcular Vazão Mássica Necessária (Quente)"),
            ('cold_mdot', "Calcular Vazão Mássica Necessária (Frio)"),
        ], format_func=lambda x: x[1])[0]
    with col_bal_2:
        heat_duty = st.number_input("Fluxo de Calor Desejado (kW)", value=417.0, disabled=(solve_target != 'heat_duty'))

    st.markdown("---")

    col_hot, col_cold = st.columns(2)
    fluid_opts = [('water', 'Água Líquida'), ('air', 'Ar (Gás Ideial)'), ('oil', 'Óleo Motor'), ('ethylene', 'Etilenoglicol')]

    with col_hot:
        st.markdown("### 🌡️ Fluido Quente (Tubos)")
        hot_fluid = st.selectbox("Tipo de Fluido Quente", fluid_opts, format_func=lambda x: x[1])[0]
        hot_inlet_t = st.number_input("Temp. Entrada Quente (°C)", value=90.0)
        hot_mdot = st.number_input("Vazão Mássica Quente (kg/s)", value=5.0, disabled=(solve_target == 'hot_mdot'))
        hot_target_outlet_t = st.number_input("Temp. Saída Quente (°C) (Alvo)", value=70.0, disabled=(solve_target in ['hot_outlet', 'heat_duty']))

    with col_cold:
        st.markdown("### 💧 Fluido Frio (Casco)")
        cold_fluid = st.selectbox("Tipo de Fluido Frio", fluid_opts, format_func=lambda x: x[1])[0]
        cold_inlet_t = st.number_input("Temp. Entrada Fria (°C)", value=25.0)
        cold_mdot = st.number_input("Vazão Mássica Fria (kg/s)", value=10.0, disabled=(solve_target == 'cold_mdot'))
        cold_target_outlet_t = st.number_input("Temp. Saída Fria (°C) (Alvo)", value=35.0, disabled=(solve_target in ['cold_outlet', 'heat_duty']))

    st.markdown("---")

    col_geom, col_foul = st.columns(2)
    with col_geom:
        st.markdown("### 📦 Geometria Externa & Tubos")
        geom_type = st.selectbox("Tipo de Trocador", [('shell-tube', 'Casco e Tubos'), ('cross-flow-bank', 'Banco de Tubos')], format_func=lambda x: x[1])[0]
        material = st.selectbox("Material de Construção", [('copper', 'Cobre'), ('aluminum', 'Alumínio'), ('steel', 'Aço Carbono'), ('ss304', 'Inox 304')], format_func=lambda x: x[1])[0]
        
        row1_g1, row1_g2 = st.columns(2)
        with row1_g1:
            shell_do = st.number_input("Diâmetro / Largura (m)", value=0.6)
        with row1_g2:
            baffle_spacing = st.number_input("Espaç. Chicanas (m)", value=0.5, disabled=(geom_type != 'shell-tube'))

        row2_g1, row2_g2, row2_g3 = st.columns(3)
        with row2_g1:
            tube_do = st.number_input("Ø Ext. Tubo(mm)", value=19.05)
        with row2_g2:
            tube_thickness = st.number_input("Espessura (mm)", value=1.65)
        with row2_g3:
            tube_length = st.number_input("Comp. (m)", value=3.0)

        row3_g1, row3_g2, row3_g3 = st.columns(3)
        with row3_g1:
            tube_pitch = st.number_input("Passo (mm)", value=25.4)
            bundle_alignment = st.selectbox("Arranjo", [('aligned', 'Alinhado'), ('staggered', 'Desalinhado')], format_func=lambda x: x[1], disabled=(geom_type == 'shell-tube'))[0]
        with row3_g2:
            tube_passes = st.number_input("Passes Tubo (N)", value=2, disabled=(geom_type != 'shell-tube'))
        with row3_g3:
            tube_pitch_longitudinal = st.number_input("P. Long. (SL) mm", value=25.4, disabled=(geom_type == 'shell-tube'))

    with col_foul:
        st.markdown("### ⚙️ Fator de Encrustração (Fouling)")
        fouling_hot = st.number_input("Fator Quente (m².K/W)", value=0.0001, format="%.4f")
        fouling_cold = st.number_input("Fator Frio (m².K/W)", value=0.0002, format="%.4f")

with tab2:
    if st.button("Executar Simulação", type="primary"):
        state = {
            'solveTarget': solve_target,
            'targetHeatDuty': heat_duty * 1000,
            'hotFluidId': hot_fluid,
            'coldFluidId': cold_fluid,
            'hotInletT': hot_inlet_t,
            'hotMdot': hot_mdot,
            'hotTargetOutletT': hot_target_outlet_t,
            'coldInletT': cold_inlet_t,
            'coldMdot': cold_mdot,
            'coldTargetOutletT': cold_target_outlet_t,
            'materialId': material,
            'geometryType': geom_type,
            'bundleAlignment': bundle_alignment,
            'tubeLength': tube_length,
            'shellDo': shell_do,
            'baffleSpacing': baffle_spacing,
            'tubeDo': tube_do,
            'tubeThickness': tube_thickness,
            'tubePitch': tube_pitch,
            'tubePitchLongitudinal': tube_pitch_longitudinal,
            'tubePasses': tube_passes,
            'foulingHot': fouling_hot,
            'foulingCold': fouling_cold
        }
        
        try:
            res = calculate(state)
            st.session_state['res'] = res
            st.session_state['state'] = state
        except Exception as e:
            st.error(f"Erro no cálculo: {e}")

    if 'res' in st.session_state:
        res = st.session_state['res']
        
        if res['warnings']:
            for w in res['warnings']:
                st.error(w)

        st.write("### 📈 Desempenho Termodinâmico")
        col_res1, col_res2, col_res3, col_res4, col_res5, col_res6 = st.columns(6)
        col_res1.metric("Calor Troc. (kW)", f"{(res['q']/1000):.2f}")
        col_res2.metric("LMTD (°C)", f"{res['lmtd']:.2f}")
        col_res3.metric("Fator F", f"{res['F']:.2f}")
        col_res4.metric("T Saída Q.", f"{res['hotOutletT']:.2f}")
        col_res5.metric("T Saída F.", f"{res['coldOutletT']:.2f}")
        col_res6.metric("U Global", f"{res['U']:.1f}")
        
        st.write("### 📐 Dimensionamento da Geometria")
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        col_g1.metric("Área Necess. (m²)", f"{res['Area']:.2f}")
        col_g2.metric("Nº Tubos", res['Nt'])
        col_g3.metric("Vel. Tubos (m/s)", f"{res['v_t']:.3f}")
        col_g4.metric("Vel. Casco (m/s)", f"{res['v_s']:.3f}")

        st.write("### 🔬 Fenômenos de Transporte")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        col_f1.metric("Reynolds Tubos", f"{res['Re_t']:.0f}")
        col_f2.metric("Reynolds Casco", f"{res['Re_s']:.0f}")
        col_f3.metric("ΔP Tubos (kPa)", f"{(res['deltaPTube']/1000):.2f}")
        col_f4.metric("ΔP Casco (kPa)", f"{(res['deltaPShell']/1000):.2f}")

        with st.expander("📄 Memória de Cálculo (Passo a Passo)"):
            st.markdown("\n\n".join(res['steps']))
    else:
        st.info("Ajuste os parâmetros na aba 'Setup' e clique em 'Executar Simulação'.")

with tab3:
    st.write("### Modelos da Geometria (2D e Isométrico)")
    if 'state' in st.session_state:
        stt = st.session_state['state']
        rs = st.session_state['res']
        
        do = stt['shellDo'] * 1000  # meters to mm
        pt = stt['tubePitch']
        n_tubes = min(rs['Nt'], 1000)
        
        col_t3_1, col_t3_2 = st.columns(2)
        with col_t3_1:
            st.markdown("#### Vista de Seção Transversal")
            svg_elements = []
            svg_width = 400
            svg_height = 400
            center_x = svg_width / 2
            center_y = svg_height / 2
            scale = min(svg_width, svg_height) / (do * 1.2) if do > 0 and stt['geometryType'] == 'shell-tube' else min(svg_width, svg_height) / (math.sqrt(n_tubes) * pt * 1.2) if n_tubes > 0 and pt > 0 else 1
            
            if stt['geometryType'] == 'shell-tube':
                # Draw shell
                svg_elements.append(f'<circle cx="{center_x}" cy="{center_y}" r="{do/2 * scale}" fill="none" stroke="#0ea5e9" stroke-width="3" />')
                
                pts_side = math.ceil(math.sqrt(n_tubes) * 1.2)
                count = 0
                for i in range(-pts_side, pts_side):
                    for j in range(-pts_side, pts_side):
                        x_dist = i * pt
                        y_dist = j * pt
                        
                        if x_dist*x_dist + y_dist*y_dist < ((do/2)*0.9)**2:
                            cx = center_x + x_dist * scale
                            cy = center_y + y_dist * scale
                            r = (stt['tubeDo']/2) * scale
                            svg_elements.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#cbd5e1" stroke="#475569" stroke-width="1" />')
                            count += 1
                            if count >= n_tubes: break
                    if count >= n_tubes: break
            else:
                w = math.sqrt(n_tubes) * pt
                w_scaled = w * scale
                rect_x = center_x - w_scaled/2
                rect_y = center_y - w_scaled/2
                svg_elements.append(f'<rect x="{rect_x}" y="{rect_y}" width="{w_scaled}" height="{w_scaled}" fill="none" stroke="#0ea5e9" stroke-width="3" />')
                
                pts_side = math.ceil(math.sqrt(n_tubes))
                count = 0
                is_staggered = stt['bundleAlignment'] == 'staggered'
                for i in range(pts_side):
                    for j in range(pts_side):
                        offset = pt/2 if (is_staggered and i%2!=0) else 0
                        x_dist = -w/2 + i * pt + offset
                        y_dist = -w/2 + j * pt
                        
                        if (x_dist < w/2) and (y_dist < w/2):
                            cx = center_x + x_dist * scale
                            cy = center_y + y_dist * scale
                            r = (stt['tubeDo']/2) * scale
                            svg_elements.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#cbd5e1" stroke="#475569" stroke-width="1" />')
                            count += 1
                            if count >= n_tubes: break
                    if count >= n_tubes: break

            svg_content = f'''
            <div style="background-color: #0f172a; padding: 10px; border-radius: 12px; border: 1px solid #1e293b; display: flex; justify-content: center;">
                <svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
                    {"".join(svg_elements)}
                </svg>
            </div>
            '''
            st.markdown(svg_content, unsafe_allow_html=True)
            
        with col_t3_2:
            st.markdown("#### Diagrama Isométrico (Esquemático de Fluxos)")
            
            # Simple Schematic logic
            schematic_svg = f'''
            <div style="background-color: #0f172a; padding: 10px; border-radius: 12px; border: 1px solid #1e293b; display: flex; justify-content: center;">
                <svg width="400" height="400" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="hotGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" style="stop-color:#ef4444;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#f97316;stop-opacity:1" />
                        </linearGradient>
                        <linearGradient id="coldGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#0ea5e9;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    
                    <!-- Cylinder / Core Body -->
                    <path d="M 120 180 L 280 140 L 320 220 L 160 260 Z" fill="#1e293b" stroke="#64748b" stroke-width="2"/>
                    <path d="M 160 260 L 320 220 L 320 240 L 160 280 Z" fill="#0f172a" stroke="#64748b" stroke-width="1"/>
                    
                    <!-- Hot Fluid In (Red) - Tubes -->
                    <path d="M 40 200 L 100 200" stroke="url(#hotGrad)" stroke-width="6" fill="none" marker-end="url(#arrowHot)"/>
                    <polygon points="100,195 110,200 100,205" fill="#f97316"/>
                    <text x="30" y="190" fill="#f8fafc" font-size="12">Quente (IN)</text>
                    
                    <!-- Hot Fluid Out -->
                    <path d="M 340 200 L 380 200" stroke="url(#hotGrad)" stroke-width="6" fill="none"/>
                    <polygon points="380,195 390,200 380,205" fill="#f97316"/>
                    <text x="330" y="190" fill="#f8fafc" font-size="12">Quente (OUT)</text>
                    
                    <!-- Cold Fluid In (Blue) - Shell/Bank -->
                    <path d="M 220 320 L 220 270" stroke="url(#coldGrad)" stroke-width="6" fill="none"/>
                    <polygon points="215,270 220,260 225,270" fill="#3b82f6"/>
                    <text x="210" y="340" fill="#f8fafc" font-size="12">Frio (IN)</text>

                    <!-- Cold Fluid Out -->
                    <path d="M 220 130 L 220 80" stroke="url(#coldGrad)" stroke-width="6" fill="none"/>
                    <polygon points="215,80 220,70 225,80" fill="#0ea5e9"/>
                    <text x="210" y="60" fill="#f8fafc" font-size="12">Frio (OUT)</text>
                </svg>
            </div>
            '''
            st.markdown(schematic_svg, unsafe_allow_html=True)

        st.markdown("---")
        st.write("### 💻 Script SolidWorks Macro (VBA)")
        st.code(generate_solidworks_macro(stt, rs), language="vbnet")
        
    else:
         st.info("Execute a simulação primeiro na aba Setup.")

with tab4:
    if 'state' in st.session_state:
        stt = st.session_state['state']
        rs = st.session_state['res']
        
        st.write("### Geração de Scripts CFD (OpenFOAM / Fluent)")
        
        cfd_col1, cfd_col2 = st.columns([1, 2])
        
        with cfd_col1:
            st.markdown("#### Configurações Base")
            sim_type = st.radio("Método", ['Permanente (Steady)', 'Transiente'])
            turb_model = st.selectbox("Modelo de Turbulência", ['k-epsilon Standard', 'k-omega SST'])
            y_plus = st.number_input("Valor Y+ Almejado (Camada Limite)", value=35.0, min_value=0.1)
            iter_total = st.number_input("Iterações Máximas", value=500, min_value=10)
            res_target = st.number_input("Critérios de Convergência (Resíduos)", value=1e-4, format="%.5f")
            
            # Atualiza objeto state com essas definições locais e recomputa o deltaT
            stt['simType'] = 'transient' if sim_type == 'Transiente' else 'steady'
            stt['turbModel'] = 'k-epsilon' if turb_model == 'k-epsilon Standard' else 'k-omega'
            stt['yPlusTarget'] = y_plus
            stt['iterSteady'] = iter_total
            stt['residualsTarget'] = res_target
            
            # Recalcula Y+ scripts rapidinhos sem precisar ir pro backend pesado
            hotF = evaluate_fluid_props(stt['hotFluidId'], stt['hotInletT'])
            coldF = evaluate_fluid_props(stt['coldFluidId'], stt['coldInletT'])
            cf_t = 0.058 * (rs['Re_t']**-0.2) if rs['Re_t'] > 0 else 0
            u_tau_t = math.sqrt((cf_t * hotF['density'] * (rs['v_t']**2) / 2) / hotF['density']) if rs['v_t'] > 0 else 0.01
            rs['dy_int'] = y_plus * hotF['mu'] / (hotF['density'] * u_tau_t) if u_tau_t > 0 else 1e-5
            
            cf_s = 0.058 * (max(rs['Re_s'], 1)**-0.2)
            u_tau_s = math.sqrt((cf_s * coldF['density'] * (rs['v_s']**2) / 2) / coldF['density']) if rs['v_s'] > 0 else 0.01
            rs['dy_ext'] = y_plus * coldF['mu'] / (coldF['density'] * u_tau_s) if u_tau_s > 0 else 1e-5

        with cfd_col2:
            st.markdown("#### Scripts Exportados (ANSYS Fluent TUI)")
            st.write("##### 1. Fluent Meshing (TUI) - PolyHexcore e Camada Limite")
            st.code(generate_fluent_meshing(stt, rs), language="scheme")
            
            st.write("##### 2. Fluent Setup & Solver (TUI) - Condições de Contorno")
            st.code(generate_fluent_setup(stt, rs), language="scheme")
            
    else:
        st.info("Execute a simulação primeiro.")
