def spans_can_merge_by_y(span1, span2, y_tolerance=1.0):
    return (
        abs(span1["origin"][1] - span2["origin"][1]) < y_tolerance and
        span1.get("block_id") == span2.get("block_id")
    )

def spans_can_merge_by_font_and_x(span1, span2):
    return (
        span1["font"] == span2["font"] and
        span1["size"] == span2["size"] and
        span1["color"] == span2["color"] and
        span2["origin"][0] >= span1["origin"][0] and
        span1.get("block_id") == span2.get("block_id")
    )

def merge_spans(span1, span2, with_space=True):
    return {
        "text": span1["text"] + (" " if with_space else "") + span2["text"],
        "font": span1["font"],
        "size": span1["size"],
        "color": span1["color"],
        "origin": span1["origin"],
        "block_id": span1["block_id"],
    }
