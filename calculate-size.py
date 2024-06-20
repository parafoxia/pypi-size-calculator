# Copyright (c) 2024, Ethan Henderson
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
import sys
from typing import Any

import requests
from tabulate import tabulate

URL = "https://pypi.org/pypi/%s/json"
REQUIREMENT_PATTERN = re.compile(
    r"""
    (?P<package>[A-Za-z0-9._-]+)?  # The name of the package.
    (?P<version>[<>~=0-9,.]+)?     # The version constraints for the package.
    (?P<markers>.*)?               # Any markers the requirement has.
    """,
    re.VERBOSE,
)


class CalculationFailed(Exception):
    def __init__(self, name: str, data: dict[str, Any]) -> None:
        super().__init__(f"Failed to calculate size of {name}\n\nData = {data}")


def calculate_size(name: str) -> None:
    if name in packages:
        return

    with requests.get(URL % name) as resp:
        data = resp.json()

    try:
        latest = data["info"]["version"]
        packages[name] = data["releases"][latest][0]["size"]
    except KeyError as exc:
        raise CalculationFailed(name, data) from exc

    for dep in data["info"]["requires_dist"] or []:
        if not (match := REQUIREMENT_PATTERN.match(dep)):
            continue

        attrs = match.groupdict()
        if "extra" in attrs["markers"]:
            continue

        calculate_size(attrs["package"])


if __name__ == "__main__":
    table = []

    for arg in sys.argv[1:]:
        print(f"Calculating size of {arg}...{' ' * 20}", end="\r")
        packages: dict[str, int] = {}
        name = arg.lower()
        calculate_size(name)
        table.append([name, sum(packages.values()) / 1024**2, len(packages) - 1])

    print(
        tabulate(
            table,
            headers=["Name", "Size (MiB)", "Deps."],
            floatfmt=",.3f",
        )
    )
