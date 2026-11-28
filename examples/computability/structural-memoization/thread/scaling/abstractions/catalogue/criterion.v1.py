def tau(plans, settlements, prior, w):
    # [τ] Sτ of catalogue: the publication repeats a settled plan that was derived or revalidated; one
    #     pattern per signature and versions.
    return publication_valid(w, plans, settlements, prior)
