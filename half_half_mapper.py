def bdr_to_prm(alpha, delta):
    """
    Maps a BDR interface (alpha, delta) to a PRM interface (C_supply, T_supply)
    using the Half-Half Theorem: T = 2 * delta, C = alpha * (T - delta)
    """
    if delta < 1e-3:
        return 0.0, 0.0

    T_supply = 2 * delta
    C_supply = alpha * (T_supply - delta)
    return round(C_supply, 2), round(T_supply, 2)
