#pragma once

#include "mesh.hpp"

#include <string>

struct WatertightResult {
    bool pass = false;
    std::string message;
};

// First failing rule wins. See mvp/solid-check.md for the rule order.
WatertightResult check_watertight(const MeshSolid& mesh);
