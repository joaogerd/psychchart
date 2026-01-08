import numpy as np

class Psychrometrics:
    """
    Módulo de cálculo psicrométrico completo.

    Todas as funções tratam temperaturas em °C, pressões em Pa e razões de mistura em kg_vapor/kg_ar_seco.

    Constantes:
      - cp (kJ/kg·°C): capacidade térmica do ar seco.
      - Hfg (kJ/kg) : calor latente de vaporização da água.
      - Rd (J/kg·K):  constante dos gases para o ar seco.
      - cp_v (kJ/kg·°C): capacidade térmica do vapor de água.
    """
    cp   = 1.006       # kJ/kg·°C
    Hfg  = 2501.0      # kJ/kg
    Rd   = 287.055     # J/kg·K
    cp_v = 1.86        # kJ/kg·°C

    @staticmethod
    def saturation_pressure(T):
        """
        Pressão de vapor de saturação (Pa) a partir da temperatura T (°C).
        Fórmula de Magnus–Tetens.
        """
        return 610.94 * np.exp((17.625 * T) / (T + 243.04))

    @staticmethod
    def humidity_ratio(T, RH, P=101325.0):
        """
        Razão de mistura W (kg_vapor/kg_ar_seco).

        Parâmetros:
          T  : Temperatura de bulbo seco (°C).
          RH : Umidade relativa (0–1).
          P  : Pressão total do ar (Pa).

        Retorna:
          W  : Razão de mistura.
        """
        p_sat = Psychrometrics.saturation_pressure(T)
        p_v   = RH * p_sat
        return 0.622 * p_v / (P - p_v)

    @staticmethod
    def enthalpy(T, W):
        """
        Entalpia do ar úmido (kJ/kg_ar_seco).

        Fórmula: h = cp*T + W*(Hfg + cp_v*T)
        """
        return Psychrometrics.cp * T + W * (Psychrometrics.Hfg + Psychrometrics.cp_v * T)

    @staticmethod
    def wet_bulb_line(T_db, T_wb, P=101325.0):
        """
        Curva de bulbo úmido constante T_wb (°C).

        Parâmetros:
          T_db: Array de temperaturas de bulbo seco (°C).
          T_wb: Temperatura de bulbo úmido (°C).
          P   : Pressão total do ar (Pa).

        Retorna:
          W_line: Razão de mistura ao longo de T_db para bulbo úmido constante.
        """
        W_sat_wb = Psychrometrics.humidity_ratio(T_wb, 1.0, P)
        return W_sat_wb - Psychrometrics.cp * (T_db - T_wb) / Psychrometrics.Hfg

    @staticmethod
    def dew_point_temperature(RH, T, P=101325.0, tol=0.01, max_iter=100):
        """
        Calcula a temperatura de ponto de orvalho T_dp (°C) para UR e T dados.

        Resolve p_sat(T_dp) = RH * p_sat(T) via método de Newton–Raphson.

        Parâmetros:
          RH       : Umidade relativa (0–1).
          T        : Temperatura de bulbo seco (°C).
          P        : Pressão total do ar (Pa).
          tol      : Tolerância de convergência em °C.
          max_iter : Número máximo de iterações.

        Retorna:
          T_dp     : Temperatura de ponto de orvalho (°C).
        """
        p_v = RH * Psychrometrics.saturation_pressure(T)
        # Inicializa T_dp com T
        T_dp = np.array(T, dtype=float)
        for _ in range(max_iter):
            p_sat_dp = Psychrometrics.saturation_pressure(T_dp)
            f        = p_sat_dp - p_v
            # derivada dp_sat/dT
            dp_dT    = p_sat_dp * 17.625 * 243.04 / ((T_dp + 243.04)**2)
            T_next   = T_dp - f / dp_dT
            if np.allclose(T_next, T_dp, atol=tol):
                break
            T_dp = T_next
        return T_dp

    @staticmethod
    def relative_humidity_from_W(T, W, P=101325.0):
        """
        Umidade relativa (0–1) a partir de razão de mistura W.

        Parâmetros:
          T: Temperatura de bulbo seco (°C).
          W: Razão de mistura (kg_vapor/kg_ar_seco).
          P: Pressão total do ar (Pa).

        Retorna:
          UR: Umidade relativa (0–1).
        """
        p_v = W * P / (0.622 + W)
        return p_v / Psychrometrics.saturation_pressure(T)

    @staticmethod
    def specific_humidity(W):
        """
        Fração mássica de água no ar úmido.

        q = W / (1 + W)
        """
        return W / (1 + W)

    @staticmethod
    def specific_volume(T, W, P=101325.0):
        """
        Volume específico do ar úmido (m³/kg_ar_seco).

        v = Rd*(T_K)*(1 + 1.6078*W) / P
        """
        T_K = T + 273.15
        return (Psychrometrics.Rd * T_K * (1 + 1.6078 * W)) / P

    @staticmethod
    def density(T, W, P=101325.0):
        """
        Densidade do ar úmido (kg/m³).

        ρ = 1 / v
        """
        return 1.0 / Psychrometrics.specific_volume(T, W, P)

    @staticmethod
    def vapor_enthalpy(T):
        """
        Entalpia específica do vapor de água (kJ/kg).

        h_v = Hfg + cp_v * T
        """
        return Psychrometrics.Hfg + Psychrometrics.cp_v * T

    @staticmethod
    def dew_point_line(T_db, RH, P=101325.0):
        """
        Curva de ponto de orvalho para variação de T_db.

        Retorna array de T_dp correspondente a cada T_db dado UR constante.
        """
        return Psychrometrics.dew_point_temperature(RH, T_db, P)

