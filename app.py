import json
import urllib.parse

symbol_map = {
    "standard_foil": "🔴 •",
    "common": "🔘 •",
    "rare": "⭐ ★",
    "double_rare": "⭐⭐ ★★",
    "illustration_rare": "🎨⭐ ★",
    "special_illustration_rare": "🎨⭐⭐ ★★",
    "pikachu_rare": "⚡ ⚡",
    "futuristic_rare": "💎✨ ★",
    "classic_collection": "🔴🟡 ★C"
}

card_data = [
    (1, "Exeggcute", "standard_foil"), (2, "Alolan Exeggutor", "standard_foil"), (3, "Volbeat", "standard_foil"),
    (4, "Illumise", "standard_foil"), (5, "Tropius", "standard_foil"), (6, "Cherubi", "standard_foil"),
    (7, "Cherrim", "standard_foil"), (8, "Vivillon", "standard_foil"), (9, "Vulpix", "standard_foil"),
    (10, "Ninetales", "standard_foil"), (11, "Moltres", "rare"), (12, "Ho-Oh", "rare"),
    (13, "Victini", "rare"), (14, "Reshiram", "rare"), (15, "Fuecoco ex", "double_rare"),
    (16, "Slowpoke", "standard_foil"), (17, "Lapras", "standard_foil"), (18, "Articuno", "rare"),
    (19, "Kyogre", "rare"), (20, "Palkia", "rare"), (21, "Greninja ex", "double_rare"),
    (22, "Wishiwashi", "standard_foil"), (23, "Pikachu", "pikachu_rare"), (24, "Pikachu", "pikachu_rare"),
    (25, "Pikachu", "pikachu_rare"), (26, "Pikachu", "pikachu_rare"), (27, "Pikachu", "pikachu_rare"),
    (28, "Pikachu", "pikachu_rare"), (29, "Pikachu", "pikachu_rare"), (30, "Pikachu", "pikachu_rare"),
    (31, "Pikachu", "pikachu_rare"), (32, "Pikachu", "pikachu_rare"), (33, "Pikachu", "pikachu_rare"),
    (34, "Pikachu", "pikachu_rare"), (35, "Pikachu", "pikachu_rare"), (36, "Pikachu", "pikachu_rare"),
    (37, "Pikachu", "pikachu_rare"), (38, "Pikachu", "pikachu_rare"), (39, "Pikachu", "pikachu_rare"),
    (40, "Pikachu", "pikachu_rare"), (41, "Pikachu", "pikachu_rare"), (42, "Pikachu", "pikachu_rare"),
    (43, "Pikachu", "pikachu_rare"), (44, "Pikachu", "pikachu_rare"), (45, "Pikachu", "pikachu_rare"),
    (46, "Pikachu", "pikachu_rare"), (47, "Pikachu", "pikachu_rare"), (48, "Pikachu", "pikachu_rare"),
    (49, "Pikachu", "pikachu_rare"), (50, "Pikachu", "pikachu_rare"), (51, "Pikachu", "pikachu_rare"),
    (52, "Pikachu", "pikachu_rare"), (53, "Pikachu ex", "double_rare"), (54, "Pikachu ex", "double_rare"),
    (55, "Zapdos", "rare"), (56, "Zekrom", "rare"), (57, "Zeraora", "rare"),
    (58, "Toxel", "standard_foil"), (59, "Toxtricity", "standard_foil"), (60, "Toxtricity", "standard_foil"),
    (61, "Morpeko", "standard_foil"), (62, "Miraidon", "rare"), (63, "Mewtwo", "rare"),
    (64, "Mewtwo ex", "double_rare"), (65, "Mew", "rare"), (66, "Mew ex", "double_rare"),
    (67, "Marill", "standard_foil"), (68, "Azumarill", "standard_foil"), (69, "Espeon", "rare"),
    (70, "Espeon ex", "double_rare"), (71, "Sylveon ex", "double_rare"), (72, "Unown", "standard_foil"),
    (73, "Drifloon", "standard_foil"), (74, "Cresselia", "rare"), (75, "Chandelure", "standard_foil"),
    (76, "Xerneas", "rare"), (77, "Comfey", "standard_foil"), (78, "Cosmog", "standard_foil"),
    (79, "Cosmoem", "standard_foil"), (80, "Lunala", "rare"), (81, "Gimmighoul", "standard_foil"),
    (82, "Groudon", "rare"), (83, "Lucario", "rare"), (84, "Seismitoad", "standard_foil"),
    (85, "Lycanroc", "standard_foil"), (86, "Koraidon", "rare"), (87, "Nidoran♀", "standard_foil"),
    (88, "Nidorina", "standard_foil"), (89, "Alolan Meowth", "standard_foil"), (90, "Gengar ex", "double_rare"),
    (91, "Umbreon", "rare"), (92, "Umbreon ex", "double_rare"), (93, "Murkrow", "standard_foil"),
    (94, "Scraggy", "standard_foil"), (95, "Zorua", "standard_foil"), (96, "Zoroark", "standard_foil"),
    (97, "Deino", "standard_foil"), (98, "Zweilous", "standard_foil"), (99, "Hydreigon", "rare"),
    (100, "Yveltal", "rare"), (101, "Galarian Meowth", "standard_foil"), (102, "Jirachi ex", "double_rare"),
    (103, "Dialga", "rare"), (104, "Ferrothorn", "standard_foil"), (105, "Solgaleo", "rare"),
    (106, "Zacian", "rare"), (107, "Zamazenta", "rare"), (108, "Gholdengo", "standard_foil"),
    (109, "Salamence ex", "double_rare"), (110, "Jangmo-o", "standard_foil"), (111, "Hakamo-o", "standard_foil"),
    (112, "Kommo-o", "standard_foil"), (113, "Meowth", "standard_foil"), (114, "Kangaskhan", "standard_foil"),
    (115, "Ditto", "standard_foil"), (116, "Eevee", "standard_foil"), (117, "Eevee", "standard_foil"),
    (118, "Eevee", "standard_foil"), (119, "Snorlax", "standard_foil"), (120, "Igglybuff", "standard_foil"),
    (121, "Lugia", "rare"), (122, "Hisuian Zorua", "standard_foil"), (123, "Hisuian Zoroark", "standard_foil"),
    (124, "Minior", "standard_foil"), (125, "Maushold", "standard_foil"), (126, "Poké Pad", "standard_foil"),
    (127, "Switch", "standard_foil"), (128, "Ultra Ball", "standard_foil"), (129, "Alolan Exeggutor", "illustration_rare"),
    (130, "Moltres", "illustration_rare"), (131, "Lapras", "illustration_rare"), (132, "Articuno", "illustration_rare"),
    (133, "Zapdos", "illustration_rare"), (134, "Toxtricity", "illustration_rare"), (135, "Morpeko", "illustration_rare"),
    (136, "Drifloon", "illustration_rare"), (137, "Chandelure", "illustration_rare"), (138, "Lycanroc", "illustration_rare"),
    (139, "Alolan Meowth", "illustration_rare"), (140, "Scraggy", "illustration_rare"), (141, "Galarian Meowth", "illustration_rare"),
    (142, "Gholdengo", "illustration_rare"), (143, "Kommo-o", "illustration_rare"), (144, "Meowth", "illustration_rare"),
    (145, "Hisuian Zorua", "illustration_rare"), (146, "Maushold", "illustration_rare"), (147, "Fuecoco ex", "special_illustration_rare"),
    (148, "Greninja ex", "special_illustration_rare"), (149, "Pikachu ex", "special_illustration_rare"),
    (150, "Pikachu ex", "special_illustration_rare"), (151, "Mewtwo ex", "special_illustration_rare"),
    (152, "Mew ex", "special_illustration_rare"), (153, "Sylveon ex", "special_illustration_rare"),
    (154, "Gengar ex", "special_illustration_rare"), (155, "Jirachi ex", "special_illustration_rare"),
    (156, "Salamence ex", "special_illustration_rare"), (157, "Mewtwo ex", "futuristic_rare"),
    (158, "Mew ex", "futuristic_rare"),
]

classic_data = [
    (58, "Pikachu"), (4, "Charizard"), (18, "Misty"), (69, "Erika's Jigglypuff"), (25, "Sneasel"),
    (106, "Shining Celebi"), (149, "Lugia"), (5, "Delcatty"), (19, "Dark Tyranitar"), (108, "Scizor ex"),
    (11, "Metagross δ"), (106, "Palkia LV.X"), (43, "Uxie"), (47, "Crobat 🔣"), (94, "Gengar"),
    (99, "Darkrai & Cresselia LEGEND"), (100, "Darkrai & Cresselia LEGEND"), (101, "N"), (85, "Rayquaza-EX"),
    (105, "Genesect-EX"), (106, "M Gardevoir-EX"), (41, "Greninja BREAK"), (89, "Solgaleo-GX"), (57, "Buzzwole-GX"),
    (33, "Pikachu & Zekrom-GX"), (138, "Zacian V"), (50, "Raikou"), (114, "Mew VMAX"), (123, "Arceus VSTAR"), (203, "Magikarp"),
]

cards = []

for num, name, rarity_key in card_data:
    num_str = f"{num:03d}"
    set_nr = f"{num_str}/128"
    rarity_title = rarity_key.replace("_", " ").title()
    search_query = f"{name.lower()} (30C {set_nr}) cardmarket"
    google_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"

    cards.append({
        "_id": f"30th_{num_str}",
        "Äger": False,
        "Namn": name,
        "Setnr.": set_nr,
        "Symbol": symbol_map[rarity_key],
        "Sällsynthet": rarity_title,
        "Köpt för (EUR)": 0.0,
        "Köpt för (SEK)": 0.0,
        "Värde (EUR)": 0.0,
        "Värde (SEK)": 0.0,
        "Google Sök": google_url
    })

for num, name in classic_data:
    set_nr = f"CC #{num}"
    search_query = f"{name.lower()} (30C {set_nr}) cardmarket"
    google_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"

    cards.append({
        "_id": f"30th_CC_{num}_{name.replace(' ', '_')}",
        "Äger": False,
        "Namn": name,
        "Setnr.": set_nr,
        "Symbol": symbol_map["classic_collection"],
        "Sällsynthet": "Classic Collection",
        "Köpt för (EUR)": 0.0,
        "Köpt för (SEK)": 0.0,
        "Värde (EUR)": 0.0,
        "Värde (SEK)": 0.0,
        "Google Sök": google_url
    })

with open("pokemon_30th_anniversary.json", "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=2)

print("Klar! Skapade pokemon_30th_anniversary.json med både EUR och SEK-kolumner!")
