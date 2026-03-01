while True:
    name = input("Enter your name: ")
    if name.strip() == "":
        print("Рядок не може бути пустим")
    else:
        print(f"Hello, {name}!")
        break

print("Hello World!")