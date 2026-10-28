import threading


class DeadlockError(RuntimeError):
    pass


class LockTracker:
    def __init__(self):
        self.guard = threading.Lock()
        self.owners = {}
        self.waiting = {}
        self.names = {}

    def register(self, lock, name):
        with self.guard:
            self.names[lock] = name

    def acquire(self, lock):
        tid = threading.get_ident()

        with self.guard:
            owner = self.owners.get(lock)

            if owner == tid:
                raise RuntimeError("Повторный захват обычного Lock запрещён.")

            if owner is not None:
                self.waiting[tid] = owner

                current = owner
                visited = set()

                while current in self.waiting:
                    if current == tid:
                        self.waiting.pop(tid, None)
                        raise DeadlockError(
                            f"Обнаружен deadlock: поток {tid} "
                            f"не может безопасно захватить {self.names[lock]}."
                        )

                    if current in visited:
                        break

                    visited.add(current)
                    current = self.waiting[current]

                if current == tid:
                    self.waiting.pop(tid, None)
                    raise DeadlockError("Обнаружен цикл ожидания.")

        try:
            lock.acquire()
        except BaseException:
            with self.guard:
                self.waiting.pop(tid, None)
            raise

        with self.guard:
            self.waiting.pop(tid, None)
            self.owners[lock] = tid

    def release(self, lock):
        tid = threading.get_ident()

        with self.guard:
            if self.owners.get(lock) != tid:
                raise RuntimeError("Текущий поток не владеет этой блокировкой.")

            del self.owners[lock]
            lock.release()


class TrackedLock:
    def __init__(self, tracker, name):
        self.lock = threading.Lock()
        self.tracker = tracker
        self.name = name
        self.tracker.register(self.lock, name)

    def acquire(self):
        self.tracker.acquire(self.lock)

    def release(self):
        self.tracker.release(self.lock)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
        return False

