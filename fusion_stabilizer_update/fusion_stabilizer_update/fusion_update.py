"""
fusion_update.py
----------------
Fusion-based quantum computing stabilizer group update module.
"""

from typing import List, Tuple, Dict

_SINGLE_MULT = {
    ('I','I'):(0,'I'), ('I','X'):(0,'X'), ('I','Y'):(0,'Y'), ('I','Z'):(0,'Z'),
    ('X','I'):(0,'X'), ('X','X'):(0,'I'), ('X','Y'):(1,'Z'), ('X','Z'):(3,'Y'),
    ('Y','I'):(0,'Y'), ('Y','X'):(3,'Z'), ('Y','Y'):(0,'I'), ('Y','Z'):(1,'X'),
    ('Z','I'):(0,'Z'), ('Z','X'):(1,'Y'), ('Z','Y'):(3,'X'), ('Z','Z'):(0,'I'),
}

def multiply_pauli(p: Tuple[int,str], q: Tuple[int,str]) -> Tuple[int,str]:
    sp, P = p
    sq, Q = q
    assert len(P) == len(Q), "Mismatched length"
    phase_exp = 0
    out_chars = []
    for a,b in zip(P,Q):
        e, r = _SINGLE_MULT[(a,b)]
        phase_exp = (phase_exp + e) % 4
        out_chars.append(r)
    if phase_exp % 2 != 0:
        raise ValueError("Non-Hermitian phase (±i) encountered.")
    sign = sp * sq * (1 if phase_exp == 0 else -1)
    return (sign, ''.join(out_chars))

def anticommutes(P: str, Q: str) -> bool:
    assert len(P) == len(Q), "Mismatched length"
    anti_pairs = {('X','Y'),('Y','X'),('X','Z'),('Z','X'),('Y','Z'),('Z','Y')}
    parity = 0
    for a,b in zip(P,Q):
        if a != 'I' and b != 'I' and a != b and (a,b) in anti_pairs:
            parity ^= 1
    return parity == 1

def pretty(p: Tuple[int,str]) -> str:
    s, P = p
    return ('+' if s>=0 else '-') + P

def update_resource_with_fusions(
    resource_gens: List[Tuple[int,str]],
    fusion_meas: List[str],
    outcomes: Dict[str,int] = None
) -> List[Tuple[int,str]]:
    if outcomes is None:
        outcomes = {}
    gens = resource_gens[:]
    n = len(gens[0][1]) if gens else (len(fusion_meas[0]) if fusion_meas else 0)

    for M in fusion_meas:
        if len(M) != n:
            raise ValueError("Measurement length does not match stabilizer length")
        outcome = outcomes.get(M, +1)
        anti_idx = [j for j,(sg, G) in enumerate(gens) if anticommutes(G, M)]
        if not anti_idx:
            gens.append((outcome, M))
            continue
        p = anti_idx[0]
        old_pivot = gens[p]
        gens[p] = (outcome, M)
        for j in anti_idx[1:]:
            gens[j] = multiply_pauli(gens[j], old_pivot)
    return gens
