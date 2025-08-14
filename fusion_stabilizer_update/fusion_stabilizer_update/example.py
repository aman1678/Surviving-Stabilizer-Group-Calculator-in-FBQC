"""
Example usage of fusion_update.py
"""

from fusion_update import update_resource_with_fusions, pretty

if __name__ == "__main__":
    resource = [
        (+1, "XXX"),
        (+1, "ZZI"),
        (+1, "IZZ"),
    ]
    fusions = ["XII", "IZI"]
    outcomes = {"XII": +1, "IZI": -1}

    print("Initial resource generators:")
    for g in resource:
        print("  ", pretty(g))

    updated = update_resource_with_fusions(resource, fusions, outcomes)

    print("\nAfter fusion measurements:")
    for g in updated:
        print("  ", pretty(g))
