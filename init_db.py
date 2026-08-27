from app.database import engine, Base
from app import models

def main():
    Base.metadata.create_all(bind=engine)
    print("The user table has been created successfully!")

if __name__ == "__main__":
    main()
