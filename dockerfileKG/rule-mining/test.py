from prefixspan import PrefixSpan

db = [
    ["a", "b", "c"],
    ["a", "c", "d", "e"],
    ["a", "b", "d"],
    ["b", "c", "e"],
]

ps = PrefixSpan(db)

print(ps.frequent(2))