def omega(plans, settlements, prior):
    # [ω] Sω of catalogue: a derived or revalidated graph, with its signature and versions, once its
    #     case is settled; nothing if the catalogue already lists that signature under these versions.
    return next_publication(plans, settlements, prior)
