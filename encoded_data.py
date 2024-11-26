import base64


def extract_ela_rht_data(data):
    extracted_data = extract_data(data, [6, 12, 3, 1, 2], [False, False, False, True, True], [False, False, False, False, True])
    return extracted_data[0], extracted_data[1] / 100


def extract_data(data, sizes, to_return, is_reversed):
    hex_data = base64.b64decode(data).hex()
    extracted_data = []
    for i in range(len(sizes)):
        section, hex_data = hex_data[:sizes[i] * 2], hex_data[sizes[i] * 2:]
        if not to_return[i]:
            continue
        if is_reversed[i]:
            section = "".join(list(section[0 + i:2 + i] for i in range(0, len(section), 2))[::-1])
        extracted_data.append(int(section, 16))
    return extracted_data
