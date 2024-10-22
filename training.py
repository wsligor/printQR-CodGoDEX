import config


def checking_party_input():
    return config.CHECKING_PARTY_INPUT and config.ACCESS_PRINTER == 'NETWORK'


if __name__ == '__main__':
    print(config.VERSION)
