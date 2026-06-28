import json
import datetime
import random

def generate_records():
    start_date = datetime.date(2026, 1, 1)
    end_date = datetime.date(2026, 7, 31)
    current_date = start_date
    
    records = []
    
    # 사실적인 계절별 날씨 생성을 위한 헬퍼
    while current_date <= end_date:
        month = current_date.month
        day = current_date.day
        date_str = current_date.strftime("%Y-%m-%d")
        
        # 기본값 설정
        min_temp = 0.0
        max_temp = 0.0
        condition = "맑음"
        precipitation_probability = 10
        precipitation = 0.0
        snowfall = 0.0
        wind_speed = 2.0
        wind_direction = "남풍"
        
        # 1월 ~ 2월: 겨울 (눈 가능성, 낮은 기온)
        if month in [1, 2]:
            min_temp = round(random.uniform(-12.0, -2.0), 1)
            max_temp = round(min_temp + random.uniform(3.0, 8.0), 1)
            wind_direction = random.choice(["북서풍", "북풍", "북동풍", "서풍"])
            wind_speed = round(random.uniform(2.0, 6.0), 1)
            
            # 눈/비 확률 시뮬레이션
            rand_val = random.random()
            if rand_val < 0.2:  # 눈 오는 날
                condition = "눈"
                precipitation_probability = random.randint(60, 95)
                snowfall = round(random.uniform(0.5, 6.0), 1)
                precipitation = round(snowfall * random.uniform(0.5, 0.9), 1)
            elif rand_val < 0.35:  # 흐림/구름많음
                condition = random.choice(["흐림", "구름많음"])
                precipitation_probability = random.randint(20, 50)
            else:
                condition = "맑음"
                precipitation_probability = random.randint(5, 15)
                
        # 3월 ~ 4월: 봄 (따뜻해지는 기온, 봄비)
        elif month in [3, 4]:
            min_temp = round(random.uniform(-1.0, 7.0), 1)
            max_temp = round(min_temp + random.uniform(7.0, 13.0), 1)
            wind_direction = random.choice(["서풍", "남서풍", "동풍", "북서풍"])
            wind_speed = round(random.uniform(1.5, 4.5), 1)
            
            rand_val = random.random()
            if rand_val < 0.15:  # 봄비
                condition = "비"
                precipitation_probability = random.randint(50, 80)
                precipitation = round(random.uniform(1.0, 10.0), 1)
            elif rand_val < 0.4:
                condition = random.choice(["흐림", "구름많음"])
                precipitation_probability = random.randint(20, 45)
            else:
                condition = "맑음"
                precipitation_probability = random.randint(5, 15)
                
        # 5월 ~ 6월: 늦봄/초여름 (비 확률 증가, 장마 시작)
        elif month in [5, 6]:
            min_temp = round(random.uniform(11.0, 19.0), 1)
            max_temp = round(min_temp + random.uniform(6.0, 12.0), 1)
            wind_direction = random.choice(["남풍", "남서풍", "남동풍", "서풍"])
            wind_speed = round(random.uniform(1.0, 3.5), 1)
            
            rand_val = random.random()
            # 6월 중순 이후는 장마철 강수 확률 업
            is_monsoon = (month == 6 and day >= 15)
            rain_chance = 0.45 if is_monsoon else 0.2
            
            if rand_val < rain_chance:
                condition = "비"
                precipitation_probability = random.randint(70, 95)
                precipitation = round(random.uniform(5.0, 35.0), 1)
            elif rand_val < 0.6:
                condition = random.choice(["흐림", "구름많음"])
                precipitation_probability = random.randint(30, 60)
            else:
                condition = "맑음"
                precipitation_probability = random.randint(10, 20)
                
        # 7월: 한여름 (고온다습, 폭우/장마)
        elif month == 7:
            min_temp = round(random.uniform(20.0, 24.5), 1)
            max_temp = round(min_temp + random.uniform(5.0, 11.0), 1)
            wind_direction = random.choice(["남풍", "남서풍", "남동풍"])
            wind_speed = round(random.uniform(1.2, 4.0), 1)
            
            rand_val = random.random()
            if rand_val < 0.35:  # 잦은 소나기/장마 폭우
                condition = "비"
                precipitation_probability = random.randint(60, 95)
                precipitation = round(random.uniform(8.0, 60.0), 1)
            elif rand_val < 0.65:
                condition = random.choice(["흐림", "구름많음"])
                precipitation_probability = random.randint(30, 55)
            else:
                condition = "맑음"
                precipitation_probability = random.randint(10, 25)
                
        records.append({
            "date": date_str,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "condition": condition,
            "precipitation_probability": precipitation_probability,
            "precipitation": precipitation,
            "snowfall": snowfall,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction
        })
        
        current_date += datetime.timedelta(days=1)
        
    return records

if __name__ == "__main__":
    records = generate_records()
    payload = {
        "table_name": "weather_data",
        "records": records
    }
    
    output_path = "/Users/wonyoung/workspace/react_agent/scratch/weather_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    print(f"성공적으로 2026년 1월 ~ 7월까지의 {len(records)}일간의 사실적인 일별 날씨 데이터 JSON을 저장했습니다.")
