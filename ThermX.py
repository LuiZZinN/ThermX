import streamlit as st
import streamlit.components.v1 as components
import math

st.set_page_config(layout="wide", page_title="Simulador de Trocador de Calor", page_icon="🔥", initial_sidebar_state="expanded")

st.markdown("""
<style>
/* Custom Light Theme overrides */
[data-testid="stAppViewContainer"] {
    background-color: #f4f7fb;
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] {
    background-color: transparent;
}

/* Custom top header */
.custom-header {
    background-color: #2b6cb0;
    color: white;
    padding: 20px 30px;
    border-radius: 8px;
    margin-bottom: 25px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.custom-header h1 {
    color: white !important;
    margin: 0;
    font-size: 24px;
    font-weight: 600;
}
.custom-header p {
    color: #e2e8f0;
    margin: 4px 0 0 0;
    font-size: 14px;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    height: 40px;
    background-color: white;
    border-radius: 6px 6px 0 0;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    color: #475569;
    padding: 0 20px;
}
.stTabs [aria-selected="true"] {
    background-color: #f4f7fb !important;
    color: #2b6cb0 !important;
    border-bottom: 2px solid #2b6cb0 !important;
    font-weight: bold;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}
[data-testid="stMetricLabel"] {
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 500;
}
[data-testid="stMetricValue"] {
    color: #1e293b;
    font-size: 1.5rem;
}

h2, h3, h4 {
    color: #1e293b !important;
}

hr {
    border-color: #e2e8f0;
}

/* Sidebar styling to look like the image */
[data-testid="stSidebar"] {
    background-color: white !important;
    border-right: 1px solid #e2e8f0;
}
.sidebar-header {
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.execute-btn button {
    background-color: #ef4444 !important;
    color: white !important;
    border-radius: 6px !important;
    border: none !important;
    font-weight: bold !important;
    margin-top: 15px !important;
}
.execute-btn button:hover {
    background-color: #dc2626 !important;
}

</style>
""", unsafe_allow_html=True)


# Define dictionaries for options
targ_opts = {
    'heat_duty': "Definir Fluxo de Calor (Calcular Ambas Saídas)",
    'hot_outlet': "Calcular Temperatura de Saída (Quente/Tubo)",
    'cold_outlet': "Calcular Temperatura de Saída (Frio/Casco)",
    'hot_mdot': "Calcular Vazão Mássica Necessária (Quente)",
    'cold_mdot': "Calcular Vazão Mássica Necessária (Frio)",
}
fluid_opts = {
    'water': 'Água Líquida',
    'air': 'Ar (Gás Ideal)',
    'engine_oil': 'Óleo Motor',
    'ethylene_glycol': 'Etilenoglicol (100%)'
}
geom_opts = {
    'shell-tube': 'Casco e Tubos',
    'cross-flow-bank': 'Banco de Tubos'
}
mat_opts = {
    'copper': 'Cobre',
    'aluminum': 'Alumínio',
    'steel': 'Aço Carbono',
    'ss304': 'Inox 304'
}
arr_opts = {
    'aligned': 'Alinhado',
    'staggered': 'Desalinhado'
}


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

    hotF = evaluate_fluid_props(state['hotFluidId'], state['hotInletT'])
    coldF = evaluate_fluid_props(state['coldFluidId'], state['coldInletT'])

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
    R, P = 1.0, 0.0
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

    T_surface = ((state['hotInletT'] + hotOutletT)/2 + (state['coldInletT'] + coldOutletT)/2) / 2
    coldF_surface = evaluate_fluid_props(state['coldFluidId'], T_surface)

    steps.append("## 1. Avaliação das Propriedades dos Fluidos")
    steps.append("As propriedades termo-físicas foram avaliadas nas temperaturas médias de cada fluido no trocador:")
    steps.append(f"- **Fluido Quente (Tubos):** $T_{{m,q}} = {T_hot_mean:.2f} ^\\circ C$")
    steps.append(f"  - $\\rho = {hotF['density']:.2f} \\; kg/m^3$, $C_p = {hotF['cp']:.2f} \\; J/kg \\cdot K$, $k = {hotF['k']:.4f} \\; W/m \\cdot K$, $\\mu = {hotF['mu']:.6f} \\; Pa \\cdot s$, $Pr = {hotF['prandtl']:.2f}$")
    steps.append(f"- **Fluido Frio (Casco/Banco):** $T_{{m,f}} = {T_cold_mean:.2f} ^\\circ C$")
    steps.append(f"  - $\\rho = {coldF['density']:.2f} \\; kg/m^3$, $C_p = {coldF['cp']:.2f} \\; J/kg \\cdot K$, $k = {coldF['k']:.4f} \\; W/m \\cdot K$, $\\mu = {coldF['mu']:.6f} \\; Pa \\cdot s$, $Pr = {coldF['prandtl']:.2f}$")
    steps.append(f"  - Propriedades na temperatura de superfície ($T_s = {T_surface:.2f} ^\\circ C$) para correção de viscosidade: $Pr_s = {coldF_surface['prandtl']:.2f}$")

    steps.append("\\n## 2. Balanço Térmico e Diferença Média de Temperatura")
    steps.append("- Resolvendo o Balanço de Energia Analítico: $Q = \\dot{m}_{quente} C_{p,quente} (T_{ent,q} - T_{sai,q}) = \\dot{m}_{frio} C_{p,frio} (T_{sai,f} - T_{ent,f})$")
    steps.append(f"  - **$Q_{{Trocado}}$ = {q/1000:.2f} kW**")
    steps.append(f"  - Vazões: $\\dot{{m}}_{{quente}} = {hotMdot:.3f} \\; kg/s$, $\\dot{{m}}_{{frio}} = {coldMdot:.3f} \\; kg/s$")
    steps.append(f"  - Temperaturas Quente: $T_{{ent}} = {state['hotInletT']:.2f} ^\\circ C \\rightarrow T_{{sai}} = {hotOutletT:.2f} ^\\circ C$")
    steps.append(f"  - Temperaturas Frio: $T_{{ent}} = {state['coldInletT']:.2f} ^\\circ C \\rightarrow T_{{sai}} = {coldOutletT:.2f} ^\\circ C$")
    steps.append(f"- Diferença de Temperatura Logarítmica Média (LMTD) calculada: **$\\Delta T_{{lm}} = {lmtd:.2f} ^\\circ C$**")
    if state['geometryType'] in ['cross-flow-bank', 'shell-tube']:
        steps.append(f"- Fator de Correção Geométrica $F$: **{F:.3f}** (Baseado nos parâmetros R={R:.3f} e P={P:.3f})")
        if F < 0.75:
            steps.append("  - ⚠️ *Aviso:* Fator F < 0.75 indica baixo rendimento para esta geometria. Considerar alterar passes ou configuração.")

    steps.append("\\n## 3. Coeficientes de Transferência de Calor (Correlações Específicas)")
    
    Do = state['tubeDo'] / 1000
    t = state['tubeThickness'] / 1000
    Di = Do - 2 * t
    Pt = state['tubePitch'] / 1000

    Nt = 20
    U, v_t, v_s, Re_t, Re_s, h_i, h_o, A_cross_t, As, N_L = 500, 0, 0, 0, 0, 1000, 1000, 0.001, 0.001, 1

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
            steps.append(f"- Número de Reynolds $Re_{{tubos}} = \\frac{{\\rho v_t D_i}}{{\\mu}} = {Re_t:.1f}$ (Regime: {'Turbulento' if Re_t > 4000 else 'Transição/Laminar'})")
            steps.append(f"- Número de Nusselt (Correlação de Dittus-Boelter / Gnielinski): $Nu_{{tubos}} = {Nu_t:.2f}$")
            steps.append(f"- Coeficiente Convectivo Interno $h_i = \\frac{{Nu_t k}}{{D_i}} = {h_i:.2f} \\; W/m^2K$")
            
            steps.append(f"**Lado do Casco / Banco (Fluido Frio):**")
            steps.append(f"- Número de Reynolds Ext. $Re_{{ext}} = {Re_s:.1f}$ (Baseado na velocidade de $\\approx {v_s:.3f}$ m/s)")
            if state['geometryType'] == 'cross-flow-bank':
                steps.append(f"- Correlação de Zhukauskas aplicada para Banco de Tubos (Arranjo {state.get('bundleAlignment')}, Constantes $C={C:.3f}, m={m:.2f}$)")
            else:
                steps.append(f"- Correlação de Kern estimada para Casco e Tubos (Chicanas = {state.get('baffleSpacing', 0.5):.2f}m)")
            steps.append(f"- Número de Nusselt Externo $Nu_{{ext}} = {Nu_s:.2f}$")
            steps.append(f"- Coeficiente Convectivo Externo $h_o = {h_o:.2f} \\; W/m^2K$")

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

    steps.append("\\n## 4. Queda de Pressão")
    steps.append("**Lado dos Tubos (Fluido Quente):**")
    steps.append(f"- Fator de Atrito de Darcy $f_t = {f_t:.4f}$")
    steps.append(f"- Queda de pressão principal: $\\Delta P_{{tubos}} = f_t \\frac{{L}}{{D_i}} \\frac{{\\rho v^2}}{{2}} = {(deltaPTube/1000):.2f} \\; kPa$")
    steps.append("**Lado do Casco/Banco (Fluido Frio):**")
    if state['geometryType'] == 'shell-tube':
        steps.append(f"- Diâmetro Equivalente do Casco $D_{{eq}} = {D_eq:.3f} \\; m$")
        steps.append(f"- Número de Chicanas Estimado: N_{{ch}} = {numBaffles}")
    else:
        steps.append(f"- Número de fileiras longitudinais $N_L = {N_L}$")
    steps.append(f"- Queda de pressão avaliada: $\\Delta P_{{ext}} = {(deltaPShell/1000):.2f} \\; kPa$")

    steps.append("\\n## 5. Resumo Geométrico e Global")
    steps.append("- Disposição dos Tubos: $N_t = {Nt}$ tubos, Diâmetro Interno: $D_i = {(Di*1000):.2f} mm$, Passo (Pitch): $P_T = {(Pt*1000):.1f} mm$")
    steps.append("- Área Livre e Velocidades:")
    steps.append(f"  - Tubos: Área da seção transversal interna $A_{{c,in}} = {(max(A_cross_t, 1e-6)):.4f} \\; m^2$ $\\rightarrow v_t = {v_t:.3f} \\; m/s$")
    if state['geometryType'] == 'shell-tube':
        steps.append(f"  - Casco: Área livre com chicanas $A_s = {(max(As, 1e-6)):.4f} \\; m^2$ $\\rightarrow v_s = {v_s:.4f} \\; m/s$")
    else:
        steps.append(f"  - Banco: Velocidade máxima no feixe $v_{{max}} = {v_s:.4f} \\; m/s$")
        
    steps.append(f"- Área Total de Troca Térmica: $A_{{total}} = {Nt * math.pi * Do * state['tubeLength']:.3f} \\; m^2$")
    steps.append(f"- Coeficiente Global de Transferência Térmica:")
    steps.append(f"  - $U = \\left[ \\frac{{1}}{{h_i}} \\frac{{D_o}}{{D_i}} + R_{{parede}} + R_{{fouling,i}} + R_{{fouling,o}} + \\frac{{1}}{{h_o}} \\right]^{{-1}} = {U:.2f} \\; W/m^2K$")


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
        'hotMdot': hotMdot, 'coldMdot': coldMdot,
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
    return f""";; ====================================================================
;; Script ANSYS Fluent Meshing (TUI) - Corrigido e Alinhado com o CFD
;; ====================================================================

;; 1. Importação do CAD Geométrico
/file/import/cad "TrocadorCalor_Geometria.STEP"

;; 2. Configuração e Geração Obrigatória da Malha de Superfície (Surface Mesh)
/objects/scoped-sizing/create curvature-size curvature global-lengths 1.0 5.0 1.2
/mesh/surface-mesh/draw-and-mesh

;; 3. Definição dos Escopos de Camadas de Prisma (Boundary Layer)
;; Comando moderno para gerenciar o crescimento geométrico global dos prismas
/mesh/scoped-prisms/set-growth-options geometric 12 1.2

;; Lado Interno: Alinhado com o relatório (dy para y+={state.get('yPlusTarget', 35.0)}) -> {results['dy_int']:.4e} m
/mesh/scoped-prisms/create/specified-first-height internal_prisms tube_walls_internal face-zones "tube_walls_internal" {results['dy_int']:.4e}

;; Lado Externo: Alinhado com o relatório (dy para y+={state.get('yPlusTarget', 35.0)}) -> {results['dy_ext']:.4e} m
/mesh/scoped-prisms/create/specified-first-height external_prisms tube_walls_external face-zones "tube_walls_external" {results['dy_ext']:.4e}

;; 4. Geração das Camadas de Prisma nas Paredes Scoped
/mesh/scoped-prisms/grow

;; 5. Inicialização e Geração da Malha Volumétrica Poliédrica
;; Primeiro o Fluent inicializa o volume a partir das superfícies e prismas
/mesh/volume/initialize
/mesh/volume/polyhedra

;; 6. Otimização de Qualidade e Exportação do Arquivo Final
/mesh/repair/improve-quality
/file/write-mesh "TrocadorCalor_Malha.msh"
"""

def generate_fluent_setup(state, results):
    is_transient = state.get('simType') == 'transient'
    steady_no = "no" if is_transient else "yes"
    
    models_tui = f'''/define/models/steady? {steady_no}
/define/models/energy? yes no no no no
/define/models/viscous/{"ke-standard? yes" if state.get('turbModel', 'k-epsilon') == 'k-epsilon' else "kw-sst? yes"}'''

    hot_mdot = state.get('hotMdot', 2.5)
    hot_t = state.get('hotInletT', 90.0) + 273.15
    cold_mdot = state.get('coldMdot', 5.0)
    cold_t = state.get('coldInletT', 25.0) + 273.15

    bnd_tui = f''';; Tubos (Quente): Mdot = {hot_mdot:.2f} kg/s | T = {hot_t-273.15:.2f} °C ({hot_t:.2f} K)
/define/boundary-conditions/mass-flow-inlet tube_inlet yes yes {hot_mdot} no {hot_t}
;; Casco (Frio): Mdot = {cold_mdot:.2f} kg/s | T = {cold_t-273.15:.2f} °C ({cold_t:.2f} K)
/define/boundary-conditions/mass-flow-inlet shell_inlet yes yes {cold_mdot} no {cold_t}'''

    res_target = state.get('residualsTarget', 1e-4)
    res_tui = f"/solve/monitors/residual/convergence-criteria {res_target} {res_target} {res_target} {res_target} {res_target} {res_target} 0.000001"

    if is_transient:
        init_tui = f'''/solve/initialize/hyb-initialization
/solve/set/time-step {results.get('estimatedTimeStep', 1e-2):.4e}

;; 7. Solução Transiente ({state.get('timeSteps', 100)} passos com max {state.get('iterPerStep', 20)} iterações por passo interno)
/solve/dual-time-iterate {state.get('timeSteps', 100)} {state.get('iterPerStep', 20)}'''
    else:
        init_tui = f'''/solve/initialize/hyb-initialization

;; 7. Solução Permanente ({state.get('iterSteady', 500)} iterações)
/solve/iterate {state.get('iterSteady', 500)}'''

    return f""";; ====================================================================
;; Script ANSYS Fluent Setup & Solve (TUI) - Corrigido e Alinhado
;; ====================================================================

;; 1. Importação Correta da Malha
/file/read-mesh "TrocadorCalor_Malha.msh"

;; 2. Ativação dos Modelos ({'Transiente' if is_transient else 'Permanente'}, Energia e Turbulência)
{models_tui}

;; 3. Condições de Contorno (Alinhadas com o Relatório Otimizado)
{bnd_tui}

;; 4. Criação dos Monitores de Superfície para Validação Térmica
/solve/monitors/surface/set-monitor "hot-outlet-temp" "mass-avg" "temperature" "tube_outlet" () yes yes "hot_out_t.out"
/solve/monitors/surface/set-monitor "cold-outlet-temp" "mass-avg" "temperature" "shell_outlet" () yes yes "cold_out_t.out"
/solve/monitors/surface/set-monitor "total-heat-flux" "integral" "heat-flux" "tube_walls" () yes yes "heat_flux.out"

;; 5. Critérios de Convergência Restritos (Energia em 1e-6)
;; Ordem padrão dos resíduos: continuity, x-vel, y-vel, z-vel, k, epsilon, energy
{res_tui}

;; 6. Inicialização e Configuração do Solucionador
{init_tui}

;; 8. Salvar os Resultados Finais
/file/write-case-data "TrocadorCalor_Resolvido.cas"
"""



# --- UI ---
st.title("🔥 ThermoX - Trocador de Calor")

# --- Initialize Session State Variables ---
if 's_targ' not in st.session_state:
    st.session_state.s_targ = 'heat_duty'
    st.session_state.s_heat_duty = 417.0
    st.session_state.s_h_fluid = 'water'
    st.session_state.s_c_fluid = 'water'
    st.session_state.s_h_in = 90.0
    st.session_state.s_h_mdot = 5.0
    st.session_state.s_h_out = 70.0
    st.session_state.s_c_in = 25.0
    st.session_state.s_c_mdot = 10.0
    st.session_state.s_c_out = 35.0
    
    st.session_state.s_g_type = 'shell-tube'
    st.session_state.s_mat = 'copper'
    st.session_state.s_do = 0.6
    st.session_state.s_baffle = 0.5
    st.session_state.s_t_do = 19.05
    st.session_state.s_t_th = 1.65
    st.session_state.s_length = 3.0
    st.session_state.s_t_pitch = 25.4
    st.session_state.s_arr = 'staggered'
    st.session_state.s_t_passes = 2
    st.session_state.s_t_pl = 25.4
    st.session_state.s_f_h = 0.0001
    st.session_state.s_f_c = 0.0002

def update_calc():
    try:
        # Pega estado anterior dos inputs (usando chaves do session_state via st.number_input key)
        state = {
            'solveTarget': st.session_state.s_targ,
            'targetHeatDuty': st.session_state.s_heat_duty * 1000,
            'hotFluidId': st.session_state.s_h_fluid,
            'coldFluidId': st.session_state.s_c_fluid,
            'hotInletT': st.session_state.s_h_in,
            'hotMdot': st.session_state.s_h_mdot,
            'hotTargetOutletT': st.session_state.s_h_out,
            'coldInletT': st.session_state.s_c_in,
            'coldMdot': st.session_state.s_c_mdot,
            'coldTargetOutletT': st.session_state.s_c_out,
            'materialId': st.session_state.s_mat,
            'geometryType': st.session_state.s_g_type,
            'bundleAlignment': st.session_state.s_arr,
            'tubeLength': st.session_state.s_length,
            'shellDo': st.session_state.s_do,
            'baffleSpacing': st.session_state.s_baffle,
            'tubeDo': st.session_state.s_t_do,
            'tubeThickness': st.session_state.s_t_th,
            'tubePitch': st.session_state.s_t_pitch,
            'tubePitchLongitudinal': st.session_state.s_t_pl,
            'tubePasses': st.session_state.s_t_passes,
            'foulingHot': st.session_state.s_f_h,
            'foulingCold': st.session_state.s_f_c
        }
        res = calculate(state)
        # Apply consequences!
        s_targ = state['solveTarget']
        if s_targ == 'heat_duty':
            st.session_state.s_h_out = float(res['hotOutletT'])
            st.session_state.s_c_out = float(res['coldOutletT'])
        elif s_targ == 'hot_outlet':
            st.session_state.s_h_out = float(res['hotOutletT'])
            st.session_state.s_heat_duty = float(res['q'] / 1000)
        elif s_targ == 'cold_outlet':
            st.session_state.s_c_out = float(res['coldOutletT'])
            st.session_state.s_heat_duty = float(res['q'] / 1000)
        elif s_targ == 'hot_mdot':
            st.session_state.s_h_mdot = float(res['hotMdot'])
            st.session_state.s_heat_duty = float(res['q'] / 1000)
        elif s_targ == 'cold_mdot':
            st.session_state.s_c_mdot = float(res['coldMdot'])
            st.session_state.s_heat_duty = float(res['q'] / 1000)
            
        st.session_state['res'] = res
        st.session_state['state'] = state
    except Exception as e:
        import traceback
        st.error(f"Error in update_calc: {e}")
        st.error(traceback.format_exc())


# Force initial calc if none exists
if 'res' not in st.session_state:
    update_calc()

# Render layout
st.markdown("<div class='custom-header'><h1>Simulador de Trocador de Calor</h1><p>Casco-tubos & Banco de Tubos • Otimização Térmica e Hidráulica</p></div>", unsafe_allow_html=True)

col_inputs, col_results = st.columns([1, 3], gap="large")

with col_inputs:
    st.markdown("<div class='sidebar-header'>⚙️ Parâmetros de Projeto</div>", unsafe_allow_html=True)
    
    st.selectbox("Calcular:", list(targ_opts.keys()), format_func=lambda x: targ_opts[x], key='s_targ', on_change=update_calc)
    if st.session_state.s_targ == 'heat_duty':
        st.number_input("Fluxo de Calor Desejado (kW)", key='s_heat_duty', on_change=update_calc)
    
    st.selectbox("Fluido Interno (Tubos)", list(fluid_opts.keys()), format_func=lambda x: fluid_opts[x], key='s_h_fluid', on_change=update_calc)
    st.selectbox("Fluido Externo (Casco)", list(fluid_opts.keys()), format_func=lambda x: fluid_opts[x], key='s_c_fluid', on_change=update_calc)
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        if st.session_state.s_targ != 'hot_mdot':
            st.number_input("Vazão Tubos (kg/s)", key='s_h_mdot', on_change=update_calc)
    with col_v2:
        if st.session_state.s_targ != 'cold_mdot':
            st.number_input("Vazão Casco (kg/s)", key='s_c_mdot', on_change=update_calc)
            
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.number_input("T. Ent Tubo (°C)", key='s_h_in', on_change=update_calc)
    with col_t2:
        if st.session_state.s_targ not in ['hot_outlet', 'heat_duty']:
            st.number_input("T. Sai Tubo (°C)", key='s_h_out', on_change=update_calc)

    col_t3, col_t4 = st.columns(2)
    with col_t3:
        st.number_input("T. Ent Casco (°C)", key='s_c_in', on_change=update_calc)
    with col_t4:
        if st.session_state.s_targ not in ['cold_outlet', 'heat_duty']:
            st.number_input("T. Sai Casco (°C)", key='s_c_out', on_change=update_calc)

    st.markdown("---")
    st.selectbox("Tipo de Trocador", list(geom_opts.keys()), format_func=lambda x: geom_opts[x], key='s_g_type', on_change=update_calc)
    st.selectbox("Material do Tubo", list(mat_opts.keys()), format_func=lambda x: mat_opts[x], key='s_mat', on_change=update_calc)
    
    row_g1, row_g2 = st.columns(2)
    with row_g1:
        st.number_input("Diâm. Casco (m)", key='s_do', step=0.01, format="%.3f", on_change=update_calc)
    with row_g2:
        if st.session_state.s_g_type == 'shell-tube':
            st.number_input("Espaç. Chicanas (m)", key='s_baffle', step=0.01, format="%.3f", on_change=update_calc)

    row_g3, row_g4 = st.columns(2)
    with row_g3:
        st.number_input("Ø Ext. Tubo (mm)", key='s_t_do', step=0.1, format="%.2f", on_change=update_calc)
    with row_g4:
        st.number_input("Espessura (mm)", key='s_t_th', step=0.1, format="%.2f", on_change=update_calc)
        
    row_g5, row_g6 = st.columns(2)
    with row_g5:
        st.number_input("Comprimento (m)", key='s_length', step=0.1, format="%.2f", on_change=update_calc)
    with row_g6:
        st.number_input("Passo (mm)", key='s_t_pitch', step=0.1, format="%.2f", on_change=update_calc)

    row_g7, row_g8 = st.columns(2)
    with row_g7:
        if st.session_state.s_g_type == 'cross-flow-bank':
            st.selectbox("Arranjo", list(arr_opts.keys()), format_func=lambda x: arr_opts[x], key='s_arr', on_change=update_calc)
        else:
            st.number_input("Passes Tubo (N)", key='s_t_passes', on_change=update_calc)
    with row_g8:
        if st.session_state.s_g_type == 'cross-flow-bank':
            st.number_input("P. Long. (SL) mm", key='s_t_pl', on_change=update_calc)
            
    st.markdown("---")
    st.markdown("**Limites para Análise de Fouling**")
    row_f5, row_f6 = st.columns(2)
    with row_f5:
        st.number_input("Fouling Tubos (m²K/W)", format="%.4f", key='s_f_h', on_change=update_calc)
    with row_f6:
        st.number_input("Fouling Casco (m²K/W)", format="%.4f", key='s_f_c', on_change=update_calc)
        
    st.markdown("<div class='execute-btn'>", unsafe_allow_html=True)
    if st.button("Simular", use_container_width=True, type="primary"):
        update_calc()
    st.markdown("</div>", unsafe_allow_html=True)

with col_results:
    if 'res' in st.session_state and st.session_state['res'] is not None:
        res = st.session_state['res']
        
        if res['warnings']:
            for w in res['warnings']:
                st.warning(w)

        # 1. Balanço Térmico & Dimensões Finais side by side
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            with st.container(border=True):
                st.markdown("#### ⚖️ Balanço Térmico")
                col_r11, col_r12 = st.columns([2, 1])
                col_r11.write("Calor Trocado (Q):")
                col_r12.write(f"**{(res['q']/1000):.2f} kW**")
                
                col_r11.write("LMTD:")
                col_r12.write(f"**{res['lmtd']:.2f} °C**")
                
                col_r11.write("T. Saída Quente:")
                col_r12.write(f"**{res['hotOutletT']:.2f} °C**")

                col_r11.write("T. Saída Fria:")
                col_r12.write(f"**{res['coldOutletT']:.2f} °C**")
                
                col_r11.write("Fator de Correção (F):")
                col_r12.write(f"**{res['F']:.3f}**")

        with col_r2:
            with st.container(border=True):
                st.markdown("#### 📐 Dimensões Finais")
                col_r21, col_r22 = st.columns([2, 1])
                col_r21.write("Nº de Tubos (Nt):")
                col_r22.write(f"**{res['Nt']}**")
                
                col_r21.write("Área de Troca (A):")
                col_r22.write(f"**{res['Area']:.2f} m²**")
                
                col_r21.write("Coef. Global (U):")
                col_r22.write(f"**{res['U']:.1f} W/m²K**")
                
                col_r21.write("Vel. Tubos:")
                col_r22.write(f"**{res['v_t']:.3f} m/s**")
                
                col_r21.write("Vel. Casco:")
                col_r22.write(f"**{res['v_s']:.3f} m/s**")

        # 2. Avaliação Hidrodinâmica
        with st.container(border=True):
            st.markdown("#### 🌊 Avaliação Hidrodinâmica")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.markdown("**LADO TUBOS**")
                c1, c2 = st.columns([2, 1])
                c1.write("Regime (Re):")
                c2.write(f"**{res['Re_t']:.0f}**")
                c1.write("Perda de Carga (ΔP):")
                c2.write(f"**{(res['deltaPTube']/1000):.2f} kPa**")
            with col_h2:
                st.markdown("**LADO CASCO**")
                c3, c4 = st.columns([2, 1])
                c3.write("Regime (Re):")
                c4.write(f"**{res['Re_s']:.0f}**")
                c3.write("Perda de Carga (ΔP):")
                c4.write(f"**{(res['deltaPShell']/1000):.2f} kPa**")

        st.markdown("---")
        with st.expander("📄 Memória de Cálculo (Passo a Passo)"):
            st.markdown("\n\n".join(res['steps']))
        
        with st.expander("🖼️ Desenho 2D & Diagramas", expanded=True):
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

                    svg_content = f'''<div style="background-color: #f8fafc; padding: 10px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; justify-content: center; height: 100%; width: 100%;">
    <svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    {"".join(svg_elements)}
    </svg>
    </div>'''
                    components.html(svg_content, height=420)
                    
                with col_t3_2:
                    st.markdown("#### Diagrama Isométrico (Esquemático)")
                    schematic_svg = f'''<div style="background-color: #f8fafc; padding: 10px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; justify-content: center; height: 100%; width: 100%;">
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
    <path d="M 120 180 L 280 140 L 320 220 L 160 260 Z" fill="#cbd5e1" stroke="#94a3b8" stroke-width="2"/>
    <path d="M 160 260 L 320 220 L 320 240 L 160 280 Z" fill="#f1f5f9" stroke="#94a3b8" stroke-width="1"/>
    <!-- Hot In -->
    <path d="M 40 200 L 100 200" stroke="url(#hotGrad)" stroke-width="6" fill="none"/>
    <polygon points="100,195 110,200 100,205" fill="#f97316"/>
    <text x="30" y="190" fill="#1e293b" font-size="12">Quente (IN)</text>
    <!-- Hot Out -->
    <path d="M 340 200 L 380 200" stroke="url(#hotGrad)" stroke-width="6" fill="none"/>
    <polygon points="380,195 390,200 380,205" fill="#f97316"/>
    <text x="330" y="190" fill="#1e293b" font-size="12">Quente (OUT)</text>
    <!-- Cold In -->
    <path d="M 220 320 L 220 270" stroke="url(#coldGrad)" stroke-width="6" fill="none"/>
    <polygon points="215,270 220,260 225,270" fill="#3b82f6"/>
    <text x="210" y="340" fill="#1e293b" font-size="12">Frio (IN)</text>
    <!-- Cold Out -->
    <path d="M 220 130 L 220 80" stroke="url(#coldGrad)" stroke-width="6" fill="none"/>
    <polygon points="215,80 220,70 225,80" fill="#0ea5e9"/>
    <text x="210" y="60" fill="#1e293b" font-size="12">Frio (OUT)</text>
    </svg>
    </div>'''
                    components.html(schematic_svg, height=420)

        with st.expander("🛠️ Scripts CFD & CAD"):
            if 'state' in st.session_state:
                stt = st.session_state['state']
                rs = st.session_state['res']
                cfd_col1, cfd_col2 = st.columns([1, 2])
                
                with cfd_col1:
                    st.markdown("#### Configurações CFD")
                    sim_type = st.radio("Método CFD", ['Permanente (Steady)', 'Transiente'])
                    turb_model = st.selectbox("Modelo de Turbulência", ['k-epsilon Standard', 'k-omega SST'])
                    y_plus = st.number_input("Valor Y+ Almejado (Parede)", value=35.0, min_value=0.1)
                    
                    if sim_type == 'Permanente (Steady)':
                        iter_total = st.number_input("Iterações Máximas", value=500, min_value=10)
                        stt['iterSteady'] = iter_total
                    else:
                        time_steps = st.number_input("Núm. Time-Steps", value=100, min_value=1)
                        iter_per_step = st.number_input("Iterações por Passo", value=20, min_value=1)
                        v_max = max(rs['v_t'], rs['v_s'])
                        L_char = (stt['tubeDi']/1000) if stt['solveTarget'] == 'hot_outlet' else (stt['tubeDo']/1000)
                        dt_estimate = L_char / v_max if v_max > 0 else 0.01
                        dt_size = st.number_input("Tamanho Time-Step (s)", value=float(f"{dt_estimate:.4e}"), format="%.4e")
                        
                        stt['timeSteps'] = time_steps
                        stt['iterPerStep'] = iter_per_step
                        rs['estimatedTimeStep'] = dt_size

                    res_target = st.number_input("Convergência (Resíduos)", value=1e-4, format="%.5f")
                    stt['simType'] = 'transient' if sim_type == 'Transiente' else 'steady'
                    stt['turbModel'] = 'k-epsilon' if turb_model == 'k-epsilon Standard' else 'k-omega'
                    stt['yPlusTarget'] = y_plus
                    stt['residualsTarget'] = res_target
                    
                    # Recalcula Y+ rápidos
                    hotF = evaluate_fluid_props(stt['hotFluidId'], stt['hotInletT'])
                    coldF = evaluate_fluid_props(stt['coldFluidId'], stt['coldInletT'])
                    cf_t = 0.058 * (rs['Re_t']**-0.2) if rs['Re_t'] > 0 else 0
                    u_tau_t = math.sqrt((cf_t * hotF['density'] * (rs['v_t']**2) / 2) / hotF['density']) if rs['v_t'] > 0 else 0.01
                    rs['dy_int'] = y_plus * hotF['mu'] / (hotF['density'] * u_tau_t) if u_tau_t > 0 else 1e-5
                    
                    cf_s = 0.058 * (max(rs['Re_s'], 1)**-0.2)
                    u_tau_s = math.sqrt((cf_s * coldF['density'] * (rs['v_s']**2) / 2) / coldF['density']) if rs['v_s'] > 0 else 0.01
                    rs['dy_ext'] = y_plus * coldF['mu'] / (coldF['density'] * u_tau_s) if u_tau_s > 0 else 1e-5

                with cfd_col2:
                    st.markdown("#### Exportar TUI (Fluent)")
                    def render_terminal(title, content):
                        st.write(f"##### {title}")
                        st.markdown(f'<div style="background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; font-size: 13px; max-height: 400px; overflow-y: auto;">{content}</div>', unsafe_allow_html=True)
                        st.write("")
                    render_terminal("1. Malha (Fluent Meshing TUI)", generate_fluent_meshing(stt, rs))
                    render_terminal("2. Solver (Fluent TUI)", generate_fluent_setup(stt, rs))
                    
                    st.markdown("---")
                    st.markdown("#### Exportar Modelagem (SolidWorks VBA)")
                    st.code(generate_solidworks_macro(stt, rs), language="vbnet")

    else:
        st.info("Ajuste os parâmetros iniciais à esquerda e clique em Simular.")
