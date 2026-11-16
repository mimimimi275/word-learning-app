from datetime import datetime, timedelta

def calculate_next_review(quality, interval, ease, stage):
    if quality < 2:
        new_stage = 0
        new_interval = 1
    else:
        ease = ease + (0.1 - (3 - quality) * (0.08 + (3 - quality)*0.02))
        if ease < 1.3:
            ease = 1.3
        new_stage = stage + 1
        if new_stage == 1:
            new_interval = 1
        elif new_stage == 2:
            new_interval = 6
        else:
            new_interval = round(interval * ease)
    next_day = (datetime.now().date() + timedelta(days=new_interval)).isoformat()
    return next_day, new_interval, ease, new_stage
