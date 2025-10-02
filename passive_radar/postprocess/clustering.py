def cluster_detections(detections):
    print("[clustering] Running clustering")
    return [{"id": i, "points": [det]} for i, det in enumerate(detections)]
