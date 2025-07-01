import random
import json

first_names = ["John", "Jane", "Alice", "Bob", "Emily", "Michael", "Sarah", "David", "Jessica", "William"]
last_names = ["Doe", "Smith", "Johnson", "Brown", "Davis", "Wilson", "Martinez", "Garcia", "Lee", "Taylor"]

cities = ["Springfield", "Lakeside", "Riverside", "Hillsboro", "Salem", "Portland", "Denver", "Austin", "Boston"]
countries = ["USA", "Canada", "UK", "Australia", "Germany", "France"]
streets = ["Maple St", "Oak Ave", "Pine Rd", "Cedar Ln", "Birch Dr", "Elm Blvd"]
roles = ["user"]

bios = [
    "Loves hiking and exploring new places.",
    "Passionate about books and coffee.",
    "Enjoys photography and traveling.",
    "Tech enthusiast and fitness lover.",
    "Always looking for the next adventure.",
    "Coffee addict and bookworm.",
    "Traveler by heart, coder by day.",
    "Loves nature, dogs, and good food.",
    "Fitness freak and tech geek.",
    "Dreams big and works hard."
]

def generate_fullname():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_username(fullname):
    parts = fullname.split()
    short = parts[0][:4]
    suffix = random.choice(['X', 'Y', 'Z']) + str(random.randint(100, 999))
    return short + suffix

def generate_email(fullname):
    domains = ["example.com", "gmail.com"]
    base = fullname.replace(" ", "")
    if random.random() > 0.5:
        return f"{base}@{random.choice(domains)}"
    else:
        extra = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=3))
        return f"{base}{extra}@gmail.com"

def generate_password(fullname):
    return fullname[:4] + "@1234"

def generate_address():
    street_num = random.randint(100, 999)
    city = random.choice(cities)
    country = random.choice(countries)
    pincode = random.randint(10000, 99999)
    address = f"{street_num} {random.choice(streets)}"
    return address, city, country, pincode

users = []
for i in range(100):
    fullname = generate_fullname()
    user = {
        "email": generate_email(fullname),
        "username": generate_username(fullname),
        "password": generate_password(fullname),
        "fullName": fullname,
        "bio": random.choice(bios),
        "roles": ["user"],
        "address": generate_address()[0],
        "city": generate_address()[1],
        "country": generate_address()[2],
        "pincode": generate_address()[3]
    }
    users.append(user)

with open("users.json", "w") as f:
    json.dump(users, f, indent=2)

print("Generated 100 users in 'users.json'")