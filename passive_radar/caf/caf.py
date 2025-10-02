def compute_caf_block(iq):
    print("[caf] Computing CAF block")
    return [[abs(x) for x in iq]]

def compute_caf_stream(iq_stream):
    for iq in iq_stream:
        yield compute_caf_block(iq)
