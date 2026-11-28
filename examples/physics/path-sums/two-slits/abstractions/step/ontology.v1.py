def omega(COIN, D, T, T0, SLITS, PARTS, slices):
    # [ω] Sω of step: the first slice of this experiment that is not recorded, from the recorded slice
    #     before it. Before the screen a slice has one part whatever the detector, so the slices
    #     t < T0 that one experiment recorded are reused by the other.
    for t in range(T + 1):
        if (t, PARTS if t >= T0 else 1) in slices:
            continue                                   # recorded: reused
        if t == 0:
            return initial()
        before = (t - 1, PARTS if t - 1 >= T0 else 1)
        if before not in slices:
            return None                                # ⊥: the slice before is not recorded (wait)
        return next_slice(COIN, D, T0, SLITS, PARTS, slices[before])[0]
    return None                                        # ⊥: every slice of this experiment is recorded
