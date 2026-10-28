from collections import defaultdict
import json
import sys


def find_cycle(graph):
    color = {}
    parent = {}

    for start in graph:
        if color.get(start, 0) != 0:
            continue

        stack = [(start, iter(graph[start]))]
        color[start] = 1

        while stack:
            node, neighbors = stack[-1]

            try:
                nxt = next(neighbors)
            except StopIteration:
                color[node] = 2
                stack.pop()
                continue

            if color.get(nxt, 0) == 0:
                parent[nxt] = node
                color[nxt] = 1
                stack.append((nxt, iter(graph[nxt])))

            elif color.get(nxt) == 1:
                cycle = [node]

                while cycle[-1] != nxt:
                    cycle.append(parent[cycle[-1]])

                cycle.reverse()
                cycle.append(nxt)
                return cycle

    return None


def detect(filename):
    with open(filename, "r", encoding="utf-8") as file:
        events = json.load(file)

    owner = {}
    waiting = {}
    graph = defaultdict(set)
    processes = set()

    for event in events:
        action = event["event"]
        pid = event["pid"]
        resource = event["resource"]

        processes.add(pid)
        graph[pid]

        if action == "acquire":
            if resource in owner:
                raise ValueError(
                    f"Ресурс {resource} уже занят процессом {owner[resource]}."
                )
            owner[resource] = pid

        elif action == "wait":
            waiting[pid] = resource

        elif action == "release":
            if owner.get(resource) != pid:
                raise ValueError(
                    f"Процесс {pid} не владеет ресурсом {resource}."
                )
            del owner[resource]

        else:
            raise ValueError(f"Неизвестное событие: {action}")

        graph = defaultdict(set, {p: set() for p in processes})

        for waiter, wanted_resource in waiting.items():
            if wanted_resource in owner:
                holder = owner[wanted_resource]
                if holder != waiter:
                    graph[waiter].add(holder)

    cycle = find_cycle(graph)

    if cycle:
        participants = cycle[:-1]
        print("Обнаружена взаимоблокировка!")
        print("Цикл:", " -> ".join(participants + [participants[0]]))
        print("Участники:", ", ".join(participants))
    else:
        print("Взаимоблокировка не обнаружена.")

    print("Граф ожидания:")
    for pid in sorted(graph):
        print(f"{pid} -> {sorted(graph[pid])}")


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "data/events.json"

    try:
        detect(filename)
    except (ValueError, KeyError, json.JSONDecodeError, OSError) as error:
        print("Ошибка:", error)

