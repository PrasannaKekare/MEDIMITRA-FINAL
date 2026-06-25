import schedule
try:
    schedule.every().day.at("22:46 ")
except Exception as e:
    print(repr(e))
