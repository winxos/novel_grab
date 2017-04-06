import json

novel_sites_config = None
try:
    with open('grab_config.json', 'r', encoding='utf-8') as fg:
        novel_sites_config = json.load(fg)
        # print("[debug] config loaded.")
except IOError as e:
    print("[error] %s" % e)
    exit()
print(novel_sites_config)
print(type(novel_sites_config))
print(novel_sites_config["sites"][0])
print(type(novel_sites_config["sites"][0]))
a = [1, 2, 3]
b = [3, 5, 6]
c = zip(a, b)
print(c)
print(type(c))
for i, c in enumerate(c):
    print(i)
