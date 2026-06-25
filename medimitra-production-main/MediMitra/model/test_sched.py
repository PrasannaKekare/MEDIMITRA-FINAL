import schedule, time
def job():
    print("Triggered!")
schedule.every(1).seconds.do(job)
for _ in range(3):
    schedule.run_pending()
    time.sleep(1)
