def tau(T, W, slices, transmitted, w):
    # [τ] Sτ of transmission: the probability of the recorded slice T over that of slice 0, once per width.
    if (W, T) not in slices or any(x["w"] == W for x in transmitted):
        return False
    return w == {"w": W, "T": T, "transmitted": slices[(W, T)]["norm"] / slices[(W, 0)]["norm"]}
