// SPDX-License-Identifier: GPL-3.0-or-later
#include "GeneralsRetailPath.h"

#ifndef GENERALS_RETAIL_ROOT
#error GENERALS_RETAIL_ROOT must name the user-supplied retail-data root
#endif

#include <vector>

bool BuildGeneralsRetailPath(const char *relativePath, std::string *result)
{
    if (relativePath == NULL || result == NULL || relativePath[0] == '\0') return false;
    std::string input(relativePath);
    if (input[0] == '/' || input[0] == '\\' || input.find(':') != std::string::npos)
        return false;

    std::vector<std::string> parts;
    std::string part;
    for (std::string::const_iterator it = input.begin(); it != input.end(); ++it) {
        const char value = *it == '\\' ? '/' : *it;
        if (value != '/') {
            part += value;
            continue;
        }
        if (part.empty() || part == "." || part == "..") return false;
        parts.push_back(part);
        part.clear();
    }
    if (part.empty() || part == "." || part == "..") return false;
    parts.push_back(part);

    std::string path(GENERALS_RETAIL_ROOT);
    while (!path.empty() && (path[path.size() - 1] == '/' || path[path.size() - 1] == '\\'))
        path.erase(path.size() - 1);
    if (path.empty()) return false;
    for (std::vector<std::string>::const_iterator it = parts.begin(); it != parts.end(); ++it) {
        path += '/';
        path += *it;
    }
    *result = path;
    return true;
}
