
def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

total_sum = 0
for number in range(1, 50001):
    if is_prime(number):
        total_sum += number

print(total_sum)
