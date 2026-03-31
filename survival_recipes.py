"""
JARVIS Survival Recipes - Database locale di ricette italiane economiche.
Filtra per budget massimo e tempo disponibile.
"""

import random
from typing import Optional

# Database ricette italiane economiche (costo stimato per persona)
RECIPES_DB = [
    {
        "nome": "Pasta al pomodoro",
        "costo": 0.80,
        "tempo": 15,
        "ingredienti": ["pasta 80g (0.20€)", "passata di pomodoro (0.30€)", "aglio", "olio", "sale"],
        "preparazione": (
            "1. Bolli l'acqua salata e cuoci la pasta 8-10 min.\n"
            "2. Soffriggi uno spicchio d'aglio in olio.\n"
            "3. Aggiungi la passata, sale, e cuoci 5 min.\n"
            "4. Scola la pasta e unisci al sugo."
        ),
        "calorie": 380,
        "tag": ["pasta", "economica", "veloce"]
    },
    {
        "nome": "Riso e lenticchie",
        "costo": 0.70,
        "tempo": 25,
        "ingredienti": ["riso 80g (0.15€)", "lenticchie secche 50g (0.20€)", "cipolla", "olio", "dado vegetale"],
        "preparazione": (
            "1. Metti in ammollo le lenticchie 30 min (oppure usa quelle in scatola).\n"
            "2. Soffriggi cipolla, aggiungi lenticchie e riso.\n"
            "3. Copri con acqua calda con dado, cuoci 20 min.\n"
            "4. Aggiusta di sale e un filo d'olio a crudo."
        ),
        "calorie": 420,
        "tag": ["riso", "lenticchie", "proteico"]
    },
    {
        "nome": "Frittata di uova",
        "costo": 0.90,
        "tempo": 10,
        "ingredienti": ["3 uova (0.60€)", "sale", "olio", "formaggio grattugiato (0.20€)"],
        "preparazione": (
            "1. Sbatti le uova con sale e formaggio.\n"
            "2. Scalda olio in padella antiaderente a fuoco medio.\n"
            "3. Versa le uova e cuoci 3 min, poi gira con un piatto.\n"
            "4. Altri 2 min e servi."
        ),
        "calorie": 350,
        "tag": ["uova", "proteico", "veloce"]
    },
    {
        "nome": "Pasta e fagioli",
        "costo": 1.20,
        "tempo": 30,
        "ingredienti": ["pasta corta 80g (0.20€)", "fagioli in scatola (0.60€)", "pomodori pelati (0.30€)", "rosmarino", "aglio"],
        "preparazione": (
            "1. Soffriggi aglio in olio, aggiungi i fagioli scolati.\n"
            "2. Aggiungi i pelati schiacciati e 300ml acqua.\n"
            "3. A bollore, butta la pasta e cuoci 10 min.\n"
            "4. Frulla metà del composto per densità, aggiusta sale."
        ),
        "calorie": 450,
        "tag": ["pasta", "fagioli", "sostanzioso"]
    },
    {
        "nome": "Pane e pomodoro",
        "costo": 0.40,
        "tempo": 5,
        "ingredienti": ["pane raffermo 2 fette (0.10€)", "pomodoro 1 (0.20€)", "olio", "sale", "basilico"],
        "preparazione": (
            "1. Taglia il pomodoro a metà e strofinalo sul pane.\n"
            "2. Condisci con olio, sale e basilico.\n"
            "3. Opzionale: gratina in forno 5 min per il croccante."
        ),
        "calorie": 200,
        "tag": ["pane", "velocissimo", "colazione", "merenda"]
    },
    {
        "nome": "Zuppa di pane raffermo",
        "costo": 0.60,
        "tempo": 20,
        "ingredienti": ["pane raffermo 100g (0.10€)", "dado vegetale (0.20€)", "cipolla", "olio", "parmigiano"],
        "preparazione": (
            "1. Soffriggi cipolla in olio 3 min.\n"
            "2. Aggiungi 500ml acqua con dado e porta a bollore.\n"
            "3. Spezza il pane e uniscilo alla zuppa.\n"
            "4. Cuoci 10 min finché il pane si scioglie. Servi con parmigiano."
        ),
        "calorie": 280,
        "tag": ["pane", "zuppa", "antispreco"]
    },
    {
        "nome": "Pasta aglio e olio",
        "costo": 0.60,
        "tempo": 15,
        "ingredienti": ["pasta 80g (0.20€)", "aglio 3 spicchi", "olio EVO (0.20€)", "peperoncino", "prezzemolo"],
        "preparazione": (
            "1. Cuoci la pasta al dente, tieni un mestolo d'acqua di cottura.\n"
            "2. Soffriggi aglio e peperoncino in olio a fuoco basso.\n"
            "3. Unisci la pasta scolata, aggiungi acqua di cottura e manteca.\n"
            "4. Servi con prezzemolo tritato."
        ),
        "calorie": 360,
        "tag": ["pasta", "economica", "classica"]
    },
    {
        "nome": "Uova strapazzate e pane",
        "costo": 0.70,
        "tempo": 8,
        "ingredienti": ["2 uova (0.40€)", "latte 2 cucchiai", "pane 2 fette (0.10€)", "burro/olio"],
        "preparazione": (
            "1. Sbatti uova con latte e un pizzico di sale.\n"
            "2. Scalda burro in padella a fuoco bassissimo.\n"
            "3. Aggiungi le uova e mescola lentamente finché cremose.\n"
            "4. Servi sul pane tostato."
        ),
        "calorie": 300,
        "tag": ["uova", "colazione", "veloce"]
    },
    {
        "nome": "Risotto al dado",
        "costo": 0.50,
        "tempo": 20,
        "ingredienti": ["riso 80g (0.15€)", "dado vegetale (0.20€)", "olio", "cipolla", "parmigiano"],
        "preparazione": (
            "1. Soffriggi cipolla tritata in olio.\n"
            "2. Tosta il riso 1 min, poi aggiungi brodo caldo poco alla volta.\n"
            "3. Mescola spesso per 16-18 min finché cremoso.\n"
            "4. Manteca con olio e parmigiano fuori dal fuoco."
        ),
        "calorie": 380,
        "tag": ["riso", "cremoso", "comfort"]
    },
    {
        "nome": "Lenticchie in umido",
        "costo": 0.80,
        "tempo": 35,
        "ingredienti": ["lenticchie 100g (0.30€)", "pomodori pelati (0.30€)", "cipolla", "carota", "sedano"],
        "preparazione": (
            "1. Soffriggi il soffritto (cipolla, carota, sedano) 5 min.\n"
            "2. Aggiungi lenticchie (già ammollate) e pelati.\n"
            "3. Copri con acqua e cuoci 25-30 min.\n"
            "4. Aggiusta di sale, servi con pane o riso."
        ),
        "calorie": 310,
        "tag": ["lenticchie", "proteico", "vegan"]
    },
]


def get_budget_recipe(
    budget_euros: float,
    time_minutes: Optional[int] = None,
    tag: Optional[str] = None
) -> dict:
    """
    Ritorna una ricetta economica italiana filtrata per budget e tempo.

    Args:
        budget_euros: Budget massimo per persona in euro
        time_minutes: Tempo massimo di preparazione in minuti (opzionale)
        tag: Filtro per tag (es. "pasta", "uova", "veloce") (opzionale)

    Returns:
        dict con nome, ingredienti, preparazione e info costo/calorie
    """
    # Filtra per budget
    candidates = [r for r in RECIPES_DB if r["costo"] <= budget_euros]

    # Filtra per tempo
    if time_minutes is not None:
        candidates = [r for r in candidates if r["tempo"] <= time_minutes]

    # Filtra per tag
    if tag is not None:
        tag_lower = tag.lower()
        candidates = [r for r in candidates if any(tag_lower in t for t in r["tag"])]

    if not candidates:
        # Fallback: mostra la più economica in assoluto
        cheapest = min(RECIPES_DB, key=lambda r: r["costo"])
        return {
            "trovata": False,
            "messaggio": f"Nessuna ricetta nel budget di {budget_euros:.2f}€. La più economica è '{cheapest['nome']}' a {cheapest['costo']:.2f}€.",
            "ricetta": cheapest
        }

    # Ordina per costo (più economica prima) e prendi le migliori 3 per randomizzare
    candidates.sort(key=lambda r: r["costo"])
    top = candidates[:3]
    chosen = random.choice(top)

    return {
        "trovata": True,
        "messaggio": _format_recipe(chosen, budget_euros),
        "ricetta": chosen
    }


def _format_recipe(recipe: dict, budget: float) -> str:
    """Formatta una ricetta per la risposta vocale di JARVIS."""
    risparmio = budget - recipe["costo"]
    lines = [
        f"Suggerisco: {recipe['nome']} — {recipe['costo']:.2f}€ a persona.",
        f"Avanzano {risparmio:.2f}€ dal budget.",
        "",
        "Ingredienti:",
        *[f"  • {i}" for i in recipe["ingredienti"]],
        "",
        "Preparazione:",
        recipe["preparazione"],
        "",
        f"Tempo: {recipe['tempo']} min  |  Calorie: {recipe['calorie']} kcal"
    ]
    return "\n".join(lines)


def get_super_cheap_recipe() -> dict:
    """Ritorna la ricetta più economica del database (per budget < 1€)."""
    cheapest = min(RECIPES_DB, key=lambda r: r["costo"])
    return {
        "trovata": True,
        "messaggio": (
            f"Budget emergenza? '{cheapest['nome']}' costa solo {cheapest['costo']:.2f}€. "
            f"Ci vogliono {cheapest['tempo']} min."
        ),
        "ricetta": cheapest
    }


def list_all_recipes() -> list:
    """Ritorna lista di (nome, costo) per tutte le ricette."""
    return [(r["nome"], r["costo"]) for r in sorted(RECIPES_DB, key=lambda r: r["costo"])]


if __name__ == "__main__":
    print("=== Test Survival Recipes ===\n")

    result = get_budget_recipe(1.00, time_minutes=20)
    print(result["messaggio"])

    print("\n--- Budget < 5€ ---")
    result2 = get_budget_recipe(5.00)
    print(result2["messaggio"])

    print("\n--- Tutte le ricette ---")
    for nome, costo in list_all_recipes():
        print(f"  {nome}: {costo:.2f}€")
