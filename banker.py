import json
import sys


def calculate_need(maximum, allocation):
    return [
        [maximum[i][j] - allocation[i][j]
         for j in range(len(maximum[i]))]
        for i in range(len(maximum))
    ]


def safety_check(available, allocation, need):
    work = available[:]
    finished = [False] * len(allocation)
    sequence = []

    while True:
        found = False

        for i in range(len(allocation)):
            if finished[i]:
                continue

            if all(need[i][j] <= work[j] for j in range(len(work))):
                work = [
                    work[j] + allocation[i][j]
                    for j in range(len(work))
                ]
                finished[i] = True
                sequence.append(i)
                found = True

        if not found:
            break

    return all(finished), sequence


def load_data(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    available = data["available"]
    allocation = data["allocation"]
    maximum = data["maximum"]

    if not allocation or len(allocation) != len(maximum):
        raise ValueError("Количество процессов в allocation и maximum не совпадает.")

    if not available or any(len(row) != len(available)
                            for row in allocation + maximum):
        raise ValueError("Размеры матриц или вектора ресурсов не совпадают.")

    if any(not isinstance(x, int) or x < 0 for x in available):
        raise ValueError("available должен содержать неотрицательные целые числа.")

    if any(not isinstance(x, int) or x < 0
           for row in allocation + maximum for x in row):
        raise ValueError("Матрицы должны содержать неотрицательные целые числа.")

    if any(allocation[i][j] > maximum[i][j]
           for i in range(len(allocation))
           for j in range(len(available))):
        raise ValueError("Выделено больше ресурсов, чем допускает maximum.")

    total = [
        available[j] + sum(allocation[i][j] for i in range(len(allocation)))
        for j in range(len(available))
    ]

    if any(maximum[i][j] > total[j]
           for i in range(len(maximum))
           for j in range(len(available))):
        raise ValueError("maximum превышает общее количество ресурсов.")

    return available, allocation, maximum


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "data/banker.json"

    available, allocation, maximum = load_data(filename)
    need = calculate_need(maximum, allocation)

    safe, sequence = safety_check(available, allocation, need)

    print("Начальное состояние:")
    print("Available:", available)
    print("Need:", need)
    print("Безопасно:", "да" if safe else "нет")

    if safe:
        print("Безопасная последовательность:",
              " -> ".join(f"P{i}" for i in sequence))
    else:
        print("Безопасная последовательность отсутствует.")

    print("\nВведите запросы ресурсов.")
    print("Формат: request PID r1 r2 ...")
    print("Пример: request 1 1 0 2")
    print("Для завершения введите exit.")

    while True:
        try:
            line = input("> ").strip()

            if line.lower() == "exit":
                break

            parts = line.split()

            if len(parts) != len(available) + 2 or parts[0] != "request":
                print("Ошибка формата. Используйте: request PID r1 r2 ...")
                continue

            pid = int(parts[1])
            request = [int(x) for x in parts[2:]]

            if not 0 <= pid < len(allocation):
                print("Ошибка: неизвестный PID.")
                continue

            if any(x < 0 for x in request):
                print("Ошибка: запрос не может содержать отрицательные числа.")
                continue

            if any(request[j] > need[pid][j]
                   for j in range(len(available))):
                print("ОТКАЗ: запрос превышает оставшуюся потребность.")
                continue

            if any(request[j] > available[j]
                   for j in range(len(available))):
                print("ОТКАЗ: сейчас недостаточно свободных ресурсов.")
                continue

            old_available = available[:]
            old_allocation = allocation[pid][:]
            old_need = need[pid][:]

            for j in range(len(available)):
                available[j] -= request[j]
                allocation[pid][j] += request[j]
                need[pid][j] -= request[j]

            safe, sequence = safety_check(available, allocation, need)

            if safe:
                print("ЗАПРОС ПРИНЯТ.")
                print("Безопасная последовательность:",
                      " -> ".join(f"P{i}" for i in sequence))
            else:
                available = old_available
                allocation[pid] = old_allocation
                need[pid] = old_need
                print("ЗАПРОС ОТКЛОНЁН: состояние небезопасно.")
                print("Выполнен откат изменений.")

            print("Available:", available)

        except ValueError as error:
            print("Ошибка ввода:", error)
        except EOFError:
            break


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, json.JSONDecodeError, OSError) as error:
        print("Ошибка загрузки данных:", error)
