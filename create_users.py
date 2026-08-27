from app.database import SessionLocal
from app.models import User
from faker import Faker
import random
from sqlalchemy import text

fake = Faker('zh_CN')
db = SessionLocal()

db.execute(text("TRUNCATE TABLE user"))
db.commit()

users = []
for i in range(50):
    users.append(User(
        username = fake.user_name() + str(random.randint(10, 99)),
        email = fake.email(),
        password = fake.password(length=10),
        nickname = fake.name(),
        age = random.randint(18, 45),
        gender = random.choice(['male', 'female', 'other'])
    ))

db.add_all(users)
db.commit()
db.close()
print("Successfully inserted 50 random users!")
