import argparse
import threading
import time


N = 5
MEALS = 20


def run(mode):
    forks = [threading.Lock() for _ in range(N)]
    meals = [0] * N

    # В режиме deadlock все философы должны взять по одной вилке.
    barrier = threading.Barrier(N) if mode == "deadlock" else None

    # Разрешаем максимум N-1 философам одновременно пытаться
    # получить вилки.
    room = threading.Semaphore(N - 1)

    def philosopher(i):
        left = i
        right = (i + 1) % N

        for _ in range(MEALS):
            if mode == "deadlock":
                first, second = left, right
            else:
                first, second = sorted((left, right))

            if mode == "limited":
                room.acquire()

            try:
                forks[first].acquire()

                try:
                    if mode == "deadlock":
                        # Все философы берут по одной вилке,
                        # прежде чем пытаться взять вторую.
                        barrier.wait()

                    forks[second].acquire()

                    try:
                        meals[i] += 1
                        time.sleep(0.001)
                    finally:
                        forks[second].release()

                finally:
                    forks[first].release()

            finally:
                if mode == "limited":
                    room.release()

    threads = [
        threading.Thread(target=philosopher, args=(i,), daemon=True)
        for i in range(N)
    ]

    for thread in threads:
        thread.start()

    timeout = 2 if mode == "deadlock" else 10

    for thread in threads:
        thread.join(timeout=timeout)

    print(f"\nРежим: {mode}")

    if any(thread.is_alive() for thread in threads):
        print("Обнаружено зависание: не все философы завершили работу.")
    else:
        print("Все философы завершили работу.")

    for i, count in enumerate(meals):
        print(f"Философ {i}: поел {count} раз")

    print("Всего приёмов пищи:", sum(meals))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["deadlock", "ordered", "limited"],
        required=True,
        help="Сценарий: deadlock, ordered или limited"
    )

    args = parser.parse_args()
    run(args.mode)

