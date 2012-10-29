# -*- coding: utf-8 -*-
# This file is part of newhackers.
# Copyright (c) 2012 Ionuț Arțăriși

# cuZmeură is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.

# cuZmeură is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with cuZmeură. If not, see <http://www.gnu.org/licenses/>.

import logging

from newhackers.utils import make_json_app


logging.basicConfig(filename="/tmp/newhackers.log", level=logging.INFO)

app = make_json_app(__name__)

import newhackers.views


if __name__ == "__main__":
    app.run(debug=True)
