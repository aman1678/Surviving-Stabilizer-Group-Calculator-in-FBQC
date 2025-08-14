
from typing import List, Tuple, Dict

# ---------- Pauli utilities ----------
# We represent a Pauli operator as (sign, string) where sign ∈ {+1,-1} and
# string is like "IXYZZ" (I,X,Y,Z per qubit).

_SINGLE_MULT = {
    # (P, Q) -> (phase_exponent_in_Z4, result)
    # phase exponent e means factor i^e (e=0: +1, 1: +i, 2: -1, 3: -i)
    ('I','I'):(0,'I'), ('I','X'):(0,'X'), ('I','Y'):(0,'Y'), ('I','Z'):(0,'Z'),
    ('X','I'):(0,'X'), ('X','X'):(0,'I'), ('X','Y'):(1,'Z'), ('X','Z'):(3,'Y'),
    ('Y','I'):(0,'Y'), ('Y','X'):(3,'Z'), ('Y','Y'):(0,'I'), ('Y','Z'):(1,'X'),
    ('Z','I'):(0,'Z'), ('Z','X'):(1,'Y'), ('Z','Y'):(3,'X'), ('Z','Z'):(0,'I'),
}

def multiply_pauli(p: Tuple[int,str], q: Tuple[int,str]) -> Tuple[int,str]:
    """Multiply two n-qubit Pauli strings (±1 phases only, but we track i^k and fold into ±1).
    Returns a Hermitian Pauli (phase in {+1,-1})."""

    sp, P = p
    sq, Q = q

    assert len(P) == len(Q), "Mismatched length"

    phase_exp = 0  # in Z4
    out_chars = []

    for a,b in zip(P,Q):
        e, r = _SINGLE_MULT[(a,b)]
        phase_exp = (phase_exp + e) % 4
        out_chars.append(r)

    # i^(phase_exp) * sp * sq -> fold i's into ±1 by requiring Hermitian output.
    # For products of Hermitian Paulis, phase_exp is always even (0 or 2).

    if phase_exp % 2 != 0:
        # Should not happen for Hermitian×Hermitian, but guard anyway:
        raise ValueError("Non-Hermitian phase encountered (±i). Check inputs.")
    
    sign = sp * sq * (1 if phase_exp == 0 else -1)

    return (sign, ''.join(out_chars))

def anticommutes(P: str, Q: str) -> bool:
    """Return True iff Pauli strings P and Q anticommute."""

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

# ---------- Stabilizer (resource) update with fusion measurements ----------

def update_resource_with_fusions(
    resource_gens: List[Tuple[int,str]],
    fusion_meas: List[str],
    outcomes: Dict[str,int] = None
) -> List[Tuple[int,str]]:
    """
    Apply a list of fusion measurements to a resource stabilizer group.

    Args
    ----
    resource_gens : list of (sign, pauli_string)  e.g., [(+1,"XXI"), (+1,"ZZI"), ...]
    fusion_meas   : list of Pauli strings to be measured, e.g., ["XZI", "IXX", ...]
    outcomes      : optional dict mapping a measurement string to ±1 outcome.
                    Default is +1 for all.

    Behavior
    --------
    For each measurement M:
      1) Find all stabilizers S_j that anticommute with M.
      2) If none anticommute: append (outcome, M) to the group (it already commutes).
      3) If some anticommute:
         - Pick one pivot index p from those.
         - Let Sp be that pivot. Replace Sp with (outcome, M).
         - For every other anti-commuting S_j, set S_j ← S_j * Sp (using the old Sp),
           which makes them commute with M.
    Returns the updated stabilizer generator list.
    """

    if outcomes is None:
        outcomes = {}

    gens = resource_gens[:]  # copy
    n = len(gens[0][1]) if gens else (len(fusion_meas[0]) if fusion_meas else 0)

    for M in fusion_meas:
        if len(M) != n:
            raise ValueError("Measurement length does not match stabilizer length")
        outcome = outcomes.get(M, +1)

        # Find all anti-commuting stabilizers
        anti_idx = [j for j,(sg, G) in enumerate(gens) if anticommutes(G, M)]

        if not anti_idx:
            # Commutes with everything: add M as a new stabilizer with the outcome sign.
            gens.append((outcome, M))
            continue

        # Choose pivot (first)
        p = anti_idx[0]
        old_pivot = gens[p]  # (sign, string)

        # Replace pivot by the measurement with its sign
        gens[p] = (outcome, M)

        # For every *other* anti-commuting stabilizer, multiply by the old pivot
        for j in anti_idx[1:]:
            gens[j] = multiply_pauli(gens[j], old_pivot)
            
        # Done with this measurement
    return gens

# ---------- User interface for input and output ----------
def user_interface():

    print("Enter the resource stabilizer generators (sign, string) one per line:")
    resource = []

    while True:
        line = input("Enter stabilizer (or 'done' to finish): ")

        if line.lower() == 'done':
            break

        try:
            sign, string = line.split(',')
            sign = int(sign.strip())
            string = string.strip()
            resource.append((sign, string))
        except ValueError:
            print("Invalid input. Please enter in the format: sign,string")

    print("\nEnter the fusion measurements (string) one per line:")
    fusions = []

    while True:
        line = input("Enter fusion measurement (or 'done' to finish): ")
        if line.lower() == 'done':
            break
        fusions.append(line.strip())

    outcomes = {}
    print("\nEnter the outcomes for each fusion measurement (optional):")

    for fusion in fusions:
        outcome = input(f"Enter outcome for '{fusion}' (default is +1): ")

        if outcome.strip() == '':
            outcomes[fusion] = +1
        else:
            try:
                outcomes[fusion] = int(outcome.strip())
            except ValueError:
                print("Invalid outcome. Defaulting to +1.")
                outcomes[fusion] = +1
    
    updated = update_resource_with_fusions(resource, fusions, outcomes)

    print("\nUpdated resource stabilizer generators after fusion measurements:")
    for g in updated:
        print("  ", pretty(g))

# ---------- Main menu and user interaction ----------
def menu():

    print("\n==========================================")
    print("Welcome to the SS Group Calculator!")
    print("=========================================\n")
    print("Please select an option:")
    print("1. Calculate Stabilizer Group")
    print("2. Exit\n")

    choice = input("Enter your choice (1 or 2): ")

    if choice == '1':
        user_interface()
        menu()
    elif choice == '2':
        print("Exiting the program. Goodbye!")
    else:
        print("Invalid choice. Please try again.")
        menu()