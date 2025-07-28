import spacy
nlp = spacy.load("en_core_web_sm")

def is_sentence_like(text):
    doc = nlp(text)
    has_subject = any(tok.dep_ in ("nsubj", "nsubjpass") for tok in doc)
    has_verb = any(tok.pos_ == "VERB" for tok in doc)
    return has_subject and has_verb
