from core import app

import commands.control  # noqa: F401
import commands.status   # noqa: F401
import commands.info     # noqa: F401
import commands.schedule # noqa: F401


def main():
    app()


if __name__ == "__main__":
    main()
