import base64


def extract_outside_humidity_and_temperature(data):
    """Return a tuple containing outside humidity and outside temperature.

    Calls extract_data() with predefined values for the ELA RHT tag.
    :param str data: base64 encoded string
    :return: humidity and temperature
    :raises ValueError: if data doesn't include the tag name in hex form"""
    # hex_string_check contains the hex representation of the tag name "P RHT 903CCD" which is always included
    # Format is 6 (UID), 12 ("P RHT 903CCD"), 3 (blank), 1 (humidity), 2 (reversed temperature)
    extracted_data = extract_data(data,
                                  [6, 12, 3, 1, 2],
                                  [False, False, False, True, True],
                                  is_reversed=[False, False, False, False, True],
                                  hex_string_check="502052485420393033434344")
    return extracted_data[0], extracted_data[1] / 100


def extract_custom_data(data):
    # name(position,size)
    # hive_number(0,1), temperature_1(1,2), temperature_2(2,2), temperature_3(3,2), humidity(4,1), weight(5,2), accelerometer(6,1), bees_out(7,1), bees_in(8,1), frequency(9,3)
    extracted_data = extract_data(data, [1, 2, 2, 2, 1, 2, 1, 1, 1, 3, 7], [True, True, True, True, True, True, True, True, True, True, False])
    print(extracted_data[0], extracted_data[1] / 10, extracted_data[2] / 10, extracted_data[3] / 10, extracted_data[4], extracted_data[5], extracted_data[6], extracted_data[7], extracted_data[8], extracted_data[9])
    return extracted_data[0], extracted_data[1] / 10, extracted_data[2] / 10, extracted_data[3] / 10, extracted_data[4], extracted_data[5]/10, extracted_data[6], extracted_data[7], extracted_data[8], extracted_data[9]


def extract_data(data, sizes, to_return, is_reversed=None, hex_string_check=None):
    """Return an array of decimal numbers.

    Converts the given base64 string to hex, splits it up based on sizes, converts those sections into decimal, and returns those marked to be returned.
    :param str data: base64 encoded string
    :param list(int) sizes: Integer array of how many bytes of hex each section comprises
    :param list(boolean) to_return: Boolean array determining which sections will be included in the returned array
    :param list(boolean) is_reversed: Boolean array determining if the respective section's hex needs to be reversed before being converted to decimal
    :param str hex_string_check: If this isn't None, a ValueError will be returned if the hex doesn't include this
    :return: Array of decimal values
    :raises ValueError: if hex_string_check isn't featured in the data"""
    if is_reversed is None:
        is_reversed = [False for s in sizes]
    hex_data = base64.b64decode(data).hex()
    if hex_string_check is not None:
        if hex_string_check not in hex_data:
            raise ValueError
    extracted_data = []
    for i in range(len(sizes)):
        section, hex_data = hex_data[:sizes[i] * 2], hex_data[sizes[i] * 2:]
        if not to_return[i]:
            continue
        if is_reversed[i]:
            section = "".join(list(section[0 + i:2 + i] for i in range(0, len(section), 2))[::-1])
        extracted_data.append(int(section, 16))
    return extracted_data
