import re

def polish_voice(text: str) -> str:
    """
    Programmatically remove common AI markers from text.
    """
    # 1. Replace em-dashes (—) with commas or spaces to break up robotic flow
    # Handle both "word — word" and "word—word"
    text = re.sub(r'\s*—\s*', ', ', text)
    
    # 2. Remove "Throat-Clearing" phrases (Case insensitive)
    throat_clearers = [
        r"In the realm of\b",
        r"In today's fast-paced world\b",
        r"It is worth noting that\b",
        r"It is important to note that\b",
        r"Navigating the complexities of\b",
        r"Notably,\b",
        r"Indeed,\b",
        r"Essentially,\b",
        r"Furthermore,\b",
        r"Moreover,\b",
        r"Additionally,\b"
    ]
    for pattern in throat_clearers:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # 3. Clean up double spaces created by removal
    text = re.sub(r'  +', ' ', text).strip()
    
    # Capitalize the first letter if we removed a leading throat-clearer
    if text:
        text = text[0].upper() + text[1:]

    return text

if __name__ == "__main__":
    # Test
    sample = "In the realm of AI, it is worth noting that — while powerful — the technology is notably complex. Indeed, navigating the complexities of this space is essentially a challenge."
    print("ORIGINAL:", sample)
    print("POLISHED:", polish_voice(sample))
