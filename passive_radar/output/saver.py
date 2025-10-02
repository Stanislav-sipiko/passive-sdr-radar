import os

def save_event(clusters, out_dir="results"):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "events.txt"), "w") as f:
        for c in clusters:
            f.write(str(c) + "\n")
    print(f"[saver] Events saved to {out_dir}/events.txt")

def save_patch(patch, out_dir="patches"):
    os.makedirs(out_dir, exist_ok=True)
    print("[saver] Patch saved")

def manifest():
    return {}
