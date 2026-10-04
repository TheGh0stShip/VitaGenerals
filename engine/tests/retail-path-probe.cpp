// SPDX-License-Identifier: GPL-3.0-or-later
#include "GeneralsRetailPath.h"

#include <cassert>
#include <string>

int main()
{
    std::string path;
    assert(BuildGeneralsRetailPath("Data\\English/Movies/EA_LOGO.BIK", &path));
    assert(path == "test-root/Data/English/Movies/EA_LOGO.BIK");
    assert(!BuildGeneralsRetailPath("../Data/Movies/a.bik", &path));
    assert(!BuildGeneralsRetailPath("Data//Movies/a.bik", &path));
    assert(!BuildGeneralsRetailPath("ux0:data/a.bik", &path));
    assert(!BuildGeneralsRetailPath("/Data/Movies/a.bik", &path));
    return 0;
}
