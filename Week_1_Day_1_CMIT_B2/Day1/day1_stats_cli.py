def mean(numbers):
    if numbers:
        return sum(numbers) / len(numbers)

def median(numbers):
    if numbers:
        sorted_numbers = sorted(numbers)
        n = len(sorted_numbers)
        mid = n //2
        if n % 2 == 0:
            return (sorted_numbers[mid - 1] + sorted_numbers[mid]) / 2
        else:   
            return sorted_numbers[mid]
        
def mode(numbers):
    frequency = {}

    for number in numbers:
        if number in frequency:
            frequency[number] += 1
        else:
            frequency[number] = 1

    highest_frequency = max(frequency.values())

    mode = []

    for number, count in frequency.items():
        if count == highest_frequency:
            mode.append(number)

    return mode


def main():
    numbers = input("Enter a list of numbers separated by spaces: ")
    
    try: 
        numbers = [float(num) for num in numbers.split()]

        print("Answers:")
        print(f"Mean   : {mean(numbers)}")
        print(f"Median : {median(numbers)}")
        print(f"Mode   : {mode(numbers)}")
        print(f"Minimum: {min(numbers)}")
        print(f"Maximum: {max(numbers)}")

    except ValueError:
        print("Invalid input. Please enter a list of numbers separated by spaces.")
    
if __name__ == "__main__":
    main()

