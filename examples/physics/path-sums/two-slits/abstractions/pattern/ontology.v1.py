def omega(D, T, PARTS, slices, patterns):
    # [ω] Sω of pattern: the probability at every site at time T, read from the recorded slice.
    #     With one part the amplitudes of the two slits have added; with two parts their
    #     probabilities add. While fewer than NEEDED slices are recorded this body is not evaluated.
    if any(p["parts"] == PARTS for p in patterns):
        return None                                    # ⊥: this experiment is answered
    if (T, PARTS) not in slices:
        return None                                    # ⊥: slice T is not recorded (wait)
    return pattern(D, PARTS, slices[(T, PARTS)])
