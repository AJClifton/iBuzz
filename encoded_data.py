import base64


def extract_ela_rht_data(data):
    extracted_data = extract_data(data, [6, 12, 3, 1, 2], [False, False, False, True, True],
                                  is_reversed=[False, False, False, False, True], hex_string_check="502052485420393033434344")
    return extracted_data[0], extracted_data[1] / 100

def extract_custom_data(data):
    extracted_data = extract_data(data, [1, 2, 2, 18], [False, True, False, False])
    return extracted_data[0] / 10,


def extract_data(data, sizes, to_return, is_reversed=None, hex_string_check=None):
    if is_reversed is None:
        is_reversed = [False for s in sizes]
    print('base64: ' + data)
    hex_data = base64.b64decode(data).hex()
    if hex_string_check is not None:
        if hex_string_check not in hex_data:
            raise Exception(ValueError)
    print('hex: ' + hex_data)
    extracted_data = []
    try:
        print('ASCII: ' + bytearray.fromhex(hex_data[20:28]).decode('utf-8'))
    except Exception as e:
        try:
            print('ASCII: ' + bytearray.fromhex(hex_data[:8]).decode('utf-8'))
        except Exception as e:
            None
    for i in range(len(sizes)):
        section, hex_data = hex_data[:sizes[i] * 2], hex_data[sizes[i] * 2:]
        if not to_return[i]:
            continue
        if is_reversed[i]:
            section = "".join(list(section[0 + i:2 + i] for i in range(0, len(section), 2))[::-1])
        extracted_data.append(int(section, 16))
    print('ELA Extracted: ' + str(extracted_data))
    return extracted_data
