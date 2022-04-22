data = [{"id": 123}, {"id": 321}]

ids = [d["id"] for d in data]
print(ids)
ids += [123, 123]
print(ids)
