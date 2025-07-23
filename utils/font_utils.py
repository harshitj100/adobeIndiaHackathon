def has_similar_font_properties(span1, span2):
    font1 = span1.get("font", "").lower()
    font2 = span2.get("font", "").lower()
    is_normal1 = not ("bold" in font1 or "black" in font1)
    is_normal2 = not ("bold" in font2 or "black" in font2)

    return (
        span1.get("font") == span2.get("font") and
        span1.get("size") == span2.get("size") and
        span1.get("color") == span2.get("color") and
        is_normal1 and is_normal2
    )
