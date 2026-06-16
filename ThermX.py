import streamlit as st
import math

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
    {'T': 300, 'density': 1.1614, 'cp': 1007, 'mu': 184.6e-7, 'k': 26.3e-3, 'pr': 0.707},
    {'T': 400, 'density': 0.8711, 'cp': 1014, 'mu': 230.1e-7, 'k': 33.8e-3, 'pr': 0.690},
    {'T': 500, 'density': 0.6964, 'cp': 1029, 'mu': 270.1e-7, 'k': 40.7e-3, 'pr': 0.684},
    {'T': 600, 'density': 0.5804, 'cp': 1051, 'mu': 305.8e-7, 'k': 46.9e-3, 'pr': 0.685},
]

water_table = [
    {'T': 300, 'density': 997.0, 'cp': 4179, 'mu': 855e-6, 'k': 0.613, 'pr': 5.83},
    {'T': 320, 'density': 989.0, 'cp': 4180, 'mu': 577e-6, 'k': 0.640, 'pr': 3.77},
    {'T': 340, 'density': 979.0, 'cp': 4188, 'mu': 420e-6, 'k': 0.660, 'pr': 2.66},
]

def evaluate_fluid_props(fluid_id, T_celcius):
    base_fluid = FLUIDS[fluid_id].copy()
    T_k = T_celcius + 273.15
    if fluid_id == 'air':
        props = get_interpolated_props(T_k, air_table)
        base_fluid.update(props)
    elif fluid_id == 'water':
        props = get_interpolated_props(T_k, water_table)
        base_fluid.update(props)
    return base_fluid

def calculate(state):
    steps = []
    warnings = []
    mat = MATERIALS[state['materialId']]

    hotMdot = state['hotMdot']
    coldMdot = state['coldMdot']
    hotOutletT = state['hotInletT'] - 10 # dummy initial
    coldOutletT = state['coldInletT'] + 10

    q = state['targetHeatDuty']
    hotOutletT = state['hotInletT'] - (q / (hotMdot * evaluate_fluid_props(state['hotFluidId'], state['hotInletT'])['cp']))
    coldOutletT = state['coldInletT'] + (q / (coldMdot * evaluate_fluid_props(state['coldFluidId'], state['coldInletT'])['cp']))

    T_hot_mean = (state['hotInletT'] + hotOutletT) / 2
    T_cold_mean = (state['coldInletT'] + coldOutletT) / 2
    
    hotF = evaluate_fluid_props(state['hotFluidId'], T_hot_mean)
    coldF = evaluate_fluid_props(state['coldFluidId'], T_cold_mean)

    dT1 = state['hotInletT'] - coldOutletT
    dT2 = hotOutletT - state['coldInletT']
    
    lmtd = 1
    if abs(dT1 - dT2) > 0.01 and dT1 > 0 and dT2 > 0:
        lmtd = (dT1 - dT2) / math.log(dT1 / dT2)
    else:
        lmtd = max(dT1, dT2, 1)

    F = 1.0
    if state['geometryType'] == 'cross-flow-bank':
        R = abs((state['hotInletT'] - hotOutletT) / (coldOutletT - state['coldInletT']))
        P = abs((coldOutletT - state['coldInletT']) / (state['hotInletT'] - state['coldInletT']))
        if R != 1 and P > 0 and P < 1:
            num = math.sqrt(R*R + 1) * math.log((1 - P) / (1 - P*R))
            denInner = (2 - P*(R + 1 - math.sqrt(R*R + 1))) / (2 - P*(R + 1 + math.sqrt(R*R + 1)))
            F_calc = num / ((R - 1) * math.log(denInner))
            if F_calc > 0.4: F = F_calc
        if F < 0.75:
            warnings.append(f"Aviso de Baixa Eficiência Térmica (F = {F:.2f}).")

    Do = state['tubeDo'] / 1000
    t = state['tubeThickness'] / 1000
    Di = Do - 2 * t
    Pt = state['tubePitch'] / 1000

    Nt = 20
    U, v_t, v_s, Re_t, Re_s, h_i, h_o = 500, 0, 0, 0, 0, 1000, 1000

    coldF_surface = evaluate_fluid_props(state['coldFluidId'], (T_hot_mean + T_cold_mean) / 2)
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
            
        v_t = hotMdot / (hotF['density'] * A_cross_t)
        Re_t = abs(hotF['density'] * v_t * Di / hotF['mu'])
        
        Nu_t = 4.36
        if Re_t >= 10000:
            Nu_t = 0.023 * (Re_t**0.8) * (hotF['prandtl']**0.3)
            
        h_i = Nu_t * hotF['k'] / Di
        
        # Escoamento externo
        As = 0
        if state['geometryType'] != 'cross-flow-bank':
            As = (Pt - Do) * state['shellDo'] * state['baffleSpacing'] / Pt
            v_s = coldMdot / (coldF['density'] * As)
            D_eq = (4 * ((Pt**2) - (math.pi * (Do**2) / 4))) / (math.pi * Do)
            Re_s = abs(coldF['density'] * v_s * D_eq / coldF['mu'])
            Nu_s = 0.36 * (Re_s**0.55) * (coldF['prandtl']**0.33)
            h_o = Nu_s * coldF['k'] / D_eq
        else:
            w = w_effective
            ST = Pt
            SL = state.get('tubePitchLongitudinal', 25) / 1000
            v_app = coldMdot / (coldF['density'] * w * state['tubeLength'])
            v_max = v_app * (ST / (ST - Do))
            
            if state['bundleAlignment'] == 'staggered':
                SD = math.sqrt((ST/2)**2 + SL**2)
                if 2 * (SD - Do) < (ST - Do):
                    v_max = v_app * (ST / (2 * (SD - Do)))
            
            v_s = v_max
            Re_s = abs(coldF['density'] * v_s * Do / coldF['mu'])
            
            C, m = 0.022, 0.84
            if state['bundleAlignment'] == 'staggered':
                if Re_s < 1000:
                    C, m = 0.51, 0.50
            
            Nu_s = C * (Re_s**m) * (coldF['prandtl']**0.36) * ((coldF['prandtl'] / coldF_surface['prandtl'])**0.25)
            h_o = Nu_s * coldF['k'] / Do

        R_wall = (Do / (2 * mat['k'])) * math.log(Do / Di)
        R_fi = state['foulingHot'] * (Do / Di)
        R_fo = state['foulingCold']
        
        U = 1 / ( (1/h_i)*(Do/Di) + R_wall + R_fi + R_fo + (1/h_o) )
        A_req = q / (U * lmtd * F)
        Nt_new = math.ceil(A_req / (math.pi * Do * state['tubeLength']))
        Nt = math.ceil(0.4 * Nt_new + 0.6 * Nt)
        
    return {
        'U': U, 'Area': Nt * math.pi * Do * state['tubeLength'],
        'Nt': Nt, 'v_t': v_t, 'v_s': v_s, 'h_i': h_i, 'h_o': h_o,
        'warnings': warnings
    }

st.title("Simulador de Trocador de Calor Térmico")

st.sidebar.header("Parâmetros do Problema")
q = st.sidebar.number_input("Carga Térmica (W)", value=417000)
T_hot_in = st.sidebar.number_input("T Quente Entrada (°C)", value=90)
M_hot = st.sidebar.number_input("Vazão Quente (kg/s)", value=5.0)

T_cold_in = st.sidebar.number_input("T Frio Entrada (°C)", value=25)
M_cold = st.sidebar.number_input("Vazão Frio (kg/s)", value=10.0)

st.sidebar.header("Geometria")
geom_type = st.sidebar.selectbox("Tipo de Trocador", ['cross-flow-bank', 'shell-tube'])
alignment = st.sidebar.selectbox("Alinhamento", ['staggered', 'aligned'])
length = st.sidebar.number_input("Comprimento do Tubo (m)", value=3.0)
shell_do = st.sidebar.number_input("Largura do Duto (m)", value=0.6)

if st.button("Simular"):
    state = {
        'solveTarget': 'heat_duty',
        'targetHeatDuty': q,
        'hotFluidId': 'water',
        'coldFluidId': 'air' if geom_type == 'cross-flow-bank' else 'water',
        'hotInletT': T_hot_in,
        'hotMdot': M_hot,
        'coldInletT': T_cold_in,
        'coldMdot': M_cold,
        'materialId': 'copper',
        'geometryType': geom_type,
        'bundleAlignment': alignment,
        'tubeLength': length,
        'shellDo': shell_do,
        'tubeDo': 19.05,
        'tubeThickness': 1.65,
        'tubePitch': 25.4,
        'foulingHot': 0.0001,
        'foulingCold': 0.0002
    }
    
    res = calculate(state)
    
    st.write("### Resultados")
    st.metric("Coeficiente Global U (W/m²K)", f"{res['U']:.2f}")
    st.metric("Área Requerida (m²)", f"{res['Area']:.2f}")
    st.metric("Número de Tubos", res['Nt'])
    st.metric("Velocidade Interna (m/s)", f"{res['v_t']:.3f}")
    st.metric("Velocidade Externa Máxima (m/s)", f"{res['v_s']:.3f}")
    
    if res['warnings']:
        st.warning("Avisos:")
        for w in res['warnings']:
            st.write(f"- {w}")
