def primes_through(bound):
    return [n for n in range(2, bound + 1) if all(n % d for d in range(2, isqrt(n) + 1))]


def power_mod(base, exponent, modulus):
    result = 1
    for bit in range(exponent.bit_length()):
        if (exponent >> bit) & 1:
            result = result * base % modulus
        base = base * base % modulus
    return result


def valid_grid(bound, length, modulus, root):
    # Two indicators on 0..bound have a linear product of degree at most 2*bound.
    # Each coefficient has at most bound+1 ordered pairs, since an addend fixes its partner.
    if (bound < 2 or length <= 2 * bound or length & (length - 1)
            or modulus <= bound + 1 or modulus not in primes_through(modulus)
            or (modulus - 1) % length or not 1 < root < modulus):
        return False
    unity = power_mod(root, (modulus - 1) // length, modulus)
    return power_mod(unity, length, modulus) == 1 and power_mod(unity, length // 2, modulus) != 1


def transform(values, length, modulus, root, inverse):
    # Radix-2 NTT. The root supplied by the contract is raised to the required order.
    data = values[:]
    stages = length.bit_length() - 1
    for index in range(length):
        reverse = 0
        for bit in range(stages):
            reverse = (reverse << 1) | ((index >> bit) & 1)
        if reverse > index:
            data[index], data[reverse] = data[reverse], data[index]
    for stage in range(1, stages + 1):
        width = 1 << stage
        stride = (modulus - 1) // width
        step = power_mod(root, modulus - 1 - stride if inverse else stride, modulus)
        for start in range(0, length, width):
            weight = 1
            for offset in range(width // 2):
                i = start + offset
                j = i + width // 2
                odd = data[j] * weight % modulus
                even = data[i]
                data[i] = (even + odd) % modulus
                data[j] = (even - odd) % modulus
                weight = weight * step % modulus
    if inverse:
        scale = power_mod(length, modulus - 2, modulus)
        return [value * scale % modulus for value in data]
    return data


def source_ready(catalogs, sources, changes, version):
    if not catalogs:
        return False
    if version == 1:
        return not sources
    return len(changes) == 1 and len(sources) == 1 and sources[0]["version"] == 1


def source_candidate(catalogs, sources, changes, side, version, bound):
    if not source_ready(catalogs, sources, changes, version):
        return None
    return {"ref": f"{side}/{version}", "side": side, "version": version,
            "bound": bound, "primes": primes_through(bound)}


def valid_source(w, catalogs, sources, changes, side, version, bound):
    if not source_ready(catalogs, sources, changes, version):
        return False
    return (w["ref"] == f"{side}/{version}" and w["side"] == side and w["version"] == version
            and w["bound"] == bound and w["primes"] == primes_through(bound))


def valid_query(w, queries, answers, lefts, rights, changes, horizon):
    return (len(queries) == len(answers) and len(lefts) == 1 and len(rights) == 1 + len(changes)
            and w["id"] == len(queries) + 1 and 0 <= w["total"] <= 2 * horizon
            and w["policy"] in ["reuse", "fresh"])


def chosen_spectrum(spectra, query, source, length, modulus, root):
    # The immutable source includes its full prime list and its producing rule version.
    for item in spectra[::-1]:
        if (item["side"] == source["side"] and item["source_ref"] == source["ref"]
                and item["length"] == length and item["modulus"] == modulus and item["root"] == root
                and (query["policy"] == "reuse" or item["query_id"] == query["id"])):
            return item
    return None


def missing_operand(queries, products, lefts, rights, spectra, length, modulus, root):
    if len(queries) <= len(products) or not lefts or not rights:
        return None
    for source in [lefts[-1], rights[-1]]:
        if chosen_spectrum(spectra, queries[-1], source, length, modulus, root) is None:
            return source
    return None


def spectrum_candidate(queries, products, lefts, rights, spectra, length, modulus, root):
    source = missing_operand(queries, products, lefts, rights, spectra, length, modulus, root)
    if source is None:
        return None
    query_id = queries[-1]["id"]
    side = source["side"]
    indicator = [1 if n in source["primes"] else 0 for n in range(length)]
    coefficients = transform(indicator, length, modulus, root, False)
    return {"ref": f"spectrum/{query_id}/{side}", "query_id": query_id, "side": side,
            "source_ref": source["ref"], "length": length, "modulus": modulus, "root": root,
            "values": coefficients}


def valid_spectrum(w, queries, products, lefts, rights, spectra, length, modulus, root):
    source = missing_operand(queries, products, lefts, rights, spectra, length, modulus, root)
    if source is None:
        return False
    query_id = queries[-1]["id"]
    side = source["side"]
    if (w["ref"] != f"spectrum/{query_id}/{side}" or w["query_id"] != query_id or w["side"] != side
            or w["source_ref"] != source["ref"] or w["length"] != length
            or w["modulus"] != modulus or w["root"] != root or len(w["values"]) != length):
        return False
    # Independent direct evaluation of the indicator polynomial at each root.
    unity = power_mod(root, (modulus - 1) // length, modulus)
    return all(w["values"][k] == sum(power_mod(unity, k*p % length, modulus)
               for p in source["primes"]) % modulus for k in range(length))


def operands(queries, products, lefts, rights, spectra, length, modulus, root):
    if len(queries) <= len(products) or not lefts or not rights:
        return None
    query = queries[-1]
    left = chosen_spectrum(spectra, query, lefts[-1], length, modulus, root)
    right = chosen_spectrum(spectra, query, rights[-1], length, modulus, root)
    if left is None or right is None:
        return None
    return [left, right]


def product_candidate(queries, products, lefts, rights, spectra, length, modulus, root):
    items = operands(queries, products, lefts, rights, spectra, length, modulus, root)
    if items is None:
        return None
    left, right = items
    query_id = queries[-1]["id"]
    values = [left["values"][k] * right["values"][k] % modulus for k in range(length)]
    counts = transform(values, length, modulus, root, True)
    return {"ref": f"product/{query_id}", "query_id": query_id, "left_ref": left["source_ref"],
            "right_ref": right["source_ref"], "left_spectrum": left["ref"],
            "right_spectrum": right["ref"], "counts": counts}


def valid_product(w, queries, products, lefts, rights, spectra, length, modulus, root):
    items = operands(queries, products, lefts, rights, spectra, length, modulus, root)
    if items is None:
        return False
    left, right = items
    query_id = queries[-1]["id"]
    if (w["ref"] != f"product/{query_id}" or w["query_id"] != query_id
            or w["left_ref"] != lefts[-1]["ref"] or w["right_ref"] != rights[-1]["ref"]
            or w["left_spectrum"] != left["ref"] or w["right_spectrum"] != right["ref"]):
        return False
    # Integer counts of ordered witnesses. This independent criterion also checks the zero tail.
    counts = [0] * length
    for a in lefts[-1]["primes"]:
        for b in rights[-1]["primes"]:
            counts[a + b] += 1
    return w["counts"] == counts


def answer_candidate(queries, products, lefts, rights, answers):
    if not queries or len(products) != len(queries) or len(answers) >= len(products):
        return None
    q, c = queries[-1], products[-1]
    pairs = [[p, q["total"] - p] for p in lefts[-1]["primes"] if q["total"] - p in rights[-1]["primes"]]
    return {"ref": f"answer/{q['id']}", "query_id": q["id"], "total": q["total"],
            "product_ref": c["ref"], "count": c["counts"][q["total"]], "pairs": pairs}


def valid_answer(w, queries, products, lefts, rights, answers):
    if not queries or len(products) != len(queries) or len(answers) >= len(products):
        return False
    q, c = queries[-1], products[-1]
    pairs = [[p, b] for p in lefts[-1]["primes"] for b in rights[-1]["primes"] if p + b == q["total"]]
    return (w["ref"] == f"answer/{q['id']}" and w["query_id"] == q["id"] and w["total"] == q["total"]
            and w["product_ref"] == c["ref"] and c["query_id"] == q["id"]
            and c["left_ref"] == lefts[-1]["ref"] and c["right_ref"] == rights[-1]["ref"]
            and w["pairs"] == pairs and w["count"] == len(pairs) == c["counts"][q["total"]])


def evidence_for_change(queries, answers, rights, changes, cap):
    if changes or len(rights) != 1 or not answers or len(queries) != len(answers):
        return None
    for answer in answers:
        if any(pair[1] > cap for pair in answer["pairs"]):
            return answer
    return None


def change_candidate(queries, answers, rights, changes, cap, successor):
    evidence = evidence_for_change(queries, answers, rights, changes, cap)
    if evidence is None:
        return None
    return {"ref": "change/right/2", "answer_ref": evidence["ref"], "old_right_ref": rights[0]["ref"],
            "cap": cap, "specifications": successor}


def valid_change(w, queries, answers, rights, changes, cap, successor):
    evidence = evidence_for_change(queries, answers, rights, changes, cap)
    if evidence is None or len(w["specifications"]) != len(successor):
        return False
    if (w["ref"] != "change/right/2" or w["answer_ref"] != evidence["ref"]
            or w["old_right_ref"] != rights[0]["ref"] or w["cap"] != cap):
        return False
    for i in range(len(successor)):
        spec = w["specifications"][i]
        if spec["role"] == "ontology":
            # The substrate binds the carried ontology to the new criterion in this same event.
            spec = {k: v for k, v in spec.items() if k != "criterion"}
        if spec != successor[i]:
            return False
    return True
