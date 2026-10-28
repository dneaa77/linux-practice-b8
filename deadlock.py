import threading
from tracked_lock import LockTracker, TrackedLock, DeadlockError


tracker = LockTracker()

lock_a = TrackedLock(tracker, "Lock A")
lock_b = TrackedLock(tracker, "Lock B")

barrier = threading.Barrier(2)


def worker_a():
    try:
        with lock_a:
            print("Поток A захватил Lock A")
            barrier.wait()
            print("Поток A пытается захватить Lock B")

            with lock_b:
                print("Поток A захватил Lock B")

    except DeadlockError as error:
        print("Поток A:", error)


def worker_b():
    try:
        with lock_b:
            print("Поток B захватил Lock B")
            barrier.wait()
            print("Поток B пытается захватить Lock A")

            with lock_a:
                print("Поток B захватил Lock A")

    except DeadlockError as error:
        print("Поток B:", error)


thread_a = threading.Thread(target=worker_a)
thread_b = threading.Thread(target=worker_b)

thread_a.start()
thread_b.start()

thread_a.join(timeout=3)
thread_b.join(timeout=3)

if thread_a.is_alive() or thread_b.is_alive():
    print("ОШИБКА: один из потоков завис.")
else:
    print("Проверка завершена: потоки не зависли.")
