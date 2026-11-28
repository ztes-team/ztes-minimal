def omega(T, W, slices, transmitted):
    # [ω] Sω of transmission: the probability beyond the barrier (x ≥ W) at time T, as a fraction of
    #     the packet: slice T holds exactly those sites. While fewer than NEEDED slices are recorded
    #     this body is not evaluated ("requires").
    if any(x["w"] == W for x in transmitted):
        return None                                    # ⊥: this width is answered
    if (W, T) not in slices:
        return None                                    # ⊥: slice T is not recorded (wait)
    return {"w": W, "T": T, "transmitted": slices[(W, T)]["norm"] / slices[(W, 0)]["norm"]}
