def isAdmin(claims: dict) -> bool:
    return claims["isAdmin"]

def isManager(claims: dict) -> bool:
    return claims["isManager"]

def isTally(claims: dict) -> bool:
    return claims["isTally"]

def isTallyAndManager(claims: dict) -> bool:
    return claims["isTally"] or claims["isManager"]