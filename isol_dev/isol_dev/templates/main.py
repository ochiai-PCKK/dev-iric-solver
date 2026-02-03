import sys


def main() -> int:
    print("isol-dev template: start")
    try:
        import iric
    except Exception as exc:
        print(f"failed to import iric: {exc}", file=sys.stderr)
        return 1

    print("iric imported successfully")
    print("isol-dev template: end")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
