from config.env import get_env

def main():
    print("APP:", get_env("APP_NAME"))
    print('Mode:', get_env("TRADING_MODE"))
    print('Symbol:', get_env('DEFAULT_SYMBOL'))

if __name__ == '__main__':
    main()