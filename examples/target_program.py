def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def normalize(values: list[int]) -> list[float]:
    total = sum(values)
    if total == 0:
        raise ValueError("total cannot be zero")
    return [value / total for value in values]


def main() -> None:
    values = [fibonacci(4), fibonacci(3), fibonacci(2)]
    print("normalized", normalize(values))


if __name__ == "__main__":
    main()
